import sys
import argparse
import re
import pcbnew

__version__ = '0.1'

TableColumns = ['Size (mils)', 'Size (mm)', 'Quantity', 'Plated', 'Tolerance (mm)', 'Tolerance (mils)']
defaults = {
        'TableColumns' : ['Size (mils)', 'Size (mm)', 'Quantity', 'Plated'],
        'table_text_size_mm' : 1.5,
        'table_title' : "DRILL CHART: TOP TO BOTTOM",
        'layer_name' : 'Eco1.User',
        }


def DrawLine(board, layer, start, end, width):
    ds = pcbnew.DRAWSEGMENT(board)
    board.Add(ds)
    ds.SetShape(pcbnew.S_SEGMENT)
    ds.SetStart(pcbnew.wxPoint(start[0], start[1]))
    ds.SetEnd(pcbnew.wxPoint(end[0], end[1]))
    ds.SetWidth(width)
    ds.SetLayer(layer)

def DrawCircle(board, layer, center, end, width):
    ds = pcbnew.DRAWSEGMENT(board)
    board.Add(ds)
    ds.SetShape(pcbnew.S_CIRCLE)
    ds.SetStart(pcbnew.wxPoint(center[0], center[1]))
    ds.SetEnd(pcbnew.wxPoint(end[0], end[1]))
    ds.SetWidth(width)
    ds.SetLayer(layer)

def DrawText(board, text_str, layer, pos, size=int(1.5*pcbnew.IU_PER_MM), thickness=None, h_align=pcbnew.GR_TEXT_HJUSTIFY_CENTER):
    if thickness == None:
        thickness=int(size/7.5)
    text = pcbnew.TEXTE_PCB(board)
    text.SetText(text_str)
    text.SetPosition(pcbnew.wxPoint(*pos))
    try:
        # this fails in version 4.0.x
        text.SetTextSize(pcbnew.wxSize(size, size))
    except AttributeError:
        # this fails in nightly 20171105 version
        text.SetSize(pcbnew.wxSize(size, size))
    text.SetThickness(thickness)
    text.SetHorizJustify(h_align)
    text.SetLayer(layer)
    board.Add(text)
        

class Marker(object):

    def __init__(self, board, layer, pos, size):
        self._board = board
        self._layer = layer
        self._posX = pos[0] 
        self._posY = pos[1]
        self._size = min(size, 5 * pcbnew.IU_PER_MM)
        self._min_width = 0.01 * pcbnew.IU_PER_MM
        self._max_width = 0.3 * pcbnew.IU_PER_MM
        self._width = int( max(self._min_width, min(self._max_width, 0.1 * self._size)))
        self._size_half = int(self._size/2)

    def DrawLine(self, start, end, width):
        DrawLine(self._board, self._layer, start, end, width)

    def DrawCircle(self, center, end, width):
        DrawCircle(self._board, self._layer, center, end, width)

    def DrawText(self, text_str):
        DrawText(self._board, text_str, self._layer, (self._posX, self._posY), int(0.7*self._size))


class MarkerCircle(Marker):

    def __init__(self, board, layer, pos, size):
        super(MarkerCircle, self).__init__(board, layer, pos, size)

        self.DrawCircle(
                (self._posX, self._posY),
                (self._posX, self._posY + self._size_half),
                self._width
                )

class MarkerCircle2(Marker):

    def __init__(self, board, layer, pos, size):
        super(MarkerCircle, self).__init__(board, layer, pos, size)

        self.DrawCircle(
                (self._posX, self._posY),
                (self._posX + self._size_half, self._posY + self._size_half),
                self._width
                )

class MarkerCross(Marker):

    def __init__(self, board, layer, pos, size):
        super(MarkerCross, self).__init__(board, layer, pos, size)
        
        self.DrawLine(
                (self._posX - self._size_half, self._posY),
                (self._posX + self._size_half, self._posY),
                self._width
                )

        self.DrawLine(
                (self._posX, self._posY - self._size_half),
                (self._posX, self._posY + self._size_half),
                self._width
                )


