# kicad-scripts

Scripts for Kicad automation

# License

These scripts are released under the [Apache License v2.0](http://www.apache.org/licenses/LICENSE-2.0)

# Warranty

These scripts are provided in the hope that they will be useful, but are provided without warranty of any kind, express or implied.

# Instructions

The Kicad plugins in this directory can be run in two ways:

- From Kicad
    
    - Link/copy the plugin_* directory in the Kicad plugin directory:
        > cd ~/.kicad_plugins
        > ln -s <path_to_scripts_dir>/plugin_drill_map .

    - Restart Kicad and access the GUI from Pcbnew -> Tools -> External Plugins
    - If the python code of the plugin is modified Kicad must be restarted to load the changes

- From command line (Linux instructions)
    
    - Create an alias for loading the Kicad specific python environment (needs to be run only once and can be put in .bashrc). This is optional but makes the next commands much cleaner
         > alias python_k="LD_LIBRARY_PATH=$LD_LIBRARY_PATH:<path_to_kicad_install_dir>/lib PYTHONPATH=<path_to_kicad_install_dir>/lib/python2.7/dist-packages/ python"
    
    - Run the script
         > python_k plugin_drill_map/drill_map.py -h
         
        or
        
         > python_k plugin_drill_map/drill_map.py board_file.kicad_pcb

