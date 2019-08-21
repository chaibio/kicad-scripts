#!/usr/bin/env python2

import sys
import os
import shutil
import re
import collections
import argparse
import subprocess
import pandas as pd
import pcbnew

__version__ = '0.1'

debug = False

defaults = {
        'output_dir' : 'OUTPUT_ASSEMBLY',
        }

config = {
        # Do Not Install Components
        'DNI_val_prefix' : ['DNI'],
        'DNI_ref_prefix' : ['FID', 'MH', 'TP', 'AL'],
        
        # Type Override (e.g. resistor installed on capacitor footprint)
        'TOV_value_prefix' : ['TOV'],
        
        # List of parts grouping criteria.
        # Criteria are tried in order and considered valid if all items in list are present for a specific part. 
        # The last criterion is used if all the other criteria are not valid
        'BOM_grouping' : [['manuf', 'manuf part'], ['description']],
        #'BOM_grouping' = [['manuf', 'manuf part','description']],
    }


def get_ref_prefix(row):
    return re.match('^(.*?)\d', row['reference']).group(1)


description_spec = {
        #prefix     columns to concatenate
        'R' : ['Resistor', 'value', 'footprint_short', 'type', 'tolerance', 'power', 'tc'] ,
        'C' : ['Capacitor', 'value', 'footprint_short', 'type', 'voltage', 'tolerance', 'power', 'esr', 'height'] ,
        'L' : ['Inductor', 'value', 'footprint_short'] ,
        'Y' : ['Crystal', 'frequency', 'tolerance', 'footprint_short'] ,
        }

    
def generate_description(row):
    """Create a description string using other fields in the row."""

    if pd.isnull(row['description']):
        ret = ''
    else:
        ret = row['description'] 

    ref_prefix = row['ref_prefix']

    if ref_prefix in description_spec.keys():
        ret = description_spec[ref_prefix][0]
        for col in description_spec[ref_prefix][1:]:
            if col in row.index:
                if not pd.isnull(row[col]):
                    ret += ' '
                    ret += row[col]
    return ret.strip()


def generate_merged_description(rows):
    """Create a description string for a merged line in the BOM
    
    If a target column contains more than one spec all specs will be listed
    
    """
    
    ref_prefix_set = set([row['ref_prefix'] for row in rows])
    if len(ref_prefix_set) > 1:
        raise Exception('Error: Cannot merge description for items with differents ref prefix: ' + ', '.join(ref_prefix_set) )

    ret = ''

    ref_prefix = list(ref_prefix_set)[0]
    if ref_prefix in description_spec.keys():
        ret = description_spec[ref_prefix][0]
        for col in description_spec[ref_prefix][1:]:
            col_list = []
            for row in rows:
                if col in row.index:
                    if not pd.isnull(row[col]):
                        col_list.append(row[col])
            col_list = list(set(col_list))
            if len(col_list) > 1:
                ret += ' (' + ' '.join(col_list) + ')'
            else:
                ret += ' ' + col_list[0]
    else:
        ret = rows[0]['description']

    return ret.strip()


fooprint_short_spec = {
        'R' : lambda x: x.split('_',1)[1],
        'C' : lambda x: x.split('_',1)[1],
        'CP' : lambda x: x.split('_',1)[1],
        'L' : lambda x: x.split('_',1)[1],
        'Y' : lambda x: x.split('_',1)[1],
        }


def get_footprint_short(row):
    """Generate a short footprint string.
    
    For example remove the prefix: R_0402 -> 0402 
    """

    ref_prefix = row['ref_prefix']
    if ref_prefix in fooprint_short_spec.keys():
        return fooprint_short_spec[ref_prefix](row['footprint'])


def split_part_numbers(row):
    """Split part number string into main and alternates."""
    
    part_no = ''
    part_no_alt = ''

    if row['manuf part'] != '':
        tmp = row['manuf part'].split(None, 1)
        part_no = tmp[0]
        if len(tmp) > 1:
            part_no_alt = tmp[1]
    row['manuf part'] = part_no
    row['manuf part alt'] = part_no_alt
            
    return row


def process_value(row):
    """Cleanup the value field."""

    if row['reference'].upper()[0] == 'R':
        # Append ohms for resistor values w/o multiplier
        if re.match('\d*\.*\d$', row['value']):
            row['value'] = row['value'] + ' ohms'

    return row

def populate_status(row):

    if row['ref_prefix'] in config['DNI_ref_prefix']:
        return False
    for dni_pre in config['DNI_val_prefix']:
        if row['value'].startswith(dni_pre):
            return False
    return True