class MarkerX(Marker):

    def __init__(self, board, layer, pos, size):
        super(MarkerX, self).__init__(board, layer, pos, size)
        
        width = int( max(self._min_width, min(self._max_width, 0.1 * self._size)))
        self.DrawLine(
                (self._posX - self._size_half, self._posY - self._size_half),
                (self._posX + self._size_half, self._posY + self._size_half),
                self._width
                )

        self.DrawLine(
                (self._posX - self._size_half, self._posY + self._size_half),
                (self._posX + self._size_half, self._posY - self._size_half),
                self._width
                )
        

class MarkerCrossCircle(MarkerCross, MarkerCircle):

    def __init__(self, board, layer, pos, size):
        super(MarkerCrossCircle, self).__init__(board, layer, pos, size)


class MarkerXCircle(MarkerX, MarkerCircle):

    def __init__(self, board, layer, pos, size):
        super(MarkerXCircle, self).__init__(board, layer, pos, size)


class MarkerSquare(Marker):

    def __init__(self, board, layer, pos, size):
        super(MarkerSquare, self).__init__(board, layer, pos, size)
        
        self.DrawLine(
                (self._posX - self._size_half, self._posY - self._size_half),
                (self._posX - self._size_half, self._posY + self._size_half),
                self._width
                )
        self.DrawLine(
                (self._posX + self._size_half, self._posY - self._size_half),
                (self._posX + self._size_half, self._posY + self._size_half),
                self._width
                )
        self.DrawLine(
                (self._posX - self._size_half, self._posY - self._size_half),
                (self._posX + self._size_half, self._posY - self._size_half),
                self._width
                )
        self.DrawLine(
                (self._posX - self._size_half, self._posY + self._size_half),
                (self._posX + self._size_half, self._posY + self._size_half),
                self._width
                )

class MarkerTriangle(Marker):

    def __init__(self, board, layer, pos, size):
        super(MarkerTriangle, self).__init__(board, layer, pos, size)
        
        x_delta = int(3.0**0.5 * self._size_half / 2)
        y_delta = int(self._size_half / 2)

        self.DrawLine(
                (self._posX - x_delta, self._posY + y_delta),
                (self._posX          , self._posY - self._size_half),
                self._width
                )

        self.DrawLine(
                (self._posX + x_delta, self._posY + y_delta),
                (self._posX          , self._posY - self._size_half),
                self._width
                )

        self.DrawLine(
                (self._posX - x_delta, self._posY + y_delta),
                (self._posX + x_delta, self._posY + y_delta),
                self._width
                )

class MarkerTriangleCircle(MarkerTriangle, MarkerCircle):

    def __init__(self, board, layer, pos, size):
        super(MarkerTriangleCircle, self).__init__(board, layer, pos, size)


class MarkerCharCircle(MarkerCircle):

    def __init__(self, board, layer, pos, size, letter):
        super(MarkerCharCircle, self).__init__(board, layer, pos, size)

        self.DrawText(letter)


class MarkerCharSquare(MarkerSquare):

    def __init__(self, board, layer, pos, size, letter):
        super(MarkerCharSquare, self).__init__(board, layer, pos, size)

        self.DrawText(letter)

def __GetMarkerList():
    ret = [MarkerCross, MarkerX, MarkerCrossCircle, MarkerXCircle, MarkerSquare, MarkerTriangle, MarkerTriangleCircle]
    import string
    __chars = string.ascii_letters + '123456789'
    ret += [(lambda b,l,p,s,c=c: MarkerCharCircle(b, l, p, s, c)) for c in __chars]
    ret += [(lambda b,l,p,s,c=c: MarkerCharSquare(b, l, p, s, c)) for c in __chars]
    return ret


MARKER_LIST = __GetMarkerList()


