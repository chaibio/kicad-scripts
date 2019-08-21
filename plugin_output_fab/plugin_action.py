# Fabrication Output Plugin 

import wx
from pcbnew import ActionPlugin, GetBoard

from .plugin_dialog import InitMainDialog

class CustomActionPlugin(ActionPlugin):

    def defaults(self):
        self.name = "Fabrication Outputs"
        self.category = "Fabrication"
        self.description = "Create fabrication outputs"

    def Run(self):
        InitMainDialog(GetBoard())