def type_override_status(row):

    if row['value'].startswith(tuple(config['TOV_value_prefix'])):
        return True
    return False


def build_part_db(board, sch_bom_fname):

    sch_bom = pd.read_csv(sch_bom_fname, dtype=str)
    # remove white space from column names   
    sch_bom.columns = [c.strip().lower() for c in sch_bom.columns]


    # Extract part info from the board file
    pcb_modules = []
    aux_origin = board.GetAuxOrigin()
    #output += format_string%('#Ref', 'PosX', 'PosY', 'Rot', 'Side', 'Type', 'Val', 'Package')
    for m in board.GetModules():
        c = m.GetCenter()
        pos_x = c.x - aux_origin.x
        pos_y = aux_origin.y - c.y
        side = 'top'
        #change for kicad 4.x
        #package = m.GetFPID().GetFootprintName().c_str()
        #change for kicad 5.x
        footprint = m.GetFPID().GetLibItemName().c_str()
        m_type = 'SMT' 
	attr = m.GetAttributes()
        rotation_deg = m.GetOrientation()/10.0
        if attr == 0:
            m_type = 'TH'
        elif attr == 1:
            m_type = 'SMT'
        else:
            m_type = 'VIRT'
        	
        if m.IsFlipped():
            side = 'bottom'

        rect = None
        for pad in m.Pads():
            if rect == None:
                rect = pad.GetBoundingBox()
            else:
                rect.Merge(pad.GetBoundingBox())

        if rect != None:
            if rotation_deg in [90, 270]:
                size_x = rect.GetHeight()
                size_y = rect.GetWidth()
            else:
                size_x = rect.GetWidth()
                size_y = rect.GetHeight()

            bb_pos_x = (rect.GetX() + rect.GetWidth() / 2) - aux_origin.x
            bb_pos_y = aux_origin.y - (rect.GetY() + rect.GetHeight() / 2)

        pcb_modules.append([m.GetReference(), m.GetValue(), footprint, pos_x, pos_y, rotation_deg, size_x, size_y, bb_pos_x, bb_pos_y, side, m_type])

    pcb_modules = pd.DataFrame(pcb_modules)
    pcb_modules.columns = ['reference', 'value_pcb', 'footprint_pcb', 'pos_x', 'pos_y', 'rotation_deg', 'size_x', 'size_y', 'bbox_pos_x', 'bbox_pos_y' ,'side', 'footprint_type']

    parts = pd.merge(sch_bom, pcb_modules, how='outer', on='reference')

    # cleanup the dataframe
    parts.fillna('', inplace=True)
    parts = parts.reset_index(drop=True)

    parts = parts.apply(process_value, axis=1)
    parts['ref_prefix'] = parts.apply(get_ref_prefix, axis=1)
    
    # footprint processing 
    parts['footprint_lib'] = parts['footprint'].apply(lambda x: x.split(':',1)[0])
    parts['footprint'] = parts['footprint'].apply(lambda x: x.split(':',1)[1])
    parts['footprint_short'] = parts.apply(get_footprint_short, axis=1)

    #parts['description'] = parts.apply(generate_description, axis=1)

    parts['populate'] = parts.apply(populate_status, axis=1)
    parts['type_override'] = parts.apply(type_override_status, axis=1)

    parts = parts.apply(split_part_numbers, axis=1)

    # check for errors
    footprint_mismatch = parts[(parts.footprint_pcb != parts.footprint) & (parts.footprint_pcb != '')]
    for index, row in footprint_mismatch.iterrows():
        raise Exception('Footprint mismatch between schematic and layout for component %s: %s <-> %s'%(row['reference'], row['footprint'], row['footprint_pcb']))

    installed_parts = parts[(parts['populate'] == True)]

    missing_manuf = installed_parts[installed_parts.manuf == '']
    for index, row in missing_manuf.iterrows():
        print('Missing "manuf" field for component %s'%(row['reference']))

    missing_manuf_part = installed_parts[installed_parts['manuf part'] == '']
    for index, row in missing_manuf_part.iterrows():
        print('Missing "manuf part" field for component %s'%(row['reference']))

    return parts