def DrillMap(
        board=None, 
        layer_name=defaults['layer_name'], 
        clear_layer=True, 
        table_columns=defaults['TableColumns'], 
        table_text_size_mm=defaults['table_text_size_mm'], 
        table_title = defaults['table_title'],
        table_position_mm=None, 
        output_log = sys.stdout
        ):

    ret = {}
    ret['warn'] = []

    if board == None:
        board = pcbnew.GetBoard()
    if not board:
        raise Exception('Error: Invalid board')

    layer = board.GetLayerID(layer_name)
    if layer < 0:
        raise Exception('Invalid layer name: %s'%layer_name)

    err = False
    try:
        table_text_size_mm = float(table_text_size_mm)
    except ValueError:
        err = True

    if table_text_size_mm < 0.1 or table_text_size_mm > 10:
        err = True

    if err:
        raise Exception('Invalid table text size (mm): %s'%table_text_size_mm)


    def get_size_mils(drill_type, drill_position_list):
        ret = "%.1f"%(drill_type[1][0] / pcbnew.IU_PER_MILS)
        if drill_type[1][0] != drill_type[1][1]:
            # oval size
            ret += " x %.1f"%(drill_type[1][1] / pcbnew.IU_PER_MILS)
        return ret

    def get_size_mm(drill_type, drill_position_list):
        ret = "%.3f"%(drill_type[1][0] / pcbnew.IU_PER_MM)
        if drill_type[1][0] != drill_type[1][1]:
            # oval size
            ret += " x %.3f"%(drill_type[1][1] / pcbnew.IU_PER_MM)
        return ret

    def get_qty(drill_type, drill_position_list):
        return "%d"%(len(drill_position_list))

    def get_plated(drill_type, drill_position_list):
        if drill_type[0]:
            return 'YES'
        else:
            return 'NO'

    def get_empty(drill_type, drill_position_list):
        return ''

    TableColumnsDict = {
            #                        header            min width
            "Symbol"           :     ["SYMBOL",          8,        get_empty      ],
            "Size (mils)"      :     ["SIZE(mils)",      10,       get_size_mils  ],
            "Size (mm)"        :     ["SIZE(mm)",        10,       get_size_mm    ],
            "Quantity"         :     ["QTY",             6,        get_qty        ],
            "Plated"           :     ["PLATED",          8,        get_plated     ],
            "Tolerance (mm)"   :     ["TOLERANCE(mm)",   16,       get_empty      ],
            "Tolerance (mils)" :     ["TOLERANCE(mils)", 16,       get_empty      ],
            }

    for col in table_columns:
        if col not in TableColumnsDict:
            raise Exception('Invalid column name: %s'%col)
    table_columns = ['Symbol'] + list(table_columns)

    drill_positions = {}
    #find TH pads
    for m in board.GetModules():
        for p in m.Pads():

            plated = True
            attribute = p.GetAttribute()
            if attribute == pcbnew.PAD_ATTRIB_STANDARD:
                plated = True
            elif attribute == pcbnew.PAD_ATTRIB_HOLE_NOT_PLATED:
                plated = False
            else:
                #SMD
                continue
            
            shape = p.GetDrillShape()
            if shape not in [pcbnew.PAD_DRILL_SHAPE_CIRCLE, pcbnew.PAD_DRILL_SHAPE_OBLONG]:
                raise Exception('Unknown drill shape: %d'%shape)

            size = p.GetDrillSize()
            position = p.GetPosition()

            drill_positions.setdefault((plated, size.Get(), shape), []).append(position.Get())


    # find VIA's
    for t in board.GetTracks():
        if type(t) is pcbnew.VIA:
            # TODO should we separate VIA types?
            #if t.GetViaType() != pcbnew.VIA_THROUGH:
            #    continue
            size = t.GetDrillValue()
            position = t.GetPosition()
            drill_positions.setdefault((True, (size, size), pcbnew.PAD_DRILL_SHAPE_CIRCLE), []).append(position.Get())

    output_log.write("Found %d drill types\n"%len(drill_positions))

    if len(drill_positions) > len(MARKER_LIST):
        ret['warn'].append('Found more drill types than available markers. Different drills have been assigned the same marker')

    # compute column widths
    for col in table_columns:
        if col == 'Symbol':
            continue
        col_width = TableColumnsDict[col][1]
        for drill_type in drill_positions.keys():
            col_width = max(col_width, len(TableColumnsDict[col][2](drill_type, drill_positions[drill_type])))
        TableColumnsDict[col][1] = col_width

    tbl_X_start = 0
    tbl_Y_start = 0
    if table_position_mm == None:
        # Search for location marker:
        marker_found = False
        for d in board.GetDrawings():
            if d.GetLayer() != layer:
                continue
            if type(d) is pcbnew.TEXTE_PCB:
              match = re.match(r'DrillTableLocationMarker\(\s*(\d+)\s*\)', d.GetText())
              if match != None:
                  pos = d.GetPosition()
                  tbl_X_start = pos.x 
                  tbl_Y_start = pos.y - int(match.groups()[0])
                  marker_found = True
                  break

        if not marker_found:
            # place the table below the board
            rect = None
            for d in board.GetDrawings():
                if d.GetLayerName() != "Edge.Cuts":
                    continue
                if rect == None:
                    rect = d.GetBoundingBox()
                else:
                    rect.Merge(d.GetBoundingBox())

            tbl_X_start = rect.GetX() + 10 * pcbnew.IU_PER_MM
            tbl_Y_start = rect.GetY() + rect.GetHeight() + 30 * pcbnew.IU_PER_MM

    else:
        tbl_X_start = int(table_position_mm[0] * pcbnew.IU_PER_MM)
        tbl_Y_start = int(table_position_mm[1] * pcbnew.IU_PER_MM)
    
    if clear_layer:
        for d in board.GetDrawings():
            if d.GetLayer() == layer:
               d.DeleteStructure()

    # Draw table
    tbl_line_width = int(0.1 * pcbnew.IU_PER_MM)
    tbl_text_size = int(table_text_size_mm * pcbnew.IU_PER_MM)
    tbl_row_width = sum([TableColumnsDict[col][1] * tbl_text_size for col in table_columns])
    tbl_row_height = 2 * tbl_text_size
    tbl_height = (len(drill_positions.keys()) + 1) * tbl_row_height 

    tbl_X = tbl_X_start
    tbl_Y = tbl_Y_start
    # Title
    tbl_X = tbl_X_start
    tbl_Y += int(tbl_row_height/2)
    DrawText(board, table_title, layer, (tbl_X_start + tbl_row_width/2, tbl_Y), tbl_text_size)
    tbl_Y += int(tbl_row_height/2)
    # Header
    tbl_X = tbl_X_start
    DrawLine(board, layer, (tbl_X, tbl_Y), (tbl_X + tbl_row_width, tbl_Y), tbl_line_width) 
    DrawText(board, 'DrillTableLocationMarker(%d)'%tbl_row_height, layer, (tbl_X, tbl_Y), int(0.05 * pcbnew.IU_PER_MM) , int(0.005 * pcbnew.IU_PER_MM), pcbnew.GR_TEXT_HJUSTIFY_LEFT)
    tbl_X = tbl_X_start
    tbl_Y += int(tbl_row_height/2)
    for i, col in enumerate(table_columns):
        tmp = int(TableColumnsDict[col][1] * tbl_text_size / 2)
        tbl_X += tmp  
        DrawText(board, TableColumnsDict[col][0], layer, (tbl_X, tbl_Y), tbl_text_size)
        tbl_X += tmp
    tbl_X = tbl_X_start
    tbl_Y += int(tbl_row_height/2)
    DrawLine(board, layer, (tbl_X, tbl_Y), (tbl_X + tbl_row_width, tbl_Y), tbl_line_width) 
    tbl_Y += int(tbl_row_height/2)
    
    for i, drill_type in enumerate(sorted(drill_positions.keys())):

        # use last marker if we have too many drill sizes
        m = min(i, len(MARKER_LIST)-1)

        # add markers to board area
        for position in drill_positions[drill_type]:
            MARKER_LIST[m](board, layer, position, min(drill_type[1]))

        # add row to table

        # write the marker in the first column
        tbl_X = tbl_X_start + TableColumnsDict['Symbol'][1] * tbl_text_size / 2
        MARKER_LIST[m](board, layer, (tbl_X, tbl_Y), tbl_text_size)

        # write the rest of the columns
        tbl_X = tbl_X_start
        for i, col in enumerate(table_columns):
            tmp = int(TableColumnsDict[col][1] * tbl_text_size / 2)
            tbl_X += tmp
            DrawText(board, TableColumnsDict[col][2](drill_type, drill_positions[drill_type]), layer, (tbl_X, tbl_Y), tbl_text_size)
            tbl_X += tmp

        tbl_X = tbl_X_start
        tbl_Y += int(0.5 * tbl_row_height)
        DrawLine(board, layer, (tbl_X, tbl_Y), (tbl_X + tbl_row_width, tbl_Y), tbl_line_width) 

        tbl_X = tbl_X_start
        tbl_Y += int(0.5 * tbl_row_height)
        
    # draw column separator lines
    line_Y = tbl_Y_start + tbl_row_height
    line_X = tbl_X_start
    DrawLine(board, layer, (line_X, line_Y), (line_X, line_Y + tbl_height), tbl_line_width)
    for col in table_columns:
        line_X += int(TableColumnsDict[col][1] * tbl_text_size)
        DrawLine(board, layer, (line_X, line_Y), (line_X, line_Y + tbl_height), tbl_line_width)

    
    # check for overlapping drills
    drill_list = []
    for drill_type in drill_positions.keys():
        size = drill_type[1]
        for position in drill_positions[drill_type]: 
            drill_list.append((position, size))

    drill_overlaps = []
    for i, drill1 in enumerate(drill_list):
        for drill2 in drill_list[i+1 : len(drill_list)+1]:
            if (abs(drill1[0][0] - drill2[0][0]) < (drill1[1][0] + drill2[1][0])/2) and (abs(drill1[0][1] - drill2[0][1]) < (drill1[1][1] + drill2[1][1])/2) :
                drill_overlaps.append((drill1[0], drill2[0]))

    for drill_overlap in drill_overlaps:
        output_log.write('Found drills overlap at (mm): (%.3f:%.3f) and (%3f:%.3f)\n'%
                (
                    drill_overlap[0][0]/pcbnew.IU_PER_MM, 
                    drill_overlap[0][1]/pcbnew.IU_PER_MM,
                    drill_overlap[1][0]/pcbnew.IU_PER_MM, 
                    drill_overlap[1][1]/pcbnew.IU_PER_MM,
                ))
    
    return ret


