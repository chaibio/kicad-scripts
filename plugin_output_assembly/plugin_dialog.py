
import os
import shutil
import wx
import traceback
import output_assembly
import pcbnew


class MainPluginDialog(wx.Dialog):

    def __init__(self, board):

        self.board = board

        wx.Dialog.__init__ ( self, None, id = wx.ID_ANY, title = "Output Assembly v(%s)"%output_assembly.__version__, pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.CAPTION|wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE )

        spacing = 5

        main_sizer = wx.BoxSizer( wx.VERTICAL )
        label_flags = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL
        ctrl_flags = wx.ALL | wx.EXPAND 

        pars_sizer = wx.FlexGridSizer(0, 2, 0, 0)
        pars_sizer.AddGrowableCol(1,1)
        static_text =  wx.StaticText(self, label = "Output Dir")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        self.output_dir_ctrl = wx.TextCtrl(self, 
                value = os.path.join(os.path.dirname(board.GetFileName()), output_assembly.defaults['output_dir'])
                )
        self.output_dir_ctrl.SetInsertionPointEnd()
        pars_sizer.Add(self.output_dir_ctrl, flag = ctrl_flags, border = spacing)

        static_text =  wx.StaticText(self, label = "Overwrite")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        self.output_dir_overwrite_ctrl = wx.CheckBox(self)
        self.output_dir_overwrite_ctrl.SetValue(True)
        pars_sizer.Add(self.output_dir_overwrite_ctrl, flag = ctrl_flags, border = spacing)

        default_bom_fname = os.path.splitext(board.GetFileName())[0] + '.csv'
        static_text =  wx.StaticText(self, label = "BOM File Name (csv)")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        self.bom_fname_ctrl = wx.TextCtrl(self, value = default_bom_fname)
        tt = wx.ToolTip('BOM csv file exported from schematic')
        self.bom_fname_ctrl.SetToolTip(tt)
        self.bom_fname_ctrl.SetInsertionPointEnd()
        pars_sizer.Add(self.bom_fname_ctrl, flag = ctrl_flags, border = spacing)

        static_text =  wx.StaticText(self, label = "Include TH")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        self.include_th_ctrl = wx.CheckBox(self)
        self.include_th_ctrl.SetValue(True)
        tt = wx.ToolTip('Include through hole components in output BOM')
        self.include_th_ctrl.SetToolTip(tt)
        pars_sizer.Add(self.include_th_ctrl, flag = ctrl_flags, border = spacing)

        static_text =  wx.StaticText(self, label = "Dump Part DB")
        pars_sizer.Add(static_text, flag = label_flags, border = spacing)
        self.dump_db_ctrl = wx.CheckBox(self)
        self.dump_db_ctrl.SetValue(False)
        tt = wx.ToolTip('Dump all part information in csv format')
        self.dump_db_ctrl.SetToolTip(tt)
        pars_sizer.Add(self.dump_db_ctrl, flag = ctrl_flags, border = spacing)

        main_sizer.Add(pars_sizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, spacing )

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
        
        overwrite = self.output_dir_overwrite_ctrl.IsChecked()
        dump_db = self.dump_db_ctrl.IsChecked()
        output_dir = self.output_dir_ctrl.GetValue()

        if os.path.exists(output_dir):
            if overwrite:
                shutil.rmtree(output_dir)
            else:
                wx.MessageBox("Output directory exists. Specify another directory or check the overwrite box.")
                return

        try:
            ret = output_assembly.OutputAssembly(
                    board = self.board,
                    output_dir = output_dir, 
                    overwrite = overwrite,
                    bom_fname = self.bom_fname_ctrl.GetValue(),
                    include_th = self.include_th_ctrl.IsChecked(),
                    dump_part_db = dump_db,
                    output_log = self.output_log_ctrl
                    )
        except Exception:
            self.output_log_ctrl.write(traceback.format_exc())
            wx.MessageBox("An exception has occured. Please check the output log")
            return
                
        message = ""
        message += "Done"
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


        