def get_data_str(
        parts, 
        spec_dict, 
        separator = ',',
        populated_only = True,
        smt_only = True,
        file_doc = None, 
        header_on = True, 
        header_prefix = ''
        ):

    if populated_only:
        parts = parts[(parts['populate'] == True)]

    if smt_only:
        parts = parts[(parts['footprint_type'] == 'SMT') ]

    parts = parts.sort_values(['reference'])

    ret = ''
    if file_doc != None:
        ret += file_doc
        ret += '\n'
    
    if header_on:
        header_list = [v[0] for k,v in spec_dict.items()]
        ret += header_prefix + separator.join(header_list)
        ret += '\n'

    for index, row in parts.iterrows():
        ret += separator.join([v[1](row[k]) for k,v in spec_dict.items()])
        ret += '\n'
    return ret


def get_centroid_data(parts):
    
    spec_dict = collections.OrderedDict([
            # db_column        header       transform func
            ('reference',     ('RefDes',    lambda x: '"%s"'%x)), 
            ('side',          ('Layer',     lambda x: '"%s"'%x)), 
            ('pos_x',         ('LocationX', lambda x: '"%.4f"'%pcbnew.ToMM(x))), 
            ('pos_y',         ('LocationY', lambda x: '"%.4f"'%pcbnew.ToMM(x))), 
            ('rotation_deg',  ('Rotation',  lambda x: '"%.4f"'%x)), 
            ]) 

    return get_data_str(
            parts,
            spec_dict,
            separator = ',',
            populated_only = True,
            smt_only = True,
            file_doc = 'Units used = mm / deg',
            header_on = True
            )


def get_MacroFab_xyrs_data(parts, include_th = True):

    def footprint_type(t):
        if t.lower() == 'smt':
            return 1
        return 2

    def populate_val(i):
        if i:
            return 1
        return 0

    spec_dict = collections.OrderedDict([
            ('reference',        ('Designator', lambda x: '%s'%x)), 
            ('bbox_pos_x',       ('X-Loc',      lambda x: '%.2f'%pcbnew.ToMils(x))), 
            ('bbox_pos_y',       ('Y-Loc',      lambda x: '%.2f'%pcbnew.ToMils(x))), 
            ('rotation_deg',     ('Rotation',   lambda x: '%.0f'%x)), 
            ('side',             ('Side',       lambda x: '%s'%x)), 
            ('footprint_type',   ('Type',       lambda x: '%s'%footprint_type(x))), 
            ('size_x',           ('X-Size',     lambda x: '%.2f'%pcbnew.ToMils(x))), 
            ('size_y',           ('Y-Size',     lambda x: '%.2f'%pcbnew.ToMils(x))), 
            ('value',            ('Value',      lambda x: '%s'%x)), 
            ('footprint',        ('Footprint',  lambda x: '%s'%x)), 
            ('populate',         ('Populate',   lambda x: '%d'%populate_val(x))), 
            ('manuf part',       ('MPN',        lambda x: '%s'%x)), 
            ]) 

    return get_data_str(
            parts,
            spec_dict,
            separator = '\t',
            populated_only = True,
            smt_only = not include_th,
            file_doc = '#Units used = mils / deg',
            header_on = True,
            header_prefix = '#'
            )