def main():

    parser = argparse.ArgumentParser(description='Script for generating drill markers and legend for a Kicad pcb')
    parser.add_argument('kicad_pcb',
            help="Kicad PCB file")
    parser.add_argument('-l', '--layer_name', default=defaults['layer_name'],
            help="Layer to use for output (default = %(default)s)")
    parser.add_argument('-c', '--clear_layer', action='store_true',
            help="Remove all drawings from the output layer")
    parser.add_argument('--table_columns', default=defaults['TableColumns'], nargs='+',
            help="List of table columns. Possible values: %s"%(', '.join(["'%s'"%c for c in  TableColumns]),))
    parser.add_argument('--table_text_size_mm', type = float, default=defaults['table_text_size_mm'], 
            help="Table text size (mm) (default = %(default)s)")
    parser.add_argument('--table_title', default=defaults['table_title'], 
            help="Table title")
    parser.add_argument('-o', '--overwrite', action='store_true', 
            help="Overwrite the original file")

    args = parser.parse_args()

    if args.table_text_size_mm < 0.1 or args.table_text_size_mm > 10:
        print('Table Text Size (mm) should be a number between 0.1 and 10')
        return 1

    board = pcbnew.LoadBoard(args.kicad_pcb)

    # without this the netclass information is lost
    board.BuildListOfNets()
    
    ret = DrillMap(
        board = board,
        layer_name = args.layer_name,
        clear_layer = args.clear_layer,
        table_columns = args.table_columns,
        table_text_size_mm = args.table_text_size_mm,
        table_title = args.table_title,
        )

    print("Done")
    for w in ret['warn']:
        print(w)

    #for i, m in enumerate(MARKER_LIST):
    #    m(board, pcbnew.Eco1_User, (3*pcbnew.IU_PER_MM, i*3*pcbnew.IU_PER_MM), int(1.5*pcbnew.IU_PER_MM))

    output_filename = args.kicad_pcb
    if not args.overwrite:
        output_filename += '.new'
    pcbnew.SaveBoard(output_filename, board)
    print("Saved updated board in %s"%output_filename)


if __name__=='__main__':
    sys.exit(main())
