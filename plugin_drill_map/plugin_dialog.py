
import wx
import traceback
import drill_map as dmap
import pcbnew


class MainPluginDialog(wx.Dialog):

    def __init__(self, board):

        self.board = board

        wx.Dialog.__init__ ( self, None, id = wx.ID_ANY, title = "Drill Map v(%s)"%dmap.__version__, pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.CAPTION|wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE )

        spacing = 5

        main_sizer = wx.BoxSizer( wx.VERTICAL )
        label_flags = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL
        ctrl_flags = wx.ALL | wx.SHAPED

        pars_sizer = wx.FlexGridSizer(0, 2, 0, 0)
        static_text =  wx.StaticText(self, label = "Table Text Size (mm)")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        self.text_size_mm_ctrl = wx.TextCtrl(self, value = '%.1f'%dmap.defaults['table_text_size_mm'])
        pars_sizer.Add(self.text_size_mm_ctrl, flag = ctrl_flags, border = spacing)

        static_text =  wx.StaticText(self, label = "Layer")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        layer_sel_list = ['Dwgs.User', 'Cmts.User', 'Eco1.User', 'Eco2.User']
        self.layer_ctrl = wx.Choice(self, choices = ['Dwgs.User', 'Cmts.User', 'Eco1.User', 'Eco2.User'])
        self.layer_ctrl.SetSelection(2)
        pars_sizer.Add(self.layer_ctrl, flag = ctrl_flags, border = spacing)

        static_text =  wx.StaticText(self, label = "Clear Layer")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        self.clear_layer_ctrl = wx.CheckBox(self)
        self.clear_layer_ctrl.SetValue(True)
        pars_sizer.Add(self.clear_layer_ctrl, flag = ctrl_flags, border = spacing)

        static_text =  wx.StaticText(self, label = "Table Title")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        self.title_ctrl = wx.TextCtrl(self, value = dmap.defaults['table_title']) 
        pars_sizer.Add(self.title_ctrl, flag = ctrl_flags, border = spacing)

        static_text =  wx.StaticText(self, label = "Table Columns")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        self.columns_ctrl = wx.CheckListBox(self, choices = dmap.TableColumns) 
        self.columns_ctrl.SetCheckedStrings(dmap.defaults['TableColumns'])
        pars_sizer.Add(self.columns_ctrl, flag = ctrl_flags, border = spacing)

        main_sizer.Add(pars_sizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND|wx.SHAPED, spacing )

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.but_run = wx.Button(self, label = "Run")
        button_sizer.Add(self.but_run, border = spacing)
        self.but_dismiss = wx.Button(self, label = "Dismiss")
        button_sizer.Add(self.but_dismiss, border = spacing)

        main_sizer.Add(button_sizer, 0, flag = wx.ALL|wx.CENTER, border = spacing)

        self.output_log_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP, size=(500,300))

        main_sizer.Add(self.output_log_ctrl, 1, flag = wx.ALL|wx.CENTER|wx.EXPAND, border = spacing)

        self.SetSizer(main_sizer)
        self.Layout()
	main_sizer.Fit(self)
	self.Centre(wx.BOTH)

        self.Bind(wx.EVT_CLOSE, self.onCloseWindow)
	self.but_dismiss.Bind(wx.EVT_BUTTON, self.onCloseWindow)
	self.but_run.Bind(wx.EVT_BUTTON, self.onRun)


    def onCloseWindow(self, event):
        self.Destroy()

    
    def onRun(self, event):

        text_size_mm = self.text_size_mm_ctrl.GetValue()

        err = False
        try:
            text_size_mm = float(text_size_mm)
        except ValueError:
            err = True

        if text_size_mm < 0.1 or text_size_mm > 10:
            err = True

        if err:
            wx.MessageBox("Table Text Size (mm) should be a number between 0.1 and 10")
            return


        columns = self.columns_ctrl.GetCheckedStrings()
        try:
            ret = dmap.DrillMap(
                    board = self.board,
                    layer_name = self.layer_ctrl.GetString(self.layer_ctrl.GetSelection()),
                    clear_layer = self.clear_layer_ctrl.IsChecked(),
                    table_columns = self.columns_ctrl.GetCheckedStrings(),
                    table_text_size_mm = text_size_mm,
                    table_title = self.title_ctrl.GetValue(),
                    output_log = self.output_log_ctrl
                    )
        except Exception:
            self.output_log_ctrl.write(traceback.format_exc())
            wx.MessageBox("An exception has occured. Please check the output log")
            return
                
        message = ""
        message += "Done"
        message += '\n'
        message += 'Please switch manually between canvases to force a refresh.'
        message += '\n\n'
        for warn in ret['warn']:
            message += warn 
            message += '\n'
        self.output_log_ctrl.write(message)

        
def InitMainDialog(board):
    """ Launch the dialog """

    dlg = MainPluginDialog(board)
    dlg.Show(True)
    dlg.SetMinSize(dlg.GetSize())
    return dlg
        