def get_bom_data(parts, include_th = True):

    # keep only active parts
    parts = parts[(parts['footprint_type'] != 'VIRT')]

    parts = parts[(parts['populate'] == True )]
    
    if not include_th:
        parts = parts[(parts['footprint_type'] == 'SMT') ]

    parts = parts.sort_values(['type_override', 'footprint_type', 'reference'], ascending=[True, True, True])

    # group the parts
    bom_dict = collections.OrderedDict()
    for index, row in parts.iterrows():
        part_id = None
        for grouping in config['BOM_grouping'][:-1]:
            if all(row[grouping]):
                part_id = tuple(row[grouping])
                break
        if not part_id:
            part_id = tuple(row[config['BOM_grouping'][-1]])
        if part_id in bom_dict:
            (bom_dict[part_id])[0] += 1
            (bom_dict[part_id])[1] += ',' + row['reference'] 
            (bom_dict[part_id])[2].append(row) 
        else:
            bom_dict[part_id] = [1, row['reference'], [row]]

    for part_id, part_bom in bom_dict.items():
        part_bom_rows = []
        part_bom_rows_tov = []
        for row in part_bom[-1]:
            if row['type_override']:
                part_bom_rows_tov.append(row)
            else:
                part_bom_rows.append(row)

        # check footprints (skip parts with type override)
        footprint_set = set([row['footprint'] for row in part_bom_rows])
        if len(footprint_set) > 1:
            raise Exception('Error: parts identified with id "%s" have multiple fooprints: %s'%(part_id,  ', '.join(footprint_set)))
        
        if len(part_bom_rows) > 0:
            # generate a merged description
            merged_description = generate_merged_description(part_bom_rows)
            part_bom[-1] = part_bom_rows[0]
            part_bom[-1]['description'] = merged_description
        else:
            # we have only type override parts
            part_bom[-1] = part_bom_rows_tov[0]
            part_bom[-1]['description'] = "Part with type override"


    ret = ''
        
    placements_total = 0
    placement_th = 0
    placement_has_BGA = 'No'
    ret += 'Item#,Qty,RefDes,Manufacturer,Mfg Part #,Mfg Part # Alt,Description,Package,Type\n'
    for i, (part_id, part_bom) in enumerate(bom_dict.items()):
        ret += '%d,%d,"%s",'%(i+1,part_bom[0],part_bom[1])
        # add tab to values to prevent automatic conversion to numbers
        ret += ','.join(['"%s\t"'%x for x in part_bom[-1][['manuf', 'manuf part', 'manuf part alt', 'description', 'footprint', 'footprint_type']]])
        ret += '\n'
        placements_total += part_bom[0]
        if part_bom[-1]['footprint_type'] == 'TH':
            placement_th += part_bom[0]
        if re.search('[bB][gG][aA]', part_bom[-1]['footprint']):
            placement_has_BGA = 'Yes'

    ret += '\n'
    ret += 'Board Summary\n'
    ret += 'Unique Part Count,%d\n'%len(bom_dict.keys())
    ret += 'Total Placements,%d\n'%placements_total
    ret += 'Through Hole Placement,%d\n'%placement_th
    ret += 'Has BGA Placements,%s\n'%placement_has_BGA
    return ret


def OutputAssembly(
        board=None, 
        output_dir = defaults['output_dir'],
        overwrite = False, 
        bom_fname = None,
        include_th = True,
        dump_part_db = False,
        output_log = sys.stdout
        ):

    ret = {}
    ret['warn'] = []

    if board == None:
        board = pcbnew.GetBoard()

    if not board:
        raise Exception('Error: Invalid board')

    if bom_fname == None:
        raise Exception("Missing BOM file")

    parts = build_part_db(board, bom_fname)

    os.makedirs(output_dir)

    if dump_part_db:
        fname = os.path.join(output_dir, "Parts.csv")
        output_log.write('Writing part database to %s\n'%fname)
        parts.to_csv(fname)

    fname = os.path.join(output_dir, "Placement.pos")
    output_log.write('Writing SMT placement data to %s\n'%fname)
    open(fname, 'w').write(get_centroid_data(parts.copy()))

    fname = os.path.join(output_dir, "Parts.XYRS")
    output_log.write('Writing XYRS data to %s\n'%fname)
    open(fname, 'w').write(get_MacroFab_xyrs_data(parts.copy(), include_th))

    fname = os.path.join(output_dir, "BOM.csv")
    output_log.write('Writing BOM to %s\n'%fname)
    open(fname, 'w').write(get_bom_data(parts.copy(), include_th))

    return ret


def main():

    parser = argparse.ArgumentParser(description='Script for generating assembly outputs for Kicad projects')
    parser.add_argument('kicad_pcb',
            help="Kicad PCB file")
    parser.add_argument('bom_fname', nargs='?', default=None,
            help="BOM csv file exported from schematic")
    parser.add_argument('--output_dir', default=defaults['output_dir'],
            help="Output directory (default = %(default)s)")
    parser.add_argument('-o', '--overwrite', action='store_true',
            help="Overwrite output directory")
    parser.add_argument('-t', '--include_th', action='store_true',
            help="Include through hole components in the generated bom")
    parser.add_argument('-d', '--debug_db', action='store_true',
            help="Dump the part database as csv")

    args = parser.parse_args()

    if os.path.exists(args.output_dir):
        if args.overwrite:
            shutil.rmtree(args.output_dir)
        else:
            print('Directory %s exists. Please specify another location or the overwrite flag.'%args.output_dir)
            return


    board = pcbnew.LoadBoard(args.kicad_pcb)

    if args.bom_fname == None:
        args.bom_fname = os.path.splitext(os.path.basename(board.GetFileName()))[0] + '.csv'

    ret = OutputAssembly(
            board = board, 
            output_dir = args.output_dir, 
            overwrite = args.overwrite,
            bom_fname = args.bom_fname,
            include_th = args.include_th,
            dump_part_db = args.debug_db
            )

    print("Done\n")
    for w in ret['warn']:
        print(w)


if __name__=='__main__':
    sys.exit(main())

