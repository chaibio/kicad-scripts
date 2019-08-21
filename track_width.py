#!/usr/bin/env python2

import sys
import pcbnew
import collections
import json

def set_trace_widths(board, target_widths):

    board.BuildListOfNets() # required so 'board' contains valid netclass data
    # build list with copper layer names
    copper_layer_count = board.GetCopperLayerCount()
    layer_names = [board.GetLayerName(layer_id) for layer_id in range(board.GetCopperLayerCount() - 1)] + [board.GetLayerName(31)]
    
    # check the target widths structure
    for nc, width_map in target_widths.items():
        # TODO check for valid net class (API only available in kicad 5)
        # nc = board.GetAllNetClasses()
        for layer_name in width_map.keys():
            if layer_name != 'Default' and layer_name not in layer_names:
                raise Exception('Invalid layer name: %s'%layer_name)
    
    # initialize counters for changes
    count = collections.OrderedDict()
    for layer_name in layer_names:
        count.setdefault(layer_name, 0)
    
    for track in board.GetTracks():
        for nc, width_map in target_widths.items():
            default_width = width_map['Default']
            if type(track) == pcbnew.TRACK and track.GetNet().GetClassName() == nc:
                layer_name = track.GetLayerName()
                if layer_name in width_map:
                    track.SetWidth(pcbnew.FromMils(width_map[layer_name]))
                else:
                    if default_width <= 0:
                        pos = track.GetPosition()
                        x = pcbnew.ToMM(pos.x)
                        y = pcbnew.ToMM(pos.y)
                        raise Exception('Found track on net %s on unexpected layer: %s at position %.2fx%.2f mm'%(track.GetNetname(), layer_name, x, y)) 
                    else:
                        track.SetWidth(pcbnew.FromMils(default_width))
                count[layer_name] += 1

    return count
    

if __name__=='__main__':
    import sys
    board_filename = sys.argv[1]
    config = json.load(open(sys.argv[2]))
    board = pcbnew.LoadBoard(board_filename)

    count = set_trace_widths(board, config["target_widths"])

    print("Tracks Change Summary:")
    for k, v in count.items():
        print('%10s : %d'%(k,v))

    pcbnew.SaveBoard(board_filename + '.new', board)
    print("Saved updated board in %s.new"%board_filename)


