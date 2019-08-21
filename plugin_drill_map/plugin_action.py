# Drill Map Plugin 

import wx
from pcbnew import ActionPlugin, GetBoard

from .plugin_dialog import InitMainDialog

class CustomActionPlugin(ActionPlugin):

    def defaults(self):
        self.name = "Drill Map"
        self.category = "Fabrication Notes"
        self.description = "Creates drill legend and markers"

    def Run(self):
        InitMainDialog(GetBoard())

