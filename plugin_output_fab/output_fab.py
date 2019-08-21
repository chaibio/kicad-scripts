#!/usr/bin/env python2

import sys
import os
import shutil
import argparse
import subprocess
import pcbnew

__version__ = '0.1'

debug = False

defaults = {
        'output_dir' : 'OUTPUT_FAB',
        }

def OutputFab(
        board=None, 
        output_dir=defaults['output_dir'], 
        overwrite=False, 
        protel_ext=False,
        output_log = sys.stdout
        ):

    ret = {}
    ret['warn'] = []

    if board == None:
        board = pcbnew.GetBoard()
    if not board:
        raise Exception('Error: Invalid board')

    os.makedirs(output_dir)

    out_file_prefix = os.path.splitext(os.path.basename(board.GetFileName()))[0]

    # TODO run DRC

    pctl = pcbnew.PLOT_CONTROLLER(board)
    popt = pctl.GetPlotOptions()
    popt.SetOutputDirectory(output_dir)

    # Set some important plot options:
    popt.SetPlotFrameRef(False)     #do not change it
    popt.SetLineWidth(pcbnew.FromMM(0.1))

    popt.SetAutoScale(False)        #do not change it
    popt.SetScale(1)                #do not change it
    popt.SetMirror(False)
    popt.SetUseGerberAttributes(False) # disable verbose header in gerber files
    popt.SetUseGerberProtelExtensions(protel_ext)
    popt.SetExcludeEdgeLayer(True);
    popt.SetUseAuxOrigin(True)

    popt.SetSubtractMaskFromSilk(True)
    popt.SetDrillMarksType(pcbnew.PCB_PLOT_PARAMS.NO_DRILL_SHAPE)

    plot_plan = [
        # fname_suffix     layer_id             comment
        ( "CuTop",         pcbnew.F_Cu,         "Top layer" ),
        ( "CuBottom",      pcbnew.B_Cu,         "Bottom layer" ),
        ( "PasteTop",      pcbnew.F_Paste,      "Paste top" ),
        ( "PasteBottom",   pcbnew.B_Paste,      "Paste Bottom" ),
        ( "SilkTop",       pcbnew.F_SilkS,      "Silk top" ),
        ( "SilkBottom",    pcbnew.B_SilkS,      "Silk bottom" ),
        ( "MaskTop",       pcbnew.F_Mask,       "Mask top" ),
        ( "MaskBottom",    pcbnew.B_Mask,       "Mask bottom" ),
        ( "EdgeCuts",      pcbnew.Edge_Cuts,    "Edges" ),
    ]

    # add inner layers if present
    for inner_layer in range ( 1, board.GetCopperLayerCount()-1 ):
        layer_name = "Int%d"%inner_layer
        plot_plan.append((layer_name ,inner_layer, "Layer %s"%layer_name))

    # now do the plot
    for layer_info in plot_plan:
        pctl.SetLayer(layer_info[1])
        pctl.OpenPlotfile(layer_info[0], pcbnew.PLOT_FORMAT_GERBER, layer_info[2])
        output_log.write('Ploting %s\n' % pctl.GetPlotFileName())
        if pctl.PlotLayer() == False:
            raise Exception("Plot error")

    # Plot the FAB notes and drill legend
    popt.SetUseAuxOrigin(False)
    # Color plotting does not work from the python interface 
    # Might need to export each layer separatelly and combine them with external tools 
    pctl.SetColorMode(True)
    pctl.OpenPlotfile("FabDrawing", pcbnew.PLOT_FORMAT_PDF, "Fab Drawing")
    output_log.write('Ploting %s\n'%pctl.GetPlotFileName())
    #popt.SetColor(pcbnew.GREEN)  # kicad 4.0
    #popt.SetColor(pcbnew.COLOR4D(0.050, 0.050, 0.050, 0.1)) # kicad 5.0
    pctl.SetLayer(pcbnew.Edge_Cuts)
    pctl.PlotLayer()
    pctl.SetLayer(pcbnew.Cmts_User)
    pctl.PlotLayer()
    pctl.SetLayer(pcbnew.Eco1_User)
    pctl.PlotLayer()
    
    # Generate drill files
    mirror = False
    minimalHeader = False
    offset = board.GetAuxOrigin()
    mergeNPTH = True

    drlwriter = pcbnew.EXCELLON_WRITER( board )
    drlwriter.SetOptions( mirror, minimalHeader, offset, mergeNPTH )
    drlwriter.SetMapFileFormat( pcbnew.PLOT_FORMAT_PDF )

    metricFmt = True
    drlwriter.SetFormat( metricFmt )

    genDrl = True
    genMap = True
    output_log.write('Create drill and map files\n')
    drlwriter.CreateDrillandMapFilesSet( pctl.GetPlotDirName(), genDrl, genMap );

    report_filename = pctl.GetPlotDirName() + out_file_prefix +'_DrillReport.rpt'
    output_log.write('Create drill report in %s\n'%report_filename)
    drlwriter.GenDrillReportFile( report_filename );

    pctl.ClosePlot()

    output_log.write('Create zip file')
    os.chdir(pctl.GetPlotDirName())
    cmd = 'zip -j {0}.zip {0}*.g?? {0}*.g? {0}-FabDrawing.pdf {0}.drl '.format(out_file_prefix)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    output_log.write(stdout)
    output_log.write(stderr)

    # TODO IPC-D-356 (it's not exposed in the python interface)
    ret['warn'].append('Please create manually the IPC-D-356 file from the File->Fabrication Outputs menu')

    return ret


def main():

    parser = argparse.ArgumentParser(description='Script for generating fabrication outputs for Kicad projects')
    parser.add_argument('kicad_pcb',
            help="Kicad PCB file")
    parser.add_argument('--output_dir', default=defaults['output_dir'],
            help="Output directory (default = %(default)s)")
    parser.add_argument('-o', '--overwrite', action='store_true',
            help="Overwrite output directory")
    parser.add_argument('-p', '--protel', action='store_true',
            help="Use Protel file extensions")

    args = parser.parse_args()

    if os.path.exists(args.output_dir):
        if args.overwrite:
            shutil.rmtree(args.output_dir)
        else:
            print('Directory %s exists. Please specify another location or the overwrite flag.'%args.output_dir)
            return


    board = pcbnew.LoadBoard(args.kicad_pcb)

    ret = OutputFab(
            board = board,
            output_dir = args.output_dir,
            overwrite = args.overwrite,
            protel_ext = args.protel
            )

    print("Done\n")
    for w in ret['warn']:
        print(w)


if __name__=='__main__':
    sys.exit(main())

