#!/usr/bin/env python
'''
Created on Sep 31, 2010

@author: Nielsen

#******************************************************************************
# This file is part of RAW.
#
#    RAW is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    RAW is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RAW.  If not, see <http://www.gnu.org/licenses/>.
#
#******************************************************************************
'''

import wx, os, subprocess, time, math, threading, Queue, numpy, cPickle, copy, sys, glob
import platform, fnmatch, shutil, platform
import wx.lib.scrolledpanel as scrolled
import wx.lib.wordwrap as wordwrap
import wx.lib.mixins.listctrl as listmix
import wx.grid as gridlib
from wx.lib.embeddedimage import PyEmbeddedImage
from numpy import ceil, floor

import wx.aui as aui
import RAWPlot, RAWImage, RAWOptions, RAWSettings, RAWCustomCtrl, RAWAnalysis, BIFT, RAWIcons, RAWGlobals
import SASFileIO, SASM, SASExceptions, SASImage, SASCalc
import matplotlib.colors as mplcol
import wx.lib.colourchooser as colorchooser
import wx.lib.buttons as wxbutton
from wx.lib.agw.balloontip import *
from wx._core import ICON_ERROR

mainworker_cmd_queue = Queue.Queue()
thread_wait_event = threading.Event()
question_return_queue = Queue.Queue()

RAWWorkDir = sys.path[0]

if os.path.split(sys.path[0])[1] in ['RAW.exe', 'raw.exe']:
    RAWWorkDir = os.path.split(sys.path[0])[0]

# RAWGlobals.init_globals()

global cancel_ift
cancel_ift = False

global workspace_saved
workspace_saved = True


#class MyAuiNotebook(aui.AuiNotebook):
#    ### TESTING CLOSE BUTTONS ON TABS ###
#
#    def __init__(self, *args, **kwargs):
#        #kwargs['style'] = kwargs.get('style', aui.AUI_NB_DEFAULT_STYLE) 
#       super(MyAuiNotebook, self).__init__(*args, **kwargs)
#        #self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.onClosePage)
#	   self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.onPageChange)
#
#	#self.SetWindowStyle(self.GetWindowStyle() & ~aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
#
#    def onPageChange(self, event):
#	   event.Skip()
#	   idx = self.GetSelection()
#	   style = self.GetWindowStyle()	
#	   print self.GetPageText(idx)
#
#	if idx != 2:	
#        	self.SetWindowStyle(style & ~aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
#		self.Refresh()
#	else:
#        	self.SetWindowStyle(style | aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
#		self.Refresh()
#
##	self.ToggleWindowStyle(aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
#
#    def onClosePage(self, event):
#        event.Skip()
#        #if self.GetPageCount() <= 2:
#        #    # Prevent last tab from being closed
#        #    self.ToggleWindowStyle(aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
#
#    def AddPage(self, *args, **kwargs):
#        super(MyAuiNotebook, self).AddPage(*args, **kwargs)
#        ## Allow closing tabs when we have more than one tab:
#        #if self.GetPageCount() > 1:
#        #    self.SetWindowStyle(self.GetWindowStyleFlag() | \
#        #        aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)


class MainFrame(wx.Frame):
    
    def __init__(self, title, frame_id):
        wx.Frame.__init__(self, None, frame_id, title, name = 'MainFrame')

        self.MenuIDs = {'exit'                : wx.NewId(),
                        'advancedOptions'     : wx.NewId(),
                        'loadSettings'        : wx.NewId(),
                        'saveSettings'        : wx.NewId(),
                        'centering'           : wx.NewId(),
                        'masking'             : wx.NewId(),
                        'goOnline'            : wx.NewId(),
                        'goOffline'           : wx.NewId(),
                        'plot1tynormal'       : wx.NewId(),
                        'plot1tyguinier'      : wx.NewId(),
                        'plot1tykratky'       : wx.NewId(),
                        'plot1typorod'        : wx.NewId(),
                        'plot1tysubtracted'   : wx.NewId(),
                        'plot2tynormal'       : wx.NewId(),
                        'plot2tyguinier'      : wx.NewId(),
                        'plot2tykratky'       : wx.NewId(),
                        'plot2tysubtracted'   : wx.NewId(),
                        'plot2typorod'        : wx.NewId(),
                        'plot1sclinlin'       : wx.NewId(),
                        'plot1scloglog'       : wx.NewId(),
                        'plot1scloglin'       : wx.NewId(),
                        'plot1sclinlog'       : wx.NewId(),
                        'plot2sclinlin'       : wx.NewId(),
                        'plot2scloglog'       : wx.NewId(),
                        'plot2scloglin'       : wx.NewId(),
                        'plot2sclinlog'       : wx.NewId(),
                        'secplottotal'        : wx.NewId(),
                        'secplotmean'         : wx.NewId(),
                        'secplotq'            : wx.NewId(),
                        'secplotframe'        : wx.NewId(),
                        'secplottime'         : wx.NewId(),
                        'secplotrg'           : wx.NewId(),
                        'secplotmw'           : wx.NewId(),
                        'secploti0'           : wx.NewId(),
                        'secplotnone'         : wx.NewId(),
                        'secplotlylin'        : wx.NewId(),
                        'secplotlylog'        : wx.NewId(),
                        'secplotrylin'        : wx.NewId(),
                        'secplotrylog'        : wx.NewId(),
                        'secplotxlin'         : wx.NewId(),
                        'secplotxlog'         : wx.NewId(),
                        'help'                : wx.NewId(),
                        'about'               : wx.NewId(),
                        'guinierfit'          : wx.NewId(),
                        'molweight'           : wx.NewId(),
                        'saveWorkspace'       : wx.NewId(),
                        'loadWorkspace'       : wx.NewId(),
                        'average'             : wx.NewId(),
                        'subtract'            : wx.NewId(),
                        'merge'               : wx.NewId(),
                        'rebin'               : wx.NewId(),
                        'interpolate'         : wx.NewId(),
                        'q*10'                : wx.NewId(),
                        'q/10'                : wx.NewId(),
                        'norm_conc'           : wx.NewId(),
                        'mwstandard'          : wx.NewId(),
                        'showimage'           : wx.NewId(),
                        'showdata'            : wx.NewId(),
                        'showheader'          : wx.NewId()}
        
        self.tbIcon = RawTaskbarIcon(self)
        
        self.guinierframe = None
        self.molweightframe = None
        self.raw_settings = RAWSettings.RawGuiSettings()
        
        self.RAWWorkDir = RAWWorkDir
          
        self.OnlineControl = OnlineController(self, self.raw_settings)
         
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths([-3, -2, -1])
        self.statusbar.SetStatusText('Mode: OFFLINE', 2)    
        self.Bind(wx.EVT_CLOSE, self._onCloseWindow)
        
        # *************** Set minimum frame size ***************
        self.SetMinSize((800,600))
        
        # /* CREATE PLOT NOTEBOOK */
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        
        self.plot_notebook = aui.AuiNotebook(self, style = aui.AUI_NB_TAB_MOVE | aui.AUI_NB_TAB_SPLIT | aui.AUI_NB_SCROLL_BUTTONS)
	#self.plot_notebook = MyAuiNotebook(self, style = aui.AUI_NB_TAB_MOVE | aui.AUI_NB_TAB_SPLIT | aui.AUI_NB_SCROLL_BUTTONS)


        plot_panel = RAWPlot.PlotPanel(self.plot_notebook, -1, 'PlotPanel')
        img_panel = RAWImage.ImagePanel(self.plot_notebook, -1, 'ImagePanel')
        iftplot_panel = RAWPlot.IftPlotPanel(self.plot_notebook, -1, 'IFTPlotPanel')
        sec_panel = RAWPlot.SECPlotPanel(self.plot_notebook,-1, 'SECPlotPanel')
        
        self.plot_notebook.AddPage(plot_panel, "Main Plot", True)
        self.plot_notebook.AddPage(iftplot_panel, "IFT Plot", False)
        self.plot_notebook.AddPage(img_panel, "Image", False)
        self.plot_notebook.AddPage(sec_panel, "SEC", False)
        
                             
        self.control_notebook = aui.AuiNotebook(self, style = aui.AUI_NB_TAB_MOVE)
        page2 = ManipulationPanel(self.control_notebook, self.raw_settings)
        page4 = SECPanel(self.control_notebook, self.raw_settings)
        page1 = FilePanel(self.control_notebook)
        page3 = IFTPanel(self.control_notebook, self.raw_settings)
        
       
        self.control_notebook.AddPage(page1, "Files", True)
        self.control_notebook.AddPage(page2, "Manipulation", False)
        self.control_notebook.AddPage(page3, "IFT", False)
        self.control_notebook.AddPage(page4, "SEC",False)
        
        self.info_panel = InformationPanel(self)
        self.centering_panel = CenteringPanel(self, -1)
        self.masking_panel = MaskingPanel(self, -1)

        self._mgr.AddPane(self.info_panel, aui.AuiPaneInfo().Name("infopanel").
                          CloseButton(False).Left().Layer(0).Caption("Information Panel").PinButton(True).Row(0).Position(0))
        self._mgr.AddPane(self.control_notebook, aui.AuiPaneInfo().Name("ctrlpanel").
                          CloseButton(False).Left().Layer(0).Caption("Control Panel").MinSize((400,300)).PinButton(True).Row(0).Position(1))
        self._mgr.AddPane(self.plot_notebook, aui.AuiPaneInfo().Name("plotpanel").
                          CloseButton(False).Centre().Layer(0).Caption("Plot Panel"))
        
        self._mgr.AddPane(self.centering_panel, aui.AuiPaneInfo().Name("centeringpanel").
                           CloseButton(False).Left().Layer(0).Caption("Centering / Calibration").
                           PinButton(True).Row(0).Position(2))

        self._mgr.AddPane(self.masking_panel, aui.AuiPaneInfo().Name("maskingpanel").
                           CloseButton(False).Left().Layer(0).Caption("Masking").
                           PinButton(True).Row(0).Position(2))

        self._mgr.GetPane(self.centering_panel).Show(False)
        self._mgr.GetPane(self.centering_panel).dock_proportion = 350000
        
        self._mgr.GetPane(self.masking_panel).Show(False)
        self._mgr.GetPane(self.masking_panel).dock_proportion = 350000

        self._mgr.GetPane(self.info_panel).FloatingSize((300,200))
        self._mgr.GetPane(self.control_notebook).dock_proportion = 350000
        
        self._mgr.GetPane(self.info_panel).dock_proportion = 120000
        
        self._mgr.Update()
        
        self._mgr.GetPane(self.control_notebook).MinSize((200,300))

	#print self.getRawSettings().getAllParams()['CompatibleFormats']

        #Load workdir from rawcfg.dat:
        self._loadCfg()
        self._createMenuBar()        
                
        # Start Plot Thread:
        self.main_worker_thread = MainWorkerThread(self, self.raw_settings)
        self.main_worker_thread.setDaemon(True)
        self.main_worker_thread.start()

        icon = raw_icon_embed.GetIcon()
        self.SetIcon(icon)
        app.SetTopWindow(self)
  
        self.SetSize((1024,768))
        self.CenterOnScreen()
        self.Show(True)

    def _onStartup(self, data):

        if not RAWGlobals.compiled_extensions:
            msg = 'Warning: failed to compile extensions. Loading/integrating images, creating masks, and running BIFT will be slower than normal. If you want to compile the extensions, please see the RAW install guide or contact the developers.'
            dlg = wx.MessageDialog(parent = self, message = msg, caption = 'Failed to compile extensions', style=wx.OK|wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()


        if len(data) > 1:
            arg = data[1]
            file, ext = os.path.splitext(arg)
            
            if ext == '.wsp':
                if os.path.exists(arg):
                     mainworker_cmd_queue.put(['load_workspace', [arg]])  
    
        else:
            file = os.path.join(RAWWorkDir, 'backup.cfg')
            
            if os.path.exists(file):
                dlg = wx.MessageDialog(parent = self, message = 'Load last saved configuration?', caption = 'Restore configuration', style=wx.YES_NO|wx.ICON_QUESTION)

                answer = dlg.ShowModal()
                dlg.Destroy()

                if answer == wx.ID_YES:
                    success = RAWSettings.loadSettings(self.raw_settings, file)
                
                    if success:
                        self.raw_settings.set('CurrentCfg', file)
                    else:
                        wx.CallAfter(wx.MessageBox,'Load failed, config file might be corrupted.',
                                      'Load failed', style = wx.ICON_EXCLAMATION)

            dirctrl = wx.FindWindowByName('DirCtrlPanel')
            dirctrl._useSavedPathIfExisits()

    
    def getRawSettings(self):
        return self.raw_settings

    def test(self):
        self._mgr.GetPane(self.info_panel).Show(False)
        self._mgr.Update()
        
    def queueTaskInWorkerThread(self, taskname, data):
        mainworker_cmd_queue.put([taskname, data])
        
    def closeBusyDialog(self):
        self._busyDialog.Destroy()
        self._busyDialog = None
    
    def showBusyDialog(self, text): 
        self._busyDialog = wx.BusyInfo(text, self)
    
    def getWorkerThreadQueue(self):
        return mainworker_cmd_queue
    
    def getQuestionReturnQueue(self):
        return question_return_queue
    
    def showMaskingPane(self):
        self._mgr.GetPane(self.masking_panel).Show(True)
        self._mgr.GetPane(self.centering_panel).Show(False)
        self._mgr.GetPane(self.control_notebook).Show(False)
        self._mgr.Update()
        self.plot_notebook.SetSelection(2)
        wx.FindWindowByName('MaskingPanel').updateView()
        
    def closeMaskingPane(self):
        self._mgr.GetPane(self.masking_panel).Show(False)
        self._mgr.GetPane(self.control_notebook).Show(True)
        self._mgr.Update()
        self.plot_notebook.SetSelection(0)
        
    def showCenteringPane(self):
        self._mgr.GetPane(self.centering_panel).Show(True)
        self._mgr.GetPane(self.control_notebook).Show(False)
        self._mgr.GetPane(self.masking_panel).Show(False)
        self._mgr.Update()
        self.plot_notebook.SetSelection(2)
        
        self.centering_panel.updateAll()
        
    def closeCenteringPane(self):
        self._mgr.GetPane(self.centering_panel).Show(False)
        self._mgr.GetPane(self.control_notebook).Show(True)
        self._mgr.Update()
        self.plot_notebook.SetSelection(0)

        
    def showQuestionDialogFromThread(self, question, label, button_list, icon = None, filename = None, save_path = None):
        ''' Function to show a question dialog from the thread '''
        
        question_dialog = RAWCustomCtrl.CustomQuestionDialog(self, question, button_list, label, icon, filename, save_path, style = wx.CAPTION)
        result = question_dialog.ShowModal()
        path = question_dialog.getPath()
        question_dialog.Destroy()        
        
        if path:
            question_return_queue.put([result, path])
        else:
            question_return_queue.put([result])  # put answer in thread safe queue 
        
        thread_wait_event.set()                 # Release thread from its waiting state
        
    def _loadCfg(self):
        
        try:
            file = 'rawcfg.dat'
            FileObj = open(file, 'r')
            savedInfo = cPickle.load(FileObj)
            FileObj.close()
            
            dirctrl = wx.FindWindowByName('DirCtrlPanel')
            dirctrl.SetPath(savedInfo['workdir'])
            
            self.ChangeParameter('ImageFormat', savedInfo['ImageFormat'])
        except:
            pass
    
    def showMolWeightFrame(self, sasm, manip_item):
        
        if self.molweightframe:
            self.molweightframe.Destroy()
        
        #if not self.guinierframe:
        self.molweightframe = RAWAnalysis.MolWeightFrame(self, 'Molecular Weight', sasm, manip_item)
        self.molweightframe.SetIcon(self.GetIcon())
        self.molweightframe.Show(True)

    def showGuinierFitFrame(self, sasm, manip_item):
        
        if self.guinierframe:
            self.guinierframe.Destroy()
        
        #if not self.guinierframe:
        self.guinierframe = RAWAnalysis.GuinierTestFrame(self, 'Guinier Fit', sasm, manip_item)
        self.guinierframe.SetIcon(self.GetIcon())
        self.guinierframe.Show(True)
        #else:
        #    self.guinierframe.SetFocus()
        #    self.guinierframe.Raise()
        #    self.guinierframe.RequestUserAttention()
    
#    def _onSaveSettings(self, evt):
#        ############################ KILLS BEAMSTOP MASK !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#        global expParams
#        
#        expParamsToSave = expParams
#    
#        file = self._createFileDialog(wx.SAVE)
#        
#        beamback = None
#        readback = None
#        
#        if os.path.splitext(file)[1] != '.cfg':
#            file = file + '.cfg'
#        
#        if file:
#            
#            if expParamsToSave['BeamStopMask'] != None:
#                beamback = expParamsToSave['BeamStopMask'].__copy__()
#            if expParamsToSave['ReadOutNoiseMask'] != None:
#                readback = expParamsToSave['ReadOutNoiseMask'].__copy__()
#        
#            expParamsToSave['BackgroundFile'] = None
#            expParamsToSave['BeamStopMask'] = None
#            expParamsToSave['ReadOutNoiseMask'] = None
#            
#            FileObj = open(file, 'w')
#            cPickle.dump(expParamsToSave, FileObj)
#            FileObj.close()
#            
#            backup_file = os.path.join(RAWWorkDir, 'backup.cfg')
#            
#            print backup_file
#            FileObj = open(backup_file, 'w')
#            cPickle.dump(expParamsToSave, FileObj)
#            FileObj.close()
#
#            expParamsToSave['BeamStopMask'] = beamback
#            expParamsToSave['ReadOutNoiseMask'] = readback    
            
    def _createSingleMenuBarItem(self, info):
        
        menu = wx.Menu()
        
        for each in info:
            
            type = each[3]
            bindFunc = each[2]
            menuid = each[1]
            label = each[0]
            
            if type == 'normal':
                menu.Append(menuid, label)
                self.Bind(wx.EVT_MENU, bindFunc, id = menuid)
            
            elif type == 'check':
                menu.AppendCheckItem(menuid, label)
                self.Bind(wx.EVT_MENU, bindFunc, id = menuid)
                
            elif type == 'radio':
                menu.AppendRadioItem(menuid, label)
                self.Bind(wx.EVT_MENU, bindFunc, id = menuid)
                
            elif type == 'submenu':
                submenu = self._createSingleMenuBarItem(bindFunc)
                menu.AppendSubMenu(submenu, label)
                
            elif type == 'separator':
                menu.AppendSeparator()
                
        return menu
    
    def _onHelp(self, event):
        msg = "In program help is not current available for RAW. For tutorials, demo videos, and installation guides, please see the RAW project home page (select Help->About for more details)."
        wx.CallAfter(wx.MessageBox, msg, 'Sorry!', style=wx.OK|wx.ICON_INFORMATION)
        # os.execl('xchm')
    
    def _createMenuBar(self):
        
        submenus = {                    
                    'viewPlot1Scale':[('Lin-Lin', self.MenuIDs['plot1sclinlin'], self._onViewMenu, 'radio'),
                                      ('Log-Lin', self.MenuIDs['plot1scloglin'], self._onViewMenu, 'radio'),
                                      ('Log-Log', self.MenuIDs['plot1scloglog'], self._onViewMenu, 'radio'),
                                      ('Lin-Log', self.MenuIDs['plot1sclinlog'], self._onViewMenu, 'radio'),
                                      ('Guinier', self.MenuIDs['plot1tyguinier'],self._onViewMenu, 'radio'),
                                      ('Kratky',  self.MenuIDs['plot1tykratky'], self._onViewMenu, 'radio'),                            
                                      ('Porod',   self.MenuIDs['plot1typorod'],  self._onViewMenu, 'radio')],
                                      
                    'viewPlot2Scale':[('Lin-Lin', self.MenuIDs['plot2sclinlin'], self._onViewMenu, 'radio'),
                                      ('Log-Lin', self.MenuIDs['plot2scloglin'], self._onViewMenu, 'radio'),
                                      ('Log-Log', self.MenuIDs['plot2scloglog'], self._onViewMenu, 'radio'),
                                      ('Lin-Log', self.MenuIDs['plot2sclinlog'], self._onViewMenu, 'radio'),
                                      ('Guinier', self.MenuIDs['plot2tyguinier'],self._onViewMenu, 'radio'),
                                      ('Kratky',  self.MenuIDs['plot2tykratky'], self._onViewMenu, 'radio'),
                                      ('Porod',   self.MenuIDs['plot2typorod'],  self._onViewMenu, 'radio')],
                    
                    'onlinemenu':    [('Offline', self.MenuIDs['goOffline'], self._onOnlineMenu, 'radio'),
                                      ('Online', self.MenuIDs['goOnline'], self._onOnlineMenu, 'radio')],

                    'viewSECLeft':   [('Integrated Intensity', self.MenuIDs['secplottotal'], self._onViewMenu, 'radio'),
                                      ('Mean Intensity', self.MenuIDs['secplotmean'], self._onViewMenu, 'radio'),
                                      ('Intensity at q = . .', self.MenuIDs['secplotq'], self._onViewMenu, 'radio')],

                    'viewSECRight':  [('RG', self.MenuIDs['secplotrg'], self._onViewMenu, 'radio'),
                                      ('MW', self.MenuIDs['secplotmw'], self._onViewMenu, 'radio'),
                                      ('I0', self.MenuIDs['secploti0'], self._onViewMenu, 'radio'),
                                      ('None', self.MenuIDs['secplotnone'], self._onViewMenu, 'radio')],

                    'viewSECX':   [('Frame Number', self.MenuIDs['secplotframe'], self._onViewMenu, 'radio'),
                                      ('Time', self.MenuIDs['secplottime'], self._onViewMenu, 'radio')],
                    'operations':    [('Subtract', self.MenuIDs['subtract'], self._onToolsMenu, 'normal'),
                                      ('Average', self.MenuIDs['average'], self._onToolsMenu, 'normal'),
                                      ('Merge', self.MenuIDs['merge'], self._onToolsMenu, 'normal'),
                                      ('Rebin', self.MenuIDs['rebin'], self._onToolsMenu, 'normal'),
                                      ('Interpolate', self.MenuIDs['interpolate'], self._onToolsMenu, 'normal'),
                                      ('Normalize by concentration', self.MenuIDs['norm_conc'], self._onToolsMenu, 'normal')],
                    'convertq':      [('q * 10', self.MenuIDs['q*10'], self._onToolsMenu, 'normal'),
                                      ('q / 10', self.MenuIDs['q/10'], self._onToolsMenu, 'normal')]}         
                                    
        
        menus = [('&File',    [('&Load Settings', self.MenuIDs['loadSettings'], self._onLoadMenu, 'normal'),
                               ('&Save Settings', self.MenuIDs['saveSettings'], self._onSaveMenu, 'normal'),
                               (None, None, None, 'separator'),
                               ('&Load Workspace', self.MenuIDs['loadWorkspace'], self._onLoadWorkspaceMenu, 'normal'),
                               ('&Save Workspace', self.MenuIDs['saveWorkspace'], self._onSaveWorkspaceMenu, 'normal'),
                               (None, None, None, 'separator'),
                               ('E&xit', self.MenuIDs['exit'], self._onFileMenu, 'normal')]),
                 
                 ('&Options', [('&Advanced Options...', self.MenuIDs['advancedOptions'], self._onOptionsMenu, 'normal'),
                              ('&Online mode', None, submenus['onlinemenu'], 'submenu')]),
                              
                 ('&View',    [('&Show image', self.MenuIDs['showimage'], self._onViewMenu, 'normal'),
                               ('&Show data', self.MenuIDs['showdata'], self._onViewMenu, 'normal'),
                               ('&Show header', self.MenuIDs['showheader'], self._onViewMenu, 'normal'),
                               (None, None, None, 'separator'),
                               ('&Top Main Plot Axes', None, submenus['viewPlot1Scale'], 'submenu'),
                               ('&Bottom Main Plot Axes', None, submenus['viewPlot2Scale'], 'submenu'),
                               ('&SEC Plot Left Y Axis', None, submenus['viewSECLeft'], 'submenu'),
                               ('&SEC Plot Right Y Axis', None, submenus['viewSECRight'], 'submenu'),
                               ('&SEC Plot X Axis', None, submenus['viewSECX'], 'submenu')
                               ]),
                              
                 ('&Tools',   [('&Operations', None, submenus['operations'], 'submenu'),
                               ('&Convert q-scale', None, submenus['convertq'], 'submenu'),
                               ('&Use as MW standard', self.MenuIDs['mwstandard'], self._onToolsMenu, 'normal'),
                               (None, None, None, 'separator'),
                               ('&Guinier fit', self.MenuIDs['guinierfit'], self._onToolsMenu, 'normal'),
                               ('&Molecular weight', self.MenuIDs['molweight'], self._onToolsMenu, 'normal'),
                               (None, None, None, 'separator'),
                               ('&Centering/Calibration', self.MenuIDs['centering'], self._onToolsMenu, 'normal'),
                               ('&Masking', self.MenuIDs['masking'], self._onToolsMenu, 'normal')
                              ]),
                              
                 ('&Help',    [('&Help!', self.MenuIDs['help'], self._onHelp, 'normal'),
                               (None, None, None, 'separator'),
                               ('&About', self.MenuIDs['about'], self._onAboutDlg, 'normal')])]
        
        menubar = wx.MenuBar()
        
        for each in menus:
         
            menuitem = self._createSingleMenuBarItem(each[1])
            menubar.Append(menuitem, each[0])    
        
        self.Bind(wx.EVT_MENU, self._onFileMenu, id = wx.ID_EXIT)

        self.SetMenuBar(menubar)
        
    def _onToolsMenu(self, evt):
        
        id = evt.GetId()
        
        if id == self.MenuIDs['guinierfit']:
                        
            manippage = wx.FindWindowByName('ManipulationPanel')

            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)
            # print page_label
            if page !=manippage:
                wx.MessageBox('The selected operation cannot be performed unless the manipulation window is selected.', 'Select Manipulation Window', style = wx.ICON_INFORMATION)
                return
            
            if len(manippage.getSelectedItems()) > 0:
                sasm = manippage.getSelectedItems()[0].getSASM()
                self.showGuinierFitFrame(sasm, manippage.getSelectedItems()[0])
            else:
                wx.MessageBox("Please select a scattering profile from the list on the manipulation page.", "No profile selected")
        
        elif id == self.MenuIDs['molweight']:
            manippage = wx.FindWindowByName('ManipulationPanel')

            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)
            # print page_label
            if page !=manippage:
                wx.MessageBox('The selected operation cannot be performed unless the manipulation window is selected.', 'Select Manipulation Window', style = wx.ICON_INFORMATION)
                return
            
            if len(manippage.getSelectedItems()) > 0:
                sasm = manippage.getSelectedItems()[0].getSASM()
                self.showMolWeightFrame(sasm, manippage.getSelectedItems()[0])
            else:
                wx.MessageBox("Please select a scattering profile from the list on the manipulation page.", "No profile selected")
        
        elif id == self.MenuIDs['centering']:
            self.showCenteringPane()
        
        elif id == self.MenuIDs['masking']:
            self.showMaskingPane()
        
        elif id == self.MenuIDs['subtract']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)
            # print page_label
            if page != wx.FindWindowByName('ManipulationPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation window is selected.', 'Select Manipulation Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            marked_item = page.getBackgroundItem()
            mainworker_cmd_queue.put(['subtract_items', [marked_item, selected_items]])

        elif id == self.MenuIDs['average']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)
            # print page_label
            if page != wx.FindWindowByName('ManipulationPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation window is selected.', 'Select Manipulation Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            mainworker_cmd_queue.put(['average_items', selected_items])

        elif id == self.MenuIDs['merge']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)
            # print page_label
            if page != wx.FindWindowByName('ManipulationPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation window is selected.', 'Select Manipulation Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            marked_item = page.getBackgroundItem()
            mainworker_cmd_queue.put(['merge_items', [marked_item, selected_items]])

        elif id == self.MenuIDs['rebin']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)
            # print page_label
            if page != wx.FindWindowByName('ManipulationPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation window is selected.', 'Select Manipulation Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()

            dlg = RebinDialog(self)
            retval = dlg.ShowModal()
            ret, logbin = dlg.getValues()
            dlg.Destroy()
            
            if retval != wx.ID_CANCEL:
                mainworker_cmd_queue.put(['rebin_items', [selected_items, ret, logbin]])

        elif id == self.MenuIDs['interpolate']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)
            # print page_label
            if page != wx.FindWindowByName('ManipulationPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation window is selected.', 'Select Manipulation Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            marked_item = page.getBackgroundItem()
            mainworker_cmd_queue.put(['interpolate_items', [marked_item, selected_items]])

        elif id == self.MenuIDs['q*10']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)

            if page != wx.FindWindowByName('ManipulationPanel') and page != wx.FindWindowByName('IFTPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation or IFT window is selected.', 'Select Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            altered=[]
            for item in selected_items:
                sasm = item.sasm

                sasm.scaleBinnedQ(10.0)
                item._updateQTextCtrl()
                altered.append(sasm)

            wx.CallAfter(sasm.plot_panel.updatePlotAfterManipulation, altered)

        elif id == self.MenuIDs['q/10']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)

            if page != wx.FindWindowByName('ManipulationPanel') and page != wx.FindWindowByName('IFTPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation or IFT window is selected.', 'Select Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            altered=[]
            for item in selected_items:
                sasm = item.sasm

                sasm.scaleBinnedQ(0.1)
                item._updateQTextCtrl()
                altered.append(sasm)

            wx.CallAfter(sasm.plot_panel.updatePlotAfterManipulation, altered)

        elif id == self.MenuIDs['norm_conc']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)
            
            if page != wx.FindWindowByName('ManipulationPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation window is selected.', 'Select Manipulation Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            mainworker_cmd_queue.put(['normalize_conc', [selected_items]])

        elif id == self.MenuIDs['mwstandard']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)
            
            if page != wx.FindWindowByName('ManipulationPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation window is selected.', 'Select Manipulation Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()

            if len(selected_items) !=1:
                wx.MessageBox('Please select one (and only one) item to use as the MW standard.', 'Select Item', style = wx.ICON_INFORMATION)
                return

            selected_items[0].useAsMWStandard()

    def _onViewMenu(self, evt):
        
        val = evt.GetId()

        if val == self.MenuIDs['showimage']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)

            if page != wx.FindWindowByName('ManipulationPanel') and page != wx.FindWindowByName('IFTPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation or IFT window is selected.', 'Select Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            if len(selected_items) !=1:
                wx.MessageBox('Please select one (and only one) item to view the image.', 'Select Item', style = wx.ICON_INFORMATION)
                return
            
            if not selected_items[0].sasm.getAllParameters().has_key('load_path'):
                wx.MessageBox('The image associated with the data could not be found.', 'Image Not Found', style = wx.ICON_INFORMATION)
                return

            selected_items[0]._onShowImage()


        elif val == self.MenuIDs['showdata']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)

            if page != wx.FindWindowByName('ManipulationPanel') and page != wx.FindWindowByName('IFTPanel') and page != wx.FindWindowByName('SECPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation or IFT window is selected.', 'Select Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            if len(selected_items) !=1:
                wx.MessageBox('Please select one (and only one) item to view the data.', 'Select Item', style = wx.ICON_INFORMATION)
                return
            if page == wx.FindWindowByName('SECPanel'):
                dlg = SECDataDialog(self, selected_items[0].secm)
            else:
                dlg = DataDialog(self, selected_items[0].sasm)
            dlg.ShowModal()
            dlg.Destroy()

        elif val == self.MenuIDs['showheader']:
            current_page = self.control_notebook.GetSelection()
            page = self.control_notebook.GetPage(current_page)

            if page != wx.FindWindowByName('ManipulationPanel') and page != wx.FindWindowByName('IFTPanel'):
                wx.MessageBox('The selected operation cannot be performed unless the manipulation or IFT window is selected.', 'Select Window', style = wx.ICON_INFORMATION)
                return

            selected_items = page.getSelectedItems()
            if len(selected_items) !=1:
                wx.MessageBox('Please select one (and only one) item to view the data.', 'Select Item', style = wx.ICON_INFORMATION)
                return

            dlg = HdrDataDialog(self, selected_items[0].sasm)
            dlg.ShowModal()
            dlg.Destroy()

        else:
            key = [k for k, v in self.MenuIDs.iteritems() if v == val][0]
            
            plotpanel = wx.FindWindowByName('PlotPanel')
            secplotpanel = wx.FindWindowByName('SECPlotPanel')
            
            if key[0:7] == 'plot2sc':
                plotpanel.plotparams['axesscale2'] = key[-6:]
                plotpanel.plotparams['plot2type'] = 'subtracted'
                plotpanel.updatePlotAxes()
                plotpanel.updatePlotType(plotpanel.subplot2)
             
            elif key[0:7] == 'plot1sc':
                plotpanel.plotparams['axesscale1'] = key[-6:]
                plotpanel.plotparams['plot1type'] = 'normal'
                plotpanel.updatePlotAxes()
                plotpanel.updatePlotType(plotpanel.subplot1)
                
            elif key[0:7] == 'plot1ty':
                plotpanel.plotparams['plot1type'] = key[7:]
                
                if key[7:] == 'guinier':
                    plotpanel.plotparams['axesscale1'] = 'loglin'
                    plotpanel.updatePlotAxes()
                
                elif key[7:] == 'kratky' or key[7:] == 'porod':
                    plotpanel.plotparams['axesscale1'] = 'linlin'
                    plotpanel.updatePlotAxes()
                    
                plotpanel.updatePlotType(plotpanel.subplot1)
                
        
            elif key[0:7] == 'plot2ty':
                plotpanel.plotparams['plot2type'] = key[7:]
                
                
                if key[7:] == 'guinier':
                    plotpanel.plotparams['axesscale2'] = 'loglin'
                    plotpanel.updatePlotAxes()
                    
                elif key[7:] == 'kratky' or key[7:] == 'porod':
                    plotpanel.plotparams['axesscale2'] = 'linlin'
                    plotpanel.updatePlotAxes()
                
                plotpanel.updatePlotType(plotpanel.subplot2)

            if key == 'secplottotal':
                secplotpanel.plotparams['y_axis_display'] = 'total'
                secplotpanel.updatePlotData(secplotpanel.subplot1)

            elif key == 'secplotmean':
                secplotpanel.plotparams['y_axis_display'] = 'mean'
                secplotpanel.updatePlotData(secplotpanel.subplot1)

            elif key == 'secplotq':
                secplotpanel.plotparams['y_axis_display'] = 'qspec'
                # print 'Calling updatePlotData'
                secplotpanel._getQValue()
                secplotpanel.updatePlotData(secplotpanel.subplot1)

            elif key == 'secplotframe':
                secplotpanel.plotparams['x_axis_display'] = 'frame'
                secplotpanel.updatePlotData(secplotpanel.subplot1)
            elif key == 'secplottime':
                secplotpanel.plotparams['x_axis_display'] = 'time'
                secplotpanel.updatePlotData(secplotpanel.subplot1)

            elif key == 'secplotrg':
                secplotpanel.plotparams['secm_plot_calc'] = 'RG'
                raxis_on = secplotpanel.plotparams['framestyle1'].find('r')
                if raxis_on>-1:
                    secplotpanel.plotparams['framestyle1'] = secplotpanel.plotparams['framestyle1'].replace('r','')
                    secplotpanel.plotparams['framestyle2'] = secplotpanel.plotparams['framestyle2']+'r'
                    secplotpanel._updateFrameStylesForAllPlots()
                secplotpanel.updatePlotData(secplotpanel.ryaxis)
                
            elif key == 'secplotmw':
                secplotpanel.plotparams['secm_plot_calc'] = 'MW'
                raxis_on = secplotpanel.plotparams['framestyle1'].find('r')
                if raxis_on>-1:
                    secplotpanel.plotparams['framestyle1'] = secplotpanel.plotparams['framestyle1'].replace('r','')
                    secplotpanel.plotparams['framestyle2'] = secplotpanel.plotparams['framestyle2']+'r'
                    secplotpanel._updateFrameStylesForAllPlots()
                secplotpanel.updatePlotData(secplotpanel.ryaxis)
                
            elif key == 'secploti0':
                secplotpanel.plotparams['secm_plot_calc'] = 'I0'
                raxis_on = secplotpanel.plotparams['framestyle1'].find('r')
                if raxis_on>-1:
                    secplotpanel.plotparams['framestyle1'] = secplotpanel.plotparams['framestyle1'].replace('r','')
                    secplotpanel.plotparams['framestyle2'] = secplotpanel.plotparams['framestyle2']+'r'
                    secplotpanel._updateFrameStylesForAllPlots()
                secplotpanel.updatePlotData(secplotpanel.ryaxis)
                
            elif key == 'secplotnone':
                secplotpanel.plotparams['secm_plot_calc'] = 'None'
                secplotpanel.updatePlotData(secplotpanel.ryaxis)

            elif key == 'secplotlylin':
                param = secplotpanel.plotparams['axesscale1']
                param = 'lin'+param[3:]
                secplotpanel.plotparams['axesscale1'] = param

                secplotpanel.updatePlotAxes()

            elif key == 'secplotlylog':
                param = secplotpanel.plotparams['axesscale1']
                param = 'log'+param[3:]
                secplotpanel.plotparams['axesscale1'] = param

                secplotpanel.updatePlotAxes()

            elif key == 'secplotrylog':
                param = secplotpanel.plotparams['axesscale2']
                param = 'log'+param[3:]
                secplotpanel.plotparams['axesscale2'] = param

                secplotpanel.updatePlotAxes()

            elif key == 'secplotrylin':
                param = secplotpanel.plotparams['axesscale2']
                param = 'lin'+ param[3:]
                secplotpanel.plotparams['axesscale2'] = param

                secplotpanel.updatePlotAxes()

            elif key == 'secplotxlin':
                param = secplotpanel.plotparams['axesscale1']
                param = param[:3]+'lin'
                secplotpanel.plotparams['axesscale1'] = param

                param = secplotpanel.plotparams['axesscale2']
                param = param[:3]+'lin'
                secplotpanel.plotparams['axesscale2'] = param

                secplotpanel.updatePlotAxes()

            elif key == 'secplotxlog':
                param = secplotpanel.plotparams['axesscale1']
                param = param[:3]+'log'
                secplotpanel.plotparams['axesscale1'] = param

                param = secplotpanel.plotparams['axesscale2']
                param = param[:3]+'log'
                secplotpanel.plotparams['axesscale2'] = param

                secplotpanel.updatePlotAxes()
    
    def _onSaveMenu(self, event):
        self._onSaveSettings(None)

    def _onOnlineMenu(self, event):
        
        id = event.GetId()
#        
        if id == self.MenuIDs['goOnline']:
            is_online = self.OnlineControl.goOnline()
            
            if is_online:
                self.setStatus('Mode: ONLINE', 2)
            else:
                menubar = self.GetMenuBar()
                item = menubar.FindItemById(self.MenuIDs['goOffline'])
                item.Check(True)
                
        else:
            self.setStatus('Mode: OFFLINE', 2)
            self.OnlineControl.goOffline()
        
        
    def _onOptionsMenu(self, event):
        
        if event.GetId() == self.MenuIDs['advancedOptions']:
            self.showOptionsDialog()
    
    def _onFileMenu(self, event):
        
        if event.GetId() == self.MenuIDs['exit'] or event.GetId() == wx.ID_EXIT:
            self._onCloseWindow(0)
            
    def _onLoadMenu(self, event):
        self._onLoadSettings(None)
    
    def _onLoadSettings(self, evt):   
        
        file = self._createFileDialog(wx.OPEN)
        
        if file:
            success = RAWSettings.loadSettings(self.raw_settings, file)
            
            if success:
                self.raw_settings.set('CurrentCfg', file)
            
            
    def _onSaveSettings(self, evt):   
        file = self._createFileDialog(wx.SAVE)
        
        if file:
            
            if os.path.splitext(file)[1] != '.cfg':
                file = file + '.cfg'
            
            success = RAWSettings.saveSettings(self.raw_settings, file)
            
            if success:
                self.raw_settings.set('CurrentCfg', file)
                
    def _onLoadWorkspaceMenu(self, evt):
        manip_panel = wx.FindWindowByName('ManipulationPanel')
        
        all_items = manip_panel.getItems()
        
        file = self._createFileDialog(wx.OPEN, 'Workspace files', '*.wsp')
        
        if file:
            if os.path.splitext(file)[1] != '.wsp':
                file = file + '.wsp'
        
            mainworker_cmd_queue.put(['load_workspace', [file]])
    
    def _onSaveWorkspaceMenu(self, evt):
        self.saveWorkspace()
        
    def saveWorkspace(self):
        
        manip_panel = wx.FindWindowByName('ManipulationPanel')
        ift_panel = wx.FindWindowByName('IFTPanel')
        sec_panel = wx.FindWindowByName('SECPanel')
        
        sasm_items = manip_panel.getItems()
        ift_items = ift_panel.getItems()
        secm_items = sec_panel.getItems()
        
        file = self._createFileDialog(wx.SAVE, 'Workspace files', '*.wsp')
        
        if file:
            if os.path.splitext(file)[1] != '.wsp':
                file = file + '.wsp'
        
            mainworker_cmd_queue.put(['save_workspace', [sasm_items, ift_items, secm_items, file]])
    
    
    def showOptionsDialog(self, focusHead = None):

        if focusHead != None:
            dialog = RAWOptions.OptionsDialog(self, self.raw_settings, focusHeader = focusHead)
        else:

            dialog = RAWOptions.OptionsDialog(self, self.raw_settings)

        dialog.ShowModal()
        
    def getMenuIds(self):
        return self.MenuIDs
    
    def setStatus(self, statustxt, idx):
        
        self.statusbar.SetStatusText(statustxt,idx)
    
    def setViewMenuScale(self, id):
        self.MenuBar.FindItemById(id).Check(True)
    
    def _onAboutDlg(self, event):
        info = wx.AboutDialogInfo()
        info.Name = "RAW"
        info.Version = "1.0.0b"
        info.Copyright = "Copyright(C) 2009 RAW"
        info.Description = "RAW is a software package primarily for SAXS 2D data reduction and 1D data analysis.\nIt provides an easy GUI for handling multiple files fast, and a\ngood alternative to commercial or protected software packages for finding\nthe Pair Distance Distribution Function\n\nPlease cite:\nBioXTAS RAW, a software program for high-throughput automated small-angle\nX-ray scattering data reduction and preliminary analysis, J. Appl. Cryst. (2009). 42, 959-964"

        info.WebSite = ("http://bioxtasraw.sourceforge.net/", "The RAW Project Homepage")
        info.Developers = [u"Soren S. Nielsen", u"Jesse B. Hopkins", u"Richard E. Gillilan", u"Jesper Nygaard", u"Kurt Andersen"]
        info.License = "This program is free software: you can redistribute it and/or modify it under the terms of the\nGNU General Public License as published by the Free Software Foundation, either version 3\n of the License, or (at your option) any later version.\n\nThis program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;\nwithout even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\nSee the GNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License along with this program.\nIf not, see http://www.gnu.org/licenses/"
        
        # Show the wx.AboutBox
        wx.AboutBox(info)
    
    def saveBackupData(self):
        
        file = 'backup.ini'
        
        try:
            file_obj = open(file, 'w')
        
            path = wx.FindWindowByName('FileListCtrl').path
            save_info = {'workdir' : path}
        
            cPickle.dump(save_info, file_obj)
            file_obj.close()
        except Exception, e:
            print e
    
    def _onCloseWindow(self, event):
        # print 'This is really working!'

        manipulation_panel = wx.FindWindowByName('ManipulationPanel')
        sec_panel = wx.FindWindowByName('SECPanel')

        answer2 = wx.ID_YES
        
        if manipulation_panel.modified_items != [] or sec_panel.modified_items != []:
            
            if manipulation_panel.modified_items !=[] and sec_panel.modified_items != []:
                message = 'manipulation and SEC '
            elif manipulation_panel.modified_items !=[] and sec_panel.modified_items == []:
                message = 'manipulation '
            else:
                message = 'SEC '

            dial2 = wx.MessageDialog(self, 'You have unsaved changes in your ' + message + 'data. Do you want to discard these changes?', 'Discard changes?', 
                                     wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            answer2 = dial2.ShowModal()
            dial2.Destroy()
        
        if answer2 == wx.ID_YES:
            self.saveBackupData()
            self.tbIcon.RemoveIcon()
            self.tbIcon.Destroy()
            self.Destroy()
        
    def _createFileDialog(self, mode, name = 'Config files', ext = '*.cfg'):
        
        file = None
        
        path = wx.FindWindowByName('FileListCtrl').path
        
        if mode == wx.OPEN:
            filters = name + ' (' + ext + ')|' + ext + '|All files (*.*)|*.*'
            dialog = wx.FileDialog( None, style = mode, wildcard = filters, defaultDir = path)
        if mode == wx.SAVE:
            filters = name + ' ('+ext+')|'+ext
            dialog = wx.FileDialog( None, style = mode | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = path)        
        
        # Show the dialog and get user input
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetPath()
            
        # Destroy the dialog
        dialog.Destroy()
        
        return file
        
class OnlineController:                                   
    def __init__(self, parent, raw_settings):
        
        self.parent = parent
        
        self.main_frame = parent

        self._raw_settings = raw_settings

        # self.update_keys = ['OnlineFilterList', 'EnableOnlineFiltering']

        self._filt_list=self._raw_settings.get('OnlineFilterList')
        self._enable_filt=self._raw_settings.get('EnableOnlineFiltering')
        
        # Setup the online file checker timer
        self.online_timer = wx.Timer()
        
        self.online_timer.Bind(wx.EVT_TIMER, self.onOnlineTimer)

        self.old_dir_list_dict = {}
        self.is_online = False
        self.seek_dir = []
        self.bg_filename = None
    
    def selectSearchDir(self):
        self.dirctrl = wx.FindWindowByName('DirCtrlPanel')
        
        path = None
        
        if self.seek_dir == []:
            self.seek_dir = str(self.dirctrl.getDirLabel())

        dirdlg = wx.DirDialog(self.parent, "Please select search directory:", str(self.seek_dir))

        if dirdlg.ShowModal() == wx.ID_OK:               
            path = dirdlg.GetPath()
            self.seek_dir = path 
            
        return path    
    
    def goOnline(self):
        
        path = self.selectSearchDir()
        
        if path != None:
            dir_list = os.listdir(path)
            
            dir_list_dict = {}
            for each_file in dir_list:
                dir_list_dict[each_file] = (os.path.getmtime(os.path.join(self.seek_dir, each_file)))
            
            self.old_dir_list_dict = dir_list_dict
            
            self.online_timer.Start(2000)
            return True
        
        return False
        
    def goOffline(self):
        self.online_timer.Stop()
   
    def onOnlineTimer(self, evt):
        ''' This function checks for new files and processes them as they come in '''
        self._filt_list=self._raw_settings.get('OnlineFilterList')
        self._enable_filt=self._raw_settings.get('EnableOnlineFiltering')
        
        self.file_list_ctrl = wx.FindWindowByName('FileListCtrl')
        dir_list = os.listdir(self.seek_dir)
        
        dir_list_dict = {}
        
        for each_file in dir_list:
            dir_list_dict[each_file] = (os.path.getmtime(os.path.join(self.seek_dir, each_file)))
            
        diff_list = list(set(dir_list_dict.items()) - set(self.old_dir_list_dict.items()))

        files_to_plot=[]

        if diff_list != []:
            if not self._enable_filt:

                for each in diff_list:
                    each_newfile = each[0]
                    
                    process_str = 'Processing incomming file: ' + str(each_newfile) 
                    self.main_frame.setStatus(process_str, 0)

                    filepath = os.path.join(self.seek_dir, str(each_newfile))

                    if self._fileTypeIsCompatible(filepath):
                        
                        if each_newfile in self.old_dir_list_dict:
                            #ONLY UPDATE IMAGE
                            mainworker_cmd_queue.put(['online_mode_update_data', [filepath]])
                            print 'Changed: ' + str(each_newfile)
                        else:
                            print process_str
                            files_to_plot.append(filepath)
                            mainworker_cmd_queue.put(['plot', [filepath]])
                            #UPDATE PLOT

            else:
                for each in diff_list:
                    load=True
                    each_newfile = each[0]

                    for item in self._filt_list:
                        if item[0]=='Ignore':
                            if item[2]=='At start':
                                if each_newfile.startswith(item[1]):
                                    load=False
                            elif item[2]=='Anywhere':
                                if each_newfile.find(item[1])!=-1:
                                    load=False
                            else:
                                if each_newfile.endswith(item[1]):
                                    load=False
                        else:
                            if item[2]=='At start':
                                if not each_newfile.startswith(item[1]):
                                    load=False
                            elif item[2]=='Anywhere':
                                if not each_newfile.find(item[1])!=-1:
                                    load=False
                            else:
                                if not each_newfile.endswith(item[1]):
                                    load=False

                    if load:
                        process_str = 'Processing incomming file: ' + str(each_newfile) 
                        self.main_frame.setStatus(process_str, 0)

                        filepath = os.path.join(self.seek_dir, str(each_newfile))

                        if self._fileTypeIsCompatible(filepath):
                            
                            if each_newfile in self.old_dir_list_dict:
                                #ONLY UPDATE IMAGE
                                mainworker_cmd_queue.put(['online_mode_update_data', [filepath]])
                                print 'Changed: ' + str(each_newfile)
                            else:
                                print process_str
                                files_to_plot.append(filepath)
                                # mainworker_cmd_queue.put(['plot', [filepath]])
                                #UPDATE PLOT
                    else:
                        print 'Ignored: '+str(each_newfile)

            mainworker_cmd_queue.put(['plot', files_to_plot])

            self.old_dir_list_dict.update(diff_list)
        
        
    def _fileTypeIsCompatible(self, path):
        root, ext = os.path.splitext(path)
        #print ext
        compatible_formats = self.main_frame.getRawSettings().get('CompatibleFormats')
        #print compatible_formats
        #print self.main_frame.getRawSettings().getAllParams()['CompatibleFormats']
        
        if str(ext) in compatible_formats: 
            return True
        else:
            print 'Not compatible file format.'
            return False
        


class MainWorkerThread(threading.Thread):
    
    def __init__(self, parent, raw_settings):
        
        threading.Thread.__init__(self)
        
        self._raw_settings = raw_settings
        self._parent = parent
        self._abort = False
        
        self.manipulation_panel = wx.FindWindowByName('ManipulationPanel')
        self.plot_panel = wx.FindWindowByName('PlotPanel')
        self.image_panel = wx.FindWindowByName('ImagePanel')
        self.main_frame = wx.FindWindowByName('MainFrame')
        self.dir_panel = wx.FindWindowByName('DirCtrlPanel')


        self.sec_plot_panel = wx.FindWindowByName('SECPlotPanel')
        self.sec_item_panel = wx.FindWindowByName('SECPanel')
        self.sec_control_panel = wx.FindWindowByName('SECControlPanel')
        
        
        self.ift_plot_panel = wx.FindWindowByName('IFTPlotPanel')
        
        self.ift_item_panel = wx.FindWindowByName('IFTPanel')
        
        self._commands = {'plot' : self._loadAndPlot,
                                    'online_mode_update_data' : self._onlineModeUpdate,
                                    'show_nextprev_img'     : self._loadAndShowNextImage,
                                    'show_image'            : self._loadAndShowImage,
                                    'subtract_filenames'    : self._subtractFilenames,
                                    'subtract_items'        : self._subtractItems,
                                    'average_items'         : self._averageItems,
                                    'save_items'            : self._saveItems,
                                    'save_iftitems'         : self._saveIftItems,
                                    'quick_reduce'          : self._quickReduce,
                                    'load_mask'             : self._loadMaskFile,
                                    'save_mask'             : self._saveMaskFile,
                                    'create_mask'           : self._createMask,
                                    'recreate_all_masks'    : self._recreateAllMasks,
                                    'calculate_abs_water_const' : self._calcAbsScWaterConst,
                                    'save_workspace'        : self._saveWorkspace,
                                    'load_workspace'        : self._loadWorkspace,
                                    'superimpose_items'     : self._superimposeItems,
                                    'save_analysis_info'    : self._saveAnalysisInfo,
                                    'save_all_analysis_info': self._saveAllAnalysisInfo,
                                    'merge_items'           : self._mergeItems,
                                    'rebin_items'           : self._rebinItems,
                                    'ift'                   : self._runIft,
				                    'interpolate_items'     : self._interpolateItems,
                                    'plot_iftfit'           : self._plotIftFit,
                                    'normalize_conc'        : self._normalizeByConc,
                                    'sec_plot'              : self._loadAndPlotSEC,
                                    'update_secm'           : self._updateSECM,
                                    'to_plot'               : self._sendSASMToPlot,
                                    'to_plot_SEC'           : self._sendSASMToPlotSEC,
                                    'average_items_sec'     : self._averageItemsSEC,
                                    'save_sec_data'         : self._saveSECData,
                                    'save_sec_item'         : self._saveSECItem,
                                    'calculate_params_sec'  : self._calculateSECParams}
         
        
    def run(self):
        
        while True:
            try:
                command, data = mainworker_cmd_queue.get()
            except Queue.Empty:
                command = None
                
            if command != None:
                
                if self._abort == True:
                    self._cleanUpAfterAbort()
                else:
                    self._commands[command](data)
        
    def _cleanUpAfterAbort(self):
        pass
    
    
    def _onlineModeUpdate(self, data):
        
        filename = data[0] 
    
        img_fmt = self._raw_settings.get('ImageFormat')
        
        try:
            if not os.path.isfile(filename):
                raise SASExceptions.WrongImageFormat('not a valid file!')
            
            img, imghdr = SASFileIO.loadImage(filename, img_fmt)
            
            if img == None:
                raise SASExceptions.WrongImageFormat('not a valid file!')
                
        except Exception, e:
            print  'File load failed: ' + str(e)
            return 
        
        parameters = {'filename' : os.path.split(filename)[1],
                      'imageHeader' : imghdr}
        
        bogus_sasm = SASM.SASM([0,1], [0,1], [0,1], parameters)
        
        self._sendImageToDisplay(img, bogus_sasm)
        
    
    def _sendSASMToIFTPlot(self, sasm, axes_num = 1, item_colour = 'black', line_color = None, no_update = False):
        
        wx.CallAfter(self.ift_plot_panel.plotSASM, sasm, axes_num, color = line_color)
        
        if no_update == False:
            wx.CallAfter(self.ift_plot_panel.fitAxis)
        
        wx.CallAfter(self.ift_plot_panel.updateLegend, 1)
        wx.CallAfter(self.ift_plot_panel.updateLegend, 2)
        
        ift_parameters = sasm.getAllParameters()
        
        wx.CallAfter(self.ift_item_panel.addItem, sasm, item_colour, ift_parameters)
        
        
    def _sendSASMToPlot(self, sasm, axes_num = 1, item_colour = 'black', line_color = None, no_update = False, notsaved = False, update_legend = True):
        
        if type(sasm) == list:
            length = len(sasm)
        
            for i in range(0, length):
                wx.CallAfter(self.plot_panel.plotSASM, sasm[i], axes_num, color = line_color)
                wx.CallAfter(self.manipulation_panel.addItem, sasm[i], item_colour, notsaved = notsaved)
        else:
            wx.CallAfter(self.plot_panel.plotSASM, sasm, axes_num, color = line_color)        
            wx.CallAfter(self.manipulation_panel.addItem, sasm, item_colour, notsaved = notsaved)
            
        if no_update == False:
            wx.CallAfter(self.plot_panel.fitAxis)

        if update_legend:
            wx.CallAfter(self.plot_panel.updateLegend, 1)
            wx.CallAfter(self.plot_panel.updateLegend, 2)


    def _sendSASMToPlotSEC(self, sasm, axes_num = 1, item_colour = 'black', line_color = None, no_update = False, notsaved = False, update_legend = True):
        
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while plotting frames...')

        if type(sasm) == list:
            length = len(sasm)
        
            for i in range(0, length):
                wx.CallAfter(self.plot_panel.plotSASM, sasm[i], axes_num, color = line_color)
                wx.CallAfter(self.manipulation_panel.addItem, sasm[i], item_colour, notsaved = notsaved)
        else:
            wx.CallAfter(self.plot_panel.plotSASM, sasm, axes_num, color = line_color)        
            wx.CallAfter(self.manipulation_panel.addItem, sasm, item_colour, notsaved = notsaved)
            
        if no_update == False:
            wx.CallAfter(self.plot_panel.fitAxis)

        if update_legend:
            wx.CallAfter(self.plot_panel.updateLegend, 1)
            wx.CallAfter(self.plot_panel.updateLegend, 2)

        wx.CallAfter(self.main_frame.closeBusyDialog) 


    def _sendSECMToPlot(self, secm, item_colour = 'black', line_color = None, no_update = False, notsaved = False, update_legend = True):
        
        if type(secm) == list:
            length = len(secm)
        
            for i in range(0, length):
                wx.CallAfter(self.sec_plot_panel.plotSECM, secm[i], color = line_color)
                wx.CallAfter(self.sec_item_panel.addItem, secm[i], item_colour, notsaved = notsaved)
        else:
            wx.CallAfter(self.sec_plot_panel.plotSECM, secm, color = line_color)
            wx.CallAfter(self.sec_item_panel.addItem, secm, item_colour, notsaved = notsaved)
            
        if no_update == False:
            wx.CallAfter(self.sec_plot_panel.fitAxis)

        if update_legend:
            wx.CallAfter(self.sec_plot_panel.updateLegend, 1)

        # wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 3)
        # file_list = wx.FindWindowByName('SECPanel')
        # wx.CallAfter(file_list.SetFocus)


    def _updateSECMPlot(self, secm, item_colour = 'black', line_color = None, no_update = False, notsaved = False):
        
        if type(secm) == list:
            # length = len(secm)
        
            wx.CallAfter(self.sec_plot_panel.updatePlotAfterManipulation, secm)

        else:
            secm_list=[secm]
            wx.CallAfter(self.sec_plot_panel.updatePlotAfterManipulation, secm_list)
            
        if no_update == False:
            wx.CallAfter(self.sec_plot_panel.fitAxis)

        wx.CallAfter(self.sec_plot_panel.updateLegend, 1)

        # wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 3)
        # file_list = wx.FindWindowByName('SECPanel')
        # wx.CallAfter(file_list.SetFocus)

        
    def _sendImageToDisplay(self, img, sasm):
        wx.CallAfter(self.image_panel.showImage, img, sasm)
    
    ################################
    # COMMANDS:
    ################################
    
    def _calcAbsScWaterConst(self, data):
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while loading files and calculating the absolute scale constant...')
    
        abs_scale_constant = 1.0
        water_filename = data[0]
        empty_filename = data[1]
        waterI0 = data[2]

        try:
            filename = water_filename
            water_sasm, img = SASFileIO.loadFile(filename, self._raw_settings, no_processing = True)
            filename = empty_filename
            empty_sasm, img = SASFileIO.loadFile(filename, self._raw_settings, no_processing = True)
                        
            abs_scale_constant = SASM.calcAbsoluteScaleWaterConst(water_sasm, empty_sasm, waterI0, self._raw_settings)
        except (SASExceptions.UnrecognizedDataFormat, SASExceptions.WrongImageFormat), msg:
            self._showDataFormatError(os.path.split(filename)[1])    
        except SASExceptions.DataNotCompatible, msg:
            self._showSubtractionError(water_sasm, empty_sasm)

        wx.CallAfter(self.main_frame.closeBusyDialog) 
        question_return_queue.put(abs_scale_constant)
    
    
    def _runBIFT(self, sasm, parameters):
        args = parameters
        ift_sasm = BIFT.doBift(sasm, *args)
        return ift_sasm
    
    def _runManualIft(self, sasm, parameters):
        dmax = parameters['dmax']
        alpha = parameters['alpha']
        
        ift_sasm = BIFT.SingleSolve(alpha, dmax, sasm, 50)
        return ift_sasm
    
    def _runGnomIft(self, data):
        pass
    
    def _runIft(self, data):
        algo = data[0]
        selected_items = data[1]
        ift_parameters = data[2]
        
        global cancel_ift
        
        for each_item in selected_items:
            
            if cancel_ift:
                cancel_ift = False
                print 'got cancel'
                break
                
            sasm = each_item.getSASM()
            
            if sasm.getParameter('orig_sasm') != None:
                sasm = sasm.getParameter('orig_sasm')
            
            old_filename = sasm.getParameter('filename')
        
            if algo == 'BIFT':
                try:     
                    #parameters = (50, 1e10, 10.0, 16, 200, 10, 20)
                    parameters = (self._raw_settings.get('PrPoints'),
                                  self._raw_settings.get('maxAlpha'),
                                  self._raw_settings.get('minAlpha'),
                                  self._raw_settings.get('AlphaPoints'),
                                  self._raw_settings.get('maxDmax'),
                                  self._raw_settings.get('minDmax'),
                                  self._raw_settings.get('DmaxPoints'))
                    
                    
                    print parameters
                    
                    try:
                        ift_sasm = self._runBIFT(sasm, parameters)
                    except ValueError, e:
                        print 'Error in: ift_sasm = self._runBIFT(sasm, parameters)'
                        print e
                        continue
                
                    print 'got ift'
                    if ift_sasm == None:
                        print 'it was none!'
                        continue
                        
                        #statusdlg = wx.FindWindowByName('BIFTStatusDlg')
                        
                        #if statusdlg != None:
                        #    wx.CallAfter(statusdlg.OnClose, 1)
                        #    return
                
                except UnboundLocalError, e:
                    wx.CallAfter(wx.MessageBox, 'BIFT Search Failed...', 'Solution Search Failure')
                    print 'doBift error: ', e
            
                    statusdlg = wx.FindWindowByName('BIFTStatusDlg')
                    if statusdlg != None:
                        wx.CallAfter(statusdlg.OnClose, 1)    
                    return
            
            if algo == 'Manual':
                
                try:
                    ift_sasm = self._runManualIft(sasm, ift_parameters)
                except ValueError, e:
                    wx.CallAfter(wx.MessageBox, 'BIFT Search Failed...', 'Solution Search Failure')
                    print 'doBift error: ', e
            
                    statusdlg = wx.FindWindowByName('BIFTStatusDlg')
                    if statusdlg != None:
                        wx.CallAfter(statusdlg.OnClose, 1)    
                    return
                
                
        
            ift_sasm.setParameter('orig_sasm', sasm.copy())
            
            old_filename, ext = os.path.splitext(old_filename)
            
            new_filename = 'B_' + old_filename + '.ift'
            ift_sasm.setParameter('filename', new_filename)
            self._sendSASMToIFTPlot(ift_sasm, item_colour = 'magenta')
        
            each_item.setCurrentIFTParameters(ift_sasm.getAllParameters())
        
            #doBift(Exp, N, alphamax, alphamin, alphaN, maxDmax, minDmax, dmaxN):
            wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 1)
        
        
        
        
        print 'trying to close'
        statusdlg = wx.FindWindowByName('BIFTStatusDlg')
        if statusdlg != None:
            wx.CallAfter(statusdlg.OnClose, 1)
        
                
         
    def _saveMaskFile(self, data):
        
        fullpath_filename = data[0]
        
        masks = data[1]
        
        path, ext = os.path.splitext(fullpath_filename)
        
        if ext != '.msk':
            fullpath_filename = fullpath_filename + '.msk'
                    
        file_obj = open(fullpath_filename, 'w')
        cPickle.dump(masks, file_obj)
        file_obj.close()
    
        #wx.CallAfter(wx.MessageBox, 'The mask has been saved.', 'Mask Saved')
        img_dim = self.image_panel.img.shape
        #wx.CallAfter(RAWImage.showUseMaskDialog, fullpath_filename, img_dim)
        
    
    def _loadMaskFile(self, data):        
            wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while loading and creating mask...')

            fullpath_filename = data[0]
            
            filenamepath, extension = os.path.splitext(fullpath_filename)
        
            if extension == '.msk':
                file_obj = open(fullpath_filename, 'r')
                masks = cPickle.load(file_obj)
                file_obj.close()
        
                i=0
                for each in masks:
                    each.maskID = i
                    i = i + 1
                        
                plot_param = self.image_panel.getPlotParameters()
                plot_param['storedMasks'].extend(masks)
                self.image_panel.setPlotParameters(plot_param)

                #Plot mask on load:                
#                parameters = {'filename' : os.path.split(filenamepath)[1],
#                              'imageHeader' : []}
#                bogus_sasm= SASM.SASM([0,1], [0,1], [0,1], parameters)
#                wx.CallAfter(self.image_panel.showImage,mask, bogus_sasm)

                wx.CallAfter(self.image_panel.plotStoredMasks)
                       
            wx.CallAfter(self.main_frame.closeBusyDialog)
    
    def _recreateAllMasks(self, data):
        
        mask_dict = self._raw_settings.get('Masks')
        img_dim = self._raw_settings.get('MaskDimension')
        
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while creating all masks...')
        
        for each_key in mask_dict.keys():
            masks = mask_dict[each_key][1]
            
            if masks != None:
                mask_img = SASImage.createMaskMatrix(img_dim, masks)
                mask_param = mask_dict[each_key]
                mask_param[0] = mask_img
                mask_param[1] = masks
        
        wx.CallAfter(self.main_frame.closeBusyDialog)
    
    def _createMask(self, data):
        
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while creating the mask...')
        
        mask_key = data[0]
        masks = data[1]
        img_dim = data[2]
        
        mask_img = SASImage.createMaskMatrix(img_dim, masks)
        
        self._raw_settings.set('MaskDimension', img_dim)
        mask_dict = self._raw_settings.get('Masks')
        mask_param = mask_dict[mask_key]
        
        mask_param[0] = mask_img
        mask_param[1] = masks
                
        wx.CallAfter(self.main_frame.closeBusyDialog)
        wx.CallAfter(wx.MessageBox, 'The mask has been created and enabled.', 'Mask creation finished', style = wx.ICON_INFORMATION)
        
    def _loadAndPlot(self, filename_list):     
        # ta=time.time()
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while plotting...')

        loaded_secm = False
        loaded_sasm = False

        do_auto_save = self._raw_settings.get('AutoSaveOnImageFiles')
       
        try:
            for i in range(len(filename_list)):

                each_filename = filename_list[i]

                if os.path.splitext(each_filename)[1] == '.sec':
                    try:
                        secm = SASFileIO.loadSECFile(each_filename)
                    except:
                        self._showDataFormatError(os.path.split(each_filename)[1], include_sec = True)
                        wx.CallAfter(self.main_frame.closeBusyDialog)
                        return
                    self._sendSECMToPlot(secm, no_update = True, update_legend = False)
                    img = None
                    loaded_secm = True

                else:
                    sasm, img = SASFileIO.loadFile(each_filename, self._raw_settings)

                    loaded_sasm = True

                    # print sasm
                    # print img
                    
                    if img != None:
                        qrange = sasm.getQrange()
                        start_point = self._raw_settings.get('StartPoint')
                        # print start_point
                        end_point = self._raw_settings.get('EndPoint')
                        # print end_point
                        qrange = (start_point, len(sasm.getBinnedQ())-end_point)
                        sasm.setQrange(qrange)
                    
                    self._sendSASMToPlot(sasm, no_update = True, update_legend = False)
        
                    if do_auto_save:
                        save_path = self._raw_settings.get('ProcessedFilePath')
                        self._saveSASM(sasm, '.dat', save_path)

                if numpy.mod(i,20) == 0:
                    if loaded_sasm:
                        wx.CallAfter(self.plot_panel.canvas.draw)
                    if loaded_secm:
                        wx.CallAfter(self.sec_plot_panel.canvas.draw)

                
        except (SASExceptions.UnrecognizedDataFormat, SASExceptions.WrongImageFormat), msg:
            self._showDataFormatError(os.path.split(each_filename)[1])
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        except SASExceptions.HeaderLoadError, msg:
            wx.CallAfter(wx.MessageBox, str(msg), 'Error Loading Headerfile', style = wx.ICON_ERROR | wx.OK)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        except SASExceptions.MaskSizeError, msg:
            wx.CallAfter(wx.MessageBox, str(msg), 'Saved mask does not fit loaded image', style = wx.ICON_ERROR)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        except SASExceptions.HeaderMaskLoadError, msg:
            wx.CallAfter(wx.MessageBox, str(msg), 'Mask information was not found in header', style = wx.ICON_ERROR)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
            
        if len(filename_list) == 1 and  img != None:
            self._sendImageToDisplay(img, sasm)
        
        if loaded_secm and not loaded_sasm:
            wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 3)
        else: 
            wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 0)
        file_list = wx.FindWindowByName('FileListCtrl')
        wx.CallAfter(file_list.SetFocus)
        
        if loaded_sasm:
            wx.CallAfter(self.plot_panel.updateLegend, 1)
            wx.CallAfter(self.plot_panel.fitAxis)
        if loaded_secm:
            wx.CallAfter(self.sec_plot_panel.updateLegend, 1)
            wx.CallAfter(self.sec_plot_panel.fitAxis)
        wx.CallAfter(self.main_frame.closeBusyDialog)

        # print time.time()-ta

    def _loadAndPlotSEC(self, data):
        filename_list=data[0]
        frame_list=data[1]

        if len(data) == 3:
            update_sec_object = data[2]
        else:
            update_sec_object = False
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while SEC data loads\n(may take a while)...')

        all_secm = True
        for name in filename_list:
            if os.path.splitext(name)[1] != '.sec':
                all_secm = False
                break

        if all_secm:
            for each_filename in filename_list:
                try:
                    secm = SASFileIO.loadSECFile(each_filename)
                except:
                    self._showDataFormatError(os.path.split(each_filename)[1],include_sec=True)
                    wx.CallAfter(self.main_frame.closeBusyDialog)
                    return

                self._sendSECMToPlot(secm)

        else:
            sasm_list=[[] for i in range(len(filename_list))]

            try:
                for j in range(len(filename_list)):
                    each_filename = filename_list[j]
                    sasm, img = SASFileIO.loadFile(each_filename, self._raw_settings)
                    
                    if img != None:
                        qrange = sasm.getQrange()
                        start_point = self._raw_settings.get('StartPoint')
                        # print start_point
                        end_point = self._raw_settings.get('EndPoint')
                        # print end_point
                        qrange = (start_point, len(sasm.getBinnedQ())-end_point)
                        sasm.setQrange(qrange)
                    
                    sasm_list[j]=sasm
                    
            except (SASExceptions.UnrecognizedDataFormat, SASExceptions.WrongImageFormat), msg:
                self._showSECFormatError(os.path.split(each_filename)[1])
                wx.CallAfter(self.main_frame.closeBusyDialog)
                return
            except SASExceptions.HeaderLoadError, msg:
                wx.CallAfter(wx.MessageBox, str(msg), 'Error Loading Headerfile', style = wx.ICON_ERROR | wx.OK)
                wx.CallAfter(self.main_frame.closeBusyDialog)
                return
            except SASExceptions.MaskSizeError, msg:
                wx.CallAfter(wx.MessageBox, str(msg), 'Saved mask does not fit loaded image', style = wx.ICON_ERROR)
                wx.CallAfter(self.main_frame.closeBusyDialog)
                return
            except SASExceptions.HeaderMaskLoadError, msg:
                wx.CallAfter(wx.MessageBox, str(msg), 'Mask information was not found in header', style = wx.ICON_ERROR)
                wx.CallAfter(self.main_frame.closeBusyDialog)
                return

            secm = SASM.SECM(filename_list, sasm_list, frame_list, {})

            self._sendSECMToPlot(secm, notsaved = True)

        if update_sec_object:
            wx.CallAfter(self.sec_control_panel.updateSECItem, secm)

        # sec_window = wx.FindWindowByName('SECPlotPanel')
        # wx.CallAfter(sec_window.SetFocus)
        wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 3)
        # file_list = wx.FindWindowByName('SECPanel')
        # wx.CallAfter(file_list.SetFocus)
        
        wx.CallAfter(self.sec_plot_panel.updateLegend, 1)
        wx.CallAfter(self.sec_plot_panel.fitAxis)
        wx.CallAfter(self.main_frame.closeBusyDialog)
    

    def _updateSECM(self, data):
        filename_list = data[0]
        frame_list = data[1]
        secm = data[2]
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while SEC data loads\n(may take a while)...')


        sasm_list=[[] for i in range(len(filename_list))]

        try:
            for j in range(len(filename_list)):
                each_filename = filename_list[j]
                sasm, img = SASFileIO.loadFile(each_filename, self._raw_settings)
                
                if img != None:
                    qrange = sasm.getQrange()
                    start_point = self._raw_settings.get('StartPoint')
                    # print start_point
                    end_point = self._raw_settings.get('EndPoint')
                    # print end_point
                    qrange = (start_point, len(sasm.getBinnedQ())-end_point)
                    sasm.setQrange(qrange)
                
                sasm_list[j]=sasm
                
        except (SASExceptions.UnrecognizedDataFormat, SASExceptions.WrongImageFormat), msg:
            self._showDataFormatError(os.path.split(each_filename)[1])
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        except SASExceptions.HeaderLoadError, msg:
            wx.CallAfter(wx.MessageBox, str(msg), 'Error Loading Headerfile', style = wx.ICON_ERROR | wx.OK)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        except SASExceptions.MaskSizeError, msg:
            wx.CallAfter(wx.MessageBox, str(msg), 'Saved mask does not fit loaded image', style = wx.ICON_ERROR)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        except SASExceptions.HeaderMaskLoadError, msg:
            wx.CallAfter(wx.MessageBox, str(msg), 'Mask information was not found in header', style = wx.ICON_ERROR)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return

        secm.append(filename_list, sasm_list, frame_list)

        self._updateCalcSECParams(secm, frame_list)

        self._updateSECMPlot(secm)

        wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 3)
        file_list = wx.FindWindowByName('SECPanel')
        wx.CallAfter(file_list.SetFocus)
        
        # wx.CallAfter(self.plot_panel.updateLegend, 1)
        # wx.CallAfter(self.plot_panel.fitAxis)
        wx.CallAfter(self.main_frame.closeBusyDialog)
    

    def _calculateSECParams(self, secm):
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait, calculating (may take a while)...')
        initial_buffer_frame, final_buffer_frame, window_size = secm.getCalcParams()

        # print initial_buffer_frame
        # print final_buffer_frame
        # print window_size

        buffer_sasm_list = secm.getSASMList(initial_buffer_frame, final_buffer_frame)

        if len(buffer_sasm_list) < 2:
            buffer_avg_sasm = buffer_sasm_list[0]
        else:
            try:
                buffer_avg_sasm = SASM.average(buffer_sasm_list)
            except SASExceptions.DataNotCompatible:
                self._showAverageError(1)
                wx.CallAfter(self.main_frame.closeBusyDialog)
                return
        
        self._insertSasmFilenamePrefix(buffer_avg_sasm, 'A_')

        secm.setAverageBufferSASM(buffer_avg_sasm)

        #Now subtract the average buffer from all of the items in the secm list
        sub_sasm = buffer_avg_sasm
        full_sasm_list = secm.getAllSASMs()

        subtracted_sasm_list = []
        
        yes_to_all = False
        for sasm in full_sasm_list:
            result = wx.ID_YES
            
            qmin, qmax = sasm.getQrange()
            sub_qmin, sub_qmax = sub_sasm.getQrange()

            if numpy.all(sasm.q[qmin:qmax] == sub_sasm.q[sub_qmin:sub_qmax]) == False and not yes_to_all:
                result = self._showQvectorsNotEqualWarning(sasm, sub_sasm)[0]
    
                if result == wx.ID_YESTOALL:
                    yes_to_all = True
                elif result == wx.ID_CANCEL:
                    wx.CallAfter(self.main_frame.closeBusyDialog)
                    return
                try:
                    if result == wx.ID_YES or result == wx.ID_YESTOALL:
                        subtracted_sasm = SASM.subtract(sasm, sub_sasm, forced = True)
                        self._insertSasmFilenamePrefix(subtracted_sasm, 'S_')
                        
                        #Insert into history of new file.
                        
                        scale2 = sub_sasm.getScale()
                        offset2 = sub_sasm.getOffset()
                        name2 = sub_sasm.getParameter('filename')

                        subtracted_sasm_list.append(subtracted_sasm)


                except SASExceptions.DataNotCompatible, msg:
                   self._showSubtractionError(sasm, sub_sasm)
                   wx.CallAfter(self.main_frame.closeBusyDialog)
                   return
            elif numpy.all(sasm.q[qmin:qmax] == sub_sasm.q[sub_qmin:sub_qmax]) == False and yes_to_all:
                try:
                    subtracted_sasm = SASM.subtract(sasm, sub_sasm, forced = True)
                    self._insertSasmFilenamePrefix(subtracted_sasm, 'S_')
                    
                    #Insert into history of new file.
                    
                    scale2 = sub_sasm.getScale()
                    offset2 = sub_sasm.getOffset()
                    name2 = sub_sasm.getParameter('filename')

                    subtracted_sasm_list.append(subtracted_sasm)
                  

                except SASExceptions.DataNotCompatible, msg:
                   self._showSubtractionError(sasm, sub_sasm)
                   wx.CallAfter(self.main_frame.closeBusyDialog)
                   return
            else:
                try:
                    subtracted_sasm = SASM.subtract(sasm, sub_sasm)
                    self._insertSasmFilenamePrefix(subtracted_sasm, 'S_')
                    
                    #Insert into history of new file.
                    
                    scale2 = sub_sasm.getScale()
                    offset2 = sub_sasm.getOffset()
                    name2 = sub_sasm.getParameter('filename')

                    subtracted_sasm_list.append(subtracted_sasm)


                except SASExceptions.DataNotCompatible, msg:
                   self._showSubtractionError(sasm, sub_sasm)
                   wx.CallAfter(self.main_frame.closeBusyDialog)
                   return

        secm.setSubtractedSASMList(subtracted_sasm_list)


        #Now calculate the RG, I0, and MW for each SASM
        rg = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        rger = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        i0 = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        i0er = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        mw = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        mwer = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)

        if window_size == 1:
            for a in range(len(subtracted_sasm_list)):
                current_sasm = subtracted_sasm_list[a]

                #use autorg to find the Rg and I0
                rg[a], rger[a], i0[a], i0er[a], indx_min, indx_max = SASCalc.autoRg(current_sasm)

                #Now use the rambo tainer 2013 method to calculate molecular weight
                mw[a], mwer[a], junk1, junk2, junk3 = SASCalc.autoMW(current_sasm, rg[a], i0[a])

        else:
            for a in range(len(subtracted_sasm_list)-(window_size-1)):
                current_sasm_list = subtracted_sasm_list[a:a+window_size]

                try:
                    current_sasm = SASM.average(current_sasm_list)
                except SASExceptions.DataNotCompatible:
                    self._showAverageError(1)
                    wx.CallAfter(self.main_frame.closeBusyDialog)
                    return

                index = a+(window_size-1)/2

                #use autorg to find the Rg and I0
                rg[index], rger[index], i0[index], i0er[index], idx_min, idx_max = SASCalc.autoRg(current_sasm)

                #Now use the rambo tainer 2013 method to calculate molecular weight
                mw[index], mwer[index], junk1, junk2, junk3 = SASCalc.autoMW(current_sasm, rg[index], i0[index])

        #Set everything that's nonsense to -1
        rg[rg<=0] = -1
        rger[rg==-1] = -1
        i0[i0<=0] = -1
        i0er[i0==-1] = -1

        mw[mw<=0] = -1
        mw[rg<=0] = -1
        mw[i0<=0] = -1
        mwer[mw==-1] = -1

        secm.setRgAndI0(rg, rger, i0, i0er)
        secm.setMW(mw, mwer)

        secm.calc_has_data = True

        self._updateSECMPlot(secm)

        wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 3)
        sec_controls = wx.FindWindowByName('SECPanel')
        wx.CallAfter(sec_controls.SetFocus)

        # print rg
        # print i0
        # print mw

        wx.CallAfter(self.main_frame.closeBusyDialog)


    def _updateCalcSECParams(self, secm, frame_list):

        first_update_frame = int(frame_list[0])
        last_update_frame = int(frame_list[-1])

        if secm.window_size == -1:
            return

        initial_buffer_frame, final_buffer_frame, window_size = secm.getCalcParams()

        # print initial_buffer_frame
        # print final_buffer_frame
        # print window_size

        buffer_sasm_list = secm.getSASMList(initial_buffer_frame, final_buffer_frame)

        if len(buffer_sasm_list) < 2:
            buffer_avg_sasm = buffer_sasm_list[0]
        else:
            try:
                buffer_avg_sasm = SASM.average(buffer_sasm_list)
            except SASExceptions.DataNotCompatible:
                self._showAverageError(1)
                wx.CallAfter(self.main_frame.closeBusyDialog)
                return
        
        self._insertSasmFilenamePrefix(buffer_avg_sasm, 'A_')

        secm.setAverageBufferSASM(buffer_avg_sasm)

        #Now subtract the average buffer from all of the items in the secm list
        sub_sasm = buffer_avg_sasm

        first_frame = first_update_frame - secm.window_size

        if first_frame <0:
            first_frame = 0

        last_frame = last_update_frame

        full_sasm_list = secm.getSASMList(first_frame, last_frame)

        subtracted_sasm_list = []
        
        yes_to_all = False
        for sasm in full_sasm_list:
            result = wx.ID_YES
            
            qmin, qmax = sasm.getQrange()
            sub_qmin, sub_qmax = sub_sasm.getQrange()

            if numpy.all(sasm.q[qmin:qmax] == sub_sasm.q[sub_qmin:sub_qmax]) == False and not yes_to_all:
                result = self._showQvectorsNotEqualWarning(sasm, sub_sasm)[0]
    
                if result == wx.ID_YESTOALL:
                    yes_to_all = True
                elif result == wx.ID_CANCEL:
                    wx.CallAfter(self.main_frame.closeBusyDialog)
                    return
                try:
                    if result == wx.ID_YES or result == wx.ID_YESTOALL:
                        subtracted_sasm = SASM.subtract(sasm, sub_sasm, forced = True)
                        self._insertSasmFilenamePrefix(subtracted_sasm, 'S_')
                        
                        #Insert into history of new file.
                        
                        scale2 = sub_sasm.getScale()
                        offset2 = sub_sasm.getOffset()
                        name2 = sub_sasm.getParameter('filename')

                        subtracted_sasm_list.append(subtracted_sasm)


                except SASExceptions.DataNotCompatible, msg:
                   self._showSubtractionError(sasm, sub_sasm)
                   wx.CallAfter(self.main_frame.closeBusyDialog)
                   return
            elif numpy.all(sasm.q[qmin:qmax] == sub_sasm.q[sub_qmin:sub_qmax]) == False and yes_to_all:
                try:
                    subtracted_sasm = SASM.subtract(sasm, sub_sasm, forced = True)
                    self._insertSasmFilenamePrefix(subtracted_sasm, 'S_')
                    
                    #Insert into history of new file.
                    
                    scale2 = sub_sasm.getScale()
                    offset2 = sub_sasm.getOffset()
                    name2 = sub_sasm.getParameter('filename')

                    subtracted_sasm_list.append(subtracted_sasm)
                  

                except SASExceptions.DataNotCompatible, msg:
                   self._showSubtractionError(sasm, sub_sasm)
                   wx.CallAfter(self.main_frame.closeBusyDialog)
                   return
            else:
                try:
                    subtracted_sasm = SASM.subtract(sasm, sub_sasm)
                    self._insertSasmFilenamePrefix(subtracted_sasm, 'S_')
                    
                    #Insert into history of new file.
                    
                    scale2 = sub_sasm.getScale()
                    offset2 = sub_sasm.getOffset()
                    name2 = sub_sasm.getParameter('filename')

                    subtracted_sasm_list.append(subtracted_sasm)


                except SASExceptions.DataNotCompatible, msg:
                   self._showSubtractionError(sasm, sub_sasm)
                   wx.CallAfter(self.main_frame.closeBusyDialog)
                   return

        secm.appendSubtractedSASMList(subtracted_sasm_list)

        #Now calculate the RG, I0, and MW for each SASM
        rg = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        rger = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        i0 = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        i0er = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        mw = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)
        mwer = numpy.zeros_like(numpy.arange(len(subtracted_sasm_list)),dtype=float)

        if window_size == 1:
            for a in range(len(subtracted_sasm_list)):
                current_sasm = subtracted_sasm_list[a]

                #use autorg to find the Rg and I0
                rg[a], rger[a], i0[a], i0er[a], indx_min, indx_max = SASCalc.autoRg(current_sasm)

                #Now use the rambo tainer 2013 method to calculate molecular weight
                mw[a], mwer[a], junk1, junk2, junk3 = SASCalc.autoMW(current_sasm, rg[a], i0[a])

        else:
            for a in range(len(subtracted_sasm_list)-(window_size-1)):
                current_sasm_list = subtracted_sasm_list[a:a+window_size]

                try:
                    current_sasm = SASM.average(current_sasm_list)
                except SASExceptions.DataNotCompatible:
                    self._showAverageError(1)
                    wx.CallAfter(self.main_frame.closeBusyDialog)
                    return

                index = a+(window_size-1)/2

                #use autorg to find the Rg and I0
                rg[index], rger[index], i0[index], i0er[index], indx_min, indx_max = SASCalc.autoRg(current_sasm)

                #Now use the rambo tainer 2013 method to calculate molecular weight
                mw[index], mwer[index], junk1, junk2, junk3 = SASCalc.autoMW(current_sasm, rg[index], i0[index])

        #Set everything that's nonsense to -1
        rg[rg<=0] = -1
        rger[rg==-1] = -1
        i0[i0<=0] = -1
        i0er[i0==-1] = -1

        mw[mw<=0] = -1
        mw[rg<=0] = -1
        mw[i0<=0] = -1
        mwer[mw==-1] = -1

        secm.appendRgAndI0(rg, rger, i0, i0er, first_frame, window_size)
        secm.appendMW(mw, mwer, first_frame, window_size)

        secm.calc_has_data = True

        self._updateSECMPlot(secm)

        wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 3)
        sec_controls = wx.FindWindowByName('SECPanel')
        wx.CallAfter(sec_controls.SetFocus)


    def _loadAndShowNextImage(self, data):
    
        current_file = data[0]
        direction = data[1]
        
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while loading image...')
       
        img_fmt = self._raw_settings.get('ImageFormat')
        
        path = self.dir_panel.file_list_box.path
        dir = sorted(os.listdir(path))
        
        if current_file == None:
            idx = 0
        else:
            idx = dir.index(current_file)
        

        while True:
            idx = idx + direction
            
            if idx < 0: break
            if idx >= len(dir): break
            
            next_file = dir[idx]
            next_file_path = os.path.join(path, next_file)
            
            try:
                img = None
                if self._fileTypeIsCompatible(next_file_path):
                    img, imghdr = SASFileIO.loadImage(next_file_path, img_fmt)
                    
                if img != None:
                    parameters = {'filename' : os.path.split(next_file_path)[1],
                                  'imageHeader' : imghdr}
        
                    bogus_sasm = SASM.SASM([0,1], [0,1], [0,1], parameters)
        
                    self._sendImageToDisplay(img, bogus_sasm)
                    break
            except Exception, e:
                pass
            
        wx.CallAfter(self.main_frame.closeBusyDialog)
        
    def _fileTypeIsCompatible(self, path):
        root, ext = os.path.splitext(path)

        compatible_formats = self.main_frame.getRawSettings().get('CompatibleFormats')
        
        if str(ext) in compatible_formats: 
            return True
        else:
            return False
     
    def _loadAndShowImage(self, filename):
        
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while loading image...')
       
        img_fmt = self._raw_settings.get('ImageFormat')
        
        try:
            if not os.path.isfile(filename):
                raise SASExceptions.WrongImageFormat('not a valid file!')
            
            img, imghdr = SASFileIO.loadImage(filename, img_fmt)
            
            if img == None:
                raise SASExceptions.WrongImageFormat('not a valid file!')
                
        except SASExceptions.WrongImageFormat, msg:
            self._showDataFormatError(os.path.split(filename)[1], include_ascii = False)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        
        parameters = {'filename' : os.path.split(filename)[1],
                      'imageHeader' : imghdr}
        
        bogus_sasm = SASM.SASM([0,1], [0,1], [0,1], parameters)
        
        self._sendImageToDisplay(img, bogus_sasm)
        wx.CallAfter(self.main_frame.plot_notebook.SetSelection, 2)
        file_list = wx.FindWindowByName('FileListCtrl')
        wx.CallAfter(file_list.SetFocus)
        wx.CallAfter(self.main_frame.closeBusyDialog)
    
    def _calibrateSASM(self, sasm):
    
        #if self._raw_settings.get('CalibrateMan'):
        sd_distance = self._raw_settings.get('SampleDistance')
        pixel_size = self._raw_settings.get('DetectorPixelSize')
        wavelength = self._raw_settings.get('WaveLength')
        
        sasm.calibrateQ(sd_distance, pixel_size, wavelength)
        
    def _showDataFormatError(self, filename, include_ascii = True, include_sec = False):
        img_fmt = self._raw_settings.get('ImageFormat')
        
        if include_ascii:
            ascii = ' or any of the supported ASCII formats'
        else:
            ascii = ''

        if include_sec:
            sec = ' or the RAW SEC format'
        else:
            sec = ''
        
        wx.CallAfter(wx.MessageBox, 'The selected file: ' + filename + '\ncould not be recognized as a '   + str(img_fmt) +
                         ' image format' + ascii + sec + '.\n\nYou can change the image format under Advanced Options in the Options menu.' ,
                          'Error loading file', style = wx.ICON_ERROR | wx.OK)

    def _showSECFormatError(self, filename, include_ascii = True):
        img_fmt = self._raw_settings.get('ImageFormat')
        
        if include_ascii:
            ascii = ' or any of the supported ASCII formats'
        else:
            ascii = ''
        
        wx.CallAfter(wx.MessageBox, 'The selected file: ' + filename + '\ncould not be recognized as a '   + str(img_fmt) +
                         ' image format' + ascii + '.\n\nIf you are loading a set of files as a SEC curve, make sure the selection contains only individual scattering profiles (no .sec files).\n\nYou can change the image format under Advanced Options in the Options menu.' ,
                          'Error loading file', style = wx.ICON_ERROR | wx.OK)
        
    def _showSubtractionError(self, sasm, sub_sasm):
        filename1 = sasm.getParameter('filename')
        q1_min, q1_max = sasm.getQrange()
        points1 = len(sasm.i[q1_min:q1_max])
        filename2 = sub_sasm.getParameter('filename')
        q2_min, q2_max = sub_sasm.getQrange()
        points2 = len(sub_sasm.i[q2_min:q2_max])
        wx.CallAfter(wx.MessageBox, filename1 + ' has ' + str(points1) + ' data points.\n'  +
            filename2 + ' has ' + str(points2) + ' data points.\n\n' +
            'Subtraction is not possible. Data files must have equal number of points.', 'Subtraction Error')
        
    def _showAverageError(self, err_no):
        
        if err_no == 1:
            wx.CallAfter(wx.MessageBox, 'The selected items must have the same total number of points to be averaged.', 'Average Error')
        elif err_no == 2:
            wx.CallAfter(wx.MessageBox, 'Please select at least two items to be averaged.' , 'Average Error')
        elif err_no == 3:
            wx.CallAfter(wx.MessageBox, 'The selected items must have the same q vectors to be averaged.' , 'Average Error')
    
    def _showPleaseSelectItemsError(self, type):
        
        if type == 'average':
            wx.CallAfter(wx.MessageBox, 'Please select the items you want to average.\n\nYou can select multiple items by holding down the CTRL or SHIFT key.' , 'No items selected')
        if type == 'subtract': 
            wx.CallAfter(wx.MessageBox, 'Please select the items you want the marked (star) item subtracted from.'+
                              '\nUse CTRL or SHIFT to select multiple items.', 'No items selected')
        if type == 'superimpose':
            wx.CallAfter(wx.MessageBox, 'Please select the items you want to superimpose.\n\nYou can select multiple items by holding down the CTRL or SHIFT key.' , 'No items selected')            
           
    def _showPleaseMarkItemError(self, type):
        
        if type == 'subtract':
            wx.CallAfter(wx.MessageBox, 'Please mark (star) the item you are using for subtraction', 'No item marked')
        if type == 'merge':
            wx.CallAfter(wx.MessageBox, 'Please mark (star) the item you are using as the main curve for merging', 'No item marked')
        if type == 'superimpose':
            wx.CallAfter(wx.MessageBox, 'Please mark (star) the item you want to superimpose to.', 'No item marked')
        if type == 'interpolate':
            wx.CallAfter(wx.MessageBox, 'Please mark (star) the item you are using as the main curve for interpolation', 'No item marked')
            
    def _showQvectorsNotEqualWarning(self, sasm, sub_sasm):
        
        sub_filename = sub_sasm.getParameter('filename')
        filename = sasm.getParameter('filename')
        
        button_list = [('Yes', wx.ID_YES), ('Yes to all', wx.ID_YESTOALL), ('No', wx.ID_NO), ('Cancel', wx.ID_CANCEL)]
        question = 'Q vectors for ' + str(filename) + ' and ' + str(sub_filename) + ' are not the same. \nContinuing subtraction will attempt to find matching q regions in or create matching q regions by binning.\nDo you wish to continue?'
        label = 'Q vectors do not match'
        icon = wx.ART_WARNING
        
        answer = self._displayQuestionDialog(question, label, button_list, icon)
        
        return answer
    
    def _showQuickReduceFinished(self, processed_files, number_of_files):
        wx.CallAfter(wx.MessageBox, 'Quick reduction finished. Processed ' + str(processed_files) + ' out of ' + str(number_of_files) + ' files.', 'Quick reduction finished', style = wx.ICON_INFORMATION)
        
    def _showOverwritePrompt(self, filename, save_path):
        
        button_list = [('Yes', wx.ID_YES), ('Yes to all', wx.ID_YESTOALL), ('No', wx.ID_NO), 
                       ('No to all', wx.ID_NOTOALL), ('Rename', wx.ID_EDIT), ('Cancel', wx.ID_CANCEL)]
        
        path = os.path.join(save_path, filename)
        
        question = 'Filename: ' + str(path) + '\nalready exists. Do you wish to overwrite the existing file?'
        label = 'File exists'
        icon = wx.ART_WARNING
        
        answer = self._displayQuestionDialog(question, label, button_list, icon, filename, save_path)
        
        return answer
        
    def _displayQuestionDialog(self, question, label, button_list, icon = None, filename = None, save_path = None):
        
        wx.CallAfter(self.main_frame.showQuestionDialogFromThread, question, label, button_list, icon, filename, save_path)
     
        thread_wait_event.wait()
        thread_wait_event.clear()
        
        answer = question_return_queue.get()
        question_return_queue.task_done()
        
        return answer    
                    
    def _subtractFilenames(self):
        pass
    
    def _plotIftFit(self, data):
             
        selected_items = data[0]
        
        selected_sasms = []
        for each_item in selected_items:
            selected_sasms.append(each_item.getSASM())
           
        for each in selected_sasms:
            
            param = each.getAllParameters()
            
            if each.getAllParameters().has_key('orig_sasm'):
                self._sendSASMToPlot(each.getParameter('orig_sasm').copy())
            if each.getAllParameters().has_key('fit_sasm'):
                self._sendSASMToPlot(each.getParameter('fit_sasm').copy())
        
    
        wx.CallAfter(self.plot_panel.updateLegend, 1)

    def _quickReduce(self, data):
        
        save_path = data[0]
        load_path = data[1]
        filename_list = data[2]
        format_ext = data[3]
        
        yes_to_all = False
        no_to_all = False
        processed_files = 0
        
        for each_filename in filename_list:
                
            full_load_path = os.path.join(load_path, each_filename)
            no_ext_filename, ext = os.path.splitext(each_filename)
                
            check_filename = no_ext_filename + format_ext
            check_path = os.path.join(save_path, check_filename)
                
            if os.path.exists(check_path) and yes_to_all == False:
                
                if no_to_all == True:
                    result = wx.ID_NO
                else:
                    result = self._showOverwritePrompt(check_filename, save_path)
                    
                if result[0] == wx.ID_NOTOALL:
                    no_to_all = True
            
                if result[0] == wx.ID_YESTOALL:
                    yes_to_all = True
                
                if result[0] == wx.ID_YES or result[0] == wx.ID_YESTOALL or result[0] == wx.ID_EDIT:
                    try:
                        sasm, img = SASFileIO.loadFile(full_load_path, self._raw_settings)
                        
                        if result[0] == wx.ID_EDIT:
                            final_save_path, new_filename = os.path.split(result[1][0])                
                            sasm.setParameter('filename', new_filename)
                        else:
                            final_save_path = save_path
                        
                        if img != None:
                            SASFileIO.saveMeasurement(sasm, final_save_path, self._raw_settings)
                            processed_files += 1
                        else:
                            self._showDataFormatError(os.path.split(each_filename)[1], include_ascii = False)
                    except (SASExceptions.UnrecognizedDataFormat, SASExceptions.WrongImageFormat), msg:
                        self._showDataFormatError(os.path.split(each_filename)[1], include_ascii = False)
            
            else:
                try:
                    sasm, img = SASFileIO.loadFile(full_load_path, self._raw_settings)
                    
                    if img != None:
                        SASFileIO.saveMeasurement(sasm, save_path, self._raw_settings)
                        processed_files += 1
                    else:
                        self._showDataFormatError(os.path.split(each_filename)[1], include_ascii = False)
                except (SASExceptions.UnrecognizedDataFormat, SASExceptions.WrongImageFormat), msg:
                    self._showDataFormatError(os.path.split(each_filename)[1], include_ascii = False)
                        
        self._showQuickReduceFinished(processed_files, len(filename_list))
    
    
    def _superimposeItems(self, data):
        
        star_item = data[0]
        selected_items = data[1]
        
        if star_item == None:
            self._showPleaseMarkItemError('superimpose')
            return 
        
        if star_item in selected_items:
            selected_items.remove(star_item)
         
        if len(selected_items) == 0:
            self._showPleaseSelectItemsError('superimpose')
            return
        
        selected_sasms = []
        for each_item in selected_items:
            selected_sasms.append(each_item.getSASM())
            
        SASM.superimpose(star_item.getSASM(), selected_sasms)
        
        for each_item in selected_items:
            each_item.updateControlsFromSASM()
        
        wx.CallAfter(self.plot_panel.updatePlotAfterManipulation, selected_sasms)
    
    def _subtractItems(self, data):
        ''' subtracts the marked item from other selected items in the
        manipulation list '''

        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while subtracting and plotting...')

        do_auto_save = self._raw_settings.get('AutoSaveOnSub')

        marked_item = data[0]
        selected_items = data[1]

        if marked_item in selected_items:
            selected_items.remove(marked_item)
        
        if marked_item == None:
            self._showPleaseMarkItemError('subtract')
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        elif len(selected_items) == 0:
            self._showPleaseSelectItemsError('subtract')
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        
        sub_sasm = marked_item.getSASM()
        
        yes_to_all = False

        for i in range(len(selected_items)):
            each = selected_items[i]
            # result = wx.ID_YES
            sasm = each.getSASM()

            print sasm.getParameter('filename')
            
            qmin, qmax = sasm.getQrange()
            sub_qmin, sub_qmax = sub_sasm.getQrange()
               
            if numpy.all(numpy.round(sasm.q[qmin:qmax],5) == numpy.round(sub_sasm.q[sub_qmin:sub_qmax],5)) == False and not yes_to_all:
                result = self._showQvectorsNotEqualWarning(sasm, sub_sasm)[0]
    
                if result == wx.ID_YESTOALL:
                    yes_to_all = True
                elif result == wx.ID_CANCEL:
                    wx.CallAfter(self.main_frame.closeBusyDialog)
                    return
                try:
                    if result == wx.ID_YES or result == wx.ID_YESTOALL:
                        subtracted_sasm = SASM.subtract(sasm, sub_sasm, forced = True)
                        self._insertSasmFilenamePrefix(subtracted_sasm, 'S_')
                        
                        #Insert into history of new file.
                        
                        scale2 = sub_sasm.getScale()
                        offset2 = sub_sasm.getOffset()
                        name2 = sub_sasm.getParameter('filename')
                        
                        self._sendSASMToPlot(subtracted_sasm, no_update = True, update_legend = False, axes_num = 2, item_colour = 'red', notsaved = True)
        
                        if do_auto_save:
                            save_path = self._raw_settings.get('SubtractedFilePath')
                            self._saveSASM(subtracted_sasm, '.dat', save_path)

                except SASExceptions.DataNotCompatible, msg:
                   self._showSubtractionError(sasm, sub_sasm)
                   wx.CallAfter(self.main_frame.closeBusyDialog)
                   return
            elif numpy.all(numpy.round(sasm.q[qmin:qmax],5) == numpy.round(sub_sasm.q[sub_qmin:sub_qmax],5)) == False and yes_to_all:
                try:
                    subtracted_sasm = SASM.subtract(sasm, sub_sasm, forced = True)
                    self._insertSasmFilenamePrefix(subtracted_sasm, 'S_')
                    
                    #Insert into history of new file.
                    
                    scale2 = sub_sasm.getScale()
                    offset2 = sub_sasm.getOffset()
                    name2 = sub_sasm.getParameter('filename')
                    
                    self._sendSASMToPlot(subtracted_sasm, no_update = True, update_legend = False, axes_num = 2, item_colour = 'red', notsaved = True)

                    if do_auto_save:
                        save_path = self._raw_settings.get('SubtractedFilePath')
                        self._saveSASM(subtracted_sasm, '.dat', save_path)

                except SASExceptions.DataNotCompatible, msg:
                   self._showSubtractionError(sasm, sub_sasm)
                   wx.CallAfter(self.main_frame.closeBusyDialog)
                   return
            else:
                try:
                    subtracted_sasm = SASM.subtract(sasm, sub_sasm)
                    self._insertSasmFilenamePrefix(subtracted_sasm, 'S_')
                    
                    #Insert into history of new file.
                    
                    scale2 = sub_sasm.getScale()
                    offset2 = sub_sasm.getOffset()
                    name2 = sub_sasm.getParameter('filename')
                    
                    self._sendSASMToPlot(subtracted_sasm, no_update = True, update_legend = False, axes_num = 2, item_colour = 'red', notsaved = True)

                    if do_auto_save:
                        save_path = self._raw_settings.get('SubtractedFilePath')
                        self._saveSASM(subtracted_sasm, '.dat', save_path)

                except SASExceptions.DataNotCompatible, msg:
                   self._showSubtractionError(sasm, sub_sasm)
                   wx.CallAfter(self.main_frame.closeBusyDialog)
                   return

            if numpy.mod(i,20) == 0:
                wx.CallAfter(self.plot_panel.canvas.draw)

        wx.CallAfter(self.plot_panel.fitAxis)
        wx.CallAfter(self.plot_panel.updateLegend, 2)
        wx.CallAfter(self.main_frame.closeBusyDialog)
                
    def _averageItems(self, item_list):
        
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while averaging and plotting...')
        
        sasm_list = []
                
        if len(item_list) < 2:
            self._showAverageError(2)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        
        for each_item in item_list:
            sasm_list.append(each_item.getSASM())
            
        try:
            avg_sasm = SASM.average(sasm_list)
        except SASExceptions.DataNotCompatible:
            self._showAverageError(3)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        
        self._insertSasmFilenamePrefix(avg_sasm, 'A_')
        
        self._sendSASMToPlot(avg_sasm, axes_num = 1, item_colour = 'green', notsaved = True)

        do_auto_save = self._raw_settings.get('AutoSaveOnAvgFiles')
        
        if do_auto_save:
            save_path = self._raw_settings.get('AveragedFilePath')
            self._saveSASM(avg_sasm, '.dat', save_path)
        
        wx.CallAfter(self.plot_panel.updateLegend, 1)
        wx.CallAfter(self.main_frame.closeBusyDialog)

    def _averageItemsSEC(self, sasm_list):
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while averaging and sending to main plot...')
                        
        if len(sasm_list) < 2:
            self._showAverageError(2)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
            
        try:
            avg_sasm = SASM.average(sasm_list)
        except SASExceptions.DataNotCompatible:
            self._showAverageError(1)
            wx.CallAfter(self.main_frame.closeBusyDialog)
            return
        
        self._insertSasmFilenamePrefix(avg_sasm, 'A_')
        
        self._sendSASMToPlot(avg_sasm, axes_num = 1, item_colour = 'green', notsaved = True)
        
        wx.CallAfter(self.plot_panel.updateLegend, 1)
        wx.CallAfter(self.main_frame.closeBusyDialog)
        
    
    def _rebinItems(self, data):
        
        selected_items = data[0]
        rebin_factor = data[1]
        log_rebin = data[2]
        
        for each in selected_items:
            sasm = each.getSASM()
        
            points = floor(len(sasm.q) / rebin_factor)
            
            if log_rebin:
                rebin_sasm = SASM.logBinning(sasm, points)
            else:
                rebin_sasm = SASM.rebin(sasm, rebin_factor)
            
            self._insertSasmFilenamePrefix(rebin_sasm, 'R_')
            
            self._sendSASMToPlot(rebin_sasm, axes_num = 1, notsaved = True)
        
            wx.CallAfter(self.plot_panel.updateLegend, 1)
        
    def _insertSasmFilenamePrefix(self, sasm, prefix = '', extension = ''):
        filename = sasm.getParameter('filename')
        new_filename, ext = os.path.splitext(filename)
        sasm.setParameter('filename', prefix + new_filename + extension)
    
    def _mergeItems(self, data):
        
        marked_item = data[0]
        selected_items = data[1]
        
        if marked_item in selected_items:
            idx = selected_items.index(marked_item)
            selected_items.pop(idx)
        
        if marked_item == None:
            self._showPleaseMarkItemError('merge')
            return 
        
        marked_sasm = marked_item.getSASM()    
        sasm_list = []
        for each_item in selected_items:
            sasm_list.append(each_item.getSASM())
        
        merged_sasm = SASM.merge(marked_sasm, sasm_list)
        
        filename = marked_sasm.getParameter('filename')
        merged_sasm.setParameter('filename', filename)
        self._insertSasmFilenamePrefix(merged_sasm, 'M_')
        
        self._sendSASMToPlot(merged_sasm, axes_num = 1, notsaved = True)
        
        wx.CallAfter(self.plot_panel.updateLegend, 1)
        #wx.CallAfter(self.main_frame.closeBusyDialog)
    
    def _interpolateItems(self, data):
        
        marked_item = data[0]
        selected_items = data[1]
        
        if marked_item in selected_items:
            idx = selected_items.index(marked_item)
            selected_items.pop(idx)
        
        if marked_item == None:
            self._showPleaseMarkItemError('interpolate')
            return 
        
        marked_sasm = marked_item.getSASM()    
        sasm_list = []
	
        for each_item in selected_items:
            sasm_list.append(each_item.getSASM())
        
        interpolate_sasm = SASM.interpolateToFit(marked_sasm, sasm_list)
        
        filename = marked_sasm.getParameter('filename')
        interpolate_sasm.setParameter('filename', filename)
        
        self._insertSasmFilenamePrefix(interpolate_sasm, 'I_')
        
        self._sendSASMToPlot(interpolate_sasm, axes_num = 1, notsaved = True)
        
        wx.CallAfter(self.plot_panel.updateLegend, 1)
                   
    
    def _saveSASM(self, sasm, filetype = 'dat', save_path = ''):
        
        newext = filetype
        
        filename = sasm.getParameter('filename')
        check_filename, ext = os.path.splitext(filename)
        check_filename = check_filename + newext
            
        filepath = os.path.join(save_path, check_filename)
        file_exists = os.path.isfile(filepath)
        filepath = save_path
        
        SASFileIO.saveMeasurement(sasm, filepath, self._raw_settings, filetype = newext)
        
        
    def _saveAnalysisInfo(self, data):
        
        all_items = data[0]
        include_data = data[1]
        save_path = data[2]
        
        selected_sasms = []
        
        check_filename, ext = os.path.splitext(save_path)
        save_path = check_filename + '.csv'

        for each_item in all_items:
            sasm = each_item.getSASM()
            selected_sasms.append(sasm)
            
#            if analysis_dict.keys() == []:
#                wx.CallAfter(wx.MessageBox, 'No analysis information was found for file: ' + sasm.getParameter('filename') + '\n\nSave was aborted.', 'Analysis information not found', style = wx.ICON_EXCLAMATION)
#                return
        
        result = SASFileIO.saveAnalysisCsvFile(selected_sasms, include_data, save_path)

    def _saveAllAnalysisInfo(self, data):
        save_path, selected_sasms = data[0], data[1]

        SASFileIO.saveAllAnalysisData(save_path, selected_sasms)
        
        
    def _saveWorkspace(self, data):
        
        sasm_items = data[0]
        ift_items = data[1]
        secm_items = data[2]
        save_path = data[3]
          
        save_dict = {}
        
        for idx in range(0, len(sasm_items)):
            
            sasm = sasm_items[idx].getSASM()
            sasm_dict = sasm.extractAll()
        
            sasm_dict['line_color'] = sasm.line.get_color()
            sasm_dict['line_width'] = sasm.line.get_linewidth()
            sasm_dict['line_style'] = sasm.line.get_linestyle()
            sasm_dict['line_marker'] = sasm.line.get_marker()
            sasm_dict['line_visible'] = sasm.line.get_visible()
            
            sasm_dict['item_controls_visible'] = sasm.item_panel.getControlsVisible()
            sasm_dict['item_font_color'] = sasm.item_panel.getFontColour()
            sasm_dict['item_selected_for_plot'] = sasm.item_panel.getSelectedForPlot()

            sasm_dict['parameters_analysis'] = sasm_dict['parameters']['analysis']  #pickle wont save this unless its raised up
    
            if sasm.axes == sasm.plot_panel.subplot1:
                sasm_dict['plot_axes'] = 1
            else:
                sasm_dict['plot_axes'] = 2
            
            save_dict['sasm_'+str(idx)] = sasm_dict

        for idx in range(0, len(ift_items)):
            
            # sasm = ift_items[idx].getSASM()
            # sasm_dict = sasm.extractAll()
        
            # sasm_dict['line_color'] = sasm.line.get_color()
            # sasm_dict['line_width'] = sasm.line.get_linewidth()
            # sasm_dict['line_style'] = sasm.line.get_linestyle()
            # sasm_dict['line_marker'] = sasm.line.get_marker()
            # sasm_dict['line_visible'] = sasm.line.get_visible()
            
            # sasm_dict['item_controls_visible'] = sasm.item_panel.getControlsVisible()
            # sasm_dict['item_font_color'] = sasm.item_panel.getFontColour()
            # sasm_dict['item_selected_for_plot'] = sasm.item_panel.getSelectedForPlot()

            # sasm_dict['parameters_analysis'] = sasm_dict['parameters']['analysis']  #pickle wont save this unless its raised up
    
            # if sasm.axes == sasm.plot_panel.subplot1:
            #     sasm_dict['plot_axes'] = 1
            # else:
            #     sasm_dict['plot_axes'] = 2
            
            # save_dict['sasm_'+str(idx)] = sasm_dict
            pass

        for idx in range(0, len(secm_items)):
            
            secm = secm_items[idx].getSECM()
            secm_dict = secm.extractAll()
        
            secm_dict['line_color'] = secm.line.get_color()
            secm_dict['line_width'] = secm.line.get_linewidth()
            secm_dict['line_style'] = secm.line.get_linestyle()
            secm_dict['line_marker'] = secm.line.get_marker()
            secm_dict['line_visible'] = secm.line.get_visible()

            secm_dict['calc_line_color'] = secm.calc_line.get_color()
            secm_dict['calc_line_width'] = secm.calc_line.get_linewidth()
            secm_dict['calc_line_style'] = secm.calc_line.get_linestyle()
            secm_dict['calc_line_marker'] = secm.calc_line.get_marker()
            secm_dict['calc_line_visible'] = secm.calc_line.get_visible()
            
            secm_dict['item_controls_visible'] = secm.item_panel.getControlsVisible()
            secm_dict['item_font_color'] = secm.item_panel.getFontColour()
            secm_dict['item_selected_for_plot'] = secm.item_panel.getSelectedForPlot()

            secm_dict['parameters_analysis'] = secm_dict['parameters']['analysis']  #pickle wont save this unless its raised up
            
            save_dict['secm_'+str(idx)] = secm_dict
        
        SASFileIO.saveWorkspace(save_dict, save_path)
        
        global workspace_saved
        workspace_saved = True
        
    def _loadWorkspace(self, data):
        
        wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while loading workspace...')
        
        load_path = data[0]
        
        item_dict = SASFileIO.loadWorkspace(load_path)
        print item_dict.keys()
        
        for each_key in item_dict.keys():
            if str(each_key).startswith('secm'):
                print 'Loading a SECM item from workspace'

                #First we need to regenerate the sasm list, so we can recreate the secm:

                secm_data = item_dict[each_key]

                sasm_list = []

                for item in secm_data['sasm_list']:
                    sasm_data = item
                    
                    new_sasm = SASM.SASM(sasm_data['i_raw'], sasm_data['q_raw'], sasm_data['err_raw'], sasm_data['parameters'])
                    new_sasm.setBinnedI(sasm_data['i_binned'])
                    new_sasm.setBinnedQ(sasm_data['q_binned'])
                    new_sasm.setBinnedErr(sasm_data['err_binned'])
                    
                    new_sasm.setScaleValues(sasm_data['scale_factor'], sasm_data['offset_value'],
                                            sasm_data['norm_factor'], sasm_data['q_scale_factor'],
                                            sasm_data['bin_size'])
                    
                    new_sasm.setQrange(sasm_data['selected_qrange'])
                    
                    try:
                        new_sasm.setParameter('analysis', sasm_data['parameters_analysis'])
                    except KeyError:
                        pass
                    
                    new_sasm._update()

                    sasm_list.append(new_sasm)

                # print sasm_list

                new_secm = SASM.SECM(secm_data['file_list'], sasm_list, secm_data['frame_list'], secm_data['parameters'])

                new_secm.setCalcParams(secm_data['intial_buffer_frame'], secm_data['final_buffer_frame'], secm_data['window_size'])
                new_secm.setRgAndI0(secm_data['rg'], secm_data['rger'], secm_data['i0'], secm_data['i0er'])
                new_secm.setMW(secm_data['mw'], secm_data['mwer'])
                new_secm.calc_has_data = secm_data['calc_has_data']


                subtracted_sasm_list = []

                for item in secm_data['subtracted_sasm_list']:
                    sasm_data = item
                    
                    new_sasm = SASM.SASM(sasm_data['i_raw'], sasm_data['q_raw'], sasm_data['err_raw'], sasm_data['parameters'])
                    new_sasm.setBinnedI(sasm_data['i_binned'])
                    new_sasm.setBinnedQ(sasm_data['q_binned'])
                    new_sasm.setBinnedErr(sasm_data['err_binned'])
                    
                    new_sasm.setScaleValues(sasm_data['scale_factor'], sasm_data['offset_value'],
                                            sasm_data['norm_factor'], sasm_data['q_scale_factor'],
                                            sasm_data['bin_size'])
                    
                    new_sasm.setQrange(sasm_data['selected_qrange'])
                    
                    try:
                        new_sasm.setParameter('analysis', sasm_data['parameters_analysis'])
                    except KeyError:
                        pass
                    
                    new_sasm._update()

                    subtracted_sasm_list.append(new_sasm)

                new_secm.setSubtractedSASMList(subtracted_sasm_list)


                try:
                    line_data = {'line_color' : secm_data['line_color'],
                                 'line_width' : secm_data['line_width'],
                                 'line_style' : secm_data['line_style'],
                                 'line_marker': secm_data['line_marker'], 
                                 'line_visible' :secm_data['line_visible']}

                    calc_line_data = {'line_color' : secm_data['calc_line_color'],
                                 'line_width' : secm_data['calc_line_width'],
                                 'line_style' : secm_data['calc_line_style'],
                                 'line_marker': secm_data['calc_line_marker'], 
                                 'line_visible' :secm_data['calc_line_visible']}
                except KeyError:
                    line_data = None    #Backwards compatibility
                    secm_data['line_visible'] = True

                wx.CallAfter(self.sec_plot_panel.plotSECM, new_secm,
                              color = secm_data['line_color'],
                              line_data = line_data,
                              calc_line_data = calc_line_data)

                wx.CallAfter(self.sec_item_panel.addItem, new_secm,
                              item_colour = secm_data['item_font_color'],
                              item_visible = secm_data['line_visible'])


            elif str(each_key).startswith('ift'):
                # print item_dict[each_key]
                print 'Loading an IFT item from workspace'


            else:
                #Backwards compatability requires us to not test the sasm prefix
                sasm_data = item_dict[each_key]
                
                new_sasm = SASM.SASM(sasm_data['i_raw'], sasm_data['q_raw'], sasm_data['err_raw'], sasm_data['parameters'])
                new_sasm.setBinnedI(sasm_data['i_binned'])
                new_sasm.setBinnedQ(sasm_data['q_binned'])
                new_sasm.setBinnedErr(sasm_data['err_binned'])
                
                new_sasm.setScaleValues(sasm_data['scale_factor'], sasm_data['offset_value'],
                                        sasm_data['norm_factor'], sasm_data['q_scale_factor'],
                                        sasm_data['bin_size'])
                
                new_sasm.setQrange(sasm_data['selected_qrange'])
                
                try:
                    new_sasm.setParameter('analysis', sasm_data['parameters_analysis'])
                except KeyError:
                    pass
                
                new_sasm._update()

                #### THIS HAS TO BE UPDATED TO ACCOUNT FOR LINESTYLES AND VISIBILITY

                try:
                    line_data = {'line_color' : sasm_data['line_color'],
                                 'line_width' : sasm_data['line_width'],
                                 'line_style' : sasm_data['line_style'],
                                 'line_marker': sasm_data['line_marker'], 
                                 'line_visible' :sasm_data['line_visible']}
                except KeyError:
                    line_data = None    #Backwards compatibility
                    sasm_data['line_visible'] = True

                wx.CallAfter(self.plot_panel.plotSASM, new_sasm,
                              sasm_data['plot_axes'], color = sasm_data['line_color'],
                              line_data = line_data)

                wx.CallAfter(self.manipulation_panel.addItem, new_sasm,
                              item_colour = sasm_data['item_font_color'],
                              item_visible = sasm_data['line_visible'])
                

            
            
            
        wx.CallAfter(self.plot_panel.updateLegend, 1)
        wx.CallAfter(self.plot_panel.updateLegend, 2)
        wx.CallAfter(self.plot_panel.fitAxis)
        wx.CallAfter(self.sec_plot_panel.updateLegend, 1)
        wx.CallAfter(self.sec_plot_panel.fitAxis)
        wx.CallAfter(self.main_frame.closeBusyDialog)

    def _backupWorkspace(self, data):
        #Note, not compatible with current save workspace function
        #Needs to be updated
        print 'Backing up workspace . . .'
        all_items = data[0]
        
        backupfile = os.path.join(RAWWorkDir, '_wspBackup.wsp')
        
        data_out = [all_items, backupfile]
        
        self._saveWorkspace(data_out)
    
    def _backupSettings(self, data):
        pass 

    def _saveIftItems(self, data):
        self._saveItems(data, iftmode=True)

    def _saveSECData(self,data):
        save_path, selected_items = data[0], data[1]

        for b in range(len(selected_items)):

            selected_secm = selected_items[b].secm
            SASFileIO.saveSECData(save_path[b], selected_secm)

    def _saveSECItem(self,data):
        save_path, selected_items = data[0], data[1]

        for b in range(len(selected_items)):

            secm = selected_items[b].secm
            secm_dict = secm.extractAll()
        
            secm_dict['line_color'] = secm.line.get_color()
            secm_dict['line_width'] = secm.line.get_linewidth()
            secm_dict['line_style'] = secm.line.get_linestyle()
            secm_dict['line_marker'] = secm.line.get_marker()
            secm_dict['line_visible'] = secm.line.get_visible()

            secm_dict['calc_line_color'] = secm.calc_line.get_color()
            secm_dict['calc_line_width'] = secm.calc_line.get_linewidth()
            secm_dict['calc_line_style'] = secm.calc_line.get_linestyle()
            secm_dict['calc_line_marker'] = secm.calc_line.get_marker()
            secm_dict['calc_line_visible'] = secm.calc_line.get_visible()
            
            secm_dict['item_controls_visible'] = secm.item_panel.getControlsVisible()
            secm_dict['item_font_color'] = secm.item_panel.getFontColour()
            secm_dict['item_selected_for_plot'] = secm.item_panel.getSelectedForPlot()

            secm_dict['parameters_analysis'] = secm_dict['parameters']['analysis']  #pickle wont save this unless its raised up

            SASFileIO.saveSECItem(save_path[b], secm_dict)

            selected_items[b].unmarkAsModified()
            
        
    def _normalizeByConc(self, data):
        selected_items = data[0]

        for each in selected_items:
            sasm = each.getSASM()
        
            if sasm.getAllParameters().has_key('Conc'):
                conc = sasm.getParameter('Conc')
                
                try:
                    conc = float(conc)
                    
                    scale = 1/conc
                    sasm.scaleRelative(scale)
                    wx.CallAfter(each.updateControlsFromSASM)
                    
                except ValueError:
                    continue
                

    def _saveItems(self, data, iftmode = False):
        
        save_path = data[0]
        item_list = data[1]
        
        overwrite_all = False
        no_to_all = False
        for item in item_list:
            sasm = item.sasm
            
            filename = sasm.getParameter('filename')
            
            check_filename, ext = os.path.splitext(filename)
            
            if iftmode:
                newext = '.ift'
            else:
                newext = '.dat'
                
            check_filename = check_filename + newext
            
            filepath = os.path.join(save_path, check_filename)
            file_exists = os.path.isfile(filepath)
            filepath = save_path
            
            if file_exists and overwrite_all == False:
                
                if no_to_all == False:
                    result = self._showOverwritePrompt(check_filename, save_path)
                    
                    if result[0] == wx.ID_CANCEL:
                        return
                
                    if result[0] == wx.ID_EDIT: #rename
                        filepath = result[1][0]
                        filepath, new_filename = os.path.split(filepath)
                        sasm.setParameter('filename', new_filename)
                        
                    if result[0] == wx.ID_YES or result[0] == wx.ID_YESTOALL or result[0] == wx.ID_EDIT:
                        SASFileIO.saveMeasurement(sasm, filepath, self._raw_settings, filetype = newext)
                        filename, ext = os.path.splitext(sasm.getParameter('filename'))
                        sasm.setParameter('filename', filename + newext)
                        wx.CallAfter(sasm.item_panel.updateFilenameLabel)
                        wx.CallAfter(item.unmarkAsModified)
                    
                    if result[0] == wx.ID_YESTOALL:
                        overwrite_all = True
                        
                    if result[0] == wx.ID_NOTOALL:
                        no_to_all = True
                
            else:
                SASFileIO.saveMeasurement(sasm, filepath, self._raw_settings, filetype = newext)
                filename, ext = os.path.splitext(sasm.getParameter('filename'))
                sasm.setParameter('filename', filename + newext)
                wx.CallAfter(sasm.item_panel.updateFilenameLabel)
                wx.CallAfter(item.unmarkAsModified)

#--- ** Info Panel **

class InfoPanel(wx.Panel):
    
    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent, name = 'InfoPanel')
        
        infoSizer = wx.BoxSizer()
        
        self.infoTextBox = wx.TextCtrl(self, -1, 'Welcome to RAW 1.0.0b!\n--------------------------------\n\n', style = wx.TE_MULTILINE)
        
        self.infoTextBox.SetBackgroundColour('WHITE')
        self.infoTextBox.SetForegroundColour('BLACK')
        
        infoSizer.Add(self.infoTextBox, 1, wx.EXPAND)
        
        self.SetSizer(infoSizer)
        
    def WriteText(self, text):
        
        self.infoTextBox.AppendText(text)
        
    def Clear(self):
        
        self.infoTextBox.Clear()
        
#***************        
#--- ** File Panel **
#***************
                             
class FilePanel(wx.Panel):
    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent, size = (400,600), name = 'FilePanel')
        
        self.plot_panel = wx.FindWindowByName('PlotPanel')
        self.manipulation_panel = wx.FindWindowByName('ManipulationPanel')
        self.main_frame = wx.FindWindowByName('MainFrame')
        self.image_panel = wx.FindWindowByName('ImagePanel')
        self.sec_panel = wx.FindWindowByName('SECPanel')
        self.sec_plot_panel = wx.FindWindowByName('SECPlotPanel')
        
        # *************** buttons ****************************
        self.dir_panel = DirCtrlPanel(self)
        
        self.button_data = ( ("Quick Reduce", self._onReduceButton),
                           ("Plot", self._onPlotButton),
                           ("Clear All", self._onClearAllButton),
                           ("Execute", self._onViewButton),
                           ("Show Image", self._onShowImageButton),
                           ("Plot SEC", self._onPlotSECButton))

        self.NO_OF_BUTTONS_IN_EACH_ROW = 3
        
        #bg_label_sizer = self._createBackgroundFileLabels()
        button_sizer = self._createButtons()
        
        # *************** Directory Control ***********************
        b2sizer = wx.BoxSizer(wx.VERTICAL) 
        b2sizer.Add((10,10), 0)
       # b2sizer.Add(bg_label_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.ALIGN_CENTRE, 10) 
        b2sizer.Add((5,5))
        b2sizer.Add(self.dir_panel, 1, wx.EXPAND| wx.LEFT | wx.RIGHT, 10)
        b2sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.TOP | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)                      

        self.SetSizer(b2sizer)
        
    def _createBackgroundFileLabels(self):
        box = wx.StaticBox(self, -1, 'Background File:')
        bg_label_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        bg_filename = wx.StaticText(self, -1, 'None')
        bg_filename.SetMinSize((230,20))
        
        bg_label_sizer.Add(bg_filename, 1, wx.EXPAND)
        
        return bg_label_sizer
        
    def _createButtons(self):
        no_of_buttons = len(self.button_data)
        no_of_rows = int(math.ceil(no_of_buttons / self.NO_OF_BUTTONS_IN_EACH_ROW))
        
        button_sizer = wx.GridSizer( cols = self.NO_OF_BUTTONS_IN_EACH_ROW, rows = no_of_rows, hgap = 3, vgap = 3)
        
        for button_txt, bindfunc in self.button_data:
            button = wx.Button(self, -1, button_txt)
            button.Bind(wx.EVT_BUTTON, bindfunc)    
            button_sizer.Add(button, 1, wx.ALIGN_CENTER | wx.EXPAND)
            
            #################################################3
            if button_txt == '' or button_txt == 'Average':
                #button.Enable(False)
                pass
                
        return button_sizer    
    
    
    def _fileTypeIsCompatible(self, path):
        root, ext = os.path.splitext(path)

        compatible_formats = self.main_frame.getRawSettings().get('CompatibleFormats')
        
        if str(ext) in compatible_formats: 
            return True
        else:
            return False
    
    def _onViewButton(self, event):
        
        filelist = wx.FindWindowByName('FileListCtrl')
        filelist.openFileInExternalViewer() 
        #wx.CallAfter(self.main_frame.test2)
        
#        dlg = TestDialog2(self, -1)
#        dlg.ShowModal()
#        dlg.Destroy()
#        plot_panel = wx.FindWindowByName('PlotPanel')
#        ax = plot_panel.subplot1
#        plot_panel._insertLegend(ax)
#        

        
    def _onPlotButton(self, event):
        
        files = []
        
        for each_filename in self.dir_panel.file_list_box.getSelectedFilenames():
            path = os.path.join(self.dir_panel.file_list_box.path, each_filename)
            files.append(path)
            
        mainworker_cmd_queue.put(['plot', files])


    def _onPlotSECButton(self, event):
        
        files = []
        
        for each_filename in self.dir_panel.file_list_box.getSelectedFilenames():
            path = os.path.join(self.dir_panel.file_list_box.path, each_filename)
            files.append(path)

        frame_list = range(len(files))
            
        mainworker_cmd_queue.put(['sec_plot', [files, frame_list]])


    
    def _onClearAllButton(self, event):
        
        global workspace_saved

        if workspace_saved == False:
            dial = SaveDialog(self, -1, 'Workspace not saved', 'The workspace has been modified, do you want to save your changes?')
        else: 
            dial = wx.MessageDialog(self, 'Are you sure you want to clear everything?', 'Are you sure?', 
                                    wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        
        answer = dial.ShowModal()
        dial.Destroy()
        
        if answer == wx.ID_CANCEL or answer == wx.ID_NO:
            return
        if answer == wx.ID_SAVE:
            self.main_frame.saveWorkspace()
            
        else:
            answer2 = wx.ID_YES
            
            for each in self.manipulation_panel.modified_items:
                print each.sasm.getParameter('filename')
            
            if self.manipulation_panel.modified_items != [] or self.sec_panel.modified_items != []:
                
                if self.manipulation_panel.modified_items !=[] and self.sec_panel.modified_items != []:
                    message = 'manipulation and SEC '
                elif self.manipulation_panel.modified_items !=[] and self.sec_panel.modified_items == []:
                    message = 'manipulation '
                else:
                    message = 'SEC '

                dial2 = wx.MessageDialog(self, 'You have unsaved changes in your ' + message + 'data. Do you want to discard these changes?', 'Discard changes?', 
                                         wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                answer2 = dial2.ShowModal()
                dial2.Destroy()
            
            if answer2 == wx.ID_YES:
                self.plot_panel.clearAllPlots()
                self.image_panel.clearFigure()
                self.manipulation_panel.clearList()
                self.sec_plot_panel.clearAllPlots()
                self.sec_panel.clearList()
        
        info_panel = wx.FindWindowByName('InformationPanel')
        info_panel.clearInfo()
    
    def _onReduceButton(self, event):
        
        selected_files = self.dir_panel.file_list_box.getSelectedFilenames()
        
        load_path = self.dir_panel.getDirLabel()
        
        dlg = QuickReduceDialog(self, load_path, selected_files)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            save_path = dlg.getPath()
        else:
            return
        
        dlg.Destroy()
        
        mainworker_cmd_queue.put(['quick_reduce', [save_path, load_path, selected_files, '.dat']])
        
        
    def _onShowImageButton(self, event):
        
        if len(self.dir_panel.file_list_box.getSelectedFilenames()) > 0:
            filename = self.dir_panel.file_list_box.getSelectedFilenames()[0]        
            path = os.path.join(self.dir_panel.file_list_box.path, filename)
            mainworker_cmd_queue.put(['show_image', path])
        
    def _onSubtractButton(self, event):
        
        pass
        #dirpanel = wx.FindWindowByName('DirCtrlPanel')
        #print dirpanel.itemDataMap
        #wx.CallAfter(self.main_frame.showCenteringPane)
        
        #RAWSettings.loadSettings(self.main_frame.raw_settings, 'testdat.dat')
        
        #dlg = SaveAnalysisInfoDialog(self)
        #dlg.ShowModal()


class CustomListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):

    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self, parent, id, style = wx.LC_REPORT |wx.LC_VIRTUAL, name = 'FileListCtrl')
        
        self.path = os.getcwd()
        self.files = []
        self.parent = parent
        self.mainframe = wx.FindWindowByName('MainFrame')        
        self.file_panel = wx.FindWindowByName('FilePanel')
        self.dirctrl_panel = parent 

        self.filteredFilesList = []
        self.dirsList = []
        self.file_list_dict = {}
        self.folder_list_dict = {}
        
        self.copylist = []
        self.cut_selected = False
        self.copy_selected = False
        
        self.InsertColumn(0, 'Name')
        self.InsertColumn(1, 'Ext')
        self.InsertColumn(2, 'Modified')
        self.InsertColumn(3, 'Size', wx.LIST_FORMAT_RIGHT)    
        self.SetColumnWidth(0, 160)
        self.SetColumnWidth(1, 40)
        self.SetColumnWidth(2, 125)
        self.SetColumnWidth(3, 70)

        self.attr1 = wx.ListItemAttr()
        self.attr1.SetBackgroundColour('#e6f1f5')
        self.attr2 = wx.ListItemAttr()
        self.attr2.SetBackgroundColour("White")

        ### Prepare list images:
        self.il = wx.ImageList(16, 16)        

        a={"sm_up":"GO_UP","sm_dn":"GO_DOWN","w_idx":"WARNING","e_idx":"ERROR","i_idx":"QUESTION"}
        for k,v in a.items():
            s="self.%s= self.il.Add(wx.ArtProvider_GetBitmap(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k,v)
            exec(s)

        self.documentimg = self.il.Add(RAWIcons.document.GetBitmap())
        self.folderimg = self.il.Add(RAWIcons.Folder.GetBitmap())
        self.upimg = self.il.Add(RAWIcons.Up.GetBitmap())            
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
    
        #Init the list:
        self.itemDataMap = {}
        self.itemIndexMap = {}.keys()
        self.SetItemCount(len({}))

        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 4)
    
        #Default sorting order:
        self.SortListItems(0, 1)
        
        self.Bind(wx.EVT_LEFT_DCLICK, self._onDoubleLeftMouseClickOrEnterKey)
        self.Bind(wx.EVT_KEY_DOWN, self._onKeyPressEvent)
        self.Bind(wx.EVT_RIGHT_UP, self._onRightMouseClick)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.onColClick)

        #---------------------------------------------------
        # These methods are callbacks for implementing the
        # "virtualness" of the list...
        
        
#    def GetSecondarySortValues(self, col, key1, key2):
#
#        def ss(key):
#            return self.itemDataMap[key][3]
#        
#        return (ss(key1), ss(key2))

    def OnGetItemText(self, item, col):
        index=self.itemIndexMap[item]
        s = self.itemDataMap[index][col]
        return s

    def OnGetItemImage(self, item):
        index=self.itemIndexMap[item]
        itemtype = self.itemDataMap[index][4]

        if itemtype == 'file':
            return self.documentimg
        elif itemtype == 'up':
            return self.upimg
        elif itemtype == 'dir':
            return self.folderimg
        else:    
            return -1

    def OnGetItemAttr(self, item):
        index=self.itemIndexMap[item]

        if (item % 2) == 0:
           return self.attr1
        elif (item % 2) == 1:
           return self.attr2
        else:
           return None

    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    #---------------------------------------------------
    # Matt C, 2006/02/22
    # Here's a better SortItems() method --
    # the ColumnSorterMixin.__ColumnSorter() method already handles the ascending/descending,
    # and it knows to sort on another column if the chosen columns have the same value.

    def SortItems(self,sorter=cmp):
        items = list(self.itemDataMap.keys())
        items.sort(sorter)
        self.itemIndexMap = items
        
        # redraw the list
        self.Refresh()

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
#    def GetSortImages(self):
#        return (self.sm_dn, self.sm_up)

    def onColClick(self, event):
        
#        if event.GetColumn() == self.sort_column:
#            self.reverse_sort = not self.reverse_sort
#        else:
#            self.reverse_sort = False
        
#        self.sort_column = event.GetColumn()

#    self.updateSorting()

        event.Skip()
        #self.updateFileList()
 
    def readFileList(self):
        try:
            self.files = os.listdir(self.path)
                
        except OSError, msg:
            print msg
            wx.MessageBox(str(msg), 'Error loading folder', style = wx.ICON_ERROR | wx.OK)
            
    def getFilteredFileList(self):
        
        sel = self.dirctrl_panel.getExtensionFilterString() 
        extIdx = sel.find('*.')
        
        if self.dirctrl_panel.getExtensionFilterString() not in self.dirctrl_panel.file_extension_list:
            filteredFiles = fnmatch.filter(self.files, sel)
        else:
            try:
                if sel[-1] == ')':
                    extension = sel[extIdx+1:-1]
                else:
                    extension = sel[extIdx+1:]
            except IndexError:
                extension = ''

            if extension == '.':
                extension = ''
        
            if extension != '.*':
                filteredFiles = []
                for each in self.files:
                    name, ext = os.path.splitext(each)
                
                    if ext.lower() == extension:
                        filteredFiles.append(name+ext)
            else:
                filteredFiles = self.files
        
        # Filelist doesnt take Unicode! convert to normal strings:
        for i in range(0, len(filteredFiles)):
            filteredFiles[i] = str(filteredFiles[i].encode("iso-8859-15", "backslashreplace"))
            
        filteredFiles.sort(key = str.lower)
        
        return filteredFiles
    
    def getListDict(self):
        return self.list_dict
    
    def refreshFileList(self):
        self.DeleteAllItems()
        
        self.dirsList = []
        
        self.file_list_dict = {}
        self.folder_list_dict = {}
        
        ### Take out the directories and sort them:
        for each in self.files:
            if os.path.isdir(os.path.join(self.path, each)):
                self.dirsList.append(str(each))
        
        self.dirsList.sort(key = str.lower)
        
        ## Remove directories fromt the file list:   
        for each in self.dirsList:
            self.files.remove(each)
        
        filteredFiles = self.getFilteredFileList()  
        
        if len(self.path) > 1:
            #self.InsertStringItem(0, '..')
            #self.SetItemImage(0,0)
            j = 1
        else:
            j = 1
        
        for i in self.dirsList:
            (name, ext) = os.path.splitext(i)
            ex = ext[1:]
            
            try:
                size = os.path.getsize(os.path.join(self.path, i))
                sec = os.path.getmtime(os.path.join(self.path, i))
            except WindowsError:
                size = 1
                sec = 1

            self.file_list_dict[j] = (name, ex, time.strftime('%Y-%m-%d %H:%M', time.localtime(sec)), '', 'dir')
                      
            j += 1
        
        end_of_folders_idx = j    
            
        for i in filteredFiles:
            (name, ext) = os.path.splitext(i)
            ex = ext[1:]
            try:
                size = os.path.getsize(os.path.join(self.path, i))
                sec = os.path.getmtime(os.path.join(self.path, i))
            except Exception, e:
                print e
                size = 0
                sec = 1

            self.file_list_dict[j] = (name, ex, time.strftime('%Y-%m-%d %H:%M', time.localtime(sec)), str(round(size/1000,1)) + ' KB', 'file')
            
            j += 1
    
        self.insertSortedFilesIntoList(end_of_folders_idx)
    
    def insertSortedFilesIntoList(self, end_of_folders_idx):

        self.file_list_dict[0] = ('..', '', '', '', 'up')
        self.itemDataMap = self.file_list_dict
        self.itemIndexMap = self.file_list_dict.keys()
        self.SetItemCount(len(self.file_list_dict))
    
        self.OnSortOrderChanged()
    

    def getSelectedFilenames(self):
         
        if self.GetSelectedItemCount() == 0:
             return []
        
        selected = []
        selIdx = self.GetFirstSelected()
        
        filename = self.GetItemText(selIdx)
        ext_item = self.GetItem(selIdx,1).GetText()
        
        if ext_item:
            fullfilename = filename + '.' + ext_item
        else:
            fullfilename = filename
        
        selected.append(fullfilename)
        
        for i in range(1, self.GetSelectedItemCount()):
            newSelIdx = self.GetNextSelected(selIdx)
            selIdx = newSelIdx
            
            filename = self.GetItemText(selIdx)
            ext_item = self.GetItem(selIdx,1).GetText()
        
            if ext_item:
                fullfilename = filename + '.' + ext_item
            else:
                fullfilename = filename
            
            selected.append(fullfilename)
    
        return selected
    
    def updateFileList(self):
        col, ascending = self.GetSortState()

        self.readFileList()
        self.refreshFileList()
        self.itemDataMap = self.file_list_dict
        self.itemIndexMap = self.file_list_dict.keys()
        
        # self.OnSortOrderChanged()
        self.SortListItems(col, ascending)
    
    def _savePathToDisk(self):
        
        save_path = os.path.join(RAWWorkDir, 'backup.ini')
        
        data = {'path' : self.path}
        
        print self.path
                
        file_obj = open(save_path, 'w')
        cPickle.dump(data, file_obj)
        file_obj.close()
        #except Exception, e:
        #    print e
        
    def setDir(self, dir):
        self.path = dir
        self.updateFileList()
        
    def getDir(self):
        return self.path
        
    def _onKeyPressEvent(self, event):
        
        shift_is_down = event.ShiftDown()
        
        if event.GetKeyCode() ==  wx.WXK_F5:
            self.readFileList()
            self.refreshFileList()
            
        elif event.GetKeyCode() ==  wx.WXK_UP:
            self._onUpKey(shift_is_down)
            
        elif event.GetKeyCode() ==  wx.WXK_DOWN:
            self._onDownKey(shift_is_down)
            
        elif event.GetKeyCode() == wx.WXK_RETURN:
            self._onDoubleLeftMouseClickOrEnterKey(event)
            
        elif event.GetKeyCode() == 83: #S
            wx.CallAfter(self.file_panel._onShowImageButton, None)
            
        elif event.GetKeyCode() == 80: #P
            wx.CallAfter(self.file_panel._onPlotButton, None)
            
        elif event.GetKeyCode() == 67: #C
            wx.CallAfter(self.file_panel._onClearAllButton, None)
        
        elif event.GetKeyCode() == 81: #Q
            wx.CallAfter(self.file_panel._onReduceButton, None)
        
        elif event.GetKeyCode() == 69: #e
            self.openFileInExternalViewer()
            
    def _onUpKey(self, shift_is_down):
        
        selidx = self.GetFirstSelected()
        no_of_items = self.GetItemCount()
        
        new_idx = selidx - 1
        
        if new_idx != -1:
            if not shift_is_down:
                self.Select(selidx, False)
            self.Select(new_idx, True)
            self.EnsureVisible(new_idx)
     
    def _onDownKey(self, shift_is_down):
        selidx = self.GetFirstSelected()
        no_of_items = self.GetItemCount()
        
        new_idx = selidx + 1
        
        if selidx < no_of_items-1 :
            if not shift_is_down:
                self.Select(selidx, False)
            
            self.Select(new_idx, True)
            self.EnsureVisible(new_idx)
    
    
    def _showPopupMenu(self):
        
        menu = wx.Menu()
              
        menu.Append(1, 'New Folder')
        menu.AppendSeparator()
        menu.Append(2, 'Rename' )
        menu.AppendSeparator()
        menu.Append(3, 'Cut')
        menu.Append(4, 'Copy')
        paste = menu.Append(5, 'Paste')
        paste.Enable(False)
        
        if self.copy_selected or self.cut_selected:
            paste.Enable(True)
            
        
        menu.AppendSeparator()
        menu.Append(6, 'Delete')
        
        self.Bind(wx.EVT_MENU, self._onPopupMenuChoice)        
        self.PopupMenu(menu)
    
    def _onRightMouseClick(self, event):
        self._showPopupMenu()
    
    def _onPopupMenuChoice(self, event):
        choice_id = event.GetId()
        
        choices = {1 : self._createNewFolder,
                   2 : self._renameFile,
                   3 : self._cutFile,
                   4 : self._copyFile,
                   5 : self._pasteFile,
                   6 : self._deleteFile}
        
        if choices.has_key(choice_id):
            choices[choice_id]()
    
    def _pasteFile(self):
        
        if self.cut_selected or self.copy_selected:
           
            for each in self.copylist:
                
                try:
                    srcdir, filename = os.path.split(each)
                    dstpath = os.path.join(self.path, filename)
                
                    if self.cut_selected:        
                        shutil.move(each, dstpath)
                    elif self.copy_selected:
                        shutil.copy(each, dstpath)
                        
                except Exception, e: 
                    wx.MessageBox('Paste failed:\n' + str(e), 'Failed')
        
            self.cut_selected = False
            self.copy_selected = False
            self.copylist = []
            
            self.updateFileList()
        
    def _copyFile(self):
        
        filename_list = self.getSelectedFilenames()
        
        self.copylist = []
        for each in filename_list:
            self.copylist.append(os.path.join(self.path, each))
            
        self.copy_selected = True
        self.cut_selected = False
        
    def _cutFile(self):
        filename_list = self.getSelectedFilenames()
        
        self.copylist = []
        for each in filename_list:
            self.copylist.append(os.path.join(self.path, each))
            
        self.copy_selected = False
        self.cut_selected = True
        
    def _createNewFolder(self):
        
        dlg = FilenameChangeDialog(self, 'New Folder')
        result = dlg.ShowModal()
        
        if result == wx.ID_OK:
            dirname = dlg.getFilename()
            
            try:
                os.mkdir(os.path.join(self.path, dirname))
            except Exception, e:
                wx.MessageBox('Folder creation failed:\n' + str(e), 'Failed')
                return
    
        self.updateFileList()
    
    def _deleteFile(self):
        
        filename_list = self.getSelectedFilenames()
        
        if len(filename_list) == 1:
            txt = 'this'
            txt2 = ''
        elif len(filename_list) > 1:
            txt = 'these'
            txt2 = 's'
        else:
            wx.MessageBox('No files selected', 'Failed')
            return
        
        dlg = wx.MessageDialog(self, 'Are you sure you want to PERMANETLY delete ' + txt + ' file'+ txt2 +'?:', 'Are you sure?', wx.YES_NO | wx.ICON_INFORMATION)
    
        answer = dlg.ShowModal()
        
        if answer == wx.ID_YES:
            for each in filename_list:
                try:
                    if os.path.isdir(os.path.join(self.path, each)):
                        os.rmdir(os.path.join(self.path, each))
                    else:
                        os.remove(os.path.join(self.path, each))
                except Exception, e:
                     wx.MessageBox('Delete failed: ' + str(e), 'Failed')
                     return
                 
        self.updateFileList()
    
    def _renameFile(self):
        
        filename = self.getSelectedFilenames()[0]
        dlg = FilenameChangeDialog(self, filename)
        
        answer = dlg.ShowModal()
        
        if answer == wx.ID_OK:
            new_filename = dlg.getFilename()
            
            if new_filename != filename:
            
                try:
                    os.rename(os.path.join(self.path, filename), os.path.join(self.path, new_filename))
                except Exception, e:
                    wx.MessageBox('Rename failed: ' + str(e), 'Failed')
                    
                self.updateFileList()
            
        dlg.Destroy()
            
        
    
    def _onDoubleLeftMouseClickOrEnterKey(self, event):
        
        if self.getSelectedFilenames() != []:
            fullfilename = self.getSelectedFilenames()[0]
        else:
            return
        
        if fullfilename == '..':
            self.path = os.path.split(self.path)[0]
            if self.path == '.':
                self.path += '/' 
            self.parent.setDirLabel(self.path)
            self.updateFileList()
            
        elif os.path.isdir(os.path.join(self.path, fullfilename)):
            self.path = os.path.join(self.path, fullfilename)
            self.parent.setDirLabel(self.path)
            self.updateFileList()
            
        else:
            
            full_dir_filename = os.path.join(self.path, fullfilename)
            
            file, ext = os.path.splitext(full_dir_filename)
            
            if ext == '.wsp':
                ret = wx.MessageBox('Are you sure you want to load this workspace?',
                              'Load workspace?', style = wx.YES_NO | wx.ICON_QUESTION)
                
                if ret == wx.YES:
                    mainworker_cmd_queue.put(['load_workspace', [full_dir_filename]])
                    
            elif ext == '.cfg':
                ret = wx.MessageBox('Are you sure you want to load this config file?',
                              'Load new configuration?', style = wx.YES_NO | wx.ICON_QUESTION)
                
                if ret == wx.YES:
                    raw_settings = self.mainframe.getRawSettings()
                    
                    try:
                        success = RAWSettings.loadSettings(raw_settings, full_dir_filename)
                    except IOError, e:
                        wx.MessageBox(str(e), 'Error loading file', style = wx.OK | wx.ICON_EXCLAMATION)
                    
                    
                    if success:
                        raw_settings.set('CurrentCfg', full_dir_filename)
                    else:
                        wx.MessageBox('Load failed, config file might be corrupted',
                              'Load failed', style = wx.YES_NO | wx.ICON_EXCLAMATION)
                
            else:    
                mainworker_cmd_queue.put(('plot', [full_dir_filename]))
            
    def openFileInExternalViewer(self):

        if self.getSelectedFilenames():
            filepath = os.path.join(self.getDir(), self.getSelectedFilenames()[0])
        else:
            return

        try:
            if platform.system() == 'Darwin':
                subprocess.call(('open', filepath))
            elif os.name == 'nt':
                subprocess.call(('start', filepath), shell = True)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', filepath))
        except Exception, e:
            print e

class DirCtrlPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, name = 'DirCtrlPanel')
        self.parent = parent
        
        self.main_frame = wx.FindWindowByName('MainFrame')
        self.raw_settings = self.main_frame.getRawSettings()
        
        self.file_extension_list = ['All files (*.*)',
                                    'No Extension files (*.)',
                                    'TIFF files (*.tiff)',
                                    'TIF files (*.tif)',
                                    'RAD Files (*.rad)',
                                    'DAT files (*.dat)',
                                    'TXT files (*.txt)',
                                    'IMG files (*.img)',
                                    'FIT files (*.fit)',
                                    'WSP files (*.wsp)',
                                    'CFG files (*.cfg)']
        
        dirctrlpanel_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.ext_choice = self._createExtentionBox()       #File extention filter
        
        self._createDirCtrl(dirctrlpanel_sizer)            #Listbox containing filenames
        
        dirctrlpanel_sizer.Add(self.ext_choice, 0, wx.EXPAND | wx.TOP, 2)
        
        self.SetSizer(dirctrlpanel_sizer, wx.EXPAND)
        
        self.selected_file = None
        self._old_path = '.'
        
        self.file_list = []
        
    
    def _useSavedPathIfExisits(self):
        #if self.raw_settings.getAllParams().has_key('CurrentFilePath'):    
        #    path = self.raw_settings.get('CurrentFilePath')
        
        path = None

        load_path = os.path.join(RAWWorkDir, 'backup.ini')

        try:
            file_obj = open(load_path, 'r')
            data = cPickle.load(file_obj)
            file_obj.close()

            path = data['workdir']
        except Exception, e:
            print e
            path = None
                    
        if path != None and os.path.exists(path):
            self.setDirLabel(path)
            self.file_list_box.setDir(path)
            print 'Switched to saved path: ' + str(path)
        

    def _createDirCtrl(self, dirctrlpanel_sizer):
        
        dir_label_sizer = wx.BoxSizer()
        
        self.dir_label = wx.TextCtrl(self, -1, "/" , size = (30,16), style = wx.TE_PROCESS_ENTER)
        self.dir_label.Bind(wx.EVT_KILL_FOCUS, self._onEnterOrFocusShiftInDirLabel)
        self.dir_label.Bind(wx.EVT_TEXT_ENTER, self._onEnterOrFocusShiftInDirLabel)

        dir_bitmap = RAWIcons.folder_search.GetBitmap()
        refresh_bitmap = RAWIcons.refreshlist2.GetBitmap()
        
        self.dir_button = wx.BitmapButton(self, -1, dir_bitmap)
        self.dir_button.Bind(wx.EVT_BUTTON, self._onSetDirButton)
        self.dir_button.SetToolTipString('Open Folder')
        
        self.refresh_button = wx.BitmapButton(self, -1, refresh_bitmap)
        self.refresh_button.Bind(wx.EVT_BUTTON, self._onRefreshButton)
        self.refresh_button.SetToolTipString('Refresh')
        
        dir_label_sizer.Add(self.dir_label, 1, wx.EXPAND | wx.RIGHT, 2)
        dir_label_sizer.Add(self.dir_button,0)
        dir_label_sizer.Add(self.refresh_button,0)
        
        self.file_list_box = CustomListCtrl(self, -1)
        self.file_list_box.Bind(wx.EVT_LIST_ITEM_SELECTED, self._onLeftMouseClick)
        self.file_list_box.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self._onRightMouseClick)
        
        dirctrlpanel_sizer.Add(dir_label_sizer, 0, wx.EXPAND | wx.BOTTOM, 2)
        dirctrlpanel_sizer.Add(self.file_list_box, 1, wx.EXPAND)
        
        self.selected_files = []
        self.bg_filename = []
              
    def _createExtentionBox(self):
        self.dropdown = wx.ComboBox(self, style = wx.TE_PROCESS_ENTER)
        self.dropdown.AppendItems(strings = self.file_extension_list)
        self.dropdown.Select(n=0)
        self.dropdown.Bind(wx.EVT_COMBOBOX, self._onExtensionComboChoice)
        self.dropdown.Bind(wx.EVT_TEXT_ENTER, self._onExtensionComboEnterKey)
        self.dropdown.Bind(wx.EVT_TEXT, self._onExtensionComboTextChange)
        return self.dropdown
    
    def getExtensionFilterString(self):
        return self.dropdown.GetValue()
    
    def _onExtensionComboTextChange(self, event):
        self.file_list_box.updateFileList()
        
    def _onExtensionComboEnterKey(self, event):
        self.file_list_box.updateFileList()

    def _onExtensionComboChoice(self, event):   
        self.file_list_box.updateFileList()
        
    def _onEnterOrFocusShiftInDirLabel(self, event):
        pathtxt = self.getDirLabel()
            
        if pathtxt != self.file_list_box.getDir():
            if os.path.isdir(pathtxt):               
                self._old_path = pathtxt
                self.file_list_box.setDir(pathtxt)
            else:
                self.setDirLabel(str(self._old_path))
    
    def _onSetDirButton(self, event):
        pathtxt = self.getDirLabel()
        dirdlg = wx.DirDialog(self, "Please select directory:", str(pathtxt))
        
        if dirdlg.ShowModal() == wx.ID_OK:               
            path = dirdlg.GetPath()
            self.file_list_box.setDir(path)
            self.setDirLabel(path)
            
    def _onRefreshButton(self, event):
        self.file_list_box.updateFileList()
            
    def setDirLabel(self, path):
        self.dir_label.SetValue(path)
        
    def getDirLabel(self):
        return self.dir_label.GetValue()
      
    def _onLeftMouseClick(self, event):
        pass
    
    def _onRightMouseClick(self, event):
        pass
    

#--- ** Manipulation panel **

class ManipulationPanel(wx.Panel):
    def __init__(self, parent, raw_settings):
        wx.Panel.__init__(self, parent, name = 'ManipulationPanel')
        
        self.button_data = ( ('Save', self._onSaveButton),
                                     ('Sync', self._onSyncButton),
                                     ('Remove', self._onRemoveButton),
                                     ('Superimpose', self._onSuperimposeButton),
                                     ('Average', self._onAverageButton),
                                     ('Subtract', self._onSubtractButton))

        self.panelsizer = wx.BoxSizer(wx.VERTICAL)
        
        self._initializeIcons()
        toolbarsizer = self._createToolbar()

        self.underpanel = scrolled.ScrolledPanel(self, -1, style = wx.BORDER_SUNKEN)
        self.underpanel.SetVirtualSize((200, 200))
        self.underpanel.SetScrollRate(20,20)
      
        self.all_manipulation_items = []
        self.selected_item_list = []
        
        self.modified_items = []
        
        self.underpanel_sizer = wx.BoxSizer(wx.VERTICAL)    
        self.underpanel.SetSizer(self.underpanel_sizer)
        
        self.buttonSizer = self.createButtons()

        self.panelsizer.Add(toolbarsizer, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.EXPAND, 5)        
        self.panelsizer.Add(self.underpanel, 1, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 3)
        self.panelsizer.Add(self.buttonSizer, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.TOP |wx.BOTTOM | wx.LEFT | wx.RIGHT, 10)
        
        self.SetSizer(self.panelsizer)
        
        self._star_marked_item = None
        self._raw_settings = raw_settings
        
    def _initializeIcons(self):
        self.collapse_all_png = RAWIcons.collapse_all.GetBitmap()
        self.expand_all_png = RAWIcons.expand_all.GetBitmap()
        
        self.show_all_png = RAWIcons.open_eye.GetBitmap()
        self.hide_all_png = RAWIcons.close_eye.GetBitmap()
        
        self.select_all_png = RAWIcons.select_all.GetBitmap()
        
    def _createToolbar(self):
        
        sizer = wx.BoxSizer()
        
        collapse_all = wx.StaticBitmap(self, -1, self.collapse_all_png)
        expand_all = wx.StaticBitmap(self, -1, self.expand_all_png)
        show_all = wx.StaticBitmap(self, -1, self.show_all_png)
        hide_all = wx.StaticBitmap(self, -1, self.hide_all_png)
        
        select_all= wx.StaticBitmap(self, -1, self.select_all_png)
        
        select_all.Bind(wx.EVT_LEFT_DOWN, self._onSelectAllButton)
        collapse_all.Bind(wx.EVT_LEFT_DOWN, self._onCollapseAllButton)
        expand_all.Bind(wx.EVT_LEFT_DOWN, self._onExpandAllButton)
        show_all.Bind(wx.EVT_LEFT_DOWN, self._onShowAllButton)
        hide_all.Bind(wx.EVT_LEFT_DOWN, self._onHideAllButton)

        select_all.SetToolTipString('Select All')
        show_all.SetToolTipString('Show All')
        hide_all.SetToolTipString('Hide All')
        
        collapse_all.SetToolTipString('Collapse All')
        expand_all.SetToolTipString('Expand All')
        
        sizer.Add(show_all, 0, wx.LEFT, 5)
        sizer.Add(hide_all, 0, wx.LEFT, 5)
        sizer.Add((1,1),1, wx.EXPAND)
        sizer.Add(select_all, 0, wx.LEFT, 5)
        sizer.Add((1,1),1, wx.EXPAND)
        sizer.Add(collapse_all, 0, wx.RIGHT, 5)
        sizer.Add(expand_all, 0, wx.RIGHT, 3)
        
        return sizer
                
    def createButtons(self):
        
        cols = 3
        rows = round(len(self.button_data)/cols)
        
        sizer = wx.GridSizer(cols = cols, rows = rows, hgap = 3, vgap = 3)
        
        for each in self.button_data:
            label = each[0]
            func = each[1]
            
            button = wx.Button(self, -1, label)
            button.Bind(wx.EVT_BUTTON, func)
            
            ##########################################
            if label == 'BIFT':
                button.Enable(False)
            
            sizer.Add(button, 1, wx.ALIGN_CENTER | wx.EXPAND)
        
        return sizer
    
    def addItem(self, sasm, item_colour = 'black', item_visible = True, notsaved = False):
        
        newItem = ManipItemPanel(self.underpanel, sasm, font_colour = item_colour,
                                 item_visible = item_visible)
        self.Freeze()
        self.underpanel_sizer.Add(newItem, 0, wx.GROW)
        self.underpanel_sizer.Layout()
        
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        self.Layout()            
        self.Refresh()
        self.Thaw()
        
        # Keeping track of all items in our list:
        self.all_manipulation_items.append(newItem)
        
        
        sasm.item_panel = newItem
        
        if notsaved:
            newItem.markAsModified()
        
    def setItemAsBackground(self, item):
        
        bg_sasm = self._raw_settings.get('BackgroundSASM')
        
        if bg_sasm != None:
            try:
                bg_sasm.itempanel.enableStar(False)
            except:
                pass
        
        self._raw_settings.set('BackgroundSASM', item.sasm)
        item.enableStar(True)
        self._star_marked_item = item
        
    def getBackgroundItem(self):
        return self._star_marked_item
        
    def clearList(self):
        self.Freeze()
        
        rest_of_items = []
        for each in self.all_manipulation_items:
            
            try:
                each.Destroy()
            except ValueError:
                rest_of_items.append(each)

                
        self.all_manipulation_items = rest_of_items
        self.underpanel_sizer.Layout()
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        
        self._star_marked_item = None
        self.modified_items = []
        
        self.Thaw()
        
    def clearBackgroundItem(self):
        self._raw_settings.set('BackgroundSASM', None)
        self._star_marked_item = None
        
    def _collapseAllItems(self):
        for each in self.all_manipulation_items:
            each.showControls(False)
        
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        self.underpanel.Layout()            
        self.underpanel.Refresh()
        
        self.Layout()            
        self.Refresh()
            
    def _expandAllItems(self):
        for each in self.all_manipulation_items:
            each.showControls(True)
        
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        self.underpanel.Layout()            
        self.underpanel.Refresh()
        
        self.Layout()            
        self.Refresh()
        

    def removeItem(self, item):
        
        self.all_manipulation_items.remove(item)
        
        if item == self._star_marked_item:
            self._star_marked_item = None
        
        item.Destroy()
        
    def getSelectedItems(self):
        
        self.selected_item_list = []
        
        for each in self.all_manipulation_items:
            if each._selected == True:
                self.selected_item_list.append(each)
            
        return self.selected_item_list
    
    def selectAll(self):
        for each in self.all_manipulation_items:
                each._selected = False
                each.toggleSelect()
    
    def deselectAllExceptOne(self, item, line = None, enableLocatorLine = False):
        
        if line == None:    
            for each in self.all_manipulation_items:
                if each != item:
                    each._selected = True
                    each.toggleSelect()
        else:
            for each in self.all_manipulation_items:
                if each.sasm.getLine() == line:
                    each._selected = False
                    each.toggleSelect()
                else:
                    each._selected = True
                    each.toggleSelect()
                    
    def removeSelectedItems(self):
       
        if len(self.getSelectedItems()) == 0: return
        
        self.Freeze()
        
        info_panel = wx.FindWindowByName('InformationPanel')
        info_panel.clearInfo()
        
        axes_that_needs_updated_legend = []
         
        for each in self.getSelectedItems():
            
            try:
                self.modified_items.remove(each)
            except:
                pass
            
            plot_panel = each.sasm.plot_panel
            
            each.sasm.line.remove()
            each.sasm.err_line[0][0].remove()
            each.sasm.err_line[0][1].remove()
            each.sasm.err_line[1][0].remove()
            
            i = plot_panel.plotted_sasms.index(each.sasm)
            plot_panel.plotted_sasms.pop(i)
            
            if not each.sasm.axes in axes_that_needs_updated_legend:
                axes_that_needs_updated_legend.append(each.sasm.axes)
            
            if each == self._star_marked_item:
                self._star_marked_item = None
            
            idx = self.all_manipulation_items.index(each)
            self.all_manipulation_items[idx].Destroy()
            self.all_manipulation_items.pop(idx)
            
        
        for eachaxes in axes_that_needs_updated_legend:
            if eachaxes == plot_panel.subplot1:
                wx.CallAfter(plot_panel.updateLegend, 1)
            else:
                wx.CallAfter(plot_panel.updateLegend, 2)
        
        wx.CallAfter(plot_panel.canvas.draw)
        
        self.underpanel_sizer.Layout()
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        self.underpanel.Refresh()    
        
        self.Thaw()
        
    def _onShowAllButton(self, event):
        
        for each in self.all_manipulation_items:
           each.showItem(True)
           
        plot_panel = wx.FindWindowByName('PlotPanel')
        wx.CallAfter(plot_panel.updateLegend, 1)
        wx.CallAfter(plot_panel.updateLegend, 2)
        wx.CallAfter(plot_panel.fitAxis)
        
        self.underpanel.Layout()            
        self.underpanel.Refresh()
            
        self.Layout()            
        self.Refresh()
           
    def _onHideAllButton(self, event):
        self.underpanel.Freeze()
        
        for each in self.all_manipulation_items:
           each.showItem(False)
        
        self.underpanel.Layout()            
        self.underpanel.Refresh()
            
        self.Layout()            
        self.Refresh()
        
        self.underpanel.Thaw()
        
        plot_panel = wx.FindWindowByName('PlotPanel')
        wx.CallAfter(plot_panel.updateLegend, 1)
        wx.CallAfter(plot_panel.updateLegend, 2)
        wx.CallAfter(plot_panel.canvas.draw)
        
    def _onSelectAllButton(self, event):
        self.selectAll()
               
    def _onCollapseAllButton(self, event):
        self._collapseAllItems()
        
    def _onExpandAllButton(self, event):
        self._expandAllItems()
            
    def _onBiftButton(self, event):
        pass
    
    def _onAverageButton(self, event):
        selected_items = self.getSelectedItems()
        mainworker_cmd_queue.put(['average_items', selected_items])
        
    def _onRemoveButton(self, event):
        self.removeSelectedItems()
    
    def _onSaveButton(self, event):
        self.saveItems()
    
    def _onSyncButton(self, event):
        syncdialog = SyncDialog(self)
        syncdialog.ShowModal()
        syncdialog.Destroy()
        
    def _onSubtractButton(self, event):
        mainworker_cmd_queue.put(['subtract_items', ( self._star_marked_item, self.getSelectedItems()  )])
        
    def _onSuperimposeButton(self, event):
        mainworker_cmd_queue.put(['superimpose_items', ( self._star_marked_item, self.getSelectedItems()  )])
        
    
    def synchronizeSelectedItems(self, sync_parameters):
        star_item = self.getBackgroundItem()
        
        if not star_item or (len(sync_parameters) == 0):
            return
        
        star_sasm = star_item.getSASM()
        
        scale = star_sasm.getScale()
        offset = star_sasm.getOffset()
        nmin, nmax = star_sasm.getQrange()
        qmin, qmax = star_sasm.getBinnedQ()[nmin], star_sasm.getBinnedQ()[nmax-1]
        linestyle = star_sasm.line.get_linestyle()
        linewidth = star_sasm.line.get_linewidth()
        linemarker = star_sasm.line.get_marker() 
        
        selected_items = self.getSelectedItems()
        
        findClosest = lambda a,l:min(l,key=lambda x:abs(x-a))
        
        for each_item in selected_items:
            if each_item == star_item:
                continue
            
            sasm = each_item.getSASM()
            
            old_nmin, old_nmax = sasm.getQrange()
            
            try:
                if 'nmin' in sync_parameters and 'nmax' in sync_parameters:
                    sasm.setQrange([nmin, nmax])
                elif 'nmin' in sync_parameters:
                    sasm.setQrange([nmin, old_nmax])
                elif 'nmax' in sync_parameters:
                    sasm.setQrange([old_nmin, nmax])                    
                    
            except SASExceptions.InvalidQrange, msg:
                dial = wx.MessageDialog(None, 'Filename : ' + sasm.getParameter('filename') + '\n\n' + str(msg),
                                'Invalid Qrange',
                                wx.OK | wx.CANCEL | wx.NO_DEFAULT | wx.ICON_QUESTION)
                answer = dial.ShowModal()
                    
                if answer == wx.ID_CANCEL:
                    return
                
            q = sasm.getBinnedQ()
            
            if 'qmin' in sync_parameters and 'qmax' in sync_parameters:
                closest = findClosest(qmin, q)
                new_nmin = numpy.where(q == closest)[0][0]
                closest = findClosest(qmax, q)
                new_nmax = numpy.where(q == closest)[0][0]
                sasm.setQrange([new_nmin, new_nmax])
            elif 'qmin' in sync_parameters:
                closest = findClosest(qmin, q)
                new_nmin = numpy.where(q == closest)[0][0]
                sasm.setQrange([new_nmin, old_nmax])    
            elif 'qmax' in sync_parameters:
                closest = findClosest(qmax, q)
                new_nmax = numpy.where(q == closest)[0][0]
                sasm.setQrange([old_nmin, new_nmax])
                
            if 'scale' in sync_parameters:
                sasm.scale(scale)
            if 'offset' in sync_parameters:
                sasm.offset(offset)
            if 'linestyle' in sync_parameters:
                sasm.line.set_linestyle(linestyle)
            if 'linewidth' in sync_parameters:
                sasm.line.set_linewidth(linewidth)
            if 'linemarker' in sync_parameters:
                sasm.line.set_marker(linemarker)
            
            each_item.updateControlsFromSASM()
        
    def movePlots(self, ExpObjList, toAxes):
        
        for each_item in ExpObjList:
            
            each = each_item.getSASM()
            
            if each.axes != toAxes:
                plotpanel = each.plot_panel
      
                each.line.remove()
                each.err_line[0][0].remove()
                each.err_line[0][1].remove()
                each.err_line[1][0].remove()
        
                line_color = each.line.get_color()
                
                if each_item.getLegendLabel() != '':
                    label = each_item.getLegendLabel()
                else:
                    label = None
                
                wx.CallAfter(plotpanel.plotSASM, each, toAxes, color = line_color, legend_label_in = label)
                
                
        plotpanel = wx.FindWindowByName('PlotPanel')
        wx.CallAfter(plotpanel.updateLegend, 1)
        wx.CallAfter(plotpanel.updateLegend, 2)
        wx.CallAfter(plotpanel.canvas.draw)
    
    def getItems(self):
        return self.all_manipulation_items
            
    def updateLayout(self):
        self.underpanel_sizer.Layout()
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
    
    def saveItems(self):
        selected_items = self.getSelectedItems()

        dirctrl_panel = wx.FindWindowByName('DirCtrlPanel')
        path = dirctrl_panel.getDirLabel()

        if len(selected_items) == 1:
            
            # filters = 'Comma Separated Files (*.csv)|*.csv'
                
            # dialog = wx.FileDialog( None, style = wx.SAVE | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = save_path) 
            fname = os.path.splitext(os.path.basename(selected_items[0].sasm.getParameter('filename')))[0]+'.dat'
            msg = "Please select save directory and enter save file name"
            dialog = wx.FileDialog(self, message = msg, style = wx.FD_SAVE, defaultDir = path, defaultFile = fname) 
                
            if dialog.ShowModal() == wx.ID_OK:               
                path = dialog.GetPath()
            else:
                return

            path=os.path.splitext(path)[0]+'.dat'
            filename = os.path.basename(path)
            selected_items[0].sasm.setParameter('filename', filename)
            wx.CallAfter(selected_items[0].updateFilenameLabel)

            save_path = os.path.dirname(path)
        
        elif len(selected_items) == 0:
            return

        else:
            dirdlg = wx.DirDialog(self, "Please select save directory (multiple files will be saved):", defaultPath = path,)
            
            if dirdlg.ShowModal() == wx.ID_OK:
                path = dirdlg.GetPath()
            else:
                return
            save_path = path
        
        mainworker_cmd_queue.put(['save_items', [save_path, selected_items]])
        

class ManipItemPanel(wx.Panel):
    def __init__(self, parent, sasm, font_colour = 'BLACK', legend_label = '', item_visible = True):
        
        wx.Panel.__init__(self, parent, style = wx.BORDER_RAISED)
        
        self.parent = parent
        self.sasm = sasm
        self.sasm.itempanel = self
        
        self.manipulation_panel = wx.FindWindowByName('ManipulationPanel')
        self.plot_panel = wx.FindWindowByName('PlotPanel')
        self.main_frame = wx.FindWindowByName('MainFrame')
        
        self.raw_settings = self.main_frame.raw_settings
        
        self.info_panel = wx.FindWindowByName('InformationPanel')
        self.info_settings = {'hdr_choice' : 0}
        
        self._selected_as_bg = False
        self._selected_for_plot = item_visible
        self._controls_visible = True
        self._selected = False
        self._legend_label = legend_label
        
        self._font_colour = font_colour
        
        filename = sasm.getParameter('filename')
               
        self.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
        self.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
        self.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
        #Label, TextCtrl_ID, SPIN_ID
        
        self._initializeIcons()
                                       
        self.qmax = len(self.sasm.q)
                             
        self.spin_controls = (("q Min:", wx.NewId(), wx.NewId(), (1, self.qmax-1), 'nlow'),        
                             ("q Max:", wx.NewId(), wx.NewId(), (2, self.qmax), 'nhigh'))
        
        self.float_spin_controls = (
                                   # ("Conc:", wx.NewId(), 'conc', '1.0', self._onScaleOffsetChange),
                                    ("Scale:", wx.NewId(), 'scale', str(sasm.getScale()), self._onScaleOffsetChange),
                                    ("Offset:", wx.NewId(), 'offset', str(sasm.getOffset()), self._onScaleOffsetChange))
    
        self.SelectedForPlot = RAWCustomCtrl.CustomCheckBox(self, -1, filename)
        self.SelectedForPlot.SetValue(True)
        self.SelectedForPlot.Bind(wx.EVT_CHECKBOX, self._onSelectedChkBox)
        self.SelectedForPlot.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
        self.SelectedForPlot.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
        self.SelectedForPlot.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
        
        self.SelectedForPlot.SetToolTipString('Show Plot')
        self.SelectedForPlot.SetForegroundColour(font_colour)
        
        self.legend_label_text = wx.StaticText(self, -1, '')
        
        self.legend_label_text.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
        self.legend_label_text.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
        self.legend_label_text.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
        
        conv = mplcol.ColorConverter()
        color = conv.to_rgb(self.sasm.line.get_mfc())
        color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        self.colour_indicator = RAWCustomCtrl.ColourIndicator(self, -1, color, size = (20,15))
        self.colour_indicator.Bind(wx.EVT_LEFT_DOWN, self._onLinePropertyButton)
        self.colour_indicator.SetToolTipString('Line Properties')

        self.bg_star = wx.StaticBitmap(self, -1, self.gray_png)
        self.bg_star.Bind(wx.EVT_LEFT_DOWN, self._onStarButton)
        self.bg_star.SetToolTipString('Mark')
        
        self.expand_collapse = wx.StaticBitmap(self, -1, self.collapse_png)
        self.expand_collapse.Bind(wx.EVT_LEFT_DOWN, self._onExpandCollapseButton)
        self.expand_collapse.SetToolTipString('Collapse/Expand')
        
        self.target_icon = wx.StaticBitmap(self, -1, self.target_png)
        self.target_icon.Bind(wx.EVT_LEFT_DOWN, self._onTargetButton)
        self.target_icon.SetToolTipString('Locate Line')

        self.info_icon = wx.StaticBitmap(self, -1, self.info_png)
        self.info_icon.Bind(wx.EVT_LEFT_DOWN, self._onInfoButton)
        self.info_icon.SetToolTipString('Show Extended Info\n--------------------------------\nRg: N/A\nI(0): N/A')
        
        self.locator_on = False
        self.locator_old_width = 1
        
        panelsizer = wx.BoxSizer()
        panelsizer.Add(self.SelectedForPlot, 0, wx.LEFT | wx.TOP, 3)
        panelsizer.Add(self.legend_label_text, 0, wx.LEFT | wx.TOP, 3)
        panelsizer.Add((1,1), 1, wx.EXPAND)
        panelsizer.Add(self.expand_collapse, 0, wx.RIGHT | wx.TOP, 5)
        panelsizer.Add(self.info_icon, 0, wx.RIGHT | wx.TOP, 5)
        panelsizer.Add(self.target_icon, 0, wx.RIGHT | wx.TOP, 4)
        panelsizer.Add(self.colour_indicator, 0, wx.RIGHT | wx.TOP, 5)
        panelsizer.Add(self.bg_star, 0, wx.LEFT | wx.RIGHT | wx.TOP, 3)
        
    
        self.topsizer = wx.BoxSizer(wx.VERTICAL)
        self.topsizer.Add(panelsizer, 1, wx.EXPAND)
        
        #self.controlSizer = wx.BoxSizer(wx.VERTICAL)
        self.controlSizer = wx.FlexGridSizer(cols = 4, rows = 2, vgap = 3, hgap = 7)
       
        self._createSimpleSpinCtrls(self.controlSizer)
        self._createFloatSpinCtrls(self.controlSizer) 
        
        self.topsizer.Add((5,5),0)
        self.topsizer.Add(self.controlSizer, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM, 5)
        
        self.SetSizer(self.topsizer)
        
        self.SetBackgroundColour(wx.Colour(250,250,250))
        
        self._initStartPosition()
        self._updateQTextCtrl()
        
        if self.sasm.getParameter('analysis').has_key('guinier'):
            self.updateInfoTip(self.sasm.getParameter('analysis'))
            
        controls_not_shown = self.main_frame.raw_settings.get('ManipItemCollapsed')
        
        if not self._selected_for_plot:
            controls_not_shown = True
        
        if controls_not_shown:
            self.showControls(not controls_not_shown)
        
        self.updateShowItemCheckBox()
        
        
    def updateInfoTip(self, analysis_dict, fromGuinierDialog = False):
        
        if analysis_dict.has_key('guinier'):
            guinier = analysis_dict['guinier']
        else:
            guinier = {}
        
        string0 = 'Show Extended Info\n--------------------------------'
        string1 = ''
        string2 = ''
        string3 = ''
        
        if guinier.has_key('Rg') and guinier.has_key('I0'):
            rg = guinier['Rg']
            i_zero = guinier['I0']
        
            string1 = '\nRg: ' + str(rg) + '\nI(0): ' + str(i_zero)
        else:
            string1 = '\nRg: N/A' + '\nI(0): N/A'
            
        if self.sasm.getAllParameters().has_key('Conc'):
            string2 = '\nConc: ' + str(self.sasm.getParameter('Conc'))
                    
        if self.sasm.getAllParameters().has_key('Notes'):
            if self.sasm.getParameter('Notes') != '':
                string3 = '\nNote: ' + str(self.sasm.getParameter('Notes'))  
        
        string = string0+string1+string2+string3
        
        if string != '':    
            self.info_icon.SetToolTipString(string)
                
        if fromGuinierDialog:     
            self.info_panel.updateInfoFromItem(self)
                
    def enableStar(self, state):
        if state == True:
            self.bg_star.SetBitmap(self.star_png)
            self._selected_as_bg = True
        else:
            self.bg_star.SetBitmap(self.gray_png)
            self._selected_as_bg = False
        
        self.bg_star.Refresh()
        
    def removeSelf(self):
        #Has to be callafter under Linux.. or it'll crash
        wx.CallAfter(self.manipulation_panel.removeSelectedItems)
        
    def getSASM(self):
        return self.sasm        
    
    def getFontColour(self):
        return self._font_colour
    
    def getSelectedForPlot(self):
        return self._selected_for_plot
    
    def getLegendLabel(self):
        return self._legend_label
    
    def updateControlsFromSASM(self):    
        scale = self.sasm.getScale()
        offset = self.sasm.getOffset()
        qmin, qmax = self.sasm.getQrange()
        
        qmin_ctrl = wx.FindWindowById(self.spin_controls[0][1])
        qmax_ctrl = wx.FindWindowById(self.spin_controls[1][1])
        qmintxt = wx.FindWindowById(self.spin_controls[0][2])
        qmaxtxt = wx.FindWindowById(self.spin_controls[1][2])
        
        qmin_ctrl.SetValue(str(qmin))
        qmax_ctrl.SetValue(str(qmax-1))        
        qmintxt.SetValue(str(round(self.sasm.q[qmin],4)))
        qmaxtxt.SetValue(str(round(self.sasm.q[qmax-1],4)))
        
        scale_ctrl = wx.FindWindowById(self.float_spin_controls[0][1])
        offset_ctrl = wx.FindWindowById(self.float_spin_controls[1][1])
    
        offset_ctrl.SetValue(str(offset))
        scale_ctrl.SetValue(str(scale))
        
        wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
    
    def toggleSelect(self):
        
        if self._selected:
            self._selected = False
            self.SetBackgroundColour(wx.Colour(250,250,250))
            self.info_panel.clearInfo()
        else:
            self._selected = True
            self.SetBackgroundColour(wx.Colour(200,200,200))
            self.SetFocusIgnoringChildren()
            self.info_panel.updateInfoFromItem(self)
        
        self.Refresh()
        
    def enableLocatorLine(self):
        
        self.locator_on = not self.locator_on
        
        if self.locator_on == True:
            self.target_icon.SetBitmap(self.target_on_png)
            self.locator_old_width = self.sasm.line.get_linewidth()
            new_width = self.locator_old_width + 2.0
            self.sasm.line.set_linewidth(new_width)
            wx.CallAfter(self.sasm.plot_panel.canvas.draw)
        else:
            self.target_icon.SetBitmap(self.target_png)
            self.sasm.line.set_linewidth(self.locator_old_width)
            wx.CallAfter(self.sasm.plot_panel.canvas.draw)
            
        self.target_icon.Refresh()
        
    def getControlsVisible(self):
        return self._controls_visible
        
    def showControls(self, state):
        
        if state == False:
            self.expand_collapse.SetBitmap(self.expand_png)
            self._controls_visible = False
            self.controlSizer.Hide(0, True)
            self.controlSizer.Hide(1, True)
            self.controlSizer.Hide(2, True)
            self.controlSizer.Hide(3, True)
            self.controlSizer.Hide(4, True)
            self.controlSizer.Hide(5, True)
            self.controlSizer.Hide(6, True)
            self.controlSizer.Hide(7, True)
        else:
            self.expand_collapse.SetBitmap(self.collapse_png)
            self._controls_visible = True
            self.controlSizer.Show(0, True)
            self.controlSizer.Show(1, True)
            self.controlSizer.Show(2, True)
            self.controlSizer.Show(3, True)
            self.controlSizer.Show(4, True)
            self.controlSizer.Show(5, True)
            self.controlSizer.Show(6, True)
            self.controlSizer.Show(7, True)
            
        self.expand_collapse.Refresh()
        self.topsizer.Layout()
        
    
    def showItem(self, state):
        self._selected_for_plot = state
        
        if self._selected_for_plot == False:
            self._controls_visible = False
            self.showControls(self._controls_visible)
        
        self.SelectedForPlot.SetValue(self._selected_for_plot)
        self.sasm.line.set_visible(self._selected_for_plot)
        self.sasm.line.set_picker(self._selected_for_plot)      #Line can't be selected when it's hidden

        if not state:
            each = self.sasm

            item_plot_panel = each.plot_panel

            err_bars = item_plot_panel.plotparams['errorbars_on']

            if err_bars:

                for each_err_line in each.err_line[0]:
                    each_err_line.set_visible(state)  
                    
                for each_err_line in each.err_line[1]:
                    each_err_line.set_visible(state)

        else:
            each = self.sasm

            item_plot_panel = each.plot_panel

            err_bars = item_plot_panel.plotparams['errorbars_on']

            if err_bars:

                for each_err_line in each.err_line[0]:
                    each_err_line.set_visible(state)  
                    
                for each_err_line in each.err_line[1]:
                    each_err_line.set_visible(state)
                    
                if state == True:
                    #Update errorbar positions
                    
                    q_min, q_max = each.getQrange()
                    q = each.q
                    i = each.i
                    
                    caplines = each.err_line[0]
                    barlinecols = each.err_line[1]
                    
                    yerr = each.err
                    x = q
                    y = i                                  
                    
                    # Find the ending points of the errorbars 
                    error_positions = (x, y-yerr), (x, y+yerr) 

                    # Update the caplines 
                    for i,pos in enumerate(error_positions): 
                        caplines[i].set_data(pos) 

                    # Update the error bars 
                    barlinecols[0].set_segments(zip(zip(x,y-yerr), zip(x,y+yerr))) 
    
    def updateShowItemCheckBox(self):
        #self.showControls(self._controls_visible)
        self.SelectedForPlot.SetValue(self._selected_for_plot)
        self.sasm.line.set_picker(self._selected_for_plot)
    
    def markAsModified(self):
        parent = self.GetParent()
        
        filename = self.sasm.getParameter('filename')
        self.SelectedForPlot.SetLabel('* ' + str(filename))
        self.SelectedForPlot.Refresh()
        self.topsizer.Layout()
        parent.Layout()            
        parent.Refresh()
        
        if self not in self.manipulation_panel.modified_items:
            self.manipulation_panel.modified_items.append(self)
    
    def unmarkAsModified(self):
        parent = self.GetParent()
        
        filename = self.sasm.getParameter('filename')
        self.SelectedForPlot.SetLabel(str(filename))
        self.SelectedForPlot.Refresh()
        self.topsizer.Layout()
        parent.Layout()            
        parent.Refresh()
        try:
            self.manipulation_panel.modified_items.remove(self)
        except:
            pass
        
    def updateFilenameLabel(self):
        filename = self.sasm.getParameter('filename')
        
        if self._legend_label == '':
            self.sasm.line.set_label(filename)
        self.plot_panel.updateLegend(self.sasm.axes)
        self.SelectedForPlot.SetLabel(str(filename))
        self.SelectedForPlot.Refresh()
        self.topsizer.Layout()
        self.GetParent().Layout()            
        self.GetParent().Refresh()
    
    
    def useAsMWStandard(self):
        
        if self.sasm.getAllParameters().has_key('Conc'):
            conc = self.sasm.getParameter('Conc')
            
            if float(conc) > 0:
                if self.sasm.getParameter('analysis').has_key('guinier'):
                    analysis = self.sasm.getParameter('analysis')
                    guinier = analysis['guinier']
                        
                    if guinier.has_key('I0'):
                        i0 = guinier['I0']
                            
                        if float(i0)>0:
                            MW = wx.GetTextFromUser('Please enter the molecular weight of the standard in units of [kDa].')
                                
                            try:
                                MW = float(MW)
                            except Exception:
                                wx.MessageBox('Invalid input!', 'ERROR', wx.OK | wx.ICON_EXCLAMATION)
                                return

                            filename = os.path.basename(self.sasm.getParameter('filename'))
                                
                            self.raw_settings.set('MWStandardMW', float(MW))
                            self.raw_settings.set('MWStandardI0', float(i0))
                            self.raw_settings.set('MWStandardConc', float(conc))
                            self.raw_settings.set('MWStandardFile', filename)

                            self.sasm.setParameter('MW', MW)
                            self.info_panel.updateInfoFromItem(self)
                                
                            wx.MessageBox('New standard parameters has been saved.', 'Saved', wx.OK | wx.ICON_INFORMATION)
                                
                    else:
                        wx.MessageBox('Please perform a Guinier analysis to obtain I0', 'I0 not found', wx.OK | wx.ICON_EXCLAMATION)
                else:
                    wx.MessageBox('Please perform a Guinier analysis to obtain I0', 'I0 not found', wx.OK | wx.ICON_EXCLAMATION)
            else:
                wx.MessageBox('Please enter the concentration in the information panel.', 'Concentration not found', wx.OK | wx.ICON_EXCLAMATION)
        else:
            wx.MessageBox('Please enter the concentration in the information panel.', 'Concentration not found', wx.OK | wx.ICON_EXCLAMATION)  #  except Exception, e:

                
    def _initializeIcons(self):
        
        self.gray_png = RAWIcons.Star_icon_notenabled.GetBitmap()
        self.star_png = RAWIcons.Star_icon_org.GetBitmap()
        
        self.collapse_png = RAWIcons.collapse.GetBitmap()
        self.expand_png = RAWIcons.expand.GetBitmap()
        
        self.target_png = RAWIcons.target.GetBitmap()
        self.target_on_png = RAWIcons.target_orange.GetBitmap()

        self.info_png = RAWIcons.info_16_2.GetBitmap()

    def _initStartPosition(self):
        
        qmin_ctrl = wx.FindWindowById(self.spin_controls[0][1])
        qmax_ctrl = wx.FindWindowById(self.spin_controls[1][1])
        
        qrange = self.sasm.getQrange()
        
        qmin_ctrl.SetValue(str(qrange[0]))
        qmax_ctrl.SetValue(str(qrange[1]-1))
        
    def _updateColourIndicator(self):
        conv = mplcol.ColorConverter()
        color = conv.to_rgb(self.sasm.line.get_color())
        color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        self.colour_indicator.updateColour(color)
        
    def _onLinePropertyButton(self, event):
        
        try:
            legend_label = self.getLegendLabel()
            dialog = LinePropertyDialog(self, self.sasm, legend_label)
            answer = dialog.ShowModal()
            new_legend_label = dialog.getLegendLabel()
            self._updateColourIndicator()
            dialog.Destroy()
            
            if answer == wx.ID_OK:
                self._legend_label = new_legend_label
                self._updateLegendLabel()
                
        except TypeError:
            return
           
        if self.sasm.axes == self.plot_panel.subplot1:
            wx.CallAfter(self.plot_panel.updateLegend, 1)
        else:
            wx.CallAfter(self.plot_panel.updateLegend, 2)
            
        self.sasm.plot_panel.canvas.draw()
        
    def _onExpandCollapseButton(self, event):
        self._controls_visible = not self._controls_visible
        self.showControls(self._controls_visible)
        
        self.manipulation_panel.underpanel.SetVirtualSize(self.manipulation_panel.underpanel.GetBestVirtualSize())
        self.GetParent().Layout()            
        self.GetParent().Refresh()
        
        self.GetParent().GetParent().Layout()            
        self.GetParent().GetParent().Refresh()
                        
    def _onTargetButton(self, event):
        self.enableLocatorLine()
        
    def _onInfoButton(self, event):
        pass
            
    def _showPopupMenu(self):

        menu = wx.Menu()
        
        number_of_selected_items = len(self.manipulation_panel.getSelectedItems())
        
#        iftmenu = wx.Menu()
#        iftmenu.Append(10, 'Run BIFT')
#        iftmenu.Append(11, 'Run GNOM using current Dmax')
#        iftmenu.AppendSeparator()
#        iftmenu.Append(12, 'Add to IFT list')
        
        convertq_menu = wx.Menu()
        convertq_menu.Append(15, 'q * 10')
        convertq_menu.Append(16, 'q / 10')
        
        submenu = menu.Append(4, 'Subtract')
        avgmenu = menu.Append(6, 'Average' )
        mermenu = menu.Append(22, 'Merge')
        rebmenu = menu.Append(23, 'Rebin')
        intmenu = menu.Append(25, 'Interpolate')
        menu.AppendSeparator()
        menu.Append(27, 'Use as MW standard')
        menu.Append(28, 'Normalize by conc')
        
        menu.AppendSeparator()
        menu.Append(5, 'Remove' )
        menu.AppendSeparator()
        menu.Append(13, 'Guinier fit')
        menu.Append(29, 'Molecular weight')
        menu.Append(24, 'Add to IFT list')
        
        if self.sasm.getAllParameters().has_key('orig_sasm'):
            menu.Append(26, 'Plot fit')
            
        #menu.AppendMenu(3, 'Indirect Fourier Transform', iftmenu)
        menu.AppendMenu(wx.NewId(), 'Convert q-scale', convertq_menu)
        
        menu.AppendSeparator()
        img = menu.Append(19, 'Show image')
        
        if not self.sasm.getAllParameters().has_key('load_path'):
            img.Enable(False)
        menu.Append(20, 'Show data')
        menu.Append(21, 'Show header')
        
        menu.AppendSeparator()
        menu.Append(8, 'Move to top plot')
        menu.Append(9, 'Move to bottom plot')
        menu.AppendSeparator()
        menu.Append(14, 'Rename')
        #menu.Append(17, 'Set legend label...')
        menu.AppendSeparator()
        menu.Append(30, 'Save all analysis info')
        menu.Append(18, 'Save item info')
        menu.Append(7, 'Save selected file(s)')
        
        self.Bind(wx.EVT_MENU, self._onPopupMenuChoice)        
        self.PopupMenu(menu)
    
    def _onShowImage(self):
        
        if self.sasm.getAllParameters().has_key('load_path'):
            path = self.sasm.getParameter('load_path')
            mainworker_cmd_queue.put(['show_image', path])
    
    def _onPopupMenuChoice(self, evt):
            
#        if evt.GetId() == 3:
#            #IFT
#            analysisPage.runBiftOnExperimentObject(self.ExpObj, expParams)
        
        if evt.GetId() == 4:
            #Subtract
            selected_items = self.manipulation_panel.getSelectedItems()
            marked_item = self.manipulation_panel.getBackgroundItem()
            mainworker_cmd_queue.put(['subtract_items', [marked_item, selected_items]])
        
        if evt.GetId() == 5:
            #Delete
            wx.CallAfter(self.manipulation_panel.removeSelectedItems)
        
        if evt.GetId() == 6:
            #Average 
            selected_items = self.manipulation_panel.getSelectedItems()
            mainworker_cmd_queue.put(['average_items', selected_items])
            
        if evt.GetId() == 7:
            self.manipulation_panel.saveItems()
                
        if evt.GetId() == 8:
            #Move to top plot
            plotpanel = wx.FindWindowByName('PlotPanel')
            selected_items = self.manipulation_panel.getSelectedItems()
            self.manipulation_panel.movePlots(selected_items, plotpanel.subplot1)
            wx.CallAfter(plotpanel.fitAxis)
                
        if evt.GetId() == 9:
            #Move to bottom plot
            plotpanel = wx.FindWindowByName('PlotPanel')
            selected_items = self.manipulation_panel.getSelectedItems()
            self.manipulation_panel.movePlots(selected_items, plotpanel.subplot2)
            wx.CallAfter(plotpanel.fitAxis)
            
        if evt.GetId() == 13:
            #Guinier fit
            Mainframe = wx.FindWindowByName('MainFrame')
            selectedSASMList = self.manipulation_panel.getSelectedItems()
            
            sasm = selectedSASMList[0].getSASM()
            Mainframe.showGuinierFitFrame(sasm, selectedSASMList[0])
            
        if evt.GetId() == 10:
            #BIFT
            analysisPage = wx.FindWindowByName('AutoAnalysisPage')
            analysisPage.runBiftOnExperimentObject(self.ExpObj.copy(), expParams)
            
        if evt.GetId() == 12:
            #Add to IFT List
            autoanalysis = wx.FindWindowByName('AutoAnalysisPage')
            
            for ExpObj in ManipulationPage.GetSelectedExpObjs():
                ExpObjIFT = ExpObj.copy()
                autoanalysis.addExpObjToList(ExpObjIFT)
            
            wx.CallAfter(wx.MessageBox, 'File(s) have been added to the IFT list', 'Files Added')
            
        if evt.GetId() == 11:
            #GNOM
            analysisPage.runBiftOnExperimentObject(self.ExpObj.copy(), expParams)
            
        if evt.GetId() == 14:
            dlg = FilenameChangeDialog(self, self.sasm.getParameter('filename'))
            dlg.ShowModal()
            filename =  dlg.getFilename()
            dlg.Destroy()
            
            if filename:
                self.sasm.setParameter('filename', filename)
                self.updateFilenameLabel()
                self.markAsModified()
        
        if evt.GetId() == 15:
            #A to s
            self.sasm.scaleBinnedQ(10.0)
            self._updateQTextCtrl()
            wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
            
        if evt.GetId() == 16:
            #s to A
            self.sasm.scaleBinnedQ(0.1)
            self._updateQTextCtrl()
            wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
        
#        if evt.GetId() == 17:
#            dlg = LegendLabelChangeDialog(self, self._legend_label)
#            answer = dlg.ShowModal()
#            legend_label = dlg.getLegendLabel()
#            dlg.Destroy()
#            
#            if answer == wx.ID_OK:
#                self._legend_label = legend_label
#                self._updateLegendLabel()
                
        if evt.GetId() == 18:
            #Save Select Analysis Info
            #self._saveAnalysisInfo()
            
            dlg = SaveAnalysisInfoDialog(self, self.main_frame.raw_settings, self.manipulation_panel.getSelectedItems())
            dlg.ShowModal()
            dlg.Destroy()
            
        if evt.GetId() == 19:
            #Show Image
            self._onShowImage()
            
        if evt.GetId() == 20:
            dlg = DataDialog(self, self.sasm)
            dlg.ShowModal()
            dlg.Destroy()
            
            wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
            
        if evt.GetId() == 21:
            dlg = HdrDataDialog(self, self.sasm)
            dlg.ShowModal()
            dlg.Destroy()
            
            #wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
        
        if evt.GetId() == 22:
            selected_items = self.manipulation_panel.getSelectedItems()
            marked_item = self.manipulation_panel.getBackgroundItem()
            mainworker_cmd_queue.put(['merge_items', [marked_item, selected_items]])
            
        if evt.GetId() == 23:
            selected_items = self.manipulation_panel.getSelectedItems()
            
            dlg = RebinDialog(self)
            retval = dlg.ShowModal()
            ret, logbin = dlg.getValues()
            dlg.Destroy()
            
            if retval != wx.ID_CANCEL:
                mainworker_cmd_queue.put(['rebin_items', [selected_items, ret, logbin]])
        
        if evt.GetId() == 24: #add to IFT
            
            selected_items = self.manipulation_panel.getSelectedItems()
            
            ift_panel = wx.FindWindowByName('IFTPanel')
            
            for each_item in selected_items:
                ift_panel.addItem(each_item.getSASM().copy())
        
        if evt.GetId() == 25:
            selected_items = self.manipulation_panel.getSelectedItems()
            marked_item = self.manipulation_panel.getBackgroundItem()
            mainworker_cmd_queue.put(['interpolate_items', [marked_item, selected_items]])
            
        if evt.GetId() == 26:
           selected_items = self.manipulation_panel.getSelectedItems()
           mainworker_cmd_queue.put(['plot_iftfit', [selected_items]])
           
        if evt.GetId() == 27:
           self.useAsMWStandard()
           
        if evt.GetId() == 28:
           selected_items = self.manipulation_panel.getSelectedItems()
           mainworker_cmd_queue.put(['normalize_conc', [selected_items]])

        if evt.GetId() == 29:
            #Molecular weight panel fit
            Mainframe = wx.FindWindowByName('MainFrame')
            selectedSASMList = self.manipulation_panel.getSelectedItems()
            
            sasm = selectedSASMList[0].getSASM()
            Mainframe.showMolWeightFrame(sasm, selectedSASMList[0])

        if evt.GetId() == 30:
            #Save All Analysis Info
            self._saveAllAnalysisInfo()
            
    
    def _saveAllAnalysisInfo(self):
        selected_items = self.manipulation_panel.getSelectedItems()

        selected_sasms = [item.sasm for item in selected_items]

        dirctrl_panel = wx.FindWindowByName('DirCtrlPanel')
        path = dirctrl_panel.getDirLabel()

        if len(selected_sasms) >= 1:
            
            filters = 'Comma Separated Files (*.csv)|*.csv'
                
            # dialog = wx.FileDialog( None, style = wx.SAVE | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = save_path) 
            fname = 'RAW_analysis.csv'
            msg = "Please select save directory and enter save file name"
            dialog = wx.FileDialog( None, message = msg, style = wx.SAVE | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = path, defaultFile = fname) 
                
            if dialog.ShowModal() == wx.ID_OK:               
                path = dialog.GetPath()
            else:
                return

            path=os.path.splitext(path)[0]+'.csv'
            save_path = path
        
        else:
            return
            
        mainworker_cmd_queue.put(['save_all_analysis_info', [save_path, selected_sasms]])
    
    def _onKeyPress(self, evt):
        
        key = evt.GetKeyCode()
        
        if ((key == wx.WXK_DELETE) or (key == wx.WXK_BACK and evt.CmdDown())) and self._selected == True:
            self.removeSelf()
            
        if key == wx.WXK_UP:
            if evt.CmdDown():
                print 'CTRL UP'
            else:
                print "UP!"
        if key == wx.WXK_DOWN:
            if evt.CmdDown():
                print 'CTRL DOWN'
            else:
                print "DOWN!"
                
        if key == 83: #S
            self._onShowImage()
            
            
    def _onRightMouseButton(self, evt):
        self.SetFocusIgnoringChildren()
        
        if not self._selected:
            self.toggleSelect()
            self.manipulation_panel.deselectAllExceptOne(self)
                    
        self._showPopupMenu()
        
    def _onLeftMouseButton(self, evt):
        ctrl_is_down = evt.CmdDown()
        shift_is_down = evt.ShiftDown()
        
        manipulation_panel = wx.FindWindowByName('ManipulationPanel')
        
        if shift_is_down:
            try:
                
                first_marked_item_idx = manipulation_panel.all_manipulation_items.index(manipulation_panel.getSelectedItems()[0])
                last_marked_item = manipulation_panel.getSelectedItems()[-1]
                last_marked_item_idx = manipulation_panel.all_manipulation_items.index(last_marked_item)
                
                this_item_idx = manipulation_panel.all_manipulation_items.index(self)
            
                if last_marked_item_idx > this_item_idx:
                    adj = 0
                    idxs = [first_marked_item_idx, this_item_idx]
                else:
                    idxs = [last_marked_item_idx, this_item_idx]
                    adj = 1
                        
                top_item = max(idxs)
                bottom_item = min(idxs)
            
                for each in manipulation_panel.all_manipulation_items[bottom_item+adj:top_item+adj]:
                    each.toggleSelect()
            except IndexError:
                pass
            
        elif ctrl_is_down:
            self.toggleSelect()
        else:
            manipulation_panel.deselectAllExceptOne(self)
            self.toggleSelect()
            
        evt.Skip()
              
    def _onStarButton(self, event):

        if self._selected_as_bg == True:
            self.enableStar(False)
            self.manipulation_panel.clearBackgroundItem()
        else:
            self.manipulation_panel.setItemAsBackground(self)
            
    def _showInvalidValueError(self):
        wx.CallAfter(wx.MessageBox, 'The entered value is invalid. Please remove non-numeric characters.', 'Invalid Value Error', style = wx.ICON_ERROR)
                    
    def _onScaleOffsetChange(self, event):
        id = event.GetId()
        
        try:
            value = float(event.GetValue())
        except ValueError:
            self._showInvalidValueError()
            return
        
        for each_label, each_id, each_name, eachInit_value, each_bindfunc in self.float_spin_controls:
            
            if id == each_id:
                
                if each_name == 'scale':
                    self.sasm.scale(value)
                elif each_name == 'offset':
                    self.sasm.offset(value)
        
        wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
        
        self.markAsModified()
        event.Skip()
        
    def _updateQTextCtrl(self):
        qmin_ctrl = wx.FindWindowById(self.spin_controls[0][1])
        qmax_ctrl = wx.FindWindowById(self.spin_controls[1][1])
        
        qmintxt = wx.FindWindowById(self.spin_controls[0][2])
        qmaxtxt = wx.FindWindowById(self.spin_controls[1][2])
        
        try:
            qmin = int(qmin_ctrl.GetValue())
            qmax = int(qmax_ctrl.GetValue())
        except ValueError:
            self._showInvalidValueError()
            return
        
        qmintxt.SetValue(str(round(self.sasm.q[qmin],4)))
        qmaxtxt.SetValue(str(round(self.sasm.q[qmax],4)))
        
        qrange = (qmin, qmax+1) # +1 to be able to use the range for array slicing [0:n+1]

        self.sasm.setQrange(qrange)   
    
    def _updateLegendLabel(self):
        
        if self._legend_label == '' or self._legend_label == None:
            self.sasm.line.set_label(self.sasm.getParameter('filename'))
            self.legend_label_text.SetLabel('')
        else:
            self.sasm.line.set_label(str(self._legend_label))
            self.legend_label_text.SetLabel('[' + str(self._legend_label) + ']')
            
        wx.CallAfter(self.sasm.plot_panel.updateLegend, self.sasm.axes)
        
    
    def _onQrangeChange(self, event):
        self._updateQTextCtrl()
        wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
        self.markAsModified()
        
    def _onEnterInQrangeTextCtrl(self, evt):
        
        id = evt.GetId()
        txtctrl = wx.FindWindowById(id)
        
        try:
            val = float(txtctrl.GetValue())
        except ValueError:
            self._showInvalidValueError()
            return
        
        if id == self.spin_controls[0][2]:
                spinctrl = wx.FindWindowById(self.spin_controls[0][1])
        elif id == self.spin_controls[1][2]:
                spinctrl = wx.FindWindowById(self.spin_controls[1][1])
        
        q = self.sasm.getBinnedQ()
        
        findClosest = lambda a,l:min(l,key=lambda x:abs(x-a))
                
        closest = findClosest(val, q)
        idx = numpy.where(q == closest)[0][0]  
        
        spinctrl.SetValue(idx)
        self._onQrangeChange(None)
        txtctrl.SelectAll()
     
    def _onSelectedChkBox(self, event):
        self._selected_for_plot = not self._selected_for_plot
        
        self.showItem(self._selected_for_plot)
        
        self.GetParent().Layout()            
        self.GetParent().Refresh()

        wx.CallAfter(self.plot_panel.updateLegend, self.sasm.axes)
        wx.CallAfter(self.sasm.plot_panel.canvas.draw)
        
        self.sasm.plot_panel.fitAxis([self.sasm.axes])
        
    def _createFloatSpinCtrls(self, control_sizer):
        
        for label, id, name, initValue, bindfunc in self.float_spin_controls:
            
            label = wx.StaticText(self, -1, label)
            
            label.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
            label.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
            label.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
            
            if initValue.find('.') == -1:
                initValue = initValue + '.0'
            
            if name == 'scale':
                spinCtrl = RAWCustomCtrl.FloatSpinCtrl(self, id, initValue, TextLength = 100, never_negative = True)
            else:
                spinCtrl = RAWCustomCtrl.FloatSpinCtrl(self, id, initValue, TextLength = 100)
                
            spinCtrl.Bind(RAWCustomCtrl.EVT_MY_SPIN, bindfunc)
            
            control_sizer.Add(label, 1, wx.TOP, 3)
            control_sizer.Add(spinCtrl, 1, wx.EXPAND)
            
        
    def _createSimpleSpinCtrls(self, control_sizer):
        
        
        for each_spinctrl in self.spin_controls:
                spin_id = each_spinctrl[1]
                spin_label_text = each_spinctrl[0]
                qtxtId = each_spinctrl[2]
                spin_range = each_spinctrl[3]
                spin_name = each_spinctrl[4]
                
                spin_min = spin_range[0]
                spin_max = spin_range[1]
    
                spin_min, spin_max = self.sasm.getBinnedQ()[0], self.sasm.getBinnedQ()[-1]
            
                nlow, nhigh = 0, (len(self.sasm.getBinnedQ())-1)
                      
                spin_label = wx.StaticText(self, -1, spin_label_text)
                spin_label.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
                spin_label.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
                spin_label.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
                        
                spin_control = RAWCustomCtrl.IntSpinCtrl(self, spin_id, min = nlow, max = nhigh, TextLength = 43) 
                                        
                if spin_name == 'nlow':
                    spin_control.SetValue(nlow)
                elif spin_name == 'nhigh':
                    spin_control.SetValue(nhigh)
                
                spin_control.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onQrangeChange)
                
                q_ctrl = wx.TextCtrl(self, qtxtId, '', size = (55,22), style = wx.PROCESS_ENTER)
                q_ctrl.Bind(wx.EVT_TEXT_ENTER, self._onEnterInQrangeTextCtrl)
                
                spin_sizer = wx.BoxSizer()
                spin_sizer.Add(q_ctrl, 0, wx.RIGHT, 3)
                spin_sizer.Add(spin_control, 0)
                
                control_sizer.Add(spin_label, 0)        
                control_sizer.Add(spin_sizer, 0)
                
#--- ** IFT Panel **

class IFTPanel(wx.Panel):
    def __init__(self, parent, raw_settings, expParams = []):
        wx.Panel.__init__(self, parent, name = 'IFTPanel')
        
        self.expParams = expParams
        self.raw_settings = raw_settings
        self.iftplot_panel = wx.FindWindowByName('IFTPlotPanel')
        
        self.paramsInGui={'Filename' : (wx.NewId(), 'filename'),
                          'Algorithm' : (wx.NewId(), 'algo'),
                          'ForceZero' : (wx.NewId(), 'forcezero'),
                          'I(0)' : (wx.NewId(), 'info'),
                          'Rg'   : (wx.NewId(), 'info'),
                          'Dmax' : (wx.NewId(), 'intctrl'),
                          'Alpha': (wx.NewId(), 'ctrl'),
                          'Qmin' : (wx.NewId(), 'listctrl'),
                          'Qmax' : (wx.NewId(), 'listctrl')}
        
        self.buttons = (#("BIFT", self._OnDoBift),
                        ("Load", self._onLoadFile),
                        #("Options", self._OnOptions),
                        #("Clear Plot", self._OnClearAll),
                        ("Save", self._onSaveButton),
                        #("Solve", self._OnManual),
                        ("Clear Plots", self._onClearList))
        
        # /* INSERT WIDGETS */ 
        
        self.panelsizer = wx.BoxSizer(wx.VERTICAL)
        
        self._initializeIcons()
        toolbarsizer = self._createToolbar()

        self.underpanel = scrolled.ScrolledPanel(self, -1, style = wx.BORDER_SUNKEN)
        self.underpanel.SetVirtualSize((200, 200))
        self.underpanel.SetScrollRate(20,20)
      
        self.all_manipulation_items = []
        self.selected_item_list = []
        
        self.underpanel_sizer = wx.BoxSizer(wx.VERTICAL)    
        self.underpanel.SetSizer(self.underpanel_sizer)
        
        self.infoBox = IFTControlPanel(self)
        #self.infoBox.Enable(False)
        
        self.panelsizer.Add(self.infoBox, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, 10)
        self.panelsizer.Add(toolbarsizer, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.EXPAND, 5)        
        self.panelsizer.Add(self.underpanel, 1, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 3)
        
        self.createButtons(self.panelsizer)
        #self.panelsizer.Add(self.buttonSizer, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.TOP |wx.BOTTOM | wx.LEFT | wx.RIGHT, 10)
        
        self.SetSizer(self.panelsizer)
        
        self._star_marked_item = None
        self._raw_settings = raw_settings
        
    def _initializeIcons(self):
        self.collapse_all_png = RAWIcons.collapse_all.GetBitmap()
        self.expand_all_png = RAWIcons.expand_all.GetBitmap()
        
        self.show_all_png = RAWIcons.open_eye.GetBitmap()
        self.hide_all_png = RAWIcons.close_eye.GetBitmap()
        
    def _createToolbar(self):
        
        sizer = wx.BoxSizer()
        
        collapse_all = wx.StaticBitmap(self, -1, self.collapse_all_png)
        expand_all = wx.StaticBitmap(self, -1, self.expand_all_png)
        show_all = wx.StaticBitmap(self, -1, self.show_all_png)
        hide_all = wx.StaticBitmap(self, -1, self.hide_all_png)
        show_all.SetToolTipString('Show All')
        hide_all.SetToolTipString('Hide All')
        
        collapse_all.SetToolTipString('Collapse All')
        expand_all.SetToolTipString('Expand All')
        
        collapse_all.Bind(wx.EVT_LEFT_DOWN, self._onCollapseAllButton)
        expand_all.Bind(wx.EVT_LEFT_DOWN, self._onExpandAllButton)
        show_all.Bind(wx.EVT_LEFT_DOWN, self._onShowAllButton)
        hide_all.Bind(wx.EVT_LEFT_DOWN, self._onHideAllButton)
        
        sizer.Add(show_all, 0, wx.LEFT, 5)
        sizer.Add(hide_all, 0, wx.LEFT, 5)
        sizer.Add((1,1),1, wx.EXPAND)
        sizer.Add(collapse_all, 0, wx.RIGHT, 5)
        sizer.Add(expand_all, 0, wx.RIGHT, 3)
        
        return sizer
    
    
    def addItem(self, sasm, item_colour = 'black', ift_parameters = {}):
        
        newItem = IFTItemPanel(self.underpanel, sasm, font_colour = item_colour, ift_parameters = ift_parameters)
        self.Freeze()
        self.underpanel_sizer.Add(newItem, 0, wx.GROW)
        self.underpanel_sizer.Layout()
        
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        self.Layout()            
        self.Refresh()
        self.Thaw()
        
        # Keeping track of all items in our list:
        self.all_manipulation_items.append(newItem)
        
        sasm.item_panel = newItem
        
        self.deselectAllExceptOne(newItem)
        newItem.toggleSelect()
        
        try:
            newItem._updateColourIndicator()
        except AttributeError:
            pass
        
    def setItemAsBackground(self, item):
        
        bg_sasm = self._raw_settings.get('BackgroundSASM')
        
        if bg_sasm != None:
            try:
                bg_sasm.itempanel.enableStar(False)
            except:
                pass
        
        self._raw_settings.set('BackgroundSASM', item.sasm)
        item.enableStar(True)
        self._star_marked_item = item
        
    def getBackgroundItem(self):
        return self._star_marked_item
        
    def clearList(self):
        self.Freeze()
        
        rest_of_items = []
        for each in self.all_manipulation_items:
            
            try:
                each.Destroy()
            except ValueError:
                rest_of_items.append(each)

                
        self.all_manipulation_items = rest_of_items
        self.underpanel_sizer.Layout()
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        
        self._star_marked_item = None
        
        self.Thaw()
        
    def clearBackgroundItem(self):
        self._raw_settings.set('BackgroundSASM', None)
        self._star_marked_item = None
        
    def _collapseAllItems(self):
        for each in self.all_manipulation_items:
            each.showControls(False)
        
        self.underpanel.Layout()            
        self.underpanel.Refresh()
        
        self.Layout()            
        self.Refresh()
            
    def _expandAllItems(self):
        for each in self.all_manipulation_items:
            each.showControls(True)
            
        self.underpanel.Layout()            
        self.underpanel.Refresh()
        
        self.Layout()            
        self.Refresh()
    
    def removeItem(self, item):
        
        self.all_manipulation_items.remove(item)
        
        if item == self._star_marked_item:
            self._star_marked_item = None
        
        item.Destroy()
        
    def getSelectedItems(self):
        
        self.selected_item_list = []
        
        for each in self.all_manipulation_items:
            if each._selected == True:
                self.selected_item_list.append(each)
            
        return self.selected_item_list
    
    def deselectAllExceptOne(self, item, line = None, enableLocatorLine = False):
        
        if line == None:    
            for each in self.all_manipulation_items:
                if each != item:
                    each._selected = True
                    each.toggleSelect()
        else:
            for each in self.all_manipulation_items:
                if each.sasm.getLine() == line:
                    each._selected = False
                    each.toggleSelect()
                else:
                    each._selected = True
                    each.toggleSelect()
                    
    def removeSelectedItems(self):
       
        if len(self.getSelectedItems()) == 0:
            return
        
        self.Freeze()
        
        info_panel = wx.FindWindowByName('InformationPanel')
        info_panel.clearInfo()
        
        axes_that_needs_updated_legend = []
         
        for each in self.getSelectedItems():
            
            if each.sasm.line != None:      
                plot_panel = each.sasm.plot_panel
            
                
                try:
                    each.sasm.line.remove()
                    
                    if each.sasm.origline != None:
                        each.sasm.origline.remove()
                    
                    if each.sasm.fitline != None:
                        each.sasm.fitline.remove()
                    
                    each.sasm.err_line[0][0].remove()
                    each.sasm.err_line[0][1].remove()
                    each.sasm.err_line[1][0].remove()
                
                    i = plot_panel.plotted_sasms.index(each.sasm)
                    plot_panel.plotted_sasms.pop(i)
                except (IndexError, ValueError):
                    pass
            
                if not each.sasm.axes in axes_that_needs_updated_legend:
                    axes_that_needs_updated_legend.append(each.sasm.axes)
                    
                for eachaxes in axes_that_needs_updated_legend:
                    if eachaxes == plot_panel.subplot1:
                        wx.CallAfter(plot_panel.updateLegend, 1)
                    else:
                        wx.CallAfter(plot_panel.updateLegend, 2)
                    

                
                wx.CallAfter(plot_panel.canvas.draw)
                
            if each == self._star_marked_item:
                self._star_marked_item = None
            
            idx = self.all_manipulation_items.index(each)
            self.all_manipulation_items[idx].Destroy()
            self.all_manipulation_items.pop(idx)

        self.underpanel_sizer.Layout()
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        self.underpanel.Refresh()    
        
        self.Thaw()
        
    def _onShowAllButton(self, event):
        
        for each in self.all_manipulation_items:
           each.showItem(True)
           
        plot_panel = wx.FindWindowByName('PlotPanel')
        wx.CallAfter(plot_panel.updateLegend, 1)
        wx.CallAfter(plot_panel.updateLegend, 2)
        wx.CallAfter(plot_panel.fitAxis)
        
        self.underpanel.Layout()            
        self.underpanel.Refresh()
            
        self.Layout()            
        self.Refresh()
           
    def _onHideAllButton(self, event):
        self.underpanel.Freeze()
        
        for each in self.all_manipulation_items:
           each.showItem(False)
        
        self.underpanel.Layout()            
        self.underpanel.Refresh()
            
        self.Layout()            
        self.Refresh()
        
        self.underpanel.Thaw()
        
        plot_panel = wx.FindWindowByName('PlotPanel')
        wx.CallAfter(plot_panel.updateLegend, 1)
        wx.CallAfter(plot_panel.updateLegend, 2)
        wx.CallAfter(plot_panel.canvas.draw)
               
    def _onCollapseAllButton(self, event):
        self._collapseAllItems()
        
    def _onExpandAllButton(self, event):
        self._expandAllItems()
            
    def _onBiftButton(self, event):
        pass
         
    def _onRemoveButton(self, event):
        self.removeSelectedItems()
    
    def _onSaveButton(self, event):
        self.saveItems()
    
    def _onSyncButton(self, event):
        syncdialog = SyncDialog(self)
        syncdialog.ShowModal()
        syncdialog.Destroy()
             
    def _onSuperimposeButton(self, event):
        mainworker_cmd_queue.put(['superimpose_items', ( self._star_marked_item, self.getSelectedItems()  )])
        
    def synchronizeSelectedItems(self, sync_parameters):
        star_item = self.getBackgroundItem()
        
        if not star_item or (len(sync_parameters) == 0):
            return
        
        star_sasm = star_item.getSASM()
        
        scale = star_sasm.getScale()
        offset = star_sasm.getOffset()
        nmin, nmax = star_sasm.getQrange()
        qmin, qmax = star_sasm.getBinnedQ()[nmin], star_sasm.getBinnedQ()[nmax-1]
        linestyle = star_sasm.line.get_linestyle()
        linewidth = star_sasm.line.get_linewidth()
        linemarker = star_sasm.line.get_marker() 
        
        selected_items = self.getSelectedItems()
        
        findClosest = lambda a,l:min(l,key=lambda x:abs(x-a))
        
        for each_item in selected_items:
            if each_item == star_item:
                continue
            
            sasm = each_item.getSASM()
            
            old_nmin, old_nmax = sasm.getQrange()
            
            try:
                if 'nmin' in sync_parameters and 'nmax' in sync_parameters:
                    sasm.setQrange([nmin, nmax])
                elif 'nmin' in sync_parameters:
                    sasm.setQrange([nmin, old_nmax])
                elif 'nmax' in sync_parameters:
                    sasm.setQrange([old_nmin, nmax])                    
                    
            except SASExceptions.InvalidQrange, msg:
                dial = wx.MessageDialog(None, 'Filename : ' + sasm.getParameter('filename') + '\n\n' + str(msg),
                                'Invalid Qrange',
                                wx.OK | wx.CANCEL | wx.NO_DEFAULT | wx.ICON_QUESTION)
                answer = dial.ShowModal()
                    
                if answer == wx.ID_CANCEL:
                    return
                
            q = sasm.getBinnedQ()
            
            if 'qmin' in sync_parameters and 'qmax' in sync_parameters:
                closest = findClosest(qmin, q)
                new_nmin = numpy.where(q == closest)[0][0]
                closest = findClosest(qmax, q)
                new_nmax = numpy.where(q == closest)[0][0]
                sasm.setQrange([new_nmin, new_nmax])
            elif 'qmin' in sync_parameters:
                closest = findClosest(qmin, q)
                new_nmin = numpy.where(q == closest)[0][0]
                sasm.setQrange([new_nmin, old_nmax])    
            elif 'qmax' in sync_parameters:
                closest = findClosest(qmax, q)
                new_nmax = numpy.where(q == closest)[0][0]
                sasm.setQrange([old_nmin, new_nmax])
                
            if 'scale' in sync_parameters:
                sasm.scale(scale)
            if 'offset' in sync_parameters:
                sasm.offset(offset)
            if 'linestyle' in sync_parameters:
                sasm.line.set_linestyle(linestyle)
            if 'linewidth' in sync_parameters:
                sasm.line.set_linewidth(linewidth)
            if 'linemarker' in sync_parameters:
                sasm.line.set_marker(linemarker)
            
            each_item.updateControlsFromSASM()
        
    def movePlots(self, ExpObjList, toAxes):
        
        for each_item in ExpObjList:
            
            each = each_item.getSASM()
            
            if each.axes != toAxes:
                plotpanel = each.plot_panel
      
                each.line.remove()
                each.err_line[0][0].remove()
                each.err_line[0][1].remove()
                each.err_line[1][0].remove()
        
                line_color = each.line.get_color()
                
                if each_item.getLegendLabel() != '':
                    label = each_item.getLegendLabel()
                else:
                    label = None
                
                wx.CallAfter(plotpanel.plotSASM, each, toAxes, color = line_color, legend_label_in = label)
                
                
        plotpanel = wx.FindWindowByName('PlotPanel')
        wx.CallAfter(plotpanel.updateLegend, 1)
        wx.CallAfter(plotpanel.updateLegend, 2)
        wx.CallAfter(plotpanel.canvas.draw)
    
    def getItems(self):
        return self.all_manipulation_items
            
    def updateLayout(self):
        self.underpanel_sizer.Layout()
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
    
    def saveItems(self):
        selected_items = self.getSelectedItems()
        
        selected_items = self.getSelectedItems()

        dirctrl_panel = wx.FindWindowByName('DirCtrlPanel')
        path = dirctrl_panel.getDirLabel()

        if len(selected_items) == 1:
            
            # filters = 'Comma Separated Files (*.csv)|*.csv'
                
            # dialog = wx.FileDialog( None, style = wx.SAVE | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = save_path) 
            fname = os.path.splitext(os.path.basename(selected_items[0].sasm.getParameter('filename')))[0]+'.ift'
            msg = "Please select save directory and enter save file name"
            dialog = wx.FileDialog(self, message = msg, style = wx.FD_SAVE, defaultDir = path, defaultFile = fname) 
                
            if dialog.ShowModal() == wx.ID_OK:               
                path = dialog.GetPath()
            else:
                return

            path=os.path.splitext(path)[0]+'.ift'
            filename = os.path.basename(path)
            selected_items[0].sasm.setParameter('filename', filename)
            wx.CallAfter(selected_items[0].updateFilenameLabel)

            save_path = os.path.dirname(path)
        
        elif len(selected_items) == 0:
            return

        else:
            dirdlg = wx.DirDialog(self, "Please select save directory (multiple files will be saved):", defaultPath = path,)
            
            if dirdlg.ShowModal() == wx.ID_OK:
                path = dirdlg.GetPath()
            else:
                return
            save_path = path
        
        mainworker_cmd_queue.put(['save_iftitems', [save_path, selected_items]])
            
        
    
##################################################################################### 

 
    def _onClearList(self, evt):
        self.Freeze()
        
        rest_of_items = []
        for each in self.all_manipulation_items:
            
            try:
                each.Destroy()
            except ValueError:
                rest_of_items.append(each)
                
        self.all_manipulation_items = rest_of_items
        self.underpanel_sizer.Layout()
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        
        self._star_marked_item = None
        
        self.Thaw()
        
        self.iftplot_panel.clearAllPlots()
        
    def _OnManual(self, evt):
        ''' Solve button '''
        
        selectedFile = self.filelist.GetSelections()
        
        if selectedFile == None or selectedFile == ():
            return
        
        selectedFile = selectedFile[0]
        
        NO_FILE_SELECTED = -1

        if selectedFile == NO_FILE_SELECTED:
            return
        else:
            SelectedExpObj = self.filelist.GetClientData(selectedFile)[0]
        
        dmax, alpha = self.infoBox.getDmaxAlpha()
        
        dmax = float(dmax)
        alpha = float(alpha)
        
        #print SelectedExpObj.type
        SelectedExpObj.setQrange(SelectedExpObj.idx)
        
        N = self.expParams['PrPoints']
        
        
        ExpObj = BIFT.SingleSolve(alpha, dmax, SelectedExpObj, N)
        
        ExpObj.isBifted = True
        
        biftPlotPanel = wx.FindWindowByName('BIFTPlotPanel')
        biftPlotPanel.PlotBIFTExperimentObject(ExpObj)
        
        self.infoBox.updateInfo([SelectedExpObj, ExpObj])
  
    def _OnClearAll(self, evt):
        plotpage = wx.FindWindowByName('BIFTPlotPanel')
        plotpage.OnClear(0)
        
    def _OnOptions(self, evt):
        
        optionsPage = wx.FindWindowByName('OptionsPage')
        optionsPage.ShowOptionsDialog(3)    # Index 1 = BIFT page
    
    def _OnDoBift(self, evt):
                
        expList = []
        for each in self.filelist.GetSelections():
            expList.append(self.filelist.GetClientData(each)[0])
        
        if expList == []:
            return
        
        for each in expList:
            each.setQrange(each.idx)
        
        calculationThread = BiftCalculationThread(self, expList) 
        calculationThread.start()
    
    def addBiftObjToList(self, ExpObj, BiftObj):
         
         for idx in range(0, self.filelist.GetCount()):
             E = self.filelist.GetClientData(idx)
             
             if ExpObj == E[0]:
                 self.filelist.SetClientData(idx, [ExpObj, BiftObj])
                 self.infoBox.updateInfo([ExpObj, BiftObj])
                 return
                  
         self.filelist.Insert(BiftObj.param['filename'], 0, [ExpObj, BiftObj])
         self.filelist.DeselectAll()
         self.filelist.SetSelection(0)
         self.infoBox.updateInfo([ExpObj, BiftObj])
         self.filelist.SetItemBackgroundColour(0, (100,100,100))
         
    def runBiftOnExperimentObject(self, ExpObj, expParams):
        
        self.expParams = expParams
        biftThread = BiftCalculationThread(self, ExpObj)
        biftThread.start()

    def _setBIFTParamsFromGui(self):
        
        for eachParam in biftparams.keys():
            
            id = self.biftParamsId.get(eachParam)[0]
            textctrl = wx.FindWindowById(id)
            value = textctrl.GetValue()
        
            biftparams[eachParam] = int(value)
    
    def _onLoadFile(self, evt):   
         
        selected_file = self._CreateFileDialog(wx.OPEN)
        
        if selected_file:
       
            sasm, img = SASFileIO.loadFile(selected_file, self.raw_settings)
            
            try:        
                self.addItem(sasm)
            except Exception:
                print 'WARNING!! Error in _OnLoadFile!!'
            
 
    def _CreateFileDialog(self, mode):
        
        file = None
        
        dirctrl_panel = wx.FindWindowByName('DirCtrlPanel')
        load_path = dirctrl_panel.getDirLabel()
        
        if mode == wx.OPEN:
            filters = 'All files (*.*)|*.*|Rad files (*.rad)|*.rad|Dat files (*.dat)|*.dat|Txt files (*.txt)|*.txt'
            dialog = wx.FileDialog( None, 'Select a file', load_path, style = mode, wildcard = filters)
        if mode == wx.SAVE:
            filters = 'Dat files (*.dat)|*.dat'
            dialog = wx.FileDialog( None, 'Name file and location', load_path, style = mode | wx.OVERWRITE_PROMPT, wildcard = filters)        
        
        # Show the dialog and get user input
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetPath()
            
        # Destroy the dialog
        dialog.Destroy()
        
        return file
    
    def createButtons(self, panelsizer):
        
        sizer = wx.GridSizer(cols = 3, rows = ceil(len(self.buttons)/3))
        
        #sizer.Add((10,10) ,1 , wx.EXPAND)
        for each in self.buttons:
            if each:
                
                label = each[0]
                bindfunc = each[1]
                
                button = wx.Button(self, -1, label)
                button.Bind(wx.EVT_BUTTON, bindfunc)
                
                sizer.Add(button, 1, wx.EXPAND | wx.ALIGN_CENTER)         
          
        panelsizer.Add(sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP | wx.ALIGN_CENTRE | wx.EXPAND, 10)
        
    def createBiftOptions(self, panelsizer):
        
        for each in self.biftoptions:
            if each:
                labeltxt = each[0]
                id = each[1]
                param_value = biftparams.get(each[2])
                
                sizer = wx.BoxSizer()

                label = wx.StaticText(self, -1, labeltxt)
                ctrl = wx.TextCtrl(self, id, str(param_value), style = wx.TE_PROCESS_ENTER, size = (45,22))

                sizer.Add(label, 1, wx.EXPAND)
                sizer.Add(ctrl,0)
                
                panelsizer.Add(sizer, 0.1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
    def createMaxMinOptions(self, panelsizer):
        
        topsizer = wx.BoxSizer()
        
        topsizer.Add((9,10),1, wx.EXPAND)
        topsizer.Add(wx.StaticText(self,-1,'Min',size = (45,15)),0)
        topsizer.Add(wx.StaticText(self,-1,'  Max',size = (45,15)),0)
        topsizer.Add(wx.StaticText(self,-1,'   Points',size = (45,15)),0)
                     
        panelsizer.Add(topsizer, 0.1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        first = True
        for each in self.biftmaxminoptions:
            
            sizer = wx.BoxSizer()
            
            labeltxt = each[0]
            
            min_id = each[1][1]
            max_id = each[1][0]
            points_id = each[1][2]
            
            max_param_value = biftparams.get(each[2][0])
            min_param_value = biftparams.get(each[2][1])
            points_param_value = biftparams.get(each[2][2])
                        
            label = wx.StaticText(self, -1, labeltxt)
            minCtrl = wx.TextCtrl(self, min_id, str(min_param_value), style = wx.TE_PROCESS_ENTER, size = (45,22))
            maxCtrl = wx.TextCtrl(self, max_id, str(max_param_value), style = wx.TE_PROCESS_ENTER, size = (45,22))        
            pointsCtrl = wx.TextCtrl(self, points_id, str(points_param_value), style = wx.TE_PROCESS_ENTER, size = (45,22))        
        
           # self.sampleScale.Bind(wx.EVT_KILL_FOCUS, self.OnSampleScaleChange)
           # self.sampleScale.Bind(wx.EVT_TEXT_ENTER, self.OnSampleScaleChange)
        
            sizer.Add(label, 1, wx.EXPAND)
            sizer.Add(minCtrl,0, wx.RIGHT, 10)
            sizer.Add(maxCtrl,0, wx.RIGHT, 10)
            sizer.Add(pointsCtrl,0)

            if not(first):
                panelsizer.Add(sizer, 0.1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
            else:
                panelsizer.Add(sizer, 0.1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
                first = False

class IFTItemPanel(wx.Panel):
    def __init__(self, parent, sasm, font_colour = 'BLACK', legend_label = '', ift_parameters = {}):
        
        wx.Panel.__init__(self, parent, style = wx.BORDER_RAISED)
        
        self.parent = parent
        self.sasm = sasm
        self.sasm.itempanel = self
        self.ift_parameters = ift_parameters
        
        self.manipulation_panel = wx.FindWindowByName('IFTPanel')
        self.plot_panel = wx.FindWindowByName('PlotPanel')
        self.main_frame = wx.FindWindowByName('MainFrame')
        self.ift_panel = wx.FindWindowByName('IFTPanel')
        self.iftctrl_panel = wx.FindWindowByName('IFTControlPanel')
        self.info_panel = wx.FindWindowByName('InformationPanel')
        self.ift_plot_panel = wx.FindWindowByName('IFTPlotPanel')
        
        self.info_settings = {'hdr_choice' : 0}
        
        self._selected_as_bg = False
        self._selected_for_plot = True
        self._controls_visible = True
        self._selected = False
        self._legend_label = legend_label
        self._lock_on = False
        
        self._font_colour = font_colour
        
        filename = sasm.getParameter('filename')
               
        self.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
        self.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
        self.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
        #Label, TextCtrl_ID, SPIN_ID
        
        self._initializeIcons()
                                       
        self.qmax = len(self.sasm.q)
                             
        self.spin_controls = (("r Min:", wx.NewId(), wx.NewId(), (1, self.qmax-1), 'nlow'),        
                             ("r Max:", wx.NewId(), wx.NewId(), (2, self.qmax), 'nhigh'))
        
        self.float_spin_controls = (
                                   # ("Conc:", wx.NewId(), 'conc', '1.0', self._onScaleOffsetChange),
                                    ("Scale:", wx.NewId(), 'scale', str(sasm.getScale()), self._onScaleOffsetChange),
                                    ("Offset:", wx.NewId(), 'offset', str(sasm.getOffset()), self._onScaleOffsetChange))
    
        self.SelectedForPlot = RAWCustomCtrl.CustomCheckBox(self, -1, filename)
        self.SelectedForPlot.SetValue(True)
        self.SelectedForPlot.Bind(wx.EVT_CHECKBOX, self._onSelectedChkBox)
        self.SelectedForPlot.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
        self.SelectedForPlot.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
        self.SelectedForPlot.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
        
        self.SelectedForPlot.SetToolTipString('Show Plot')
        self.SelectedForPlot.SetForegroundColour(font_colour)
        
        self.legend_label_text = wx.StaticText(self, -1, '')
        
        self.legend_label_text.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
        self.legend_label_text.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
        self.legend_label_text.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
        
        conv = mplcol.ColorConverter()
        #color = conv.to_rgb(self.sasm.line.get_mfc())
        color = [1,1,1]
        color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        self.colour_indicator = RAWCustomCtrl.ColourIndicator(self, -1, color, size = (20,15))
        self.colour_indicator.Bind(wx.EVT_LEFT_DOWN, self._onLinePropertyButton)
        self.colour_indicator.SetToolTipString('Line Properties')

        self.bg_star = wx.StaticBitmap(self, -1, self.gray_png)
        self.bg_star.Bind(wx.EVT_LEFT_DOWN, self._onStarButton)
        self.bg_star.SetToolTipString('Mark')
        
        self.expand_collapse = wx.StaticBitmap(self, -1, self.collapse_png)
        self.expand_collapse.Bind(wx.EVT_LEFT_DOWN, self._onExpandCollapseButton)
        self.expand_collapse.SetToolTipString('Collapse/Expand')
        
        self.target_icon = wx.StaticBitmap(self, -1, self.target_png)
        self.target_icon.Bind(wx.EVT_LEFT_DOWN, self._onTargetButton)
        self.target_icon.SetToolTipString('Locate Line')

        #self.info_icon = wx.StaticBitmap(self, -1, self.info_png)
        #self.info_icon.Bind(wx.EVT_LEFT_DOWN, self._onInfoButton)
        #self.info_icon.SetToolTipString('Show Extended Info\n--------------------------------\nRg: N/A\nI(0): N/A')
        
        
        if self.ift_parameters == {}:
            self.lock_icon = wx.StaticBitmap(self, -1, self.lock_open_grayed_png)
        else:    
            self.lock_icon = wx.StaticBitmap(self, -1, self.lock_open_png)
    
        self.lock_icon.Bind(wx.EVT_LEFT_DOWN, self._onLockButton)
        self.lock_icon.SetToolTipString('Lock Fit Plot')
        
        
        
        self.locator_on = False
        self.locator_old_width = 1
        
        panelsizer = wx.BoxSizer()
        panelsizer.Add(self.SelectedForPlot, 0, wx.LEFT | wx.TOP, 3)
        panelsizer.Add(self.legend_label_text, 0, wx.LEFT | wx.TOP, 3)
        panelsizer.Add((1,1), 1, wx.EXPAND)
        panelsizer.Add(self.expand_collapse, 0, wx.RIGHT | wx.TOP, 5)
        panelsizer.Add(self.lock_icon, 0, wx.RIGHT | wx.TOP, 5)
        panelsizer.Add(self.target_icon, 0, wx.RIGHT | wx.TOP, 4)
        panelsizer.Add(self.colour_indicator, 0, wx.RIGHT | wx.TOP, 5)
        panelsizer.Add(self.bg_star, 0, wx.LEFT | wx.RIGHT | wx.TOP, 3)
        
        self.topsizer = wx.BoxSizer(wx.VERTICAL)
        self.topsizer.Add(panelsizer, 1, wx.EXPAND)
        
        self.controlSizer = wx.BoxSizer(wx.VERTICAL)
        self.controlSizer = wx.FlexGridSizer(cols = 4, rows = 2, vgap = 3, hgap = 7)
       
        self._createSimpleSpinCtrls(self.controlSizer)
        self._createFloatSpinCtrls(self.controlSizer) 
        
        self.topsizer.Add((5,5),0)
        self.topsizer.Add(self.controlSizer, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM, 5)
        
        self.SetSizer(self.topsizer)
        
        self.SetBackgroundColour(wx.Colour(250,250,250))
        
        self._initStartPosition()
        self._updateQTextCtrl()
        
        # if self.sasm.getParameter('analysis').has_key('guinier'):
        #     self.updateInfoTip(self.sasm.getParameter('analysis'))
            
        #controls_not_shown = self.main_frame.raw_settings.get('ManipItemCollapsed')
        controls_not_shown = True
        if controls_not_shown:
            self.showControls(not controls_not_shown)
               
    
    def updateInfoTip(self, analysis_dict, fromGuinierDialog = False):
        
        
        if analysis_dict.has_key('guinier'):
            guinier = analysis_dict['guinier']
        else:
            guinier = {}
        
        string0 = 'Show Extended Info\n--------------------------------'
        string1 = ''
        string2 = ''
        string3 = ''
        
        if guinier.has_key('Rg') and guinier.has_key('I0'):
            rg = guinier['Rg']
            i_zero = guinier['I0']
        
            string1 = '\nRg: ' + str(rg) + '\nI(0): ' + str(i_zero)
        else:
            string1 = '\nRg: N/A' + '\nI(0): N/A'
            
        if self.sasm.getAllParameters().has_key('Conc'):
            string2 = '\nConc: ' + str(self.sasm.getParameter('Conc'))   
        
        if self.sasm.getAllParameters().has_key('Notes'):
            if self.sasm.getParameter('Notes') != '':
                string3 = '\nNote: ' + str(self.sasm.getParameter('Notes'))  
        
        string = string0+string1+string2+string3
        
        if string != '':    
            self.info_icon.SetToolTipString(string)
                  
        if fromGuinierDialog:
            self.info_panel.updateInfoFromItem(self)
            
            
    def setCurrentIFTParameters(self, ift_parameters):
        self.ift_parameters = ift_parameters
        
    def getIftParameters(self):
        return self.ift_parameters
    
    def enableStar(self, state):
        if state == True:
            self.bg_star.SetBitmap(self.star_png)
            self._selected_as_bg = True
        else:
            self.bg_star.SetBitmap(self.gray_png)
            self._selected_as_bg = False
        
        self.bg_star.Refresh()
        
    def removeSelf(self):
        #Has to be callafter under Linux.. or it'll crash
        wx.CallAfter(self.manipulation_panel.removeSelectedItems)
        
    def getSASM(self):
        return self.sasm        
    
    def getFontColour(self):
        return self._font_colour
    
    def getSelectedForPlot(self):
        return self._selected_for_plot
    
    def getLegendLabel(self):
        return self._legend_label
    
    def updateControlsFromSASM(self):    
        scale = self.sasm.getScale()
        offset = self.sasm.getOffset()
        qmin, qmax = self.sasm.getQrange()
        
        qmin_ctrl = wx.FindWindowById(self.spin_controls[0][1])
        qmax_ctrl = wx.FindWindowById(self.spin_controls[1][1])
        qmintxt = wx.FindWindowById(self.spin_controls[0][2])
        qmaxtxt = wx.FindWindowById(self.spin_controls[1][2])
        
        qmin_ctrl.SetValue(str(qmin))
        qmax_ctrl.SetValue(str(qmax-1))        
        qmintxt.SetValue(str(round(self.sasm.q[qmin],4)))
        qmaxtxt.SetValue(str(round(self.sasm.q[qmax-1],4)))
        
        scale_ctrl = wx.FindWindowById(self.float_spin_controls[0][1])
        offset_ctrl = wx.FindWindowById(self.float_spin_controls[1][1])
    
        offset_ctrl.SetValue(str(offset))
        scale_ctrl.SetValue(str(scale))
        
        wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
    
    def toggleSelect(self):
        
        if self._selected:
            self._selected = False
            self.SetBackgroundColour(wx.Colour(250,250,250))
            self.info_panel.clearInfo()
            self.iftctrl_panel.updateInfo()
        else:
            self._selected = True
            self.SetBackgroundColour(wx.Colour(200,200,200))
            self.SetFocusIgnoringChildren()
            self.info_panel.updateInfoFromItem(self)
            self.iftctrl_panel.updateInfo()
        
        self.Refresh()
        
    def enableLocatorLine(self):
        
        self.locator_on = not self.locator_on
        
        if self.locator_on == True:
            self.target_icon.SetBitmap(self.target_on_png)
            self.locator_old_width = self.sasm.line.get_linewidth()
            new_width = self.locator_old_width + 2.0
            self.sasm.line.set_linewidth(new_width)
            wx.CallAfter(self.sasm.plot_panel.canvas.draw)
        else:
            self.target_icon.SetBitmap(self.target_png)
            self.sasm.line.set_linewidth(self.locator_old_width)
            wx.CallAfter(self.sasm.plot_panel.canvas.draw)
            
        self.target_icon.Refresh()
        
    def getControlsVisible(self):
        return self._controls_visible
        
    def showControls(self, state):
        
        if state == False:
            self.expand_collapse.SetBitmap(self.expand_png)
            self._controls_visible = False
            self.controlSizer.Hide(0, True)
            self.controlSizer.Hide(1, True)
            self.controlSizer.Hide(2, True)
            self.controlSizer.Hide(3, True)
            self.controlSizer.Hide(4, True)
            self.controlSizer.Hide(5, True)
            self.controlSizer.Hide(6, True)
            self.controlSizer.Hide(7, True)
        else:
            self.expand_collapse.SetBitmap(self.collapse_png)
            self._controls_visible = True
            self.controlSizer.Show(0, True)
            self.controlSizer.Show(1, True)
            self.controlSizer.Show(2, True)
            self.controlSizer.Show(3, True)
            self.controlSizer.Show(4, True)
            self.controlSizer.Show(5, True)
            self.controlSizer.Show(6, True)
            self.controlSizer.Show(7, True)
            
        self.expand_collapse.Refresh()
        self.topsizer.Layout()
        
    
    def showItem(self, state):
        self._selected_for_plot = state
        
        if self._selected_for_plot == False:
            self._controls_visible = False
            self.showControls(self._controls_visible)
        
        self.SelectedForPlot.SetValue(self._selected_for_plot)
        self.sasm.line.set_visible(self._selected_for_plot)
        self.sasm.line.set_picker(self._selected_for_plot)      #Line can't be selected when it's hidden
        
    def updateFilenameLabel(self):
        filename = self.sasm.getParameter('filename')
        
        if self._legend_label == '':
            self.sasm.line.set_label(filename)
        self.ift_plot_panel.updateLegend(1)
        self.SelectedForPlot.SetLabel(str(filename))
        self.SelectedForPlot.Refresh()
        self.topsizer.Layout()
        self.GetParent().Layout()            
        self.GetParent().Refresh()
    
    def _initializeIcons(self):
        
        self.gray_png = RAWIcons.Star_icon_notenabled.GetBitmap()
        self.star_png = RAWIcons.Star_icon_org.GetBitmap()
        
        self.collapse_png = RAWIcons.collapse.GetBitmap()
        self.expand_png = RAWIcons.expand.GetBitmap()
        
        self.target_png = RAWIcons.target.GetBitmap()
        self.target_on_png = RAWIcons.target_orange.GetBitmap()

        #self.info_png = RAWIcons.info_16_2.GetBitmap()
        self.lock_open_png = RAWIcons.stock_lock_open.GetBitmap()
        self.lock_closed_png = RAWIcons.stock_lock_closed.GetBitmap()
        self.lock_open_grayed_png = RAWIcons.stock_lock_open_grayed.GetBitmap()
        
    def _initStartPosition(self):
        
        qmin_ctrl = wx.FindWindowById(self.spin_controls[0][1])
        qmax_ctrl = wx.FindWindowById(self.spin_controls[1][1])
        
        qrange = self.sasm.getQrange()
        
        qmin_ctrl.SetValue(str(qrange[0]))
        
    def _updateColourIndicator(self):
        conv = mplcol.ColorConverter()
        color = conv.to_rgb(self.sasm.line.get_mfc())
        color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        self.colour_indicator.updateColour(color)
        
    def _onLinePropertyButton(self, event):
        # print 'here?'
        legend_label = self.getLegendLabel()
        dialog = LinePropertyDialog(self, self.sasm.line, legend_label)
        dialog.ShowModal()
        dialog.Destroy()
        self._updateColourIndicator()
        
        if self.sasm.axes == self.ift_plot_panel.subplot1:
            wx.CallAfter(self.ift_plot_panel.updateLegend, 1)
        else:
            wx.CallAfter(self.ift_plot_panel.updateLegend, 2)
            
        self.sasm.plot_panel.canvas.draw()
        
    def _onExpandCollapseButton(self, event):
        self._controls_visible = not self._controls_visible
        self.showControls(self._controls_visible)
        
        self.GetParent().Layout()            
        self.GetParent().Refresh()
        
        self.GetParent().GetParent().Layout()            
        self.GetParent().GetParent().Refresh()
            
    def _onTargetButton(self, event):
        self.enableLocatorLine()
        
    def _onInfoButton(self, event):
        pass
    
    def _onLockButton(self, event):
        if self.ift_parameters == {}:
            return
        
        self._lock_on = not self._lock_on
        
        if self._lock_on:
            self.lock_icon.SetBitmap(self.lock_closed_png)
        else:
            self.lock_icon.SetBitmap(self.lock_open_png)
            
    def _showPopupMenu(self):

        menu = wx.Menu()
        
        number_of_selected_items = len(self.manipulation_panel.getSelectedItems())
        
#        iftmenu = wx.Menu()
#        iftmenu.Append(10, 'Run BIFT')
#        iftmenu.Append(11, 'Run GNOM using current Dmax')
#        iftmenu.AppendSeparator()
#        iftmenu.Append(12, 'Add to IFT list')
        
        convertq_menu = wx.Menu()
        convertq_menu.Append(15, '>> 10')
        convertq_menu.Append(16, '<< 10^-1')
        
        submenu = menu.Append(4, 'Subtract')
        avgmenu = menu.Append(6, 'Average' )
        menu.Append(14, 'Rename')
            
        menu.AppendSeparator()
        menu.Append(5, 'Remove' )
        menu.AppendSeparator()
        #menu.Append(13, 'Guinier fit...')
        
        menu.AppendMenu(wx.NewId(), 'Convert q-scale', convertq_menu)
        
        menu.AppendSeparator()
        img = menu.Append(19, 'Show image')
        
        if not self.sasm.getAllParameters().has_key('load_path'):
            img.Enable(False)
        menu.Append(20, 'Show data')
        menu.Append(21, 'Show header')
        
        menu.AppendSeparator()
        menu.Append(8, 'Move to top plot')
        menu.Append(9, 'Move to bottom plot')
        menu.AppendSeparator()
        menu.Append(17, 'Set legend label')
        menu.Append(18, 'Save item info')
        menu.AppendSeparator()
        menu.Append(7, 'Save selected file(s)')
        
        self.Bind(wx.EVT_MENU, self._onPopupMenuChoice)        
        self.PopupMenu(menu)
    
    def _onShowImage(self):
        
        if self.sasm.getAllParameters().has_key('load_path'):
            path = self.sasm.getParameter('load_path')
            mainworker_cmd_queue.put(['show_image', path])
    
    def _onPopupMenuChoice(self, evt):
        
        if evt.GetId() == 4:
            #Subtract
            selected_items = self.manipulation_panel.getSelectedItems()
            marked_item = self.manipulation_panel.getBackgroundItem()
            mainworker_cmd_queue.put(['subtract_items', [marked_item, selected_items]])
        
        if evt.GetId() == 5:
            #Delete
            wx.CallAfter(self.manipulation_panel.removeSelectedItems)
        
        if evt.GetId() == 6:
            #Average 
            selected_items = self.manipulation_panel.getSelectedItems()
            mainworker_cmd_queue.put(['average_items', selected_items])
            
        if evt.GetId() == 7:
            self.manipulation_panel.saveItems()
                
        if evt.GetId() == 8:
            #Move to top plot
            plotpanel = wx.FindWindowByName('PlotPanel')
            selected_items = self.manipulation_panel.getSelectedItems()
            self.manipulation_panel.movePlots(selected_items, plotpanel.subplot1)
            wx.CallAfter(plotpanel.fitAxis)
                
        if evt.GetId() == 9:
            #Move to bottom plot
            plotpanel = wx.FindWindowByName('PlotPanel')
            selected_items = self.manipulation_panel.getSelectedItems()
            self.manipulation_panel.movePlots(selected_items, plotpanel.subplot2)
            wx.CallAfter(plotpanel.fitAxis)
            
        if evt.GetId() == 13:
            #Guinier fit
            Mainframe = wx.FindWindowByName('MainFrame')
            selectedSASMList = self.manipulation_panel.getSelectedItems()
            
            sasm = selectedSASMList[0].getSASM()
            Mainframe.showGuinierFitFrame(sasm, selectedSASMList[0])
            
        if evt.GetId() == 10:
            #BIFT
            analysisPage = wx.FindWindowByName('AutoAnalysisPage')
            analysisPage.runBiftOnExperimentObject(self.ExpObj.copy(), expParams)
            
        if evt.GetId() == 12:
            #Add to IFT List
            autoanalysis = wx.FindWindowByName('AutoAnalysisPage')
            
            for ExpObj in ManipulationPage.GetSelectedExpObjs():
                ExpObjIFT = ExpObj.copy()
                autoanalysis.addExpObjToList(ExpObjIFT)
            
            wx.CallAfter(wx.MessageBox, 'File(s) have been added to the IFT list', 'Files Added')
            
        if evt.GetId() == 11:
            #GNOM
            analysisPage.runBiftOnExperimentObject(self.ExpObj.copy(), expParams)
            
        if evt.GetId() == 14:
            dlg = FilenameChangeDialog(self, self.sasm.getParameter('filename'))
            dlg.ShowModal()
            filename =  dlg.getFilename()
            dlg.Destroy()
            
            if filename:
                self.sasm.setParameter('filename', filename)
                self.updateFilenameLabel()
        
        if evt.GetId() == 15:
            #A to s
            self.sasm.scaleBinnedQ(10.0)
            self._updateQTextCtrl()
            wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
            
        if evt.GetId() == 16:
            #s to A
            self.sasm.scaleBinnedQ(0.1)
            self._updateQTextCtrl()
            wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
        
        if evt.GetId() == 17:
            dlg = LegendLabelChangeDialog(self, self._legend_label)
            answer = dlg.ShowModal()
            legend_label = dlg.getLegendLabel()
            dlg.Destroy()
            
            if answer == wx.ID_OK:
                self._legend_label = legend_label
                self._updateLegendLabel()
                
        if evt.GetId() == 18:
            #Save Analysis Info
            #self._saveAnalysisInfo()
            
            dlg = SaveAnalysisInfoDialog(self, self.main_frame.raw_settings, self.manipulation_panel.getSelectedItems())
            dlg.ShowModal()
            dlg.Destroy()
            
        if evt.GetId() == 19:
            #Show Image
            self._onShowImage()
            
        if evt.GetId() == 20:
            dlg = DataDialog(self, self.sasm)
            dlg.ShowModal()
            dlg.Destroy()
            
            wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
            
        if evt.GetId() == 21:
            dlg = HdrDataDialog(self, self.sasm)
            dlg.ShowModal()
            dlg.Destroy()
            
            #wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
    
    def _saveAnalysisInfo(self):
        selected_items = self.manipulation_panel.getSelectedItems()
            
        if len(selected_items) == 0:
            return
        
        dirctrl_panel = wx.FindWindowByName('DirCtrlPanel')
        save_path = dirctrl_panel.getDirLabel()
        
        filters = 'Comma Separated Files (*.csv)|*.csv'
            
        dialog = wx.FileDialog( None, style = wx.SAVE | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = save_path) 
        #dirdlg = wx.DirDialog(self, "Please select save directory:", str(save_path))
            
        if dialog.ShowModal() == wx.ID_OK:               
            save_path = dialog.GetPath()
        else:
             return
            
        mainworker_cmd_queue.put(['save_analysis_info', [selected_items, save_path]])
    
    def _onKeyPress(self, evt):
        
        key = evt.GetKeyCode()

        if ((key == wx.WXK_DELETE) or (key == wx.WXK_BACK and evt.CmdDown())) and self._selected == True:
            self.removeSelf()
            
        if key == wx.WXK_UP:
            if evt.CmdDown():
                print 'CTRL UP'
            else:
                print "UP!"
        if key == wx.WXK_DOWN:
            if evt.CmdDown():
                print 'CTRL DOWN'
            else:
                print "DOWN!"
                
        if key == 83: #S
            self._onShowImage()
            
            
    def _onRightMouseButton(self, evt):
        if not self._selected:
            self.toggleSelect()
            self.manipulation_panel.deselectAllExceptOne(self)
                    
        self._showPopupMenu()
        
    def _onLeftMouseButton(self, evt):
        ctrl_is_down = evt.CmdDown()
        shift_is_down = evt.ShiftDown()
        
        manipulation_panel = wx.FindWindowByName('IFTPanel')
        
        if shift_is_down:
            try:
                
                first_marked_item_idx = manipulation_panel.all_manipulation_items.index(manipulation_panel.getSelectedItems()[0])
                last_marked_item = manipulation_panel.getSelectedItems()[-1]
                last_marked_item_idx = manipulation_panel.all_manipulation_items.index(last_marked_item)
                
                this_item_idx = manipulation_panel.all_manipulation_items.index(self)
            
                if last_marked_item_idx > this_item_idx:
                    adj = 0
                    idxs = [first_marked_item_idx, this_item_idx]
                else:
                    idxs = [last_marked_item_idx, this_item_idx]
                    adj = 1
                        
                top_item = max(idxs)
                bottom_item = min(idxs)
            
                for each in manipulation_panel.all_manipulation_items[bottom_item+adj:top_item+adj]:
                    each.toggleSelect()
            except IndexError:
                pass
            
        elif ctrl_is_down:
            self.toggleSelect()
        else:
            manipulation_panel.deselectAllExceptOne(self)
            self.toggleSelect()
            
            if self._selected:
                
                if self._legend_label == '':
                    wx.CallAfter(self.ift_plot_panel.plotFit, self.sasm)
                else:
                    wx.CallAfter(self.ift_plot_panel.plotFit, self.sasm, legend_label_in = self._legend_label)
                
                wx.CallAfter(self.ift_plot_panel.updateLegend, 2)
        
        evt.Skip()
              
    def _onStarButton(self, event):

        if self._selected_as_bg == True:
            self.enableStar(False)
            self.manipulation_panel.clearBackgroundItem()
        else:
            self.manipulation_panel.setItemAsBackground(self)
            
    def _showInvalidValueError(self):
        wx.CallAfter(wx.MessageBox, 'The entered value is invalid. Please remove non-numeric characters.', 'Invalid Value Error', style = wx.ICON_ERROR)
                    
    def _onScaleOffsetChange(self, event):
        id = event.GetId()
        
        try:
            value = float(event.GetValue())
        except ValueError:
            self._showInvalidValueError()
            return
        
        for each_label, each_id, each_name, eachInit_value, each_bindfunc in self.float_spin_controls:
            
            if id == each_id:
                
                if each_name == 'scale':
                    self.sasm.scale(value)
                elif each_name == 'offset':
                    self.sasm.offset(value)
        
        wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])

        event.Skip()
        
    def _updateQTextCtrl(self):
        qmin_ctrl = wx.FindWindowById(self.spin_controls[0][1])
        qmax_ctrl = wx.FindWindowById(self.spin_controls[1][1])
        
        qmintxt = wx.FindWindowById(self.spin_controls[0][2])
        qmaxtxt = wx.FindWindowById(self.spin_controls[1][2])
        
        try:
            qmin = int(qmin_ctrl.GetValue())
            qmax = int(qmax_ctrl.GetValue())
        except ValueError:
            self._showInvalidValueError()
            return
        
        qmintxt.SetValue(str(round(self.sasm.q[qmin],4)))
        qmaxtxt.SetValue(str(round(self.sasm.q[qmax],4)))
        
        qrange = (qmin, qmax+1) # +1 to be able to use the range for array slicing [0:n+1]

        self.sasm.setQrange(qrange)   
    
    def _updateLegendLabel(self):
        
        if self._legend_label == '' or self._legend_label == None:
            self.sasm.line.set_label(self.sasm.getParameter('filename'))
            self.sasm.fitline.set_label(self.sasm.getParameter('filename'))
      
            self.legend_label_text.SetLabel('')
        else:
            self.sasm.line.set_label(str(self._legend_label))
            self.sasm.fitline.set_label(str(self._legend_label) + ' (FIT)')
            self.legend_label_text.SetLabel('[' + str(self._legend_label) + ']')
            
        wx.CallAfter(self.sasm.plot_panel.updateLegend, 1)
        wx.CallAfter(self.sasm.plot_panel.updateLegend, 2)
        
    
    def _onQrangeChange(self, event):
        self._updateQTextCtrl()
        wx.CallAfter(self.sasm.plot_panel.updatePlotAfterManipulation, [self.sasm])
        
    def _onEnterInQrangeTextCtrl(self, evt):
        
        id = evt.GetId()
        txtctrl = wx.FindWindowById(id)
        
        try:
            val = float(txtctrl.GetValue())
        except ValueError:
            self._showInvalidValueError()
            return
        
        if id == self.spin_controls[0][2]:
                spinctrl = wx.FindWindowById(self.spin_controls[0][1])
        elif id == self.spin_controls[1][2]:
                spinctrl = wx.FindWindowById(self.spin_controls[1][1])
        
        q = self.sasm.getBinnedQ()
        
        findClosest = lambda a,l:min(l,key=lambda x:abs(x-a))
                
        closest = findClosest(val, q)
        idx = numpy.where(q == closest)[0][0]  
        
        spinctrl.SetValue(idx)
        self._onQrangeChange(None)
        txtctrl.SelectAll()
     
    def _onSelectedChkBox(self, event):
        self._selected_for_plot = not self._selected_for_plot
        
        self.showItem(self._selected_for_plot)
        
        self.GetParent().Layout()            
        self.GetParent().Refresh()
        
        wx.CallAfter(self.ift_plot_panel.updateLegend, self.sasm.axes)
        wx.CallAfter(self.sasm.plot_panel.canvas.draw)
        
        self.sasm.plot_panel.fitAxis([self.sasm.axes])
        
    def _createFloatSpinCtrls(self, control_sizer):
        
        for label, id, name, initValue, bindfunc in self.float_spin_controls:
            
            label = wx.StaticText(self, -1, label)
            
            label.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
            label.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
            label.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
            
            if initValue.find('.') == -1:
                initValue = initValue + '.0'
            
            if name == 'scale':
                spinCtrl = RAWCustomCtrl.FloatSpinCtrl(self, id, initValue, TextLength = 100, never_negative = True)
            else:
                spinCtrl = RAWCustomCtrl.FloatSpinCtrl(self, id, initValue, TextLength = 100)
                
            spinCtrl.Bind(RAWCustomCtrl.EVT_MY_SPIN, bindfunc)
            
            control_sizer.Add(label, 1, wx.TOP, 3)
            control_sizer.Add(spinCtrl, 1, wx.EXPAND)
            
        
    def _createSimpleSpinCtrls(self, control_sizer):
        
        
        for each_spinctrl in self.spin_controls:
                spin_id = each_spinctrl[1]
                spin_label_text = each_spinctrl[0]
                qtxtId = each_spinctrl[2]
                spin_range = each_spinctrl[3]
                spin_name = each_spinctrl[4]
                
                spin_min = spin_range[0]
                spin_max = spin_range[1]
    
                spin_min, spin_max = self.sasm.getBinnedQ()[0], self.sasm.getBinnedQ()[-1]
            
                nlow, nhigh = 0, (len(self.sasm.getBinnedQ())-1)
                      
                spin_label = wx.StaticText(self, -1, spin_label_text)
                spin_label.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
                spin_label.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
                spin_label.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
                        
                spin_control = RAWCustomCtrl.IntSpinCtrl(self, spin_id, min = nlow, max = nhigh, TextLength = 43) 
                                        
                if spin_name == 'nlow':
                    spin_control.SetValue(nlow)
                elif spin_name == 'nhigh':
                    spin_control.SetValue(nhigh)
                
                spin_control.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onQrangeChange)
                
                q_ctrl = wx.TextCtrl(self, qtxtId, '', size = (55,22), style = wx.PROCESS_ENTER)
                q_ctrl.Bind(wx.EVT_TEXT_ENTER, self._onEnterInQrangeTextCtrl)
                
                spin_sizer = wx.BoxSizer()
                spin_sizer.Add(q_ctrl, 0, wx.RIGHT, 3)
                spin_sizer.Add(spin_control, 0)
                
                control_sizer.Add(spin_label, 0)        
                control_sizer.Add(spin_sizer, 0)

class IFTControlPanel(wx.Panel):
    
    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent, -1, name = 'IFTControlPanel')
        
        self.parent = parent
        
        self.ift_panel = wx.FindWindowByName('IFTPanel')
        self.sasm = None
        
        self.controlData = (  ('File :', parent.paramsInGui['Filename']),
                          #    ('I(0) :', parent.paramsInGui['I(0)']),
                          #    ('Rg :',   parent.paramsInGui['Rg']),
                              ('Dmax :', parent.paramsInGui['Dmax']),
                              ('Alpha (log):',parent.paramsInGui['Alpha']),
                              ('Algorithm :', parent.paramsInGui['Algorithm']),
                              ('Force zero :', parent.paramsInGui['ForceZero']) )
                          #    ('Qmin :', parent.paramsInGui['Qmin']),
                          #    ('Qmax :', parent.paramsInGui['Qmax']))
                          
        
        topsizer = self.createControls()
        
        self.currentExpObj = None
        
        self.SetSizer(topsizer)
        
    def createControls(self):
        
        cols = 4
        rows = len(self.controlData)
        sizer = wx.FlexGridSizer(cols = cols, rows = rows, vgap = 5, hgap = 5)
        
        for each in self.controlData:
            
            label = each[0]
            type = each[1][1]
            id = each[1][0]
            
            if type == 'filename':
                labelbox = wx.StaticText(self, -1, label)
                self.filename_label = wx.StaticText(self, id, '', size = (60,20))
                sizer.Add(labelbox, 0)
                sizer.Add(self.filename_label, 0)
                sizer.Add((1,1),0)
                sizer.Add((1,1),0)
                
            elif type == 'forcezero':
                #labelbox = wx.StaticText(self, -1, label)
                self.dzero_chkbox = wx.CheckBox(self, -1, 'r(0)')
                self.dmax_chkbox = wx.CheckBox(self, -1, 'r(Dmax)')
                chkbox = wx.CheckBox(self, -1, 'Continous')
                box = wx.BoxSizer() 
                #sizer.Add(labelbox, 0,  wx.ALIGN_CENTER_VERTICAL)
                box.Add(self.dzero_chkbox, 0, wx.RIGHT, 5)
                box.Add(self.dmax_chkbox, 0)
                sizer.Add(box,0)
                sizer.Add(wx.StaticText(self, -1, 'Update :'),0, wx.ALIGN_CENTER)
                sizer.Add(chkbox, 0, wx.ALIGN_CENTER)
                sizer.Add((1,1),0)
               
                self.dzero_chkbox.SetValue(True)
                self.dmax_chkbox.SetValue(True)
                
                ###################################
                self.dzero_chkbox.Enable(False)     #Not ready yet
                self.dmax_chkbox.Enable(False)
                chkbox.Enable(False)
                ###################################
                
            elif type == 'algo':
                #labelbox = wx.StaticText(self, -1, label)
                self.algo_choice = wx.Choice(self, id, size = (80,-1), choices = ['BIFT', 'Manual'])
                self.algo_choice.Select(0)
                
                #ctrl.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onSpinChange)
                
                button = wx.Button(self, -1, 'Run')
                button2 = wx.Button(self, -1, 'Settings')
                
                button2.Bind(wx.EVT_BUTTON, self._onSettingsButton)
                button.Bind(wx.EVT_BUTTON, self._onRunButton)
                   
                #sizer.Add(labelbox, 0, wx.ALIGN_CENTER_VERTICAL)
                sizer.Add(self.algo_choice, 0, wx.ALIGN_LEFT)
                sizer.Add(button, 0, wx.ALIGN_CENTER)
                sizer.Add(button2, 0, wx.ALIGN_CENTER)
                sizer.Add((1,1),0)
            
            elif type == 'info':
                labelbox = wx.StaticText(self, -1, label)
                infobox = wx.TextCtrl(self, id, '', size = (60,20))
                infobox.SetEditable(False)
                sizer.Add(labelbox, 0)
                sizer.Add(infobox, 0)
            
            elif type == 'ctrl':
                labelbox = wx.StaticText(self, -1, label)
                ctrl = RAWCustomCtrl.FloatSpinCtrl(self, id, TextLength = 80)
                ctrl.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onSpinChange)
                sizer.Add(labelbox, 0, wx.ALIGN_CENTER)
                sizer.Add(ctrl, 0, wx.ALIGN_CENTER)
                
            elif type == 'intctrl':
                labelbox = wx.StaticText(self, -1, label)
                ctrl = RAWCustomCtrl.FloatSpinCtrl(self, id, TextLength = 80)
                ctrl.SetValue('80')
                ctrl.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onSpinChange)
                sizer.Add(labelbox, 0, wx.ALIGN_CENTER_VERTICAL)
                sizer.Add(ctrl, 0, wx.ALIGN_CENTER)
            
            elif type == 'listctrl':
                labelbox = wx.StaticText(self, -1, label)
                ctrl = RAWCustomCtrl.IntSpinCtrl(self, id, [1.0])
                ctrl.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onSpinChange)
                sizer.Add(labelbox, 0)
                sizer.Add(ctrl, 0, wx.ALIGN_CENTER)
                
        return sizer   
    
    def _onSettingsButton(self, evt):
        mainframe = wx.FindWindowByName('MainFrame')
        
        mainframe.showOptionsDialog('IFT')
    
    
    def _onRunButton(self, evt):    
        selected_algo = self.algo_choice.GetStringSelection()
        selected_items = self.ift_panel.getSelectedItems()
        
        dmax_ctrl = wx.FindWindowById(self.controlData[1][1][0])
        alpha_ctrl = wx.FindWindowById(self.controlData[2][1][0])
        
        dmax = dmax_ctrl.GetValue()
        alpha = alpha_ctrl.GetValue()
        
        data = {'dmax' : dmax, 
                'alpha': alpha}
                
        if len(selected_items) > 0:
            mainworker_cmd_queue.put(['ift', [selected_algo, selected_items, data]])
            
            dlg = IFTSearchStatusDialog(self, -1)    
            dlg.ShowModal()
            dlg.Destroy()
        
        
    def onUpdateTimer(self, evt):
        print 'TIMER!'
        
    def _onSpinChange(self, evt):
        
        if evt.GetId() == self.parent.paramsInGui['Qmin'][0]:
            QMIN = wx.FindWindowById(self.parent.paramsInGui['Qmin'][0])
            idx = QMIN.GetIdx()
            c = self.currentExpObj.idx
            c[0] = idx
            self.currentExpObj.idx = c
        
        if evt.GetId() == self.parent.paramsInGui['Qmax'][0]:
            QMAX = wx.FindWindowById(self.parent.paramsInGui['Qmax'][0])
            idx = QMAX.GetIdx()
            c = self.currentExpObj.idx
            c[1] = idx
            self.currentExpObj.idx = c
            
    def clear(self):
        for each in self.controlData:
            label = each[0]
            type = each[1][1]
            id = each[1][0]
            
            if type == 'info' or type == 'filename':
                infobox = wx.FindWindowById(id)
                infobox.SetLabel('')
            elif type == 'ctrl':
                ctrl = wx.FindWindowById(id)
                ctrl.SetValue('1.00')
    
    def getDmaxAlpha(self):
        
        D = wx.FindWindowById(self.parent.paramsInGui['Dmax'][0])
        dmax = D.GetValue()
            
        A = wx.FindWindowById(self.parent.paramsInGui['Alpha'][0])
        alpha = A.GetValue()
        
        return (dmax, alpha)
    
    def updateInfo(self):   
        
        
        items = self.ift_panel.getSelectedItems()
        
        if len(items) == 1:
            sasm = items[0].getSASM()
            filename = sasm.getParameter('filename')
            self.filename_label.SetLabel(str(filename))
            
            D = wx.FindWindowById(self.parent.paramsInGui['Dmax'][0])
            if items[0].getIftParameters().has_key('dmax'):
                D.SetValue(str(items[0].getIftParameters()['dmax']))
            else:
                D.SetValue('N/A')
                
                
            A = wx.FindWindowById(self.parent.paramsInGui['Alpha'][0])
            if items[0].getIftParameters().has_key('alpha'):
                A.SetValue(str(items[0].getIftParameters()['alpha']))
            else:
                A.SetValue('N/A')
            
            
            info_panel = wx.FindWindowByName('InformationPanel')
            
            
            
            
        elif len(items) > 1:
            self.filename_label.SetLabel('Multiple Selections')
        else:
            self.clearInfo()
        
        
    def clearInfo(self):
        self.filename_label.SetLabel('')




#--- ** SEC Panel **

class SECPanel(wx.Panel):
    def __init__(self, parent, raw_settings, expParams = []):
        wx.Panel.__init__(self, parent, name = 'SECPanel')
        
        self.expParams = expParams
        self._raw_settings = raw_settings
        self.sec_plot_panel = wx.FindWindowByName('SECPlotPanel')

        self.all_manipulation_items = []

        self.modified_items = []
        
        self.otherParams={'Frame List' : (wx.NewId(), 'framelist'),
                        'Manual' : (wx.NewId(), 'manual')}

        self.paramsInGui={'Filename'               : (wx.NewId(), 'filename'),
                          'Image Header'           : (wx.NewId(), 'imghdr'),
                          'Directory'              : (wx.NewId(), 'dir'),
                          'Initial Run #'          : (wx.NewId(), 'irunnum'),
                          'Final Run #'            : (wx.NewId(), 'frunnum'),
                          'Initial Frame #'        : (wx.NewId(), 'iframenum'),
                          'Final Frame #'          : (wx.NewId(), 'fframenum'),
                          'Initial Selected Frame' : (wx.NewId(), 'isframenum'),
                          'Final Selected Frame'   : (wx.NewId(), 'fsframenum'),
                          'Calculate'              : (wx.NewId(), 'calc'),
                          'Initial Buffer Frame'   : (wx.NewId(), 'ibufframe'),
                          'Final Buffer Frame'     : (wx.NewId(), 'fbufframe'),
                          'Window Size'            : (wx.NewId(), 'wsize'),
                          'Plot Choice'            : (wx.NewId(), 'choice'),
                          'Right Axis Min'         : (wx.NewId(), 'raxismin'),
                          'Right Axis Max'         : (wx.NewId(), 'raxismax')}
        
        self.buttons = (("Save",self._onSaveButton),
                        ("Remove", self._onRemoveButton),
                        ("Clear SEC Data", self._onClearList))
        
        # /* INSERT WIDGETS */ 
        
        self.panelsizer = wx.BoxSizer(wx.VERTICAL)

        self._initializeIcons()
        toolbarsizer = self._createToolbar()

        self.underpanel = scrolled.ScrolledPanel(self, -1, style = wx.BORDER_SUNKEN)
        self.underpanel.SetVirtualSize((200, 200))
        self.underpanel.SetScrollRate(20,20)
      
        self.all_manipulation_items = []
        self.selected_item = []

        self.starred_item = None
        
        self.underpanel_sizer = wx.BoxSizer(wx.VERTICAL)    
        self.underpanel.SetSizer(self.underpanel_sizer)
        
        self.infoBox = SECControlPanel(self)
        
        self.panelsizer.Add(self.infoBox, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER | wx.EXPAND, 10)
        self.panelsizer.Add(toolbarsizer, 0, wx.LEFT | wx.TOP | wx.RIGHT | wx.EXPAND, 5)        
        self.panelsizer.Add(self.underpanel, 1, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 3)
        
        self.createButtons(self.panelsizer)
        
        self.SetSizer(self.panelsizer)
            
    def _onRemoveButton(self, event):
        self.removeSelectedItems()

    
    def _onSaveButton(self, event):
        self._saveItems()

    def _initializeIcons(self):
        # self.collapse_all_png = RAWIcons.collapse_all.GetBitmap()
        # self.expand_all_png = RAWIcons.expand_all.GetBitmap()
        
        self.show_all_png = RAWIcons.open_eye.GetBitmap()
        self.hide_all_png = RAWIcons.close_eye.GetBitmap()

        self.select_all_png = RAWIcons.select_all.GetBitmap()


    def _createToolbar(self):
        
        sizer = wx.BoxSizer()
        
        select_all= wx.StaticBitmap(self, -1, self.select_all_png)    
        # collapse_all = wx.StaticBitmap(self, -1, self.collapse_all_png)
        # expand_all = wx.StaticBitmap(self, -1, self.expand_all_png)
        show_all = wx.StaticBitmap(self, -1, self.show_all_png)
        hide_all = wx.StaticBitmap(self, -1, self.hide_all_png)
        show_all.SetToolTipString('Show All')
        hide_all.SetToolTipString('Hide All')
        select_all.SetToolTipString('Select All')
        
        # collapse_all.SetToolTipString('Collapse All')
        # expand_all.SetToolTipString('Expand All')
        
        # collapse_all.Bind(wx.EVT_LEFT_DOWN, self._onCollapseAllButton)
        # expand_all.Bind(wx.EVT_LEFT_DOWN, self._onExpandAllButton)
        show_all.Bind(wx.EVT_LEFT_DOWN, self._onShowAllButton)
        hide_all.Bind(wx.EVT_LEFT_DOWN, self._onHideAllButton)
        select_all.Bind(wx.EVT_LEFT_DOWN, self._onSelectAllButton)
        
        sizer.Add(show_all, 0, wx.LEFT, 5)
        sizer.Add(hide_all, 0, wx.LEFT, 5)
        sizer.Add((1,1),1, wx.EXPAND)
        sizer.Add(select_all, 0, wx.LEFT, 5)
        sizer.Add((1,1),1, wx.EXPAND)
        # sizer.Add(collapse_all, 0, wx.RIGHT, 5)
        # sizer.Add(expand_all, 0, wx.RIGHT, 3)
        
        return sizer

    def _collapseAllItems(self):
        for each in self.all_manipulation_items:
            each.showControls(False)
        
        self.underpanel.Layout()            
        self.underpanel.Refresh()
        
        self.Layout()            
        self.Refresh()
            
    def _expandAllItems(self):
        for each in self.all_manipulation_items:
            each.showControls(True)
            
        self.underpanel.Layout()            
        self.underpanel.Refresh()
        
        self.Layout()            
        self.Refresh()

    def selectAll(self):
        for each in self.all_manipulation_items:
                each._selected = False
                each.toggleSelect()

    def _onShowAllButton(self, event):
        
        for each in self.all_manipulation_items:
           each.showItem(True)
           
        wx.CallAfter(self.sec_plot_panel.updateLegend, 1)
        # wx.CallAfter(self.sec_plot_panel.updateLegend, 2)
        wx.CallAfter(self.sec_plot_panel.fitAxis)
        
        self.underpanel.Layout()            
        self.underpanel.Refresh()
            
        self.Layout()            
        self.Refresh()
           
    def _onHideAllButton(self, event):
        self.underpanel.Freeze()
        
        for each in self.all_manipulation_items:
           each.showItem(False)
        
        self.underpanel.Layout()            
        self.underpanel.Refresh()
            
        self.Layout()            
        self.Refresh()
        
        self.underpanel.Thaw()
        
        wx.CallAfter(self.sec_plot_panel.updateLegend, 1)
        # wx.CallAfter(self.sec_plot_panel.updateLegend, 2)
        wx.CallAfter(self.sec_plot_panel.canvas.draw)
               
    def _onCollapseAllButton(self, event):
        self._collapseAllItems()
        
    def _onExpandAllButton(self, event):
        self._expandAllItems()

    def _onSelectAllButton(self, event):
        self.selectAll()

    def getSelectedItems(self):
        
        self.selected_item_list = []
        
        for each in self.all_manipulation_items:
            if each._selected == True:
                self.selected_item_list.append(each)
            
        return self.selected_item_list

    def deselectAllExceptOne(self, item, line = None, enableLocatorLine = False):
        if line == None:    
            for each in self.all_manipulation_items:
                if each != item:
                    each._selected = True
                    each.toggleSelect()
        else:
            for each in self.all_manipulation_items:
                if each.secm.getLine() == line or each.secm.getCalcLine() == line:
                    each._selected = False
                    each.toggleSelect()
                else:
                    each._selected = True
                    each.toggleSelect()

    def removeSelectedItems(self):

        sec_control_panel = wx.FindWindowByName('SECControlPanel')
       
        if len(self.getSelectedItems()) == 0:
            return
        
        self.Freeze()
        
        axes_that_needs_updated_legend = []
         
        for each in self.getSelectedItems():

            try:
                self.modified_items.remove(each)
            except:
                pass

            if each.secm == sec_control_panel.secm:
                sec_control_panel.secm = None
            
            if each.secm.line != None:      
                plot_panel = each.secm.plot_panel
            
                try:
                    each.secm.line.remove()
                    
                    if each.secm.origline != None:
                        each.secm.origline.remove()
                
                    i = plot_panel.plotted_secms.index(each.secm)
                    plot_panel.plotted_secms.pop(i)
                except (IndexError, ValueError):
                    pass
            
                if not each.secm.axes in axes_that_needs_updated_legend:
                    axes_that_needs_updated_legend.append(each.secm.axes)
                    
                for eachaxes in axes_that_needs_updated_legend:
                    if eachaxes == plot_panel.subplot1:
                        wx.CallAfter(plot_panel.updateLegend, 1)
                    else:
                        wx.CallAfter(plot_panel.updateLegend, 2)

            if each.secm.calc_line != None:      
                plot_panel = each.secm.plot_panel
            
                try:
                    each.secm.calc_line.remove()
                
                except (IndexError, ValueError):
                    pass
            
                if not each.secm.calc_axes in axes_that_needs_updated_legend:
                    axes_that_needs_updated_legend.append(each.secm.calc_axes)
                    
                for eachaxes in axes_that_needs_updated_legend:
                    if eachaxes == plot_panel.subplot1:
                        wx.CallAfter(plot_panel.updateLegend, 1)
                    else:
                        wx.CallAfter(plot_panel.updateLegend, 2)
                    
                wx.CallAfter(plot_panel.canvas.draw)
                
            if each == self.starred_item:
                self.starred_item = None
            
            idx = self.all_manipulation_items.index(each)
            self.all_manipulation_items[idx].Destroy()
            self.all_manipulation_items.pop(idx)

        self.underpanel_sizer.Layout()
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        self.underpanel.Refresh()    
        
        self.Thaw()

    def addItem(self, secm, item_colour = 'black', item_visible = True, notsaved = False):
        
        newItem = SECItemPanel(self.underpanel, secm, font_colour = item_colour,
                                 item_visible = item_visible)
        self.Freeze()
        self.underpanel_sizer.Add(newItem, 0, wx.GROW)
        self.underpanel_sizer.Layout()
        
        self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        self.Layout()            
        self.Refresh()
        self.Thaw()
        
        # Keeping track of all items in our list:
        self.all_manipulation_items.append(newItem)
        
        
        secm.item_panel = newItem
        
        if notsaved:
            newItem.markAsModified()
    
    def saveData(self):
        selected_items = self.getSelectedItems()

        dirctrl_panel = wx.FindWindowByName('DirCtrlPanel')
        path = dirctrl_panel.getDirLabel()

        if len(selected_items) == 1:
            
            filters = 'Comma Separated Files (*.csv)|*.csv'
                
            # dialog = wx.FileDialog( None, style = wx.SAVE | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = save_path) 
            fname = os.path.splitext(os.path.basename(selected_items[0].secm.getParameter('filename')))[0]+'.csv'
            msg = "Please select save directory and enter save file name"
            dialog = wx.FileDialog( None, message = msg, style = wx.SAVE | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = path, defaultFile = fname) 
                
            if dialog.ShowModal() == wx.ID_OK:               
                path = dialog.GetPath()
            else:
                return

            path=os.path.splitext(path)[0]+'.csv'
            save_path = [path]
        
        elif len(selected_items) == 0:
            return

        else:
            dirdlg = wx.DirDialog(self, "Please select save directory (multiple files will be saved):", defaultPath = path)
            
            if dirdlg.ShowModal() == wx.ID_OK:
                path = dirdlg.GetPath()
            else:
                return
            save_path=[]

            for item in selected_items:
                # print item.secm.getParameter('filename')
                # print item.secm.line.get_label()
                name=os.path.splitext(os.path.basename(item.secm.getParameter('filename')))[0]+'_sec_data.csv'
                save_path.append(os.path.join(path, name))

        
        mainworker_cmd_queue.put(['save_sec_data', [save_path, selected_items]])

    def _saveItems(self):
        selected_items = self.getSelectedItems()

        dirctrl_panel = wx.FindWindowByName('DirCtrlPanel')
        path = dirctrl_panel.getDirLabel()

        if len(selected_items) == 1:
            
            # filters = 'Comma Separated Files (*.csv)|*.csv'
                
            # dialog = wx.FileDialog( None, style = wx.SAVE | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = save_path) 
            fname = os.path.splitext(os.path.basename(selected_items[0].secm.getParameter('filename')))[0]+'.sec'
            msg = "Please select save directory and enter save file name"
            dialog = wx.FileDialog(self, message = msg, style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT, defaultDir = path, defaultFile = fname) 
                
            if dialog.ShowModal() == wx.ID_OK:               
                path = dialog.GetPath()
            else:
                return

            path=os.path.splitext(path)[0]+'.sec'
            save_path = [path]
        
        elif len(selected_items) == 0:
            return

        else:
            dirdlg = wx.DirDialog(self, "Please select save directory (multiple files will be saved):", defaultPath = path,)
            
            if dirdlg.ShowModal() == wx.ID_OK:
                path = dirdlg.GetPath()
            else:
                return
            save_path=[]

            for item in selected_items:
                # print item.secm.getParameter('filename')
                # print item.secm.line.get_label()
                name=os.path.splitext(os.path.split(item.secm.getParameter('filename'))[1])[0]+'.sec'
                save_path.append(os.path.join(path, name))

        
        mainworker_cmd_queue.put(['save_sec_item', [save_path, selected_items]])
            
    def _OnClearAll(self, evt):
        plotpage = wx.FindWindowByName('SECPlotPanel')
        plotpage.OnClear(0)

    def _onClearList(self, evt):
        self.Freeze()
        
        rest_of_items = []
        for each in self.all_manipulation_items:
            
            try:
                each.Destroy()
            except ValueError:
                rest_of_items.append(each)
            except AttributeError:
                each = None
                
        self.all_manipulation_items = rest_of_items
        # self.underpanel_sizer.Layout()
        # self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        
        # self._star_marked_item = None
        
        self.Thaw()
        
        self.sec_plot_panel.clearAllPlots()

    def clearList(self):
        self.Freeze()
        
        rest_of_items = []
        for each in self.all_manipulation_items:
            
            try:
                each.Destroy()
            except ValueError:
                rest_of_items.append(each)
            except AttributeError:
                each = None

                
        self.all_manipulation_items = rest_of_items
        # self.underpanel_sizer.Layout()
        # self.underpanel.SetVirtualSize(self.underpanel.GetBestVirtualSize())
        
        # self._star_marked_item = None
        self.modified_items = []
        
        self.Thaw()
    
    def _onLoadFile(self, evt):   
         
        selected_file = self._CreateFileDialog(wx.OPEN)
        
        if selected_file:
       
            sasm, img = SASFileIO.loadFile(selected_file, self.raw_settings)
            
            try:        
                self.addItem(sasm)
            except Exception:
                print 'WARNING!! Error in _OnLoadFile!!'
            
 
    def _CreateFileDialog(self, mode):
        
        file = None
        
        dirctrl_panel = wx.FindWindowByName('DirCtrlPanel')
        load_path = dirctrl_panel.getDirLabel()
        
        if mode == wx.OPEN:
            filters = 'All files (*.*)|*.*|Rad files (*.rad)|*.rad|Dat files (*.dat)|*.dat|Txt files (*.txt)|*.txt'
            dialog = wx.FileDialog( None, 'Select a file', load_path, style = mode, wildcard = filters)
        if mode == wx.SAVE:
            filters = 'Dat files (*.dat)|*.dat'
            dialog = wx.FileDialog( None, 'Name file and location', load_path, style = mode | wx.OVERWRITE_PROMPT, wildcard = filters)        
        
        # Show the dialog and get user input
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetPath()
            
        # Destroy the dialog
        dialog.Destroy()
        
        return file
    
    def createButtons(self, panelsizer):
        
        sizer = wx.GridSizer(cols = 3, rows = ceil(len(self.buttons)/3))
        
        #sizer.Add((10,10) ,1 , wx.EXPAND)
        for each in self.buttons:
            if each:
                
                label = each[0]
                bindfunc = each[1]
                
                button = wx.Button(self, -1, label)
                button.Bind(wx.EVT_BUTTON, bindfunc)
                
                sizer.Add(button, 1, wx.EXPAND | wx.ALIGN_CENTER)         
          
        panelsizer.Add(sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP | wx.ALIGN_CENTRE | wx.EXPAND, 10)

    def setItemAsData(self, item):
        
        bg_secm = self._raw_settings.get('DataSECM')
        
        if bg_secm != None:
            try:
                bg_secm.itempanel.enableStar(False)
                self.clearDataItem()
            except:
                pass
        elif self.getDataItem() != None:
            bg_secm = self.getDataItem()
            try:
                bg_secm.itempanel.enableStar(False)
                self.clearDataItem()
            except:
                pass

        
        self._raw_settings.set('DataSECM', item.secm)
        item.enableStar(True)
        self.starred_item = item
        
    def getDataItem(self):
        return self.starred_item

    def clearDataItem(self):
        self._raw_settings.set('DataSECM', None)
        self.starred_item = None

    def getItems(self):
        return self.all_manipulation_items


class SECItemPanel(wx.Panel):
    def __init__(self, parent, secm, font_colour = 'BLACK', legend_label = '', item_visible = True):
        
        wx.Panel.__init__(self, parent, style = wx.BORDER_RAISED)
        
        self.parent = parent
        self.secm = secm
        self.secm.itempanel = self
        
        # self.manipulation_panel = wx.FindWindowByName('ManipulationPanel')
        # self.plot_panel = wx.FindWindowByName('PlotPanel')
        self.sec_plot_panel = wx.FindWindowByName('SECPlotPanel')
        self.main_frame = wx.FindWindowByName('MainFrame')
        self.sec_control_panel = wx.FindWindowByName('SECControlPanel')
        self.sec_panel = wx.FindWindowByName('SECPanel')
        
        self.raw_settings = self.main_frame.raw_settings
        
        self.info_panel = wx.FindWindowByName('InformationPanel')
        self.info_settings = {'hdr_choice' : 0}
        
        self._selected_as_bg = False
        self._selected_for_plot = item_visible
        self._controls_visible = True
        self._selected = False
        self._legend_label = legend_label
        
        self._font_colour = font_colour
        
        filename = secm.getParameter('filename')
               
        self.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
        self.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
        self.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
        #Label, TextCtrl_ID, SPIN_ID
        
        self._initializeIcons()
                                       
        # self.qmax = len(self.secm.q)
                             
        # self.spin_controls = (("q Min:", wx.NewId(), wx.NewId(), (1, self.qmax-1), 'nlow'),        
        #                      ("q Max:", wx.NewId(), wx.NewId(), (2, self.qmax), 'nhigh'))
        
        # self.float_spin_controls = (
        #                            # ("Conc:", wx.NewId(), 'conc', '1.0', self._onScaleOffsetChange),
        #                             ("Scale:", wx.NewId(), 'scale', str(secm.getScale()), self._onScaleOffsetChange),
        #                             ("Offset:", wx.NewId(), 'offset', str(secm.getOffset()), self._onScaleOffsetChange))
    
        self.SelectedForPlot = RAWCustomCtrl.CustomCheckBox(self, -1, filename)
        self.SelectedForPlot.SetValue(True)
        self.SelectedForPlot.Bind(wx.EVT_CHECKBOX, self._onSelectedChkBox)
        self.SelectedForPlot.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
        self.SelectedForPlot.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
        self.SelectedForPlot.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
        
        self.SelectedForPlot.SetToolTipString('Show Plot')
        self.SelectedForPlot.SetForegroundColour(font_colour)
        
        self.legend_label_text = wx.StaticText(self, -1, '')
        
        self.legend_label_text.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
        self.legend_label_text.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
        self.legend_label_text.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
        
        conv = mplcol.ColorConverter()
        color = conv.to_rgb(self.secm.line.get_mfc())
        color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        self.colour_indicator = RAWCustomCtrl.ColourIndicator(self, -1, color, size = (20,15))
        self.colour_indicator.Bind(wx.EVT_LEFT_DOWN, self._onLinePropertyButton)
        self.colour_indicator.SetToolTipString('Line Properties')

        self.bg_star = wx.StaticBitmap(self, -1, self.gray_png)
        self.bg_star.Bind(wx.EVT_LEFT_DOWN, self._onStarButton)
        self.bg_star.SetToolTipString('Mark')
        
        # self.expand_collapse = wx.StaticBitmap(self, -1, self.collapse_png)
        # self.expand_collapse.Bind(wx.EVT_LEFT_DOWN, self._onExpandCollapseButton)
        # self.expand_collapse.SetToolTipString('Collapse/Expand')
        
        self.target_icon = wx.StaticBitmap(self, -1, self.target_png)
        self.target_icon.Bind(wx.EVT_LEFT_DOWN, self._onTargetButton)
        self.target_icon.SetToolTipString('Locate Line')

        self.info_icon = wx.StaticBitmap(self, -1, self.info_png)
        self.info_icon.Bind(wx.EVT_LEFT_DOWN, self._onInfoButton)
        self.info_icon.SetToolTipString('Show Extended Info\n--------------------------------\nFirst buffer frame: N/A\nLast buffer frame: N/A\nAverage window size: N/A')
        
        self.locator_on = False
        self.locator_old_width = 1
        
        panelsizer = wx.BoxSizer()
        panelsizer.Add(self.SelectedForPlot, 0, wx.LEFT | wx.TOP, 3)
        panelsizer.Add(self.legend_label_text, 0, wx.LEFT | wx.TOP, 3)
        panelsizer.Add((1,1), 1, wx.EXPAND)
        # panelsizer.Add(self.expand_collapse, 0, wx.RIGHT | wx.TOP, 5)
        panelsizer.Add(self.info_icon, 0, wx.RIGHT | wx.TOP, 5)
        panelsizer.Add(self.target_icon, 0, wx.RIGHT | wx.TOP, 4)
        panelsizer.Add(self.colour_indicator, 0, wx.RIGHT | wx.TOP, 5)
        panelsizer.Add(self.bg_star, 0, wx.LEFT | wx.RIGHT | wx.TOP, 3)
        
    
        self.topsizer = wx.BoxSizer(wx.VERTICAL)
        self.topsizer.Add(panelsizer, 1, wx.EXPAND)
        
        #self.controlSizer = wx.BoxSizer(wx.VERTICAL)
        self.controlSizer = wx.FlexGridSizer(cols = 4, rows = 2, vgap = 3, hgap = 7)
       
        # self._createSimpleSpinCtrls(self.controlSizer)
        # self._createFloatSpinCtrls(self.controlSizer) 
        
        self.topsizer.Add((5,5),0)
        self.topsizer.Add(self.controlSizer, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM, 5)
        
        self.SetSizer(self.topsizer)
        
        self.SetBackgroundColour(wx.Colour(250,250,250))
        
        # self._initStartPosition()
        # self._updateQTextCtrl()
        
        if self.secm.initial_buffer_frame != -1:
            self.updateInfoTip()
            
        # controls_not_shown = self.main_frame.raw_settings.get('ManipItemCollapsed')
        
        # if not self._selected_for_plot:
        #     controls_not_shown = True
        
        # if controls_not_shown:
        #     self.showControls(not controls_not_shown)
        
        self.updateShowItemCheckBox()


    def updateInfoTip(self):
        
        initial = self.secm.initial_buffer_frame
        final = self.secm.final_buffer_frame
        window = self.secm.window_size

        if initial == -1 or final == -1 or window == -1:
            self.info_icon.SetToolTipString('Show Extended Info\n--------------------------------\nFirst buffer frame: N/A\nLast buffer frame: N/A\nAverage window size: N/A')
        else:
            self.info_icon.SetToolTipString('Show Extended Info\n--------------------------------\nFirst buffer frame: %i\nLast buffer frame: %i\nAverage window size: %i' %(initial, final, window))

    def _onInfoButton(self, event):
        pass
                
    def enableStar(self, state):
        if state == True:
            self.bg_star.SetBitmap(self.star_png)
            self._selected_as_bg = True
        else:
            self.bg_star.SetBitmap(self.gray_png)
            self._selected_as_bg = False
        
        self.bg_star.Refresh()
        
    def removeSelf(self):
        #Has to be callafter under Linux.. or it'll crash
        wx.CallAfter(self.sec_panel.removeSelectedItems)
        
    def getSECM(self):
        return self.secm        
    
    def getFontColour(self):
        return self._font_colour
    
    def getSelectedForPlot(self):
        return self._selected_for_plot
    
    def getLegendLabel(self):
        return self._legend_label
    
    def updateControlsFromSECM(self):    
        scale = self.secm.getScale()
        offset = self.secm.getOffset()
        qmin, qmax = self.secm.getQrange()
        
        qmin_ctrl = wx.FindWindowById(self.spin_controls[0][1])
        qmax_ctrl = wx.FindWindowById(self.spin_controls[1][1])
        qmintxt = wx.FindWindowById(self.spin_controls[0][2])
        qmaxtxt = wx.FindWindowById(self.spin_controls[1][2])
        
        qmin_ctrl.SetValue(str(qmin))
        qmax_ctrl.SetValue(str(qmax-1))        
        qmintxt.SetValue(str(round(self.secm.q[qmin],4)))
        qmaxtxt.SetValue(str(round(self.secm.q[qmax-1],4)))
        
        scale_ctrl = wx.FindWindowById(self.float_spin_controls[0][1])
        offset_ctrl = wx.FindWindowById(self.float_spin_controls[1][1])
    
        offset_ctrl.SetValue(str(offset))
        scale_ctrl.SetValue(str(scale))
        
        wx.CallAfter(self.secm.plot_panel.updatePlotAfterManipulation, [self.secm])
    
    def toggleSelect(self):
        
        if self._selected:
            self._selected = False
            self.SetBackgroundColour(wx.Colour(250,250,250))
            self.info_panel.clearInfo()
        else:
            self._selected = True
            self.SetBackgroundColour(wx.Colour(200,200,200))
            self.SetFocusIgnoringChildren()
            self.info_panel.clearInfo()
            # self.info_panel.updateInfoFromItem(self)
        
        self.Refresh()
        
    def enableLocatorLine(self):
        
        self.locator_on = not self.locator_on
        
        if self.locator_on == True:
            self.target_icon.SetBitmap(self.target_on_png)
            self.locator_old_width = self.secm.line.get_linewidth()
            new_width = self.locator_old_width + 2.0
            self.secm.line.set_linewidth(new_width)

            if self.secm.calc_has_data and self.secm.calc_is_plotted:
                self.secm.calc_line.set_linewidth(new_width)
            wx.CallAfter(self.secm.plot_panel.canvas.draw)
        else:
            self.target_icon.SetBitmap(self.target_png)
            self.secm.line.set_linewidth(self.locator_old_width)
            if self.secm.calc_has_data and self.secm.calc_is_plotted:
                self.secm.calc_line.set_linewidth(self.locator_old_width)
            wx.CallAfter(self.secm.plot_panel.canvas.draw)
            
        self.target_icon.Refresh()
        
    def getControlsVisible(self):
        return self._controls_visible
        
    def showControls(self, state):
        
        if state == False:
            self.expand_collapse.SetBitmap(self.expand_png)
            self._controls_visible = False
            self.controlSizer.Hide(0, True)
            self.controlSizer.Hide(1, True)
            self.controlSizer.Hide(2, True)
            self.controlSizer.Hide(3, True)
            self.controlSizer.Hide(4, True)
            self.controlSizer.Hide(5, True)
            self.controlSizer.Hide(6, True)
            self.controlSizer.Hide(7, True)
        else:
            self.expand_collapse.SetBitmap(self.collapse_png)
            self._controls_visible = True
            self.controlSizer.Show(0, True)
            self.controlSizer.Show(1, True)
            self.controlSizer.Show(2, True)
            self.controlSizer.Show(3, True)
            self.controlSizer.Show(4, True)
            self.controlSizer.Show(5, True)
            self.controlSizer.Show(6, True)
            self.controlSizer.Show(7, True)
            
        self.expand_collapse.Refresh()
        self.topsizer.Layout()
        
    
    def showItem(self, state):
        self._selected_for_plot = state
        
        if self._selected_for_plot == False:
            self._controls_visible = False
            # self.showControls(self._controls_visible)
        
        self.SelectedForPlot.SetValue(self._selected_for_plot)
        self.secm.line.set_visible(self._selected_for_plot)
        self.secm.line.set_picker(self._selected_for_plot)      #Line can't be selected when it's hidden

        if self.sec_plot_panel.plotparams['secm_plot_calc'] != 'None' and self.secm.calc_has_data:
            self.secm.calc_line.set_visible(self._selected_for_plot)
            self.secm.calc_line.set_picker(self._selected_for_plot)      #Line can't be selected when it's hidden
        self.secm.is_visible = self._selected_for_plot
    
    def updateShowItemCheckBox(self):
        #self.showControls(self._controls_visible)
        self.SelectedForPlot.SetValue(self._selected_for_plot)
        self.secm.line.set_picker(self._selected_for_plot)
    
    def markAsModified(self):
        parent = self.GetParent()
        
        filename = self.secm.getParameter('filename')
        self.SelectedForPlot.SetLabel('* ' + str(filename))
        self.SelectedForPlot.Refresh()
        self.topsizer.Layout()
        parent.Layout()            
        parent.Refresh()
        
        if self not in self.sec_panel.modified_items:
            self.sec_panel.modified_items.append(self)
    
    def unmarkAsModified(self):
        parent = self.GetParent()
        
        filename = self.secm.getParameter('filename')
        self.SelectedForPlot.SetLabel(str(filename))
        self.SelectedForPlot.Refresh()
        self.topsizer.Layout()
        parent.Layout()            
        parent.Refresh()
        try:
            self.sec_panel.modified_items.remove(self)
        except:
            pass
        
    def updateFilenameLabel(self):
        filename = self.secm.getParameter('filename')
        
        if self._legend_label == '':
            self.secm.line.set_label(filename)
        self.sec_plot_panel.updateLegend(self.secm.axes)
        self.SelectedForPlot.SetLabel(str(filename))
        self.SelectedForPlot.Refresh()
        self.topsizer.Layout()
        self.GetParent().Layout()            
        self.GetParent().Refresh()
                
    def _initializeIcons(self):
        
        self.gray_png = RAWIcons.Star_icon_notenabled.GetBitmap()
        self.star_png = RAWIcons.Star_icon_org.GetBitmap()
        
        self.collapse_png = RAWIcons.collapse.GetBitmap()
        self.expand_png = RAWIcons.expand.GetBitmap()
        
        self.target_png = RAWIcons.target.GetBitmap()
        self.target_on_png = RAWIcons.target_orange.GetBitmap()

        self.info_png = RAWIcons.info_16_2.GetBitmap()

    def _initStartPosition(self):
        
        qmin_ctrl = wx.FindWindowById(self.spin_controls[0][1])
        qmax_ctrl = wx.FindWindowById(self.spin_controls[1][1])
        
        qrange = self.secm.getQrange()
        
        qmin_ctrl.SetValue(str(qrange[0]))
        
    def _updateColourIndicator(self):
        conv = mplcol.ColorConverter()
        color = conv.to_rgb(self.secm.line.get_color())
        color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        self.colour_indicator.updateColour(color)
        
    def _onLinePropertyButton(self, event):
        # print 'got this far'
        try:
            legend_label = self.getLegendLabel()
            # print legend_label
            dialog = SECMLinePropertyDialog(self, self.secm, legend_label)
            answer = dialog.ShowModal()
            new_legend_label = dialog.getLegendLabel()
            self._updateColourIndicator()
            dialog.Destroy()
            
            if answer == wx.ID_OK:
                self._legend_label = new_legend_label
                self._updateLegendLabel()
                
        except TypeError:
            return
           
        if self.secm.axes == self.sec_plot_panel.subplot1:
            wx.CallAfter(self.sec_plot_panel.updateLegend, 1)
        else:
            wx.CallAfter(self.sec_plot_panel.updateLegend, 2)
            
        self.secm.plot_panel.canvas.draw()
        
    def _onExpandCollapseButton(self, event):
        self._controls_visible = not self._controls_visible
        self.showControls(self._controls_visible)
        
        self.sec_panel.underpanel.SetVirtualSize(self.sec_panel.underpanel.GetBestVirtualSize())
        self.GetParent().Layout()            
        self.GetParent().Refresh()
        
        self.GetParent().GetParent().Layout()            
        self.GetParent().GetParent().Refresh()
                        
    def _onTargetButton(self, event):
        self.enableLocatorLine()
            
    def _showPopupMenu(self):

        menu = wx.Menu()
        
        number_of_selected_items = len(self.sec_panel.getSelectedItems())
        
        menu.Append(1, 'Remove' )
        menu.Append(2, 'Export data')
        menu.Append(3, 'Save')
        menu.AppendSeparator()
        
        menu.Append(4, 'Show data')
        
        menu.AppendSeparator()
        menu.Append(5, 'Rename')
        
        
        self.Bind(wx.EVT_MENU, self._onPopupMenuChoice)        
        self.PopupMenu(menu)
    
    def _onPopupMenuChoice(self, evt):
            
#        if evt.GetId() == 3:
#            #IFT
#            analysisPage.runBiftOnExperimentObject(self.ExpObj, expParams)
                
        if evt.GetId() == 1:
            #Delete
            wx.CallAfter(self.sec_panel.removeSelectedItems)
        
        if evt.GetId() == 2:
            self.sec_panel.saveData()

        if evt.GetId() == 3:
            self.sec_panel._saveItems()

        if evt.GetId() == 4:
            dlg = SECDataDialog(self, self.secm)
            dlg.ShowModal()
            dlg.Destroy()
            
        if evt.GetId() == 5:
            dlg = FilenameChangeDialog(self, self.secm.getParameter('filename'))
            dlg.ShowModal()
            filename =  dlg.getFilename()
            dlg.Destroy()
            
            if filename:
                self.secm.setParameter('filename', filename)
                self.updateFilenameLabel()
                self.markAsModified()
                        
    
    def _onKeyPress(self, evt):
        
        key = evt.GetKeyCode()
        
        if ((key == wx.WXK_DELETE) or (key == wx.WXK_BACK and evt.CmdDown())) and self._selected == True:
            self.removeSelf()
            
        if key == wx.WXK_UP:
            if evt.CmdDown():
                print 'CTRL UP'
            else:
                print "UP!"
        if key == wx.WXK_DOWN:
            if evt.CmdDown():
                print 'CTRL DOWN'
            else:
                print "DOWN!"
            
            
    def _onRightMouseButton(self, evt):
        self.SetFocusIgnoringChildren()
        
        if not self._selected:
            self.toggleSelect()
            self.sec_panel.deselectAllExceptOne(self)
                    
        self._showPopupMenu()
        
    def _onLeftMouseButton(self, evt):
        ctrl_is_down = evt.CmdDown()
        shift_is_down = evt.ShiftDown()
        
        sec_panel = wx.FindWindowByName('SECPanel')
        
        if shift_is_down:
            try:
                
                first_marked_item_idx = sec_panel.all_manipulation_items.index(sec_panel.getSelectedItems()[0])
                last_marked_item = sec_panel.getSelectedItems()[-1]
                last_marked_item_idx = sec_panel.all_manipulation_items.index(last_marked_item)
                
                this_item_idx = sec_panel.all_manipulation_items.index(self)
            
                if last_marked_item_idx > this_item_idx:
                    adj = 0
                    idxs = [first_marked_item_idx, this_item_idx]
                else:
                    idxs = [last_marked_item_idx, this_item_idx]
                    adj = 1
                        
                top_item = max(idxs)
                bottom_item = min(idxs)
            
                for each in sec_panel.all_manipulation_items[bottom_item+adj:top_item+adj]:
                    each.toggleSelect()
            except IndexError:
                pass
            
        elif ctrl_is_down:
            self.toggleSelect()
        else:
            sec_panel.deselectAllExceptOne(self)
            self.toggleSelect()
            
        evt.Skip()
              
    def _onStarButton(self, event):

        if self._selected_as_bg == True:
            self.enableStar(False)
            self.sec_panel.clearDataItem()
        else:
            self.sec_panel.setItemAsData(self)
            
    def _showInvalidValueError(self):
        wx.CallAfter(wx.MessageBox, 'The entered value is invalid. Please remove non-numeric characters.', 'Invalid Value Error', style = wx.ICON_ERROR)
                    
    def _onScaleOffsetChange(self, event):
        id = event.GetId()
        
        try:
            value = float(event.GetValue())
        except ValueError:
            self._showInvalidValueError()
            return
        
        for each_label, each_id, each_name, eachInit_value, each_bindfunc in self.float_spin_controls:
            
            if id == each_id:
                
                if each_name == 'scale':
                    self.secm.scale(value)
                elif each_name == 'offset':
                    self.secm.offset(value)
        
        wx.CallAfter(self.secm.plot_panel.updatePlotAfterManipulation, [self.secm])
        
        self.markAsModified()
        event.Skip()
        
    def _updateQTextCtrl(self):
        qmin_ctrl = wx.FindWindowById(self.spin_controls[0][1])
        qmax_ctrl = wx.FindWindowById(self.spin_controls[1][1])
        
        qmintxt = wx.FindWindowById(self.spin_controls[0][2])
        qmaxtxt = wx.FindWindowById(self.spin_controls[1][2])
        
        try:
            qmin = int(qmin_ctrl.GetValue())
            qmax = int(qmax_ctrl.GetValue())
        except ValueError:
            self._showInvalidValueError()
            return
        
        qmintxt.SetValue(str(round(self.secm.q[qmin],4)))
        qmaxtxt.SetValue(str(round(self.secm.q[qmax],4)))
        
        qrange = (qmin, qmax+1) # +1 to be able to use the range for array slicing [0:n+1]

        self.secm.setQrange(qrange)   
    
    def _updateLegendLabel(self):
        
        if self._legend_label == '' or self._legend_label == None:
            self.secm.line.set_label(self.secm.getParameter('filename'))
            self.legend_label_text.SetLabel('')
        else:
            self.secm.line.set_label(str(self._legend_label))
            self.legend_label_text.SetLabel('[' + str(self._legend_label) + ']')
            
        wx.CallAfter(self.secm.plot_panel.updateLegend, self.secm.axes)
        
    
    def _onQrangeChange(self, event):
        self._updateQTextCtrl()
        wx.CallAfter(self.secm.plot_panel.updatePlotAfterManipulation, [self.secm])
        self.markAsModified()
        
    def _onEnterInQrangeTextCtrl(self, evt):
        
        id = evt.GetId()
        txtctrl = wx.FindWindowById(id)
        
        try:
            val = float(txtctrl.GetValue())
        except ValueError:
            self._showInvalidValueError()
            return
        
        if id == self.spin_controls[0][2]:
                spinctrl = wx.FindWindowById(self.spin_controls[0][1])
        elif id == self.spin_controls[1][2]:
                spinctrl = wx.FindWindowById(self.spin_controls[1][1])
        
        q = self.secm.getBinnedQ()
        
        findClosest = lambda a,l:min(l,key=lambda x:abs(x-a))
                
        closest = findClosest(val, q)
        idx = numpy.where(q == closest)[0][0]  
        
        spinctrl.SetValue(idx)
        self._onQrangeChange(None)
        txtctrl.SelectAll()
     
    def _onSelectedChkBox(self, event):
        self._selected_for_plot = not self._selected_for_plot
        
        self.showItem(self._selected_for_plot)
        
        self.GetParent().Layout()            
        self.GetParent().Refresh()
        
        wx.CallAfter(self.sec_plot_panel.updateLegend, self.secm.axes)
        wx.CallAfter(self.secm.plot_panel.canvas.draw)
        
        wx.CallAfter(self.secm.plot_panel.fitAxis)
        
    def _createFloatSpinCtrls(self, control_sizer):
        
        for label, id, name, initValue, bindfunc in self.float_spin_controls:
            
            label = wx.StaticText(self, -1, label)
            
            label.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
            label.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
            label.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
            
            if initValue.find('.') == -1:
                initValue = initValue + '.0'
            
            if name == 'scale':
                spinCtrl = RAWCustomCtrl.FloatSpinCtrl(self, id, initValue, TextLength = 100, never_negative = True)
            else:
                spinCtrl = RAWCustomCtrl.FloatSpinCtrl(self, id, initValue, TextLength = 100)
                
            spinCtrl.Bind(RAWCustomCtrl.EVT_MY_SPIN, bindfunc)
            
            control_sizer.Add(label, 1, wx.TOP, 3)
            control_sizer.Add(spinCtrl, 1, wx.EXPAND)
            
        
    def _createSimpleSpinCtrls(self, control_sizer):
        
        
        for each_spinctrl in self.spin_controls:
                spin_id = each_spinctrl[1]
                spin_label_text = each_spinctrl[0]
                qtxtId = each_spinctrl[2]
                spin_range = each_spinctrl[3]
                spin_name = each_spinctrl[4]
                
                spin_min = spin_range[0]
                spin_max = spin_range[1]
    
                spin_min, spin_max = self.secm.getBinnedQ()[0], self.secm.getBinnedQ()[-1]
            
                nlow, nhigh = 0, (len(self.secm.getBinnedQ())-1)
                      
                spin_label = wx.StaticText(self, -1, spin_label_text)
                spin_label.Bind(wx.EVT_LEFT_DOWN, self._onLeftMouseButton)
                spin_label.Bind(wx.EVT_RIGHT_DOWN, self._onRightMouseButton)
                spin_label.Bind(wx.EVT_KEY_DOWN, self._onKeyPress)
                        
                spin_control = RAWCustomCtrl.IntSpinCtrl(self, spin_id, min = nlow, max = nhigh, TextLength = 43) 
                                        
                if spin_name == 'nlow':
                    spin_control.SetValue(nlow)
                elif spin_name == 'nhigh':
                    spin_control.SetValue(nhigh)
                
                spin_control.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onQrangeChange)
                
                q_ctrl = wx.TextCtrl(self, qtxtId, '', size = (55,22), style = wx.PROCESS_ENTER)
                q_ctrl.Bind(wx.EVT_TEXT_ENTER, self._onEnterInQrangeTextCtrl)
                
                spin_sizer = wx.BoxSizer()
                spin_sizer.Add(q_ctrl, 0, wx.RIGHT, 3)
                spin_sizer.Add(spin_control, 0)
                
                control_sizer.Add(spin_label, 0)        
                control_sizer.Add(spin_sizer, 0)


class SECControlPanel(wx.Panel):
    
    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent, -1, name = 'SECControlPanel')
        
        self.parent = parent

        self.main_frame = wx.FindWindowByName('MainFrame')
        
        self.sec_panel = wx.FindWindowByName('SECPanel')
        self.sec_plot_panel = wx.FindWindowByName('SECPlotPanel')

        self._raw_settings = self.main_frame.raw_settings

        self.filename = ''
        self.frame_list = []
        self._manual=False
        self.image_prefix = ""
        self.directory = ""
        self.initial_run_number = ""
        self.final_run_number = ""
        self.initial_frame_number = ""
        self.final_frame_number = ""
        self.initial_selected_frame = ""
        self.final_selected_frame = ""
        self.secm = None

        self.initial_buffer_frame=""
        self.final_buffer_frame=""
        self.window_size = "5"
        self._calculate = False
        self.right_axis_min = ""
        self.right_axis_max = ""
        self.plot_choice = 'RG'

        self.controlData = (  ('File :', parent.paramsInGui['Filename'], self.filename),
                              ('Frame List :', parent.otherParams['Frame List'], self.frame_list),
                              ('Manual', parent.otherParams['Manual'], self._manual),
                              ('Directory :', parent.paramsInGui['Directory'], self.directory),
                              ('Image Prefix :', parent.paramsInGui['Image Header'], self.image_prefix),
                              ('Initial Run # :', parent.paramsInGui['Initial Run #'], self.initial_run_number),
                              ('Final Run # :',parent.paramsInGui['Final Run #'], self.final_run_number),
                              ('Initial Frame # :', parent.paramsInGui['Initial Frame #'], self.initial_frame_number),
                              ('Final Frame # :',parent.paramsInGui['Final Frame #'], self.final_frame_number), 
                              ('Initial Selected Frame :', parent.paramsInGui['Initial Selected Frame'], self.initial_selected_frame),
                              ('Final Selected Frame :', parent.paramsInGui['Final Selected Frame'], self.final_selected_frame),
                              ('Calculate Structural Parameters :', parent.paramsInGui['Calculate'], self._calculate),
                              ('Initial Buffer Frame', parent.paramsInGui['Initial Buffer Frame'], self.initial_buffer_frame),
                              ('Final Buffer Frame', parent.paramsInGui['Final Buffer Frame'], self.final_buffer_frame),
                              ('Window Size :', parent.paramsInGui['Window Size'], self.window_size),
                              ('Plot : ', parent.paramsInGui['Plot Choice'], self.plot_choice),
                              ('Right Axis Min', parent.paramsInGui['Right Axis Min'], self.right_axis_min),
                              ('Right Axis Max', parent.paramsInGui['Right Axis Max'], self.right_axis_max))

        
        topsizer = self.createControls()
        
        self.currentExpObj = None
        
        self.SetSizer(topsizer)
        
    def createControls(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        cols = 6
        rows = 2
        fnum_sizer = wx.FlexGridSizer(cols = cols, rows = rows, vgap = 4, hgap = 4)
        fnum_sizer.SetFlexibleDirection(wx.HORIZONTAL)
        fnum_sizer.AddGrowableCol(0)
        fnum_sizer.AddGrowableCol(2)
        fnum_sizer.AddGrowableCol(4)
        fnum_sizer.AddGrowableCol(5)

        select_button = wx.Button(self, -1, 'Select file in SEC run')
        select_button.Bind(wx.EVT_BUTTON, self._onSelectButton)

        sizer.Add(select_button, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 4)

        # sizer.Add((1,1),0)
        # sizer.Add(select_button,0, wx.ALIGN_CENTER)
        # sizer.Add((1,1),0)
        # sizer.Add((1,1),0)
        
        for each in self.controlData:
            
            label = each[0]
            type = each[1][1]
            id = each[1][0]
                
            if type == 'imghdr':

                labelbox = wx.StaticText(self, -1, label)

                self.image_prefix_box=wx.TextCtrl(self, id=id, value=self.image_prefix, style = wx.TE_READONLY)

                img_sizer = wx.BoxSizer(wx.HORIZONTAL)

                img_sizer.Add(labelbox, 0, wx.ALIGN_RIGHT | wx.ALL, border = 2)
                img_sizer.Add(self.image_prefix_box, 2, wx.ALIGN_LEFT | wx.ALL, border = 2)
                img_sizer.AddStretchSpacer(1)
                sizer.Add(img_sizer, 0, flag = wx.EXPAND | wx.ALIGN_LEFT | wx.TOP, border = 4)

               
        #         ###################################
                
            elif type == 'irunnum':
                labelbox = wx.StaticText(self, -1, "Run : ")
                # labelbox2=wx.StaticText(self,-1," to ")

                self.initial_run_number_box = wx.TextCtrl(self, id=id, value=self.initial_run_number, size = (50,20), style = wx.TE_READONLY)

                run_sizer = wx.BoxSizer(wx.HORIZONTAL)



                run_sizer.AddStretchSpacer(0)
                run_sizer.Add(labelbox,0)
                run_sizer.Add(self.initial_run_number_box,2, wx.EXPAND)
                run_sizer.AddStretchSpacer(1)
                # run_sizer.AddStretchSpacer(3)
                # run_sizer.AddStretchSpacer(3)
                # fnum_sizer.Add(labelbox2,0)

                


            elif type == 'frunnum':
                # self.final_run_number_box = wx.TextCtrl(self, id=id, value=self.final_run_number, size = (50,20))

                # fnum_sizer.Add(self.final_run_number_box,1, wx.EXPAND)
                # fnum_sizer.AddStretchSpacer(3)
                pass
            
            elif type == 'iframenum':
                labelbox = wx.StaticText(self, -1, "Frames : ")
                labelbox2=wx.StaticText(self,-1," to ")

                self.initial_frame_number_box = wx.TextCtrl(self, id=id, value=self.initial_frame_number, size = (50,20), style = wx.TE_READONLY)

                # fnum_sizer.AddStretchSpacer(3)
                run_sizer.Add(labelbox,0)
                run_sizer.Add(self.initial_frame_number_box,2, wx.EXPAND)
                run_sizer.Add(labelbox2,0)

            elif type == 'fframenum':
                self.final_frame_number_box = wx.TextCtrl(self, id=id, value=self.final_frame_number, size = (50,20), style = wx.TE_READONLY)

                run_sizer.Add(self.final_frame_number_box,2, wx.EXPAND)
                # run_sizer.AddStretchSpacer(3)

                sizer.Add(run_sizer, 0, flag = wx.EXPAND | wx.ALIGN_LEFT | wx.TOP, border = 4)

        
        # sizer.Add(fnum_sizer, 1, flag = wx.EXPAND | wx.ALIGN_CENTER | wx.TOP, border = 4)

        load_button = wx.Button(self, -1, 'Load')
        load_button.Bind(wx.EVT_BUTTON, self._onLoadButton)

        update_button = wx.Button(self, -1, 'Update')
        update_button.Bind(wx.EVT_BUTTON, self._onUpdateButton)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        button_sizer.Add(load_button, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 4)
        button_sizer.AddSpacer((5,0))
        button_sizer.Add(update_button, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 4)

        sizer.Add(button_sizer, 1, flag = wx.ALIGN_CENTER | wx.TOP)

        line_sizer = wx.StaticLine(parent = self, style = wx.LI_HORIZONTAL)

        sizer.Add(line_sizer, 0, flag = wx.EXPAND | wx.LEFT | wx.RIGHT, border = 10)

        selected_sizer = wx.BoxSizer(wx.HORIZONTAL)

        selected_sizer.AddStretchSpacer(1)

        for each in self.controlData:
            
            label = each[0]
            type = each[1][1]
            id = each[1][0]

            if type == 'isframenum':

                labelbox = wx.StaticText(self, -1, "Select Data Frames : ")
                labelbox2 = wx.StaticText(self, -1, " To ")
                self.initial_selected_box = wx.TextCtrl(self, id, value = self.initial_selected_frame, size = (50,20))


                selected_sizer.Add(labelbox,0)
                selected_sizer.Add(self.initial_selected_box,1)
                selected_sizer.Add(labelbox2,0)

            elif type == 'fsframenum':
                self.final_selected_box = wx.TextCtrl(self, id, value = self.final_selected_frame, size = (50,20))
                selected_sizer.Add(self.final_selected_box,1)

        selected_sizer.AddStretchSpacer(1)

        sizer.Add(selected_sizer,0, flag = wx.EXPAND | wx.TOP | wx.ALIGN_CENTER, border = 12)

        
        ####
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        frames_plot_button = wx.Button(self, -1, 'Frames To Main Plot')
        frames_plot_button.Bind(wx.EVT_BUTTON, self._onFramesToMainPlot)
        average_plot_button = wx.Button(self, -1, 'Average To Main Plot')
        average_plot_button.Bind(wx.EVT_BUTTON, self._onAverageToMainPlot)

        
        button_sizer.Add(frames_plot_button, 0, flag = wx.ALIGN_CENTER | wx.TOP, border = 8)
        button_sizer.Add(average_plot_button, 0, flag = wx.ALIGN_CENTER | wx.TOP, border = 8)

        sizer.Add(button_sizer, 0, flag = wx.ALIGN_CENTER | wx.BOTTOM, border = 4)


        ####
        line_sizer2 = wx.StaticLine(parent = self, style = wx.LI_HORIZONTAL)
        sizer.Add(line_sizer2, 0, flag = wx.EXPAND | wx.LEFT | wx.RIGHT, border = 10)


        ####
        calc_heading_sizer = wx.BoxSizer(wx.HORIZONTAL)

        labelbox = wx.StaticText(self, -1, 'Calculate/Plot Structural Parameters :')

        calc_heading_sizer.AddStretchSpacer(1)
        calc_heading_sizer.Add(labelbox,0, flag=wx.ALIGN_CENTER)
        calc_heading_sizer.AddStretchSpacer(1)
        sizer.Add(calc_heading_sizer,0, flag = wx.EXPAND | wx.TOP | wx.ALIGN_CENTER, border = 8)

        average_sizer = wx.BoxSizer(wx.HORIZONTAL)

        for each in self.controlData:
            
            label = each[0]
            type = each[1][1]
            id = each[1][0]

            if type =='ibufframe':
                labelbox = wx.StaticText(self, -1, "Buffer Range : ")
                labelbox2=wx.StaticText(self,-1," To ")

                self.initial_buffer_box = wx.TextCtrl(self, id=id, value=self.initial_buffer_frame, size = (50,20))

                average_sizer.Add(labelbox,0)
                average_sizer.Add(self.initial_buffer_box,2, wx.EXPAND)
                average_sizer.Add(labelbox2,0)

            elif type =='fbufframe':
                self.final_buffer_box = wx.TextCtrl(self, id=id, value=self.final_buffer_frame, size = (50,20))

                average_sizer.Add(self.final_buffer_box,2, wx.EXPAND)
                average_sizer.AddStretchSpacer(1)

            elif type == 'wsize':
                labelbox3 = wx.StaticText(self, -1, label)

                self.window_size_box = wx.TextCtrl(self, id=id, value=self.window_size, size = (50,20))

                average_sizer.Add(labelbox3,0)
                average_sizer.Add(self.window_size_box,2, wx.EXPAND)

        sizer.Add(average_sizer,0, flag = wx.EXPAND | wx.TOP | wx.ALIGN_CENTER, border = 8)


        ####
        calc_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        calc_parameters_button = wx.Button(self, -1, 'Set/Update Parameters')
        calc_parameters_button.Bind(wx.EVT_BUTTON, self._onSetCalcParams)

        calc_button_sizer.Add(calc_parameters_button, 0, flag = wx.ALIGN_CENTER | wx.TOP, border = 8)

        sizer.Add(calc_button_sizer, 0, flag = wx.ALIGN_CENTER | wx.BOTTOM, border = 4)
                
        return sizer   


    def updateSECItem(self,secm):
        self.secm = secm
    
    
    def _onSelectButton(self, evt):    

        hdr_format = self._raw_settings.get('ImageHdrFormat')

        if hdr_format == 'G1, CHESS' or hdr_format == 'G1 WAXS, CHESS':
            fname = self.parent._CreateFileDialog(wx.OPEN)

            if fname == None:
                return

            try:
                sasm, img = SASFileIO.loadFile(fname, self.parent._raw_settings)
                    
            except (SASExceptions.UnrecognizedDataFormat, SASExceptions.WrongImageFormat), msg:
                img_fmt = self._raw_settings.get('ImageFormat')
                
                ascii = ' or any of the supported ASCII formats'

                
                wx.CallAfter(wx.MessageBox, 'The selected file: ' + fname + '\ncould not be recognized as a '   + str(img_fmt) +
                                 ' image format' + ascii + '.\n\nYou can change the image format under Advanced Options in the Options menu.' ,
                                  'Error loading file', style = wx.ICON_ERROR | wx.OK)
                fname = None
            except SASExceptions.HeaderLoadError, msg:
                wx.CallAfter(wx.MessageBox, str(msg), "Can't find Header file for selected image", style = wx.ICON_ERROR | wx.OK)
                fname = None
            except SASExceptions.MaskSizeError, msg:
                wx.CallAfter(wx.MessageBox, str(msg), 'Saved mask does not fit selected image', style = wx.ICON_ERROR)
                fname = None
            except SASExceptions.HeaderMaskLoadError, msg:
                wx.CallAfter(wx.MessageBox, str(msg), 'Mask information was not found in header', style = wx.ICON_ERROR)
                wx.CallAfter(self.main_frame.closeBusyDialog)
                return

            sasm = None
            img = None

            if fname != None:
                self.directory, self.filename = os.path.split(fname)
                # self.file_box.SetValue(self.filename)
                # self.directory_box.SetValue(self.directory)
                self._fillBoxes()

        else:
             wx.CallAfter(wx.MessageBox, 'The "%s" header format is not supported for automated SEC-SAXS file loading. You can use the "Plot SEC" button in the file window to plot any SEC-SAXS data. Please contact the RAW developers if you want to add automated loading support for a particular header format.' %(hdr_format) ,
                                      'Error loading file', style = wx.ICON_ERROR | wx.OK)

    def _onLoadButton(self,evt):
        file_list, frame_list = self._makeFileList()

        if len(file_list) > 0:

            mainworker_cmd_queue.put(['sec_plot', [file_list, frame_list, True]])

        else:
            wx.MessageBox("Can't find files to load", style=wx.ICON_ERROR | wx.OK)
        

    def _onUpdateButton(self,evt):
        #Need to add to this function to update the structural parameters

        if self.secm != None:
            old_frame_list = copy.copy(self.frame_list)
            self._fillBoxes()

            dif_frame_list = list(set(self.frame_list)-set(old_frame_list))

            dif_frame_list.sort(key=lambda frame: int(frame))

            # print dif_frame_list

            if len(dif_frame_list)>0:

              file_list, modified_frame_list = self._makeFileList(dif_frame_list)

            else:
                file_list=[]

            # print file_list

            if len(file_list) > 0:
                mainworker_cmd_queue.put(['update_secm', [file_list, modified_frame_list, self.secm]])


    def _onFramesToMainPlot(self,evt):
        ######################## NEEDS TO ADD ITEMS TO LEGEND ############################
        self._updateControlValues()

        sasm_list=[]

        selected_item = self.sec_panel.getDataItem()

        if len(self.initial_selected_frame)>0 and len(self.final_selected_frame)>0 and len(self.sec_panel.all_manipulation_items) > 0:

            if len(self.sec_panel.all_manipulation_items) == 1:

                secm = self.sec_panel.all_manipulation_items[0].secm

                sasm_list = secm.getSASMList(self.initial_selected_frame, self.final_selected_frame)

            elif len(self.sec_panel.all_manipulation_items)>1:

                if selected_item != None:
                    secm = selected_item.secm
                    sasm_list = secm.getSASMList(self.initial_selected_frame, self.final_selected_frame)

                else:
                    msg = "To send data to the main plot, select a SEC curve by starring it."
                    wx.CallAfter(wx.MessageBox, msg, "No SEC curve selected", style = wx.ICON_ERROR | wx.OK)
                # print 'test'

        elif len(self.sec_panel.all_manipulation_items) > 0:
            msg = "To send data to the main plot, enter a valid frame range (missing start or end frame)."
            wx.CallAfter(wx.MessageBox, msg, "Invalid frame range", style = wx.ICON_ERROR | wx.OK)

        if len(sasm_list)>0:
            if secm.axes.xaxis.get_label_text() == 'Time (s)':
                msg = "Warning: Plot is displaying time. Make sure frame #s, not time, are selected to send to plot. Proceed?"
                dlg = wx.MessageDialog(self.main_frame, msg, "Verify Frame Range", style = wx.ICON_QUESTION | wx.YES_NO)
                proceed = dlg.ShowModal()
                dlg.Destroy()
            else:
                proceed = wx.ID_YES

            if proceed == wx.ID_YES:
                # wx.CallAfter(self.main_frame.showBusyDialog, 'Please wait while sending frames to plot...')
                mainworker_cmd_queue.put(['to_plot_SEC', sasm_list])
                # wx.CallAfter(self.main_frame.closeBusyDialog) 

    def _onAverageToMainPlot(self,evt):
        ######################## NEEDS TO ADD ITEMS TO LEGEND ############################
        self._updateControlValues()

        sasm_list=[]

        selected_item = self.sec_panel.getDataItem()

        if len(self.initial_selected_frame)>0 and len(self.final_selected_frame)>0 and len(self.sec_panel.all_manipulation_items) > 0:

            if len(self.sec_panel.all_manipulation_items) == 1:

                secm = self.sec_panel.all_manipulation_items[0].secm

                sasm_list = secm.getSASMList(self.initial_selected_frame, self.final_selected_frame)

            elif len(self.sec_panel.all_manipulation_items)>1:

                if selected_item != None:
                    secm = selected_item.secm
                    sasm_list = secm.getSASMList(self.initial_selected_frame, self.final_selected_frame)

                else:
                    msg = "To send data to the main plot, select a SEC curve by starring it."
                    wx.CallAfter(wx.MessageBox, msg, "No SEC curve selected", style = wx.ICON_ERROR | wx.OK)
                # print 'test'

        elif len(self.sec_panel.all_manipulation_items) > 0:
            msg = "To send data to the main plot, enter a valid frame range (missing start or end frame)."
            wx.CallAfter(wx.MessageBox, msg, "Invalid frame range", style = wx.ICON_ERROR | wx.OK)

        if len(sasm_list)>0:

            if secm.axes.xaxis.get_label_text() == 'Time (s)':
                msg = "Warning: Plot is displaying time. Make sure frame #s, not time, are selected to send to plot. Proceed?"
                dlg = wx.MessageDialog(self.main_frame, msg, "Verify Frame Range", style = wx.ICON_QUESTION | wx.YES_NO)
                proceed = dlg.ShowModal()
                dlg.Destroy()
            else:
                proceed = wx.ID_YES

            if proceed == wx.ID_YES:
                mainworker_cmd_queue.put(['average_items_sec', sasm_list])

    def _onSetCalcParams(self, event):
        ibufId = self._findWindowId('ibufframe')
        fbufId = self._findWindowId('fbufframe')
        wsizeId = self._findWindowId('wsize')

        ibufWindow = wx.FindWindowById(ibufId)
        fbufWindow = wx.FindWindowById(fbufId)
        wsizeWindow = wx.FindWindowById(wsizeId)

        try:
            initial_frame = int(ibufWindow.GetValue())
        except:
            msg = "Invalid value for initial buffer frame."
            wx.CallAfter(wx.MessageBox, msg, "Invalid frame range", style = wx.ICON_ERROR | wx.OK)
            return
        try:
            final_frame = int(fbufWindow.GetValue())
        except:
            msg = "Invalid value for final buffer frame."
            wx.CallAfter(wx.MessageBox, msg, "Invalid frame range", style = wx.ICON_ERROR | wx.OK)
            return
        try:
            window = int(wsizeWindow.GetValue())
        except:
            msg = "Invalid value for sliding window size."
            wx.CallAfter(wx.MessageBox, msg, "Invalid window size", style = wx.ICON_ERROR | wx.OK)
            return

        if initial_frame > final_frame:
            msg = "Initial buffer frame cannot be greater than final buffer frame."
            wx.CallAfter(wx.MessageBox, msg, "Invalid frame range", style = wx.ICON_ERROR | wx.OK)
            return
        elif initial_frame <0:
            msg = "Initial buffer frame cannot be less than zero."
            wx.CallAfter(wx.MessageBox, msg, "Invalid frame range", style = wx.ICON_ERROR | wx.OK)
            return
        elif window <1:
            msg = "Sliding window size cannot be less than one."
            wx.CallAfter(wx.MessageBox, msg, "Invalid window size", style = wx.ICON_ERROR | wx.OK)
            return

        if self.sec_plot_panel.subplot1.xaxis.get_label_text() == 'Time (s)':
            msg = "Warning: Plot is displaying time. Make sure frame #s, not time, are selected to use as buffer. Set values anyways?"
            dlg = wx.MessageDialog(self.main_frame, msg, "Verify Frame Range", style = wx.ICON_QUESTION | wx.YES_NO)
            proceed = dlg.ShowModal()
            dlg.Destroy()
        else:
            proceed = wx.ID_YES

        if proceed == wx.ID_NO:
            return

        
        selected_item = self.sec_panel.getDataItem()

        if len(self.sec_panel.all_manipulation_items) == 0:
            wx.MessageBox("SEC-SAXS data must be loaded to set parameters.", style=wx.ICON_ERROR | wx.OK)
            return
        elif len(self.sec_panel.all_manipulation_items)>1 and selected_item == None:
            wx.MessageBox("Star the SEC-SAXS item for which you wish to set the parameters.", style=wx.ICON_ERROR | wx.OK)
            return
        elif len(self.sec_panel.all_manipulation_items)>1:
            secm = selected_item.secm
        else:
            secm = self.sec_panel.all_manipulation_items[0].secm

        frame_list = secm.frame_list

        # print frame_list

        if len(numpy.where(initial_frame==frame_list)[0]) == 0:
            msg = "Invalid value for intial buffer frame, it must be in the data set."
            wx.CallAfter(wx.MessageBox, msg, "Invalid frame range", style = wx.ICON_ERROR | wx.OK)
            return
        elif len(numpy.where(final_frame==frame_list)[0]) == 0:
            msg = "Invalid value for final buffer frame, it must be in the data set."
            wx.CallAfter(wx.MessageBox, msg, "Invalid frame range", style = wx.ICON_ERROR | wx.OK)
            return
        elif window > len(frame_list):
            msg = "Invalid value for sliding window size, it must be smaller than the data set."
            wx.CallAfter(wx.MessageBox, msg, "Invalid window size", style = wx.ICON_ERROR | wx.OK)
            return

        self.initial_buffer_frame = initial_frame
        self.final_buffer_frame = final_frame
        self.window_size = window

        newParams = secm.setCalcParams(self.initial_buffer_frame, self.final_buffer_frame, self.window_size)

        secm.item_panel.updateInfoTip()
        secm.item_panel.markAsModified()

        if newParams:
            mainworker_cmd_queue.put(['calculate_params_sec', secm])


    def _findWindowId(self,type):
        id=-1

        for item in self.controlData:
            item_type = item[1][1]
            item_id = item[1][0]

            if type == item_type:
                id = item_id

        return id


    def _updateControlValues(self):

        for parameter in self.controlData:

            # print parameter

            label = parameter[0]
            ptype = parameter[1][1]
            pid = parameter[1][0]
            # pvalue = parameter[2]

            # print label
            # print ptype
            # print pid
            # print pvalue
            if ptype != 'framelist':
                data = wx.FindWindowById(pid)

                if ptype == 'imghdr':
                    self.image_prefix = data.GetValue()

                elif ptype == 'irunnum':
                    self.initial_run_number = data.GetValue()

                # elif ptype == 'frunnum':
                #     self.final_run_number = data.GetValue()

                elif ptype == 'iframenum':
                    self.initial_frame_number = data.GetValue()

                elif ptype == 'fframenum':
                    self.final_frame_number = data.GetValue()

                elif ptype == 'isframenum':
                    self.initial_selected_frame = data.GetValue()

                elif ptype == 'fsframenum':
                    self.final_selected_frame = data.GetValue()

    
    def _updateCalcValues(self):
        for parameter in self.controlData:

            label = parameter[0]
            ptype = parameter[1][1]
            pid = parameter[1][0]

            if ptype != 'framelist' and ptype !='manual':
                data = wx.FindWindowById(pid)

                if ptype =='ibufframe':
                    self.initial_buffer_frame = data.GetValue()

                elif ptype == 'fbufframe':
                    self.final_buffer_frame = data.GetValue()

                elif ptype == 'wsize':
                    self.window_size = data.GetValue()

                elif ptype == 'choice':
                    self.plot_choice = data.GetString(data.GetCurrentSelection())

                elif ptype == 'raxismin':
                    self.right_axis_min = data.GetValue()

                elif ptype == 'raxismax':
                    self.right_axis_max = data.GetValue()

    def _makeFileList(self,modified_frame_list=[]):

        self._updateControlValues()

        file_list = []

        if len(modified_frame_list) == 0 :
            modified_frame_list = copy.copy(self.frame_list)

            # print modified_frame_list

        hdr_format = self._raw_settings.get('ImageHdrFormat')

        if hdr_format == 'G1, CHESS' or hdr_format == 'G1 WAXS, CHESS':

            if self.image_prefix != '' or self.filename != '':
                for frame in modified_frame_list:
                    name = os.path.join(self.directory, '%s_%s_%s' %(self.image_prefix, self.initial_run_number, frame))
                    # print name
                    if os.path.isfile(name+'.dat'):
                        file_list.append(name+'.dat')
                    elif os.path.isfile(name+'.tiff'):
                        file_list.append(name+'.tiff')
                    else:
                        files = glob.glob(name+'.*')
                        if len(files)>0:
                            file_list.append(f[0])
                        else:
                            modified_frame_list.pop(self.frame_list.index(frame))

        return file_list, modified_frame_list

        # if self.image_prefix != '' or self.filename != '':
        #     rfill=len(self.initial_run_number)

        #     for run in range(int(self.initial_run_number), int(self.final_run_number)+1):
        #         for frame in frame_list:


    def _fillBoxes(self):

        hdr_format = self._raw_settings.get('ImageHdrFormat')

        if hdr_format == 'G1, CHESS' or hdr_format == 'G1 WAXS, CHESS':

            if self.filename != '':

                count_filename, run_number, frame_number = SASFileIO.parseCHESSG1Filename(os.path.join(self.directory, self.filename))

                # print count_filename

                filelist=glob.glob(count_filename + '_' + run_number + '_*')

                self.frame_list = self._getFrameList(filelist)

                junk, self.image_prefix = os.path.split(count_filename)

                self.image_prefix_box.SetValue(self.image_prefix)

                self.initial_run_number = run_number

                self.initial_run_number_box.SetValue(run_number)

                # self.final_run_number_box.SetValue(run_number)

                self.initial_frame_number = self.frame_list[0]

                self.initial_frame_number_box.SetValue(self.initial_frame_number)

                self.final_selected_frame = self.frame_list[-1]
                    
                self.final_frame_number_box.SetValue(self.final_selected_frame)

                self._updateControlValues


    def _getFrameList(self, filelist):

        framelist=[]

        hdr_format = self._raw_settings.get('ImageHdrFormat')

        if hdr_format == 'G1, CHESS' or hdr_format == 'G1 WAXS, CHESS':
            
            for f in filelist:
                frame=SASFileIO.parseCHESSG1Filename(f)[2]
                # print frame

                framelist.append(frame)

            framelist=list(set(framelist))

            framelist.sort(key=lambda frame: int(frame))


        return framelist
            

    def clearAll(self):
        for each in self.controlData:
            label = each[0]
            type = each[1][1]
            id = each[1][0]

            if type != 'framelist' and type != 'manual' and type != 'filename' and type != 'dir' and type != 'frunnum' and type != 'wsize' and type != 'calc' and type != 'choice' and type != 'calc':
                infobox = wx.FindWindowById(id)
                infobox.SetValue('')
            elif type == 'framelist':
                self.frame_list=[]
            elif type == 'wsize':
                infobox = wx.FindWindowById(id)
                infobox.SetValue('5')
            elif type == 'choice':
                infobox = wx.FindWindowById(id)
                infobox.SetSelection(0)

            # else:
            #     infobox = wx.FindWindowById(id)
            #     infobox.SetValue(False)

        self.secm=None
        self._calculate = False

        self._updateControlValues
        self._updateCalcValues()


#--- ** Centering Panel **

class MaskingPanel(wx.Panel):
    
    def __init__(self, parent,id):
        
        wx.Panel.__init__(self, parent, id, name = 'MaskingPanel')
        
        self.mask_choices = {'Beamstop mask' : 'BeamStopMask',
                             'Readout-Dark mask' : 'ReadOutNoiseMask',
                             'ROI Counter mask' : 'TransparentBSMask',
                             'SAXSLAB BS mask' : 'SaxslabBSMask'}
        
        self.CIRCLE_ID, self.RECTANGLE_ID, self.POLYGON_ID = wx.NewId(), wx.NewId(), wx.NewId()
        self.all_button_ids = [self.CIRCLE_ID, self.RECTANGLE_ID, self.POLYGON_ID]
        
        self._main_frame = wx.FindWindowByName('MainFrame')
        self.image_panel = wx.FindWindowByName('ImagePanel')
        
        self._initBitmaps()
        manual_box = wx.StaticBox(self, -1, 'Mask Drawing')
        self.manual_boxsizer = wx.StaticBoxSizer(manual_box)
        self.manual_boxsizer.Add((1,1), 1, wx.EXPAND)
        self.manual_boxsizer.Add(self._createDrawButtons(), 0, wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        self.manual_boxsizer.Add((1,1), 1, wx.EXPAND)
        
        auto_box = wx.StaticBox(self, -1, 'Mask Creation')
        auto_boxsizer = wx.StaticBoxSizer(auto_box)
        auto_boxsizer.Add(self._createMaskSelector(), 1, wx.EXPAND |wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        
        option_box = wx.StaticBox(self, -1, 'Mask Drawing Options')
        option_boxsizer = wx.StaticBoxSizer(option_box)
        option_boxsizer.Add(self._createMaskOptions(), 1, wx.EXPAND |wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        
        button_sizer = self._createButtonSizer()
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.manual_boxsizer, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(option_boxsizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self.sizer.Add(auto_boxsizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self.sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        
        self.SetSizer(self.sizer)
        
        self._center = [0,0]
        self.show_center = False
        #self.updateCenterFromSettings()
        
    def setTool(self, tool):
        self.image_panel.setTool(tool)
        
    def _createDrawButtons(self):
        
        sizer = wx.BoxSizer()
    
        self.circle_button = wxbutton.GenBitmapToggleButton(self, self.CIRCLE_ID, self.circle_bmp, size = (80,80))
        self.rectangle_button = wxbutton.GenBitmapToggleButton(self, self.RECTANGLE_ID, self.rectangle_bmp, size = (80,80))
        self.polygon_button = wxbutton.GenBitmapToggleButton(self, self.POLYGON_ID, self.polygon_bmp, size = (80,80))
        
        self.circle_button.Bind(wx.EVT_BUTTON, self._onDrawButton)
        self.rectangle_button.Bind(wx.EVT_BUTTON, self._onDrawButton)
        self.polygon_button.Bind(wx.EVT_BUTTON, self._onDrawButton)
        
        self.circle_button.Bind(wx.EVT_BUTTON, self._onDrawButton)
        self.rectangle_button.Bind(wx.EVT_BUTTON, self._onDrawButton)
        self.polygon_button.Bind(wx.EVT_BUTTON, self._onDrawButton)
        sizer.Add(self.circle_button, 0)
        sizer.Add(self.rectangle_button,0)
        sizer.Add(self.polygon_button,0)
        
        
        save_button= wx.Button(self, -1, "Save")
        save_button.Bind(wx.EVT_BUTTON, self._onSaveMaskToFile)
        
        load_button= wx.Button(self, -1, "Load")
        load_button.Bind(wx.EVT_BUTTON, self._onLoadMaskFromFile)
        
        clear_button= wx.Button(self, -1, "Clear")
        clear_button.Bind(wx.EVT_BUTTON, self._onClearDrawnMasks)
        
        button_sizer = wx.BoxSizer()
        button_sizer.Add(save_button, 0, wx.RIGHT, 3)
        button_sizer.Add(load_button, 0, wx.RIGHT, 3)
        button_sizer.Add(clear_button, 0)
        
        
        final_sizer = wx.BoxSizer(wx.VERTICAL)
        
        final_sizer.Add(sizer,0)
        final_sizer.Add(button_sizer,0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)
        
        return final_sizer
    
    def _createMaskOptions(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        center_chkbox = wx.CheckBox(self, -1, 'Show Beam Center')
        center_chkbox.Bind(wx.EVT_CHECKBOX, self._onShowCenterChkbox)
    
        sizer.Add(center_chkbox, 0)
        #sizer.Add(button_sizer,0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 5)
            
        return sizer
        
    def _onShowCenterChkbox(self, event):
        
        x_c = self._main_frame.raw_settings.get('Xcenter')
        y_c = self._main_frame.raw_settings.get('Ycenter')
        
        cent = (x_c, y_c)
        
        chkbox = event.GetEventObject()
        
        if chkbox.GetValue() == True:
            self.show_center = True
            wx.CallAfter(self.image_panel.drawCenterPatch, cent)
        else:
            self.show_center = False
            wx.CallAfter(self.image_panel.removeCenterPatch)
    
    def _createMaskSelector(self):
        
        sizer = wx.BoxSizer()

        self.selector_choice = wx.Choice(self, -1, choices = self.mask_choices.keys())
        self.selector_choice.Select(2)
        
        set_button = wx.Button(self, -1, 'Set', size = (60,-1))
        set_button.Bind(wx.EVT_BUTTON, self._onSetButton)
        
        clear_button = wx.Button(self, -1, 'Remove', size = (65,-1))
        clear_button.Bind(wx.EVT_BUTTON, self._onClearButton)
        
        show_button = wx.Button(self, -1, 'Show', size = (60,-1))
        show_button.Bind(wx.EVT_BUTTON, self._onShowButton)
        
        sizer.Add(self.selector_choice, 1, wx.EXPAND | wx.RIGHT, 5)
        sizer.Add(clear_button, 0)
        sizer.Add(set_button,0)
        sizer.Add(show_button,0)
        
        return sizer
    
    def _calcSaxslabBSMask(self):
        sasm = self.image_panel.current_sasm
        
        img_hdr = sasm.getParameter('imageHeader')
        img = self.image_panel.img
        
        if img != None and img_hdr != None:
            mask_params = SASImage.createMaskFromHdr(img, img_hdr, flipped = self._main_frame.raw_settings.get('DetectorFlipped90'))
        
        print mask_params
        print mask_params[0]._points
        print mask_params[0]._radius
        #mask_params contains the mask and the individual maskshapes
                
        return [None, mask_params]
    
    def _onShowButton(self, event):
        selected_mask = self.selector_choice.GetStringSelection()
        mask_key = self.mask_choices[selected_mask]
        
        plot_parameters = self.image_panel.getPlotParameters()        
        mask_dict = self._main_frame.raw_settings.get('Masks')
            
        if mask_key == 'SaxslabBSMask':
            mask_params = self._calcSaxslabBSMask()
        else:    
            mask_params = mask_dict[mask_key]
        
        saved_mask = mask_params[1]
        
        masks_copy = []     # Need to copy the masks to new objects, ortherwise all kinds of strange things happen
                            # when you switch between masks or modify masks.
        
        if saved_mask != None:
            for each in saved_mask:
                masks_copy.append(copy.copy(each))
            plot_parameters['storedMasks'] = masks_copy
            wx.CallAfter(self.image_panel.plotStoredMasks)
        else:
            wx.CallAfter(self.image_panel.clearAllMasks)
            wx.MessageBox('No mask has been set for this mask type.', 'No mask set.', style = wx.ICON_EXCLAMATION)
    
    def _onSetButton(self, event):
        
        selected_mask = self.selector_choice.GetStringSelection()
        
        if selected_mask != '':
            mask_key = self.mask_choices[selected_mask]
            
            mask_dict = self._main_frame.raw_settings.get('Masks')
            
            if mask_dict[mask_key][1] != None:
                dial = wx.MessageDialog(None, 'Do you want to overwrite the existing mask?', 'Overwrite exisiting mask?', 
                                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                answer = dial.ShowModal()

                if answer == wx.ID_NO:
                    return
            
            plot_parameters = self.image_panel.getPlotParameters()
            masks = plot_parameters['storedMasks']
            masks_copy = []
            
            for each in masks:
                masks_copy.append(copy.copy(each))
            
            if masks == [] or self.image_panel.img == None:
                wx.MessageBox('No masks has been drawn. Draw a mask before setting it as the current mask.', 'Setting mask failed') 
                return
            
            img_dim = self.image_panel.img.shape
    
            if len(masks) != 0:
                queue = self._main_frame.getWorkerThreadQueue()
                queue.put(['create_mask', [mask_key, masks_copy, img_dim]])
                            
        
    def _onClearButton(self, event):
        
        selected_mask = self.selector_choice.GetStringSelection()
        
        if selected_mask != '':
            
            dial = wx.MessageDialog(None, 'Are you sure you want to delete this mask?', 'Are you sure?', 
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            answer = dial.ShowModal()

            if answer == wx.ID_NO:
                return
            
            mask_key = self.mask_choices[selected_mask]
            mask_dict = self._main_frame.raw_settings.get('Masks')
            mask_dict[mask_key] = [None, None]
            self.image_panel.clearAllMasks()
    
    def _onClearDrawnMasks(self, event):
        wx.CallAfter(self.image_panel.clearAllMasks)
    
    def _onLoadMaskFromFile(self, event):
        file = self._createFileDialog(wx.OPEN)
        
        if file:
            queue = self._main_frame.getWorkerThreadQueue()
            queue.put(['load_mask', [file]])
    
    def _onSaveMaskToFile(self, event):
        
        file = self._createFileDialog(wx.SAVE)
        
        if file:
            plot_parameters = self.image_panel.getPlotParameters()
            masks = plot_parameters['storedMasks']
            masks_copy = []
        
            for each in masks:
                masks_copy.append(copy.copy(each))
        
            queue = self._main_frame.getWorkerThreadQueue()
            queue.put(['save_mask', [file, masks_copy]])
    
    def _onDrawButton(self, event):
        button = event.GetEventObject()
        id = button.GetId()
        
        if button.GetToggle():
            self.disableDrawButtons(id)
            
            if self.CIRCLE_ID == id:
                self.setTool('circle')
            elif self.RECTANGLE_ID == id:
                self.setTool('rectangle')
            elif self.POLYGON_ID == id:
                self.setTool('polygon')
                    
    def disableDrawButtons(self, id = None):
        for each in self.all_button_ids:
                if each != id:
                    wx.FindWindowById(each).SetToggle(False)
        
    def _createButtonSizer(self):
        sizer = wx.BoxSizer()
        
        ok_button = wx.Button(self, wx.ID_OK, 'OK')
        #cancel_button = wx.Button(self, wx.ID_CANCEL, 'Cancel')
        
        sizer.Add(ok_button, 0, wx.RIGHT, 10)
        #sizer.Add(cancel_button, 0)
        
        ok_button.Bind(wx.EVT_BUTTON, self._onOkButton)
        #cancel_button.Bind(wx.EVT_BUTTON, self._onCancelButton)
    
        return sizer
    
    def _onOkButton(self, event):
        self.image_panel.stopMaskCreation()
        wx.CallAfter(self.image_panel.clearAllMasks)
        wx.CallAfter(self._main_frame.closeMaskingPane)
    
    def _onCancelButton(self, event):
        self.image_panel.stopMaskCreation()
        wx.CallAfter(self._main_frame.closeMaskingPane)
        wx.CallAfter(self.image_panel.clearAllMasks)
    
    def updateView(self):
        wx.CallAfter(self.image_panel.clearPatches)
        if self.show_center:
            x_c = self._main_frame.raw_settings.get('Xcenter')
            y_c = self._main_frame.raw_settings.get('Ycenter')
        
            cent = (x_c, y_c)
            wx.CallAfter(self.image_panel.drawCenterPatch, cent)
             
    def _createFileDialog(self, mode):
         
        file = None
        
        path = wx.FindWindowByName('FileListCtrl').path
        
        if mode == wx.OPEN:
            filters = 'Mask files (*.msk)|*.msk|All files (*.*)|*.*'
            dialog = wx.FileDialog( None, style = mode, wildcard = filters, defaultDir = path)
        if mode == wx.SAVE:
            filters = 'Mask files (*.msk)|*.msk'
            dialog = wx.FileDialog( None, style = mode | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = path)        
        
        # Show the dialog and get user input
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetPath()
            
        # Destroy the dialog
        dialog.Destroy()
        
        return file
    
    def _initBitmaps(self):
        
        workdir = self._main_frame.RAWWorkDir
        
        self.circle_bmp = RAWIcons.CircleIcon.GetBitmap()
        self.rectangle_bmp = RAWIcons.RectangleIcon.GetBitmap()
        self.polygon_bmp = RAWIcons.PolygonIcon3.GetBitmap()

class CenteringPanel(wx.Panel):
    
    
    def __init__(self, parent,id):
        
        wx.Panel.__init__(self, parent, id, name = 'CenteringPanel')
        
        self.ID_UP, self.ID_DOWN, self.ID_RIGHT, self.ID_LEFT, self.ID_TARGET =  ( wx.NewId(), wx.NewId(), wx.NewId(), wx.NewId(), wx.NewId())
        
        self._x_center = None
        self._y_center = None
        self._repeat_timer = wx.Timer()
        self._repeat_timer.Bind(wx.EVT_TIMER, self._onRepeatTimer)
        
        self.manual_widget_list = []
        
        self._main_frame = wx.FindWindowByName('MainFrame')
        self.image_panel = wx.FindWindowByName('ImagePanel')
        
        self._initBitmaps()
        manual_box = wx.StaticBox(self, -1, 'Manual Center/Calibration Adjustments')
        self.manual_boxsizer = wx.StaticBoxSizer(manual_box)
        
        button_sizer = self._createCenteringButtonsSizer()
        info_sizer = self._createCenteringInfoSizer()
        
        self.manual_boxsizer.Add(info_sizer, 0, wx.ALL, 5)
        self.manual_boxsizer.Add((1,1), 1, wx.EXPAND)
        self.manual_boxsizer.Add(button_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.RIGHT, 15)
        
        auto_box = wx.StaticBox(self, -1, 'Automatic Centering')
        auto_boxsizer = wx.StaticBoxSizer(auto_box)
        
        auto_sizer = self._createAutoCenteringSizer()
        auto_boxsizer.Add(auto_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        button_sizer = self._createButtonSizer()
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.manual_boxsizer, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(auto_boxsizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self.sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        
        self.SetSizer(self.sizer)
        
        self._center = [0,0]
        self.updateCenterFromSettings()
        wx.CallAfter(self._updateAgbeRings)
                
    def _initBitmaps(self):
        
        workdir = self._main_frame.RAWWorkDir
        
        self.up_arrow_img = RAWIcons.center_arrow_up.GetImage()
        self.right_arrow_img = self.up_arrow_img.Rotate90()
        self.down_arrow_img = self.right_arrow_img.Rotate90()
        self.left_arrow_img = self.down_arrow_img.Rotate90()
        
        self.up_arrow_bmp = self.up_arrow_img.ConvertToBitmap()
        self.right_arrow_bmp = self.right_arrow_img.ConvertToBitmap()
        self.down_arrow_bmp = self.down_arrow_img.ConvertToBitmap()
        self.left_arrow_bmp = self.left_arrow_img.ConvertToBitmap()
        
        self.target_bmp = RAWIcons.center_target.GetBitmap()
    
    def _createAutoCenteringSizer(self):
        
        sizer = wx.BoxSizer()
        
        choices = ['Silver-Behenate']
        
        self.method_text = wx.StaticText(self, -1, 'Method:')
        
        self.auto_method_choice = wx.Choice(self, -1, choices = choices)
        self.auto_method_choice.Select(0)
        
        method_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        method_sizer.Add(self.method_text,0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        method_sizer.Add(self.auto_method_choice, 0)
        
        self.auto_start_button = wx.Button(self, -1, 'Start')
        self.auto_start_button.Bind(wx.EVT_BUTTON, self._onAutoCenterStartButton)
        
        #Automatic centering doesn't work on compiled versions!
        #self.auto_start_button.Enable(False)
        
        sizer.Add(method_sizer,0, wx.RIGHT, 10)
        sizer.Add((1,1), 1, wx.EXPAND)
        sizer.Add(self.auto_start_button,0)
        
        return sizer
    
    def _createCenteringButtonsSizer(self):
        
        buttonsizer = wx.FlexGridSizer(rows = 3, cols = 3)
        
        up_button = wx.BitmapButton(self, self.ID_UP, self.up_arrow_bmp)
        down_button = wx.BitmapButton(self,self.ID_DOWN, self.down_arrow_bmp)
        right_button = wx.BitmapButton(self, self.ID_RIGHT , self.right_arrow_bmp)
        left_button = wx.BitmapButton(self, self.ID_LEFT, self.left_arrow_bmp)
        target_button = wx.BitmapButton(self, self.ID_TARGET, self.target_bmp)
        
        up_button.Bind(wx.EVT_LEFT_DOWN, self._onCenteringButtons)
        down_button.Bind(wx.EVT_LEFT_DOWN, self._onCenteringButtons)
        right_button.Bind(wx.EVT_LEFT_DOWN, self._onCenteringButtons)
        left_button.Bind(wx.EVT_LEFT_DOWN, self._onCenteringButtons)
        
        up_button.Bind(wx.EVT_LEFT_UP, self._onCenteringButtonsUp)
        down_button.Bind(wx.EVT_LEFT_UP, self._onCenteringButtonsUp)
        right_button.Bind(wx.EVT_LEFT_UP, self._onCenteringButtonsUp)
        left_button.Bind(wx.EVT_LEFT_UP, self._onCenteringButtonsUp)
        
        
        target_button.Bind(wx.EVT_BUTTON, self._onTargetButton)
        
        buttonsizer.Add((1,1))
        buttonsizer.Add(up_button, 0)
        buttonsizer.Add((1,1))
        buttonsizer.Add(left_button,0)
        buttonsizer.Add(target_button, 0)
        buttonsizer.Add(right_button, 0)
        buttonsizer.Add((1,1))
        buttonsizer.Add(down_button, 0)
        buttonsizer.Add((1,1))
        
        self.manual_widget_list.append(up_button)
        self.manual_widget_list.append(down_button)
        self.manual_widget_list.append(left_button)
        self.manual_widget_list.append(right_button)
        self.manual_widget_list.append(target_button)
        
        return buttonsizer
    
    def _createCenteringInfoSizer(self):
        
        info_sizer = wx.BoxSizer()
        
        step_list= ['0.1', '1', '2', '5', '10', '20', '50', '100', '500']
        pattern_list = ['None', 'Silver-Behenate']
        
        self._x_cent_text = wx.TextCtrl(self, -1, '0', size = (65, -1), style = wx.TE_PROCESS_ENTER)
        self._y_cent_text = wx.TextCtrl(self, -1, '0', size = (65, -1), style = wx.TE_PROCESS_ENTER)
        self._y_cent_text.Bind(wx.EVT_TEXT_ENTER, self._onEnterInCenterCtrl)
        self._x_cent_text.Bind(wx.EVT_TEXT_ENTER, self._onEnterInCenterCtrl)
        self._x_cent_text.Bind(wx.EVT_KILL_FOCUS, self._onEnterInCenterCtrl)
        self._y_cent_text.Bind(wx.EVT_KILL_FOCUS, self._onEnterInCenterCtrl)
        
        # self._step_combo = wx.ComboBox(self, -1, choices = step_list, size = self._x_cent_text.GetSize())
        self._step_combo = wx.ComboBox(self, -1, choices = step_list)
        self._step_combo.Select(1)
        
        self._wavelen_text = RAWCustomCtrl.FloatSpinCtrl(self, -1, TextLength = 80)
        self._pixel_text = RAWCustomCtrl.FloatSpinCtrl(self, -1, TextLength = 80)
        self._sd_text = RAWCustomCtrl.FloatSpinCtrl(self, -1, TextLength = 80)
        
        self._sd_text.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onSampDetDistSpin)
        self._wavelen_text.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onPixelWavelengthChange)
        self._pixel_text.Bind(RAWCustomCtrl.EVT_MY_SPIN, self._onPixelWavelengthChange)
                
        self._pattern_list = wx.Choice(self, -1, choices = pattern_list)
        self._pattern_list.Select(1)
        self._pattern_list.Bind(wx.EVT_CHOICE, self._onPatternChoice)
        
        wavelen_label = wx.StaticText(self, -1, 'Wavelength:')
        sd_label = wx.StaticText(self, -1, 'Sample-Detector Distance:')
        pixel_label = wx.StaticText(self, -1, 'Detector Pixel Size:')
        
        ylabel = wx.StaticText(self, -1, 'Y center:')
        xlabel = wx.StaticText(self, -1, 'X center:')
        step_label = wx.StaticText(self, -1, 'Steps:')
        pattern_label = wx.StaticText(self, -1, 'Pattern:')
        
        sd_unit_label = wx.StaticText(self, -1, 'mm')
        pixelsize_unit_label = wx.StaticText(self, -1, 'um')
        wavelength_unit_label = wx.StaticText(self, -1, 'A')
        
        x_sizer = wx.BoxSizer(wx.VERTICAL)
        y_sizer = wx.BoxSizer(wx.VERTICAL)
        step_sizer = wx.BoxSizer(wx.VERTICAL)
        wave_sizer = wx.BoxSizer(wx.VERTICAL)
        pixel_sizer = wx.BoxSizer(wx.VERTICAL)
        sd_sizer = wx.BoxSizer(wx.VERTICAL)
        pattern_sizer = wx.BoxSizer(wx.VERTICAL)
    
        sd_unit_sizer = wx.BoxSizer()
        pixelsize_unit_sizer = wx.BoxSizer()
        wavelength_unit_sizer = wx.BoxSizer()
    
        step_sizer.Add(step_label,0, wx.TOP,-1)
        step_sizer.Add(self._step_combo, 0)
        x_sizer.Add(xlabel, 0)
        x_sizer.Add(self._x_cent_text,0)        
        y_sizer.Add(ylabel, 0)
        y_sizer.Add(self._y_cent_text,0)
    
        sd_unit_sizer.Add(self._sd_text, 0, wx.RIGHT, 5)
        sd_unit_sizer.Add(sd_unit_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        pixelsize_unit_sizer.Add(self._pixel_text, 0, wx.RIGHT, 5)
        pixelsize_unit_sizer.Add(pixelsize_unit_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        wavelength_unit_sizer.Add(self._wavelen_text, 0, wx.RIGHT, 5)
        wavelength_unit_sizer.Add(wavelength_unit_label, 0, wx.ALIGN_CENTER_VERTICAL)
    
        wave_sizer.Add(wavelen_label, 0)
        wave_sizer.Add(wavelength_unit_sizer, 0)
        
        sd_sizer.Add(sd_label, 0)
        sd_sizer.Add(sd_unit_sizer, 0)
        
        pixel_sizer.Add(pixel_label, 0)
        pixel_sizer.Add(pixelsize_unit_sizer, 0)
        
        pattern_sizer.Add(pattern_label, 0)
        pattern_sizer.Add(self._pattern_list, 0)
        
    
        self.final_sizer = wx.BoxSizer(wx.VERTICAL)
    
        self.xycenter_sizer = wx.BoxSizer()
        self.xycenter_sizer.Add(x_sizer,0, wx.RIGHT, 5)
        self.xycenter_sizer.Add(y_sizer,0, wx.RIGHT, 5)
        self.xycenter_sizer.Add(step_sizer,0)
        
        self.calib_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.calib_sizer.Add(wave_sizer, 0, wx.BOTTOM, 5)
        self.calib_sizer.Add(sd_sizer, 0, wx.BOTTOM, 5)
        self.calib_sizer.Add(pixel_sizer, 0, wx.BOTTOM, 5)
        self.calib_sizer.Add(pattern_sizer,0, wx.BOTTOM, 5)
        
        self.final_sizer.Add(self.xycenter_sizer,0, wx.BOTTOM, 5)
        self.final_sizer.Add(self.calib_sizer,0)
        
        self.manual_widget_list.append(self._x_cent_text)
        self.manual_widget_list.append(self._y_cent_text)
        self.manual_widget_list.append(self._step_combo)
        self.manual_widget_list.append(self._wavelen_text)
        self.manual_widget_list.append(self._pixel_text)
        self.manual_widget_list.append(self._sd_text)
        self.manual_widget_list.append(self._pattern_list)
        
        return self.final_sizer
            
    def _createButtonSizer(self):
        sizer = wx.BoxSizer()
        
        ok_button = wx.Button(self, wx.ID_OK, 'OK')
        cancel_button = wx.Button(self, wx.ID_CANCEL, 'Cancel')
        
        sizer.Add(ok_button, 0, wx.RIGHT, 10)
        sizer.Add(cancel_button, 0)
        
        ok_button.Bind(wx.EVT_BUTTON, self._onOkButton)
        cancel_button.Bind(wx.EVT_BUTTON, self._onCancelButton)
    
        return sizer
    
    def _onEnterInCenterCtrl(self, event):
        
        x = str(self._x_cent_text.GetValue()).replace(',','.')
        y = str(self._y_cent_text.GetValue()).replace(',','.')
        
        try:
            self.setCenter([float(x),float(y)])
        except ValueError:
            pass
        
    def _onOkButton(self, event):
        self.image_panel.enableCenterClickMode(False)
        self.image_panel.enableAgbeAutoCentMode(False)
        self.image_panel.agbe_selected_points = []
        
        button = self.auto_start_button
        if button.GetLabelText() == 'Done':
            button.SetLabel('Start')
            self._enableControls(True)
        
        wx.CallAfter(self._main_frame.closeCenteringPane)
        wx.CallAfter(self.image_panel.clearPatches)
        
        self._main_frame.raw_settings.set('Xcenter', self._center[0])
        self._main_frame.raw_settings.set('Ycenter', self._center[1])
        
        sd, wavelength, pixel_size = self._getCalibValues()
        
        self._main_frame.raw_settings.set('SampleDistance', sd)
        self._main_frame.raw_settings.set('WaveLength', wavelength)
        self._main_frame.raw_settings.set('DetectorPixelSize', pixel_size)
        
        sd_pixels = round(SASImage.calcFromSDToAgBePixels(sd, wavelength, pixel_size / 1000.0),0)
                
        self._main_frame.raw_settings.set('PixelCalX', sd_pixels)
    
    def _getCalibValues(self):
        
        sd = float(self._sd_text.GetValue())
        wavelength = float(self._wavelen_text.GetValue())
        pixel_size = float(self._pixel_text.GetValue())

        return sd, wavelength, pixel_size

    def _onCancelButton(self, event):
        self.image_panel.enableCenterClickMode(False)
        self.image_panel.enableAgbeAutoCentMode(False)
        self.image_panel.agbe_selected_points = []
        
        self.updateCenterFromSettings()
        wx.CallAfter(self._main_frame.closeCenteringPane)
        wx.CallAfter(self.image_panel.clearPatches)
        
        button = self.auto_start_button
        if button.GetLabelText() == 'Done':
            button.SetLabel('Start')
            self._enableControls(True)
            
            
    
    def _onRepeatTimer(self, event):
        steps = int(self._step_combo.GetValue())
        wx.Yield()
        wx.CallAfter(self._moveCenter, self._pressed_button_id, steps)
    
    def _onCenteringButtonsUp(self, event):

        self._repeat_timer.Stop()
        event.Skip()
    
    def _onCenteringButtons(self, event):
        id = event.GetId()
        
        steps = float(self._step_combo.GetValue())
        self._pressed_button_id = id
        wx.CallAfter(self._moveCenter, id, steps)
        
        if platform.system() != 'Darwin':
            self._repeat_timer.Start(100)
        
        event.Skip()
    
    def _moveCenter(self, id, steps):
        
        if id == self.ID_UP:
            self._center[1] += steps
        if id == self.ID_DOWN:
            self._center[1] -= steps
        if id == self.ID_RIGHT:
            self._center[0] += steps
        if id == self.ID_LEFT:
            self._center[0] -= steps
            
        self.updateCenterTextCtrls()
        wx.CallAfter(self._updatePlots)
        
    def _onPixelWavelengthChange(self, event):
        self._updatePlots()
        
    def _onTargetButton(self, event): 
        self.image_panel.enableCenterClickMode()
        
        wx.MessageBox('Click on the image to move the center to a new location.', 'Select center on image')
    
    def _onPatternChoice(self, event):
        selection = self._pattern_list.GetSelection()
        
        if selection == 1: #Agbe
            wx.CallAfter(self._updateAgbeRings)
            
        elif selection == 0: #none
            wx.CallAfter(self.image_panel.clearPatches)
            
    def _onSampDetDistSpin(self, event):
        self._updatePlots()
        
    def _onAutoCenterStartButton(self, event):
        button = event.GetEventObject()
        
        if button.GetLabelText() == 'Start':
            button.SetLabel('Done')
            self._startAgbeAutoCentering()
        elif button.GetLabelText() == 'Done':
            button.SetLabel('Start')
            self._endAgbeAutoCentering()
            #self._updatePlots()
           
    def _endAgbeAutoCentering(self):
        for each in self.manual_widget_list:
            each.Enable(True)
        
        self.image_panel.enableAgbeAutoCentMode(False)
        points = self.image_panel.getSelectedAgbePoints()
        img = self.image_panel.img
        
        try:
            x, r = SASImage.calcCenterCoords(img, points, tune = True)  # x = (x_c,y_c)
        except SASExceptions.CenterNotFound:
            self.image_panel.agbe_selected_points = []
            wx.MessageBox('The center could not be found.\nPlease try again or use the manual settings.', 'Center was not found')
            return
        
        self._center = [x[0], x[1]]
        
        wavelength = float(self._wavelen_text.GetValue())
        pixel_size = float(self._pixel_text.GetValue())
        
        sd_dist = round(SASImage.calcAgBeSampleDetectorDist(r, wavelength, pixel_size / 1000.0),1)
        self._sd_text.SetValue(str(sd_dist))
        self.updateCenterTextCtrls()
        
        self._pattern_list.Select(1)
        wx.CallAfter(self.image_panel._drawAgBeRings, x, r)
        self.image_panel.agbe_selected_points = []

    def _enableControls(self, state):
        
        for each in self.manual_widget_list:
            each.Enable(state)

    def _startAgbeAutoCentering(self):
        
        self._enableControls(False)
        
        wx.CallAfter(self.image_panel.clearPatches)
        answer = wx.MessageBox('Please select at least 3 points just outside the inner circle of the AgBe image and then press the "Done" button', 'AgBe Center Calibration', wx.OK | wx.CANCEL)
        
        self.image_panel.enableAgbeAutoCentMode()
        
    def _updateAgbeRings(self):
        
        sd_distance, wavelength, pixel_size = self._getCalibValues()
        
        sample_detec_pixels = SASImage.calcFromSDToAgBePixels(sd_distance, wavelength, pixel_size / 1000.0)
                
        wx.CallAfter(self.image_panel.clearPatches)
        wx.CallAfter(self.image_panel._drawAgBeRings, self._center, sample_detec_pixels)
    
    def updateCenterTextCtrls(self):
        self._x_cent_text.SetValue(str(self._center[0]))
        self._y_cent_text.SetValue(str(self._center[1]))
    
    def _updatePlots(self):
        
        if self._pattern_list.GetSelection() == 1:
            self._updateAgbeRings()
            
    def updateCenterFromSettings(self):    
        x_center = self._main_frame.raw_settings.get('Xcenter')
        y_center = self._main_frame.raw_settings.get('Ycenter')
        
        wavelength = self._main_frame.raw_settings.get('WaveLength')
        pixel_size = self._main_frame.raw_settings.get('DetectorPixelSize') 
        samp_detc_dist = self._main_frame.raw_settings.get('SampleDistance')
        
        self._sd_text.SetValue(str(samp_detc_dist))
        self._pixel_text.SetValue(str(pixel_size))
        self._wavelen_text.SetValue(str(wavelength))
        
        self._center = [x_center, y_center]
        self.updateCenterTextCtrls()
    
    def _updateSampleDetectorDist(self):
        
        wavelength = float(self._wavelen_text.GetValue())
        pixel_size = float(self._pixel_text.GetValue())
        samp_dist = float(self._sd_text.GetValue())
        
        samp_dist_in_pixels = SASImage.calcFromSDToAgBePixels(samp_dist, wavelength, pixel_size)
        
        print samp_dist_in_pixels
        
        samp_dist_in_mm = round(SASImage.calcAgBeSampleDetectorDist(samp_dist_in_pixels, wavelength, pixel_size),1)
        
        self._sd_text.SetValue(str(samp_dist_in_mm))      
        
        print 'wops!'
        
    def updateAll(self):
        self._updatePlots()
        self.updateCenterFromSettings()
    
    def setCenter(self, center):
        self._center = center
        self.updateCenterTextCtrls()
        self._updatePlots()
        


#----- **** InformationPanel ****

class InformationPanel(wx.Panel):
    
    def __init__(self, parent):
        
        self.font_size1 = 11
        self.font_size2 = 12
            
        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.font_size1 = 8
            self.font_size2 = 10
        
        self.used_font1 = wx.Font(self.font_size1, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.used_font2 = wx.Font(self.font_size2, wx.SWISS, wx.NORMAL, wx.NORMAL)
        
        wx.Panel.__init__(self, parent, name = 'InformationPanel')
        
        infoSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.analysis_data = [('Rg:', 'Rg', wx.NewId()),
                              ('I0:', 'I0', wx.NewId()),
                              ('MW:', 'MW', wx.NewId())]
        
        self.conc_data = ('Conc:', 'Conc', wx.NewId())
        
        self.analysis_info_sizer = self._createAnalysisInfoSizer()
        
        infoSizer.Add(self.analysis_info_sizer, 0, wx.ALL | wx.EXPAND, 5)
    

        #header_note_box = wx.StaticBox(self, -1, 'Header data / Notes')
        #header_note_boxsizer = wx.StaticBoxSizer(header_note_box, orient = wx.VERTICAL)
        
        header_note_boxsizer = wx.BoxSizer(wx.VERTICAL)
        
        note_txt = wx.StaticText(self,-1,'Description / Notes:')
        note_txt.SetFont(self.used_font1)
        
        hdrbrow_txt = wx.StaticText(self,-1,'Header browser:')
        hdrbrow_txt.SetFont(self.used_font1)
        
        header_note_boxsizer.Add(note_txt, 0)
        header_note_boxsizer.Add(self._createNoteSizer(), 0, wx.ALL | wx.EXPAND, 5)
        header_note_boxsizer.Add(hdrbrow_txt, 0)
        self.header_browser_sizer = self._createHeaderBrowserSizer()
        header_note_boxsizer.Add(self.header_browser_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        infoSizer.Add(header_note_boxsizer, 1, wx.EXPAND | wx.ALL, 5)
 
        self.SetSizer(infoSizer)
        
        self.header_choice_key = None
        self.header_choice_hdr = None
        self.selectedItem = None
        self.sasm = None
        self.num_of_file_hdr_keys = 0
        self.num_of_imghdr_keys = 0
        
        self._disableAllControls()
    def _disableAllControls(self):
        for each in self.GetChildren():
            each.Enable(False)

    def _enableAllControls(self):
        for each in self.GetChildren():
            each.Enable(True)
        
    def _createHeaderBrowserSizer(self):
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.header_choice = wx.Choice(self, -1)
        self.header_txt = wx.TextCtrl(self, -1, '', style = wx.TE_CENTRE)
        self.header_choice.SetFont(self.used_font1)
        self.header_txt.SetFont(self.used_font1)
        self.header_choice.Bind(wx.EVT_CHOICE, self._onHeaderBrowserChoice)
        
        sizer.Add(self.header_choice, .5, wx.EXPAND | wx.RIGHT, 5)
        sizer.Add(self.header_txt, 1, wx.EXPAND)
        
        return sizer
    
    def _createAnalysisInfoSizer(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.name_label = wx.StaticText(self, -1, 'Name:')
        self.name_txt = wx.StaticText(self, -1, 'None')
        
        self.name_label.SetFont(self.used_font1)
        self.name_txt.SetFont(self.used_font1)
        
        
        name_sizer.Add(self.name_label, 0, wx.RIGHT, 10)
        name_sizer.Add(self.name_txt, 1, wx.EXPAND)
        
        analysis_sizer = wx.BoxSizer()
        for each in self.analysis_data:
            label = each[0]
            id = each[2]
            value = 'N/A'
            
            label_txt = wx.StaticText(self, -1, label)
            value_txt = wx.TextCtrl(self, id, value, size = (60, -1), style = wx.TE_READONLY)
            label_txt.SetFont(self.used_font1)
            value_txt.SetFont(self.used_font1)
            value_txt.SetSize((60,-1))
            
            siz = wx.BoxSizer()
            siz.Add(label_txt, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 3)
            siz.Add(value_txt, 1, wx.EXPAND)
            
            analysis_sizer.Add(siz, 1, wx.RIGHT | wx.EXPAND, 10)
            
        ## add conc ctrl:
        label_txt = wx.StaticText(self, -1, self.conc_data[0])
        label_txt.SetFont(self.used_font1)
        
        self.conc_txt = wx.TextCtrl(self, self.conc_data[2], 'N/A', size = (60, -1))
        self.conc_txt.Bind(wx.EVT_KILL_FOCUS, self._onNoteTextKillFocus)
        self.conc_txt.Bind(wx.EVT_TEXT, self._updateConc)
        self.conc_txt.SetFont(self.used_font1)
        
        siz = wx.BoxSizer()
        siz.Add(label_txt, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 3)
        siz.Add(self.conc_txt, 1, wx.EXPAND)    
        analysis_sizer.Add(siz, 1, wx.RIGHT | wx.EXPAND, 10)
            
        sizer.Add(name_sizer, 0, wx.EXPAND | wx.BOTTOM, 10)
        sizer.Add(analysis_sizer, 1, wx.EXPAND | wx.RIGHT, 5)
        
        return sizer
    
    def _createNoteSizer(self):
        sizer = wx.BoxSizer()
                
        self.noteTextBox = wx.TextCtrl(self, -1, '')
        self.noteTextBox.SetBackgroundColour('WHITE')
        self.noteTextBox.SetForegroundColour('BLACK')
        
        #length, height = self.noteTextBox.GetTextExtent('TEST')
        #self.noteTextBox.SetMaxSize((-1,30))
        #self.noteTextBox.SetSize((-1, 2*height))
        
        self.noteTextBox.Bind(wx.EVT_KILL_FOCUS, self._onNoteTextKillFocus)
        
        sizer.Add(self.noteTextBox, 1, wx.EXPAND)
        
        return sizer
    
    def _onNoteTextKillFocus(self, event):
        
        note_txt = self.noteTextBox.GetValue()
        
        try:        
            self.sasm.setParameter('Notes', note_txt)
        except AttributeError:
            pass
    
        try:
            conc = self.conc_txt.GetValue().replace(',','.')
            if self.sasm != None and conc != 'N/A':
            
                float(conc)
                self.sasm.setParameter('Conc', float(conc))
        
            
        except Exception, e:
            print e
            print 'info error, Conc'
    
    
        if self.sasm != None and self.selectedItem != None:
            try:
                self.selectedItem.updateInfoTip(self.sasm.getParameter('analysis'))
            except Exception, e:
                pass

    def _updateConc(self, event):
        try:
            conc = self.conc_txt.GetValue().replace(',','.')
            if self.sasm != None and conc != 'N/A' and conc != 'N/' and conc !='N' and conc !='/A' and conc !='A' and conc != 'NA' and conc != '' and conc !='.':
            
                float(conc)
                self.sasm.setParameter('Conc', float(conc))
        
            
        except Exception, e:
            print e
            print 'info error, Conc'
        
    def _onHeaderBrowserChoice(self, event):
        
        key = self.header_choice.GetStringSelection()
        sel_idx = self.header_choice.GetSelection()
        
        if self.sasm == None or key == 'No header info':
            return
        
        self.header_choice_key = key
        
        if sel_idx < (self.num_of_file_hdr_keys):
            self.header_choice_hdr = 'counters'
        else:
            self.header_choice_hdr = 'imageHeader'
        
        img_hdr = self.sasm.getParameter('imageHeader')
        file_hdr = self.sasm.getParameter('counters')
        
        if self.header_choice_hdr == 'imageHeader' and img_hdr.has_key(key):
            self.header_txt.SetValue(str(img_hdr[key]))
        if self.header_choice_hdr == 'counters' and file_hdr.has_key(key):
            self.header_txt.SetValue(str(file_hdr[key]))
            
        if sel_idx != wx.NOT_FOUND:
            self.selectedItem.info_settings['hdr_choice'] = sel_idx
        else:
            self.selectedItem.info_settings['hdr_choice'] = 0
    
    def clearInfo(self):
        self._disableAllControls()
        
        if self.sasm != None and self.selectedItem != None:
            try:
                self.selectedItem.updateInfoTip(self.sasm.getParameter('analysis'))
            except Exception, e:
                pass
        
        try:
            note_txt = self.noteTextBox.GetValue()
            self.sasm.setParameter('Notes', note_txt)
        
            # conc = self.conc_txt.GetValue().replace(',','.')
            
            # try:
            #     if conc != 'N/A' and conc != 'N\A' and self.sasm != None:
            #         float(conc)
            #         self.sasm.setParameter('Conc', float(conc))
            # except Exception, e:
            #     print e
            #     print 'info error, Conc'
            
        except AttributeError:
            pass
        
        self.name_txt.SetLabel('')
        
        for each in self.analysis_data:
            id = each[2]
            
            label = wx.FindWindowById(id)
            label.SetValue('N/A')
            
        self.header_txt.SetValue('')
        self.header_choice.SetItems([''])
        self.noteTextBox.SetValue('')
        self.conc_txt.SetValue('N/A')
        self.num_of_file_hdr_keys = 0
        self.num_of_imghdr_keys = 0
        
        self.sasm = None
        self.selectedItem = None
        
        self.analysis_info_sizer.Layout()
        self.Refresh()   

    def updateInfoFromItem(self, item):
        self.clearInfo()
        
        self.sasm = item.getSASM()
                
        # ## THE FACT THAT THIS HAS TO BE DONE IS SO>!@ STRANGE!! 
        # if self.sasm.getParameter('analysis').has_key('guinier'):
        #     analysis_dict = self.sasm.getParameter('analysis')
        #     guinier = analysis_dict['guinier']
        #     try:
        #         self.sasm.setParameter('Conc', guinier['Conc'])
        #     except KeyError:
        #         pass
        ########################################################
                
        self.selectedItem = item
        
        filename = self.sasm.getParameter('filename')
        self.name_txt.SetLabel(str(filename))
        
        if self.sasm.getParameter('analysis').has_key('guinier'):
            analysis_dict = self.sasm.getParameter('analysis')
            guinier = analysis_dict['guinier']
        
            if guinier.has_key('Rg') and guinier.has_key('I0'):
                rg = guinier['Rg']
                i_zero = guinier['I0']
        
                for each in self.analysis_data:
                    key = each[1]
                    id = each[2]
                    
                    txt = wx.FindWindowById(id)
                    
                    if guinier.has_key(key):
                        txt.SetValue(str(guinier[key]))       
                        
        if self.sasm.getAllParameters().has_key('Conc'):
            conc_ctrl = wx.FindWindowById(self.conc_data[2])
            conc_ctrl.SetValue(str(self.sasm.getParameter('Conc')))
            
        if self.sasm.getAllParameters().has_key('MW'):
            mw_ctrl = wx.FindWindowById(self.analysis_data[2][2])
            mw_ctrl.SetValue(str(self.sasm.getParameter('MW')))
        
        all_choices = []
        file_hdr = {}
        img_hdr = {}
        if self.sasm.getAllParameters().has_key('counters'):
            file_hdr = self.sasm.getParameter('counters')            
            all_filehdr_keys = file_hdr.keys()
            all_choices.extend(all_filehdr_keys)
            self.num_of_file_hdr_keys = len(all_filehdr_keys)
        
        if self.sasm.getAllParameters().has_key('imageHeader'):
            img_hdr = self.sasm.getParameter('imageHeader')
            all_imghdr_keys = img_hdr.keys()
            all_choices.extend(all_imghdr_keys)
            self.num_of_imghdr_keys = len(all_imghdr_keys)
            
            
        if len(all_choices) > 0:    
            self.header_choice.SetItems(all_choices)
            
            try:
                if self.header_choice_key != None:
                    if self.header_choice_hdr == 'imageHeader' and img_hdr.has_key(self.header_choice_key):
                        idx = all_imghdr_keys.index(self.header_choice_key)
                        idx = idx + self.num_of_file_hdr_keys
                        self.header_choice.SetSelection(idx)
                        
                    elif self.header_choice_hdr == 'counters' and file_hdr.has_key(self.header_choice_key):
                        idx = all_filehdr_keys.index(self.header_choice_key)
                        self.header_choice.SetSelection(idx)
                    else:
                        self.header_choice.SetSelection(item.info_settings['hdr_choice'])
                else:
                    self.header_choice.SetSelection(item.info_settings['hdr_choice'])
                    
                self._onHeaderBrowserChoice(None)
            except Exception, e:
                self.header_choice.SetSelection(0)
                print e
                print 'InfoPanel error'
        
        else:
            self.header_choice.SetItems(['No header info'])
            self.header_choice.Select(0)
        
        if self.sasm.getParameter('Notes') != None:
            self.noteTextBox.SetValue(self.sasm.getParameter('Notes'))
        
        self.analysis_info_sizer.Layout()
        self.header_browser_sizer.Layout()
        
        self._enableAllControls()
        self.Refresh()   
    
    def WriteText(self, text):    
        self.infoTextBox.AppendText(text)
        

class SaveAnalysisInfoPanel(wx.Panel):
    
    def __init__(self, parent, item_list = None, include_data = None):
        wx.Panel.__init__(self, parent, name = 'SaveAnalysisInfoPanel')
        
        self.SetMinSize((600,400))
        
        self.variable_data = {}
        
        self.item_list = item_list
        self.included_data = {}
        sizer = wx.BoxSizer()
        
        self.include_listctrl = SaveAnalysisListCtrl(self, -1, style = wx.LC_REPORT | wx.LC_NO_HEADER)
        self.variable_listctrl = SaveAnalysisListCtrl(self, -1, style = wx.LC_REPORT | wx.LC_NO_HEADER)
        
        include_sizer = wx.BoxSizer(wx.VERTICAL)
        include_sizer.Add(wx.StaticText(self, -1, 'Include list:'), 0)
        include_sizer.Add(self.include_listctrl, 1, wx.EXPAND)
        
        variable_sizer = wx.BoxSizer(wx.VERTICAL)
        variable_sizer.Add(wx.StaticText(self, -1, 'Variable list:'), 0)
        variable_sizer.Add(self.variable_listctrl, 1, wx.EXPAND)
        
        self.include_button = wx.Button(self, -1, '->')
        self.exclude_button = wx.Button(self, -1, '<-')
        
        self.include_button.Bind(wx.EVT_BUTTON, self._onIncludeButton)
        self.exclude_button.Bind(wx.EVT_BUTTON, self._onExcludeButton)
        
        self.button_sizer = wx.BoxSizer(wx.VERTICAL)
        self.button_sizer.Add(self.include_button, 0)
        self.button_sizer.Add(self.exclude_button, 0)
        
        sizer.Add(variable_sizer, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.button_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        sizer.Add(include_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(sizer)
        
        self.variable_listctrl.InsertColumn(0, 'name')
        width, height = self.variable_listctrl.GetSize()
        
        self.variable_listctrl.SetColumnWidth(0, 300)
        
        self._addGeneralVariables()
        self._addGuinierVariables()
        self._addMWVariables()
        self._addFileHdrVariables()
        self._addImageHdrVariables()
    
        self._updateIncludeList(include_data)
        
    def _onIncludeButton(self, event):
        selected_items = self.variable_listctrl.getSelectedItems()
        
        all_items = []
        
        for each_item in selected_items:
            data = copy.copy(self.variable_data[each_item])
            
            if data[1] == None:
                continue
            
            txt = self.variable_listctrl.GetItem(each_item).GetText()
            all_items.append(data)
  
            idx = self.include_listctrl.GetItemCount()
            self.include_listctrl.InsertStringItem(idx, txt)
                
            self.included_data[idx] = data   
        
    def _onExcludeButton(self, event):
        selected_items = self.include_listctrl.getSelectedItems()
        
        if len(selected_items) > 0:
            each = selected_items[0]
        else:
            return
        
        self.include_listctrl.DeleteItem(each)
        del self.included_data[each]
        
        self._updateIncludedData()
            
    def _updateIncludedData(self):
        
        idx = 0
        new_dict = {}
        for each in sorted(self.included_data.keys()):
            
            new_dict[idx] = self.included_data[each]
            idx = idx+1
            
        self.included_data = new_dict
               
    def _getAllImageHdrKeys(self):
        all_imghdr_keys = []
        
        all_keys = []
        for each_item in self.item_list:
            each_sasm = each_item.getSASM()
            
            if each_sasm.getAllParameters().has_key('imageHeader'):
               img_hdr = each_sasm.getParameter('imageHeader')
               keys = img_hdr.keys()
               all_keys.extend(keys)
               
        all_imghdr_keys.extend(set(all_keys))
        
        return all_imghdr_keys
            
    def _getAllFileHdrKeys(self):
        all_filehdr_keys = []
        
        all_keys = []
        for each_item in self.item_list:
            each_sasm = each_item.getSASM()
            
            if each_sasm.getAllParameters().has_key('counters'):
               img_hdr = each_sasm.getParameter('counters')
               keys = img_hdr.keys()
               all_keys.extend(keys)
               
        all_filehdr_keys.extend(set(all_keys))
        
        return all_filehdr_keys
    
    def _getAllGuinierKeys(self):
        all_guinier_keys = []
        
        all_keys = []
        for each_item in self.item_list:
            each_sasm = each_item.getSASM()
            
            if each_sasm.getParameter('analysis').has_key('guinier'):
               analysis = each_sasm.getParameter('analysis')
               guinier = analysis['guinier']
               keys = guinier.keys()
               all_keys.extend(keys)
               
        all_guinier_keys.extend(set(all_keys))
        
        return all_guinier_keys

    def _getAllMWKeys(self):
        all_mw_keys = []
        
        all_keys = []
        for each_item in self.item_list:
            each_sasm = each_item.getSASM()
            
            if each_sasm.getParameter('analysis').has_key('molecularWeight'):
                analysis = each_sasm.getParameter('analysis')
                mw = analysis['molecularWeight']
                key_list = []
                keys = mw.keys()
                for each_key in keys:
                    subkeys = mw[each_key].keys()
                    for each_subkey in subkeys:
                        key_list.append((each_key, each_subkey))
                
                all_keys.extend(key_list)
               
        all_mw_keys.extend(set(all_keys))
        
        return all_mw_keys
        
    
    def _addGeneralVariables(self):
        general_data = [('General', None), ('\tConcentration', 'Conc'), ('\tDescription / Notes', 'Notes'),
                        ('\tScale', 'scale'), ('\tOffset', 'offset')]
        
        idx = 0
        for each in general_data: 
            self.variable_listctrl.InsertStringItem(idx, each[0])
            self.variable_data[idx] = ['general' , each[1], each[0]]
            
            idx = idx + 1
            
        self.variable_listctrl.SetItemBackgroundColour(0, 'GRAY')
    
    def _addGuinierVariables(self):
        keys = self._getAllGuinierKeys()
        
        if len(keys) == 0:
            return
        
        idx = self.variable_listctrl.GetItemCount()
                
        self.variable_listctrl.InsertStringItem(idx, 'Guinier Analysis')
        self.variable_data[idx] = ['guinier', None]
        
        self.variable_listctrl.SetItemBackgroundColour(idx, 'GRAY')
        idx = idx + 1
        for each in keys: 
            self.variable_listctrl.InsertStringItem(idx, '\t'+each)
            self.variable_data[idx] = ['guinier', each, each]         
            idx = idx + 1

    def _addMWVariables(self):
        keys = self._getAllMWKeys()

        # print keys
        
        if len(keys) == 0:
            return
        
        idx = self.variable_listctrl.GetItemCount()
                
        self.variable_listctrl.InsertStringItem(idx, 'MW Analysis')
        self.variable_data[idx] = ['molecularWeight', None]
        
        self.variable_listctrl.SetItemBackgroundColour(idx, 'GRAY')
        idx = idx + 1
        for each in keys: 
            self.variable_listctrl.InsertStringItem(idx, '\t%s_%s' %(each[0], each[1]))
            self.variable_data[idx] = ['molecularWeight', each[0], each[1]]         
            idx = idx + 1

    
    def _addFileHdrVariables(self):
        keys = self._getAllFileHdrKeys()
        
        if len(keys) == 0:
            return
        
        idx = self.variable_listctrl.GetItemCount()
        
        self.variable_listctrl.InsertStringItem(idx, 'Header File')
        self.variable_data[idx] = ['Header File', None]
        self.variable_listctrl.SetItemBackgroundColour(idx, 'GRAY')
        idx = idx + 1
        for each in keys: 
            self.variable_listctrl.InsertStringItem(idx, '\t'+each)
            self.variable_data[idx] = ['counters', each, each]                   
            idx = idx + 1
    
    def _addImageHdrVariables(self):
        keys = self._getAllImageHdrKeys()
        
        if len(keys) == 0:
            return
        
        idx = self.variable_listctrl.GetItemCount()
        
        self.variable_listctrl.InsertStringItem(idx, 'Image Header')
        self.variable_data[idx] = ['Image Header', None]
        self.variable_listctrl.SetItemBackgroundColour(idx, 'GRAY')
        idx = idx + 1
        for each in keys: 
            self.variable_listctrl.InsertStringItem(idx, '\t'+each)
            self.variable_data[idx] = ['imageHeader', each, each]        
            idx = idx + 1
            
    def getIncludeData(self):
        return self.included_data
    
    def _updateIncludeList(self, include_data):
        
        if include_data == None:
            return
        
        for each in sorted(include_data.keys()):
            idx = self.include_listctrl.GetItemCount()
            self.include_listctrl.InsertStringItem(idx, include_data[each][2])
                
            self.included_data[idx] = include_data[each]

        
#----- **** Dialogs ****

class IFTSearchStatusDialog(wx.Dialog):
     def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, 'BIFT Search', name = 'BIFTStatusDlg', size = (280,230))
        
        self.widget_data = [
          ('filename', 'Processing data :', wx.NewId()),
          ('evidence', 'Evidence :', wx.NewId()),
          ('chi', 'Chi :', wx.NewId()),
          ('alpha', 'Alpha :', wx.NewId()),
          ('dmax', 'Dmax :', wx.NewId()),
          ('cur_point', 'Current search point :', wx.NewId()),
          ('tot_points', 'Total search points :', wx.NewId())]
         
         
        skip_button = wx.Button(self, -1, 'Skip')
        button = wx.Button(self, -1, 'Cancel')
        button.Bind(wx.EVT_BUTTON, self._onCancel)
        skip_button.Bind(wx.EVT_BUTTON, self._onSkip)
        
        button_sizer = wx.BoxSizer()
        button_sizer.Add(button, 0)
        button_sizer.Add(skip_button, 0, wx.LEFT, 10)
        
        self.status_text = wx.StaticText(self, -1, 'Performing grid search')
        
        self.count = 0
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onStatusTimer, self.timer)
        self.timer.Start(250)
        
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer = self.createDataWidgets()
        
        top_sizer.Add(sizer, 0, wx.ALL, 10)
        top_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 10)
        top_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 10)
        
        self.SetSizer(top_sizer)
        
        self.CenterOnParent()
     
     def _onCancel(self, evt):
         BIFT.cancel_bift = True
         
         global cancel_ift
         cancel_ift = True
         
         self.timer.Stop()
         
     def _onSkip(self, evt):
         BIFT.cancel_bift = True
     
     def createDataWidgets(self):
         
         sizer = wx.FlexGridSizer(cols = 2, rows = len(self.widget_data), vgap = 3, hgap = 5)
         
         for each in self.widget_data:
             label = each[1]
             id = each[2]
             
             sizer.Add(wx.StaticText(self, -1, label), 1)
             sizer.Add(wx.StaticText(self, id, ''), 1)
             
         return sizer
         
     def updateData(self, status_data, fine_tune = False):
         for each in self.widget_data:
             key = each[0]
             id = each[2]
             txt = wx.FindWindowById(id)
            
             txt.SetLabel(str(status_data[key]))
             
         if fine_tune:
             self.status_text.SetLabel('Finetuning solution')
             
     def onStatusTimer(self, evt):
         self.count = self.count + 1
         
         if self.count == 5:
             self.count = 0
             
         label = self.status_text.GetLabel()
         label = label.strip('.')
         
         self.status_text.SetLabel(label + (self.count * '.'))
        
         
     def onUpdateTimer(self, evt):

        try:
            status_data = self.search_status_queue.get()
        except Queue.Empty:
            status_data = None
            
        
        if status_data == 'END':
            self.timer.Stop()
            return
        
        if status_data != None:
            self.updateData(status_data)
        
     def OnClose(self, evt):
         self.timer.Stop()
         self.EndModal(wx.ID_OK)
        
class SaveDialog(wx.Dialog):
    def __init__(self, parent, id, title, text):
        wx.Dialog.__init__(self, parent, id, title)

        sizer =  wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, text), 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)
        
        button_sizer = wx.BoxSizer()
      
        button_sizer.Add(wx.Button(self, wx.ID_SAVE, 'Save'), 0, wx.RIGHT, 5)
        button_sizer.Add(wx.Button(self, wx.ID_DELETE, 'Discard'), 0, wx.RIGHT, 5)
        button_sizer.Add(wx.Button(self, wx.ID_CANCEL, 'Cancel'), 0)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)
        
        self.Bind(wx.EVT_BUTTON, self._onCancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self._onDiscard, id=wx.ID_DELETE)
        self.Bind(wx.EVT_BUTTON, self._onSave, id=wx.ID_SAVE)

        self.SetSizer(sizer)
        self.Fit()
        
    def _onCancel(self, event):
        self.EndModal(wx.ID_CANCEL)
    
    def _onDiscard(self, event):
        self.EndModal(wx.ID_DELETE)
    
    def _onSave(self, event):
        self.EndModal(wx.ID_SAVE)
        
class SaveAnalysisListCtrl(wx.ListCtrl):
    
    def __init__(self, parent, id, *args, **kwargs):
        
        wx.ListCtrl.__init__(self, parent, id, *args, **kwargs)
        self.populateList()
        
    def populateList(self):
        self.InsertColumn(0, 'Name')
        self.SetColumnWidth(0, 300)
        
    def add(self, expr):
        no_of_items = self.GetItemCount()
        self.SetStringItem(no_of_items, 0, expr)
        
    def moveItemUp(self, idx):
        if idx > 0:
            data = self.getItemData(idx)
            self.DeleteItem(idx)
            self.InsertStringItem(idx-1, data[0])
            self.SetStringItem(idx-1, 1, data[1])
            self.Select(idx-1, True)
            
    def moveItemDown(self, idx):
        if idx < self.GetItemCount()-1:
            data = self.getItemData(idx)
            self.DeleteItem(idx)
            self.InsertStringItem(idx+1, data[0])
            self.SetStringItem(idx+1, 1, data[1])
            self.Select(idx+1, True)
        
    def getItemData(self, idx):
        data1 = self.GetItemText(idx)
        item = self.GetItem(idx, 1)
        data2 = item.GetText()
        
        return [data1, data2]
        
    def getSelectedItems(self):
        """    Gets the selected items for the list control.
          Selection is returned as a list of selected indices,
          low to high.
        """
        selection = []
        index = self.GetFirstSelected()
        
        if index == -1:
            return []
        
        selection.append(index)
        
        while len(selection) != self.GetSelectedItemCount():
            index = self.GetNextSelected(index)
            selection.append(index)

        return selection
    
    def getAllItems(self):
        ''' returns a list with all items and operator '''
        all_items = []
        for i in range(0, self.GetItemCount()):
             all_items.append(self.getItemData(i))
        
        return all_items
    
    def GetValue(self):
        ''' Creating a function to mimic other normal control widgets,
        this makes it easier to update and save settings for this
        control.'''
        
        return self.getAllItems()
    
    def SetValue(self, value_list):
        
        if value_list == None:
            return
        
        for each in value_list:
            op = each[0]
            expr = each[1]    
            self.add(op, expr)

class SaveAnalysisInfoDialog(wx.Dialog):
    
    def __init__(self, parent, raw_settings, item_list = None, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, -1, 'Select variables to include in the comma separated file.', *args, **kwargs)
        
        self.raw_settings = raw_settings
        
        include_data = self.raw_settings.get('csvIncludeData')
        
        self.item_list = item_list    
        self.panel = SaveAnalysisInfoPanel(self, item_list = item_list, include_data = include_data)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.sizer.Add(self.panel,0, wx.ALL, 10)
        buttonsizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        self.sizer.Add(buttonsizer,0, wx.BOTTOM | wx.RIGHT | wx.LEFT | wx.ALIGN_RIGHT, 10)
        
        self.Bind(wx.EVT_BUTTON, self._onOk, id = wx.ID_OK)
        
        self.SetSizer(self.sizer)
        self.Fit()
        
    def _onOk(self, event):
        include_data = self.panel.getIncludeData()
        
        if len(include_data) > 0:
            
            save_path = self._showSaveDialog()
            if save_path == None:
                return
            
            data = [self.item_list, include_data, save_path]
            mainworker_cmd_queue.put(['save_analysis_info', data])
            #make the workerthread make a csv file.
        
        self.raw_settings.set('csvIncludeData', include_data)
        self.EndModal(wx.ID_OK)
        
    
    def _showSaveDialog(self):
            
        dirctrl_panel = wx.FindWindowByName('DirCtrlPanel')
        save_path = dirctrl_panel.getDirLabel()
        
        filters = 'Comma Separated Files (*.csv)|*.csv'
            
        dialog = wx.FileDialog( None, style = wx.SAVE | wx.OVERWRITE_PROMPT, wildcard = filters, defaultDir = save_path) 
            
        if dialog.ShowModal() == wx.ID_OK:               
            save_path = dialog.GetPath()
            return save_path
        else:
             return None

class TestDialog(wx.Dialog):
    
    def __init__(self, parent, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        
        #self.panel = CenteringPanel(self, -1)
    
        self.panel = InformationPanel(self)
        
        self.sizer = wx.BoxSizer()
        
        self.sizer.Add(self.panel,0, wx.ALL, 10)
        self.SetSizer(self.sizer)
        self.Fit()
   
class HdrDataDialog(wx.Dialog):
    
    def __init__(self, parent, sasm = None, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, -1, 'Header Data Display', *args, **kwargs)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.grid_changed = False
        self.sasm = sasm
        
        #For testing
        if self.sasm == None:
            data_len = 100
            filename_label = wx.StaticText(self, -1, 'Filename :')
        else:
            data_len = len(sasm.getBinnedI())
            filename_label = wx.StaticText(self, -1, 'Filename : ' + sasm.getParameter('filename'))
        
        self.data_grid = gridlib.Grid(self)
        self.data_grid.SetDefaultCellAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE) 
        
        data_len = self._getNumOfHeaderValues()
                
        self.data_grid.CreateGrid(data_len, 2)
        self.data_grid.SetColLabelValue(0, 'Key')
        self.data_grid.SetColLabelValue(1, 'Value')
        self.data_grid.SetMinSize((400,400))
        
        self.sizer.Add(filename_label, 0, wx.TOP | wx.LEFT, 10)
        self.sizer.Add(self.data_grid, 1, wx.ALL, 10)
        self.sizer.Add(self._CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.Bind(wx.EVT_BUTTON, self._onOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self._onCancel, id=wx.ID_CANCEL)
        self.Bind(gridlib.EVT_GRID_CELL_CHANGE, self._onChange)
        self.Bind(gridlib.EVT_GRID_EDITOR_SHOWN, self._onEditCell)
        
        self.SetSizer(self.sizer)
        
        if self.sasm != None:
            self._insertData()
        
        self.data_grid.AutoSizeColumns()
        self.Fit()
        
        self.CenterOnParent()
    
    def _onEditCell(self, event):
        col = self.data_grid.GridCursorCol
        row = self.data_grid.GridCursorRow
        
        self.saved_value = self.data_grid.GetCellValue(row, col)
        
        event.Skip()
    
    def _onChange(self, event):
        
        try:
            col = self.data_grid.GridCursorCol
            row = self.data_grid.GridCursorRow
        
            value = self.data_grid.GetCellValue(row, col)
            float(value)
            self.grid_changed = True
        except ValueError:
            wx.MessageBox('Illegal value entered', 'Invalid Entry', style=ICON_ERROR)
            self.data_grid.SetCellValue(row, col, self.saved_value)
            
    def _getNumOfHeaderValues(self):
        
        all_keys = []
        
        if self.sasm.getAllParameters().has_key('counters'):
            file_hdr = self.sasm.getParameter('counters')
            keys = file_hdr.keys()
            all_keys.extend(keys)
            
        if self.sasm.getAllParameters().has_key('imageHeader'):
            img_hdr = self.sasm.getParameter('imageHeader')
            keys = img_hdr.keys()    
            all_keys.extend(keys)
            
        return len(all_keys)
        
    def _insertData(self):
          
        imghdr_data_len = 0
        filehdr_data_len = 0

        if self.sasm.getAllParameters().has_key('counters'):
            file_hdr = self.sasm.getParameter('counters')
            keys = file_hdr.keys()
        
            if len(keys) > 0:
                filehdr_data_len = len(keys)
                
                for i in range(0, filehdr_data_len):
                    self.data_grid.SetCellValue(i, 0, str(keys[i]))
                    self.data_grid.SetCellValue(i, 1, str(file_hdr[keys[i]]))        
        
        if self.sasm.getAllParameters().has_key('imageHeader'):
            img_hdr = self.sasm.getParameter('imageHeader')
            keys = img_hdr.keys()
        
            if len(keys) > 0:
                imghdr_data_len = len(keys)
                
                for i in range(filehdr_data_len, filehdr_data_len + imghdr_data_len):
                    self.data_grid.SetCellValue(i, 0, str(keys[i-filehdr_data_len]))
                    self.data_grid.SetCellValue(i, 1, str(img_hdr[keys[i-filehdr_data_len]]))

    
    def _writeData(self):
        data_len = len(self.sasm.getBinnedI())
        
        new_I = []
        new_Q = []
        new_Err = []
        
        for i in range(0, data_len):
            new_Q.append(float(self.data_grid.GetCellValue(i, 0)))
            new_I.append(float(self.data_grid.GetCellValue(i, 1)))
            new_Err.append(float(self.data_grid.GetCellValue(i, 2)))   
            
        self.sasm.setBinnedI(numpy.array(new_I))
        self.sasm.setBinnedQ(numpy.array(new_Q))
        self.sasm.setBinnedErr(numpy.array(new_Err))
        
        self.sasm._update()
        
    def _onOk(self, event):
#        if self.grid_changed:
#            self._writeData()
            
        self.EndModal(wx.ID_OK)
    def _onCancel(self, event):
        self.EndModal(wx.ID_CANCEL) 
        
class DataDialog(wx.Dialog):
    
    def __init__(self, parent, sasm = None, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, -1, 'Data Display', *args, **kwargs)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.grid_changed = False
        self.sasm = sasm
        #For testing
        if self.sasm == None:
            data_len = 100
            filename_label = wx.StaticText(self, -1, 'Filename :')
        else:
            data_len = len(sasm.getBinnedI())
            filename_label = wx.StaticText(self, -1, 'Filename : ' + sasm.getParameter('filename'))
        
        self.data_grid = gridlib.Grid(self)
        self.data_grid.SetDefaultCellAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE) 
        
        self.data_grid.CreateGrid(data_len, 3)
        self.data_grid.SetColLabelValue(0, 'q')
        self.data_grid.SetColLabelValue(1, 'i')
        self.data_grid.SetColLabelValue(2, 'err')
        self.data_grid.SetMinSize((600,400))
        
        self.sizer.Add(filename_label, 0, wx.TOP | wx.LEFT, 10)
        self.sizer.Add(self.data_grid, 1, wx.ALL, 10)
        self.sizer.Add(self._CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.Bind(wx.EVT_BUTTON, self._onOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self._onCancel, id=wx.ID_CANCEL)
        self.Bind(gridlib.EVT_GRID_CELL_CHANGE, self._onChange)
        self.Bind(gridlib.EVT_GRID_EDITOR_SHOWN, self._onEditCell)
        
        self.SetSizer(self.sizer)
        
        if self.sasm != None:
            self._insertData()
        
        
        self.data_grid.AutoSizeColumns()
        self.Fit()
        
#        try:
#            file_list_ctrl = wx.FindWindowByName('PlotPanel')
#            pos = file_list_ctrl.GetScreenPosition()
#            self.MoveXY(pos[0], pos[1])
#        except:
#            pass

        self.CenterOnParent()
    
    def _onEditCell(self, event):
        col = self.data_grid.GridCursorCol
        row = self.data_grid.GridCursorRow
        
        self.saved_value = self.data_grid.GetCellValue(row, col)
        
        event.Skip()
    
    def _onChange(self, event):
        
        try:
            col = self.data_grid.GridCursorCol
            row = self.data_grid.GridCursorRow
        
            value = self.data_grid.GetCellValue(row, col)
            float(value)
            self.grid_changed = True
        except ValueError:
            wx.MessageBox('Illegal value entered', 'Invalid Entry', style=ICON_ERROR)
            self.data_grid.SetCellValue(row, col, self.saved_value)
        
    def _insertData(self):
        data_len = len(self.sasm.getBinnedI())
        
        I = self.sasm.getBinnedI()
        Q = self.sasm.getBinnedQ()
        Err = self.sasm.getBinnedErr()
        
        for i in range(0, data_len):
            self.data_grid.SetCellValue(i, 0, str(Q[i]))
            self.data_grid.SetCellValue(i, 1, str(I[i]))
            self.data_grid.SetCellValue(i, 2, str(Err[i]))
    
    def _writeData(self):
        data_len = len(self.sasm.getBinnedI())
        
        new_I = []
        new_Q = []
        new_Err = []
        
        for i in range(0, data_len):
            new_Q.append(float(self.data_grid.GetCellValue(i, 0)))
            new_I.append(float(self.data_grid.GetCellValue(i, 1)))
            new_Err.append(float(self.data_grid.GetCellValue(i, 2)))   
            
        self.sasm.setBinnedI(numpy.array(new_I))
        self.sasm.setBinnedQ(numpy.array(new_Q))
        self.sasm.setBinnedErr(numpy.array(new_Err))
        
        self.sasm._update()
        
    def _onOk(self, event):
        if self.grid_changed:
            self._writeData()
            
        self.EndModal(wx.ID_OK)
    def _onCancel(self, event):
        self.EndModal(wx.ID_CANCEL)


class SECDataDialog(wx.Dialog):
    
    def __init__(self, parent, secm = None, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, -1, 'Data Display', *args, **kwargs)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sec_plot_panel = wx.FindWindowByName('SECPlotPanel')

        self.grid_changed = False
        self.secm = secm
        #For testing

        if self.secm.qref != 0:
            self.showq=True
        else:
            self.showq=False

        time = self.secm.getTime()

        if len(time)>0 and time[0] != -1 and len(time) == len(self.secm.frame_list):
            self.showtime = True
        else:
            self.showtime = False

        self.showcalc = self.secm.calc_has_data

        if self.secm == None:
            data_len = 100
            filename_label = wx.StaticText(self, -1, 'Filename :')
        else:
            data_len = len(self.secm.total_i)
            filename_label = wx.StaticText(self, -1, 'Filename : ' + secm.getFilename())

        self.data_grid = gridlib.Grid(self)
        self.data_grid.EnableEditing(False)
        self.data_grid.SetDefaultCellAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE) 

        columns = 4

        if self.showq:
            columns = columns + 1
        if self.showtime:
            columns = columns + 1
        if self.showcalc:
            columns = columns + 5
        
        self.data_grid.CreateGrid(data_len, columns)
        self.data_grid.SetColLabelValue(0, 'Frame Number')
        self.data_grid.SetColLabelValue(1, 'Integrated Intensity')
        self.data_grid.SetColLabelValue(2, 'Mean Intensity')

        index = 3
        if self.showq:
            self.data_grid.SetColLabelValue(index, 'Intensity at q = %f' %(self.secm.qref))
            index = index +1
        if self.showtime:
            self.data_grid.SetColLabelValue(index, 'Time (s)')
            index = index +1
        if self.showcalc:
            self.data_grid.SetColLabelValue(index, 'Rg (A)')
            index = index +1
            self.data_grid.SetColLabelValue(index, 'Rg error (A)')
            index = index +1
            self.data_grid.SetColLabelValue(index, 'I0')
            index = index +1
            self.data_grid.SetColLabelValue(index, 'I0 error')
            index = index +1
            self.data_grid.SetColLabelValue(index, 'MW (kDa)')
            index = index +1

        self.data_grid.SetColLabelValue(index, 'File Name')



        self.data_grid.SetMinSize((600,400))
        
        self.sizer.Add(filename_label, 0, wx.TOP | wx.LEFT, 10)
        self.sizer.Add(self.data_grid, 1, wx.ALL, 10)
        self.sizer.Add(self._CreateButtonSizer(wx.OK), 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)
        
        self.Bind(wx.EVT_BUTTON, self._onOk, id=wx.ID_OK)
        
        self.SetSizer(self.sizer)
        
        if self.secm != None:
            self._insertData()
        
        
        self.data_grid.AutoSizeColumns()
        self.Fit()
        
#        try:
#            file_list_ctrl = wx.FindWindowByName('PlotPanel')
#            pos = file_list_ctrl.GetScreenPosition()
#            self.MoveXY(pos[0], pos[1])
#        except:
#            pass

        self.CenterOnParent()
    
    def _onEditCell(self, event):
        col = self.data_grid.GridCursorCol
        row = self.data_grid.GridCursorRow
        
        self.saved_value = self.data_grid.GetCellValue(row, col)
        
        event.Skip()
    
    def _onChange(self, event):
        
        try:
            col = self.data_grid.GridCursorCol
            row = self.data_grid.GridCursorRow
        
            value = self.data_grid.GetCellValue(row, col)
            float(value)
            self.grid_changed = True
        except ValueError:
            wx.MessageBox('Illegal value entered', 'Invalid Entry', style=ICON_ERROR)
            self.data_grid.SetCellValue(row, col, self.saved_value)
        
    def _insertData(self):

        data_len = len(self.secm.total_i)
        
        frame_number = range(data_len)

        for i in range(data_len):
            self.data_grid.SetCellValue(i, 0, str(frame_number[i]))
            self.data_grid.SetCellValue(i, 1, str(self.secm.total_i[i]))
            self.data_grid.SetCellValue(i, 2, str(self.secm.mean_i[i]))

            index = 3
            if self.showq:
                self.data_grid.SetCellValue(i, index, str(self.secm.I_of_q[i]))
                index = index +1
            if self.showtime:
                self.data_grid.SetCellValue(i, index, str(self.secm.time[i]))
                index = index +1
            if self.showcalc:
                self.data_grid.SetCellValue(i, index, str(self.secm.rg_list[i]))
                index = index +1
                self.data_grid.SetCellValue(i, index, str(self.secm.rger_list[i]))
                index = index +1
                self.data_grid.SetCellValue(i, index, str(self.secm.i0_list[i]))
                index = index +1
                self.data_grid.SetCellValue(i, index, str(self.secm.i0er_list[i]))
                index = index +1
                self.data_grid.SetCellValue(i, index, str(self.secm.mw_list[i]))
                index = index +1

            self.data_grid.SetCellValue(i, index, os.path.split(self.secm._file_list[i])[1])
    
    def _writeData(self):
        data_len = len(self.secm.getBinnedI())
        
        new_I = []
        new_Q = []
        new_Err = []
        
        for i in range(0, data_len):
            new_Q.append(float(self.data_grid.GetCellValue(i, 0)))
            new_I.append(float(self.data_grid.GetCellValue(i, 1)))
            new_Err.append(float(self.data_grid.GetCellValue(i, 2)))   
            
        self.secm.setBinnedI(numpy.array(new_I))
        self.secm.setBinnedQ(numpy.array(new_Q))
        self.secm.setBinnedErr(numpy.array(new_Err))
        
        self.secm._update()
        
    def _onOk(self, event):
        if self.grid_changed:
            self._writeData()
            
        self.EndModal(wx.ID_OK)
    def _onCancel(self, event):
        self.EndModal(wx.ID_CANCEL)
    

class TestDialog2(wx.Dialog):
    
    def __init__(self, parent, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        
        self.panel = MaskingPanel(self, -1)
        
        self.sizer = wx.BoxSizer()
        
        self.sizer.Add(self.panel,0, wx.ALL, 10)
        self.SetSizer(self.sizer)
        self.Fit()
        
class SyncDialog(wx.Dialog):
    
    def __init__(self, parent, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, -1, 'Synchronize', *args, **kwargs)
            
        self.chkbox_list = [('q min', 'qmin', wx.NewId()),
                       ('q max', 'qmax', wx.NewId()),
                       ('n min', 'nmin', wx.NewId()),
                       ('n max', 'nmax', wx.NewId()),
                       ('scale', 'scale', wx.NewId()),
                       ('offset', 'offset', wx.NewId()),
                       ('line style', 'linestyle', wx.NewId()),
                       ('line width', 'linewidth', wx.NewId()),
                       ('line marker', 'linemarker', wx.NewId())]
        
        self.selected_boxes = []
        
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        
        sync_box = wx.StaticBox(self, -1, 'Synchronize Parameters')
        sync_boxsizer = wx.StaticBoxSizer(sync_box)
        sync_boxsizer.SetOrientation(wx.VERTICAL)
        
        for each in self.chkbox_list:
            label, key, id = each
            chkbox = wx.CheckBox(self, id, label, name = key)
            chkbox.Bind(wx.EVT_CHECKBOX, self._onCheckBox)
            sync_boxsizer.Add(chkbox, 0, wx.TOP | wx.LEFT, 5)
            
        sync_boxsizer.Add((5,5),0)

        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        self.Bind( wx.EVT_BUTTON, self._onOkClicked, id=wx.ID_OK )
        
        top_sizer.Add(sync_boxsizer, 1, wx.EXPAND | wx.ALL, 10)
        top_sizer.Add(button_sizer, 0, wx.ALL, 10)
            
        self.SetSizer(top_sizer)
        
        self.Fit()
        self.CenterOnParent()
    
    def _onOkClicked(self, event):
        manipulation_panel = wx.FindWindowByName('ManipulationPanel')
        
        wx.CallAfter(manipulation_panel.synchronizeSelectedItems, self.selected_boxes)
        
        self.EndModal(wx.ID_OK)
    
    def _onCheckBox(self, event):
        
        chkbox = event.GetEventObject()
        
        if chkbox.IsChecked():
            self.selected_boxes.append(chkbox.GetName())
        else:
            self.selected_boxes.remove(chkbox.GetName())
         
class QuickReduceDialog(wx.Dialog):
    
    def __init__(self, parent, path, selected_files, *args, **kwargs):
        
        wx.Dialog.__init__(self,parent, -1, 'Quick Reduce Settings', *args, **kwargs)
        
        self._path = path
        filecount_label = wx.StaticText(self, -1, '# of files selected : ' + str(len(selected_files)))
        
        savedir_label = wx.StaticText(self, -1, 'Save Directory :')
        format_label = wx.StaticText(self, -1, 'Format :')
        
        savedir_sizer = wx.BoxSizer()
        self.save_textctrl = wx.TextCtrl(self, -1, path, size = (400, -1))
        
        folder_bmp = wx.ArtProvider.GetBitmap(wx.ART_FOLDER,  wx.ART_MENU)
        save_search_button = wx.BitmapButton(self, -1, folder_bmp)
        save_search_button.Bind(wx.EVT_BUTTON, self._onSearchButton)
        
        savedir_sizer.Add(self.save_textctrl, 1, wx.RIGHT | wx.EXPAND, 2)
        savedir_sizer.Add(save_search_button, 0)
        
        format_choice = wx.Choice(self, -1, choices = ['.rad (RAW)', '.dat (ATSAS)'])
        format_choice.Select(0)
        
        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        self.Bind( wx.EVT_BUTTON, self._onOkClicked, id=wx.ID_OK )
        
        final_sizer = wx.BoxSizer(wx.VERTICAL)
        final_sizer.Add(filecount_label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
        final_sizer.Add(savedir_label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
        final_sizer.Add(savedir_sizer, 0, wx.LEFT | wx.RIGHT, 10)
        final_sizer.Add(format_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        final_sizer.Add(format_choice, 0, wx.LEFT | wx.RIGHT, 10)
        final_sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP, 10)
        final_sizer.Add(button_sizer, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 10)
        
        self.SetSizer(final_sizer)
        
        self.Fit()
        self.CenterOnParent()
    
    def _onOkClicked(self, event):
        
        self._path = self.save_textctrl.GetValue()
        if not os.path.exists(self._path):
            wx.MessageBox('Path does not exist or contains illegal characters.', 'Path not valid', style = wx.ICON_ERROR)
            return
        else:
            self.EndModal(wx.ID_OK)
        
    def _onSearchButton(self, event):

        dirdlg = wx.DirDialog(self, "Please select directory:", str(self._path))
            
        if dirdlg.ShowModal() == wx.ID_OK:
            self._path = dirdlg.GetPath()
            self.save_textctrl.SetValue(str(self._path))
            
    def getPath(self):
        return self._path
        

class FilenameChangeDialog(wx.Dialog):
    
    def __init__(self, parent, filename, dlgtype = None, *args, **kwargs):
        
        if dlgtype == 'Folder':
            hdr = 'Folder Name'
        else:
            hdr = 'Change Name'
            
        wx.Dialog.__init__(self,parent, -1, hdr, *args, **kwargs)
        
        self.ok_button = wx.Button(self, -1, 'OK')
        self.cancel_button = wx.Button(self, -1, 'Cancel')
        self._filename = None
        
        self.ok_button.Bind(wx.EVT_BUTTON, self._onOKButton)
        self.cancel_button.Bind(wx.EVT_BUTTON, self._onCancelButton)
        
        button_sizer = wx.BoxSizer()
        button_sizer.Add(self.ok_button,0, wx.RIGHT, 5)
        button_sizer.Add(self.cancel_button,0)        
        
        label = wx.StaticText(self, -1, 'Name :')
        self.ctrl = wx.TextCtrl(self, -1, '', size = (200, -1))
        self.ctrl.SetValue(str(filename))
        
        filename_sizer = wx.BoxSizer()
        filename_sizer.Add(label,0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        filename_sizer.Add(self.ctrl, 1, wx.EXPAND | wx.RIGHT, 5)
        
        final_sizer = wx.BoxSizer(wx.VERTICAL)
        
        final_sizer.Add(filename_sizer, 0, wx.ALL, 15)
        final_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        
        self.SetSizer(final_sizer)
        self.Fit()
        self.CenterOnParent()
    
    def _onOKButton(self, event):
        self._filename = self.ctrl.GetValue()
        self.EndModal(wx.ID_OK)
        
    def _onCancelButton(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def getFilename(self):
        return self._filename
    
        

class LegendLabelChangeDialog(wx.Dialog):
    
    def __init__(self, parent, legend_label, *args, **kwargs):
        
        wx.Dialog.__init__(self,parent, -1, 'Change Legend Label', *args, **kwargs)
        
        self.ok_button = wx.Button(self, -1, 'OK')
        self.cancel_button = wx.Button(self, -1, 'Cancel')
        self._legend_label = ''
        
        self.ok_button.Bind(wx.EVT_BUTTON, self._onOKButton)
        self.cancel_button.Bind(wx.EVT_BUTTON, self._onCancelButton)
        
        button_sizer = wx.BoxSizer()
        button_sizer.Add(self.ok_button,0, wx.RIGHT, 5)
        button_sizer.Add(self.cancel_button,0)        
        
        label_txt = 'Label :'
        label = wx.StaticText(self, -1,label_txt)
        self.ctrl = wx.TextCtrl(self, -1, '', size = (200, -1))
        self.ctrl.SetValue(str(legend_label))
        
        filename_sizer = wx.BoxSizer()
        filename_sizer.Add(label,0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        filename_sizer.Add(self.ctrl, 1, wx.EXPAND | wx.RIGHT, 5)
        
        final_sizer = wx.BoxSizer(wx.VERTICAL)
        
        final_sizer.Add(filename_sizer, 0, wx.ALL, 15)
        final_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        
        self.SetSizer(final_sizer)
        self.Fit()
        self.CenterOnParent()
    
    def _onOKButton(self, event):
        self._legend_label = self.ctrl.GetValue()
        self.EndModal(wx.ID_OK)
        
    def _onCancelButton(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def getLegendLabel(self):
        return self._legend_label


class RebinDialog(wx.Dialog):
    
    def __init__(self, parent, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, -1, 'Rebinning', *args, **kwargs)
        
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        
        choices = ['2','3','4','5','6','7','8','9','10']
        text = wx.StaticText(self, -1, 'Select bin reduction factor :')
        self.choice = wx.Choice(self, -1, choices = choices)
        self.choice.Select(0)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.log_box = wx.CheckBox(self, -1, 'Logarithmic')

        buttonsizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        self.Bind( wx.EVT_BUTTON, self._onOkClicked, id=wx.ID_OK )
        
        sizer.Add(text, 1)
        sizer.Add(self.choice, 0)
        sizer.Add(self.log_box, 0, wx.TOP, 5)
        
        top_sizer.Add(sizer, 1, wx.ALL, 10)
        top_sizer.Add(buttonsizer, 1, wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL)
        
        self.SetSizer(top_sizer)
        self.Fit()
        
        self.CenterOnParent()

    def _onOkClicked(self, event):
        ret = int(self.choice.GetStringSelection())
        log_rebin = self.log_box.GetValue()

        self.EndModal(ret)

    def getValues(self):
        ret = int(self.choice.GetStringSelection())
        log_rebin = self.log_box.GetValue()

        return [ret, log_rebin]

class ColourChangeDialog(wx.Dialog):
    
    def __init__(self, parent, sasm, linename, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, -1, 'Pick a Colour', *args, **kwargs)
        
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.linename = linename
        self.sasm = sasm
        
        old_color = self.getOldColour()
        
        if old_color == "None": #Transparant marker
            old_color = self.sasm.line.get_color()
        
        conv = mplcol.ColorConverter()
        color = conv.to_rgb(old_color)
        self._old_linecolour = color
        color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        self._linecolour = color
        
        buttonsizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        self.Bind( wx.EVT_BUTTON, self._onOkClicked, id=wx.ID_OK )
        
        self.colourchoice = colorchooser.PyColourChooser(self, -1)
        self.colourchoice.SetValue(self._linecolour)
        self.colourchoice.palette.Bind(wx.EVT_LEFT_UP, self.updateLine)
        
        for each in self.colourchoice.colour_boxs:
            each.GetColourBox().Bind(wx.EVT_LEFT_UP, self.updateLine)
        
        sizer.Add(self.colourchoice, 1)
        
        top_sizer.Add(sizer, 0, wx.ALL, 10)
        top_sizer.Add(buttonsizer, 0, wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 10)
        
        self.SetSizer(top_sizer)
        self.Fit()
        
        self.CenterOnParent()
        
    def getOldColour(self):
        
        if self.linename == 'MarLineColour':
            return self.sasm.line.get_markeredgecolor()
        elif self.linename == 'MarFillColour':
            return self.sasm.line.get_markerfacecolor()
        elif self.linename == 'LineColour':
            return self.sasm.line.get_color()
        elif self.linename == 'ErrColour':
            return self.sasm.line.get_color()
        elif self.linename == 'CalcMarLineColour':
            return self.sasm.calc_line.get_markeredgecolor()
        elif self.linename == 'CalcMarFillColour':
            return self.sasm.calc_line.get_markerfacecolor()
        elif self.linename == 'CalcLineColour':
            return self.sasm.calc_line.get_color()
            
    def updateLine(self, event):
        colour =  self.colourchoice.GetValue().Get(False)
        colour =  (colour[0]/255.0, colour[1]/255.0, colour[2]/255.0)
        
        if self.linename == 'MarFillColour':
            self.sasm.line.set_markerfacecolor(colour)
        elif self.linename == 'MarLineColour':
            self.sasm.line.set_markeredgecolor(colour)
        elif self.linename == 'LineColour':
            self.sasm.line.set_color(colour)
        elif self.linename == 'ErrColour':
            
            for each in self.sasm.err_line:
                for line in each:
                    line.set_color(colour)
        
        elif self.linename == 'CalcMarFillColour':
            self.sasm.calc_line.set_markerfacecolor(colour)
        elif self.linename == 'CalcMarLineColour':
            self.sasm.calc_line.set_markeredgecolor(colour)
        elif self.linename == 'CalcLineColour':
            self.sasm.calc_line.set_color(colour)

        
        self.sasm.plot_panel.canvas.draw()
        
        event.Skip()

    def _onOkClicked(self, event):
        self.EndModal(wx.ID_OK)
        
    def _onCancel(self, event):
        pass

class LinePropertyDialog(wx.Dialog):
    
    def __init__(self, parent, sasm, legend_label, *args, **kwargs):
        if sasm.line == None:
            wx.MessageBox('Unable to change line properties.\nNo plot has been made for this item.', 'No plot')
            return
            
        
        wx.Dialog.__init__(self, parent, -1, "Line Properties", *args, **kwargs)
        
        self.sasm = sasm
        self.line = sasm.line
        self.legend_label = legend_label
        
        self.linewidth_combo_choices = ['1.0', '2.0', '3.0', '4.0', '5.0']
        self.linestyle_list_choices = ['None', '-', '--', '-.', ':']
        self.linemarker_list_choices = ['None', '+', '*', ',','.','1','2','3','4','<', '>', 'D', 'H', '^','_','d','h','o','p','s','v','x','|']
        
        self._linestyle = self.line.get_linestyle()
        self._linemarker = self.line.get_marker()
        self._linewidth = self.line.get_linewidth()
        
        conv = mplcol.ColorConverter()
        color = conv.to_rgb(self.line.get_color())
        self._old_linecolour = color
        color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        self._linecolour = color
        
        
        mfc = self.line.get_markerfacecolor()
        if mfc != "None":
            color = conv.to_rgb(self.line.get_markerfacecolor())
            self._marcolour = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
            self.hollow_marker = False
        else:
            color = conv.to_rgb(self.line.get_markeredgecolor())
            self._marcolour =  wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
            self.hollow_marker = True
        
        color = conv.to_rgb(self.line.get_markeredgecolor())
        self._marlinecolour = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        color = conv.to_rgb(self.sasm.err_line[0][0].get_color())
        self._errcolour = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        self._old_linestyle = self.line.get_linestyle()
        self._old_linemarker = self.line.get_marker()
        self._old_linewidth = self.line.get_linewidth()
        self._old_marcolour = self.line.get_markerfacecolor()
        self._old_marlinecolour = self.line.get_markeredgecolor()
        self._old_marsize = self.line.get_markersize()
        self._old_errcolour = self.sasm.err_line[0][0].get_color()
        self._old_errlinewidth = self.sasm.err_line[0][0].get_linewidth()

        errstyle = self.sasm.err_line[1][0].get_linestyle()
        strange_errlinestyles = {(None, None) : '-',
                                (0,(6.0, 6.0))    : '--',
                                (0,(3.0, 5.0, 1.0, 5.0)) : '-.',
                                (0,(1.0, 3.0)) : ':'}
        
        self._old_errlinestyle = strange_errlinestyles[errstyle[0]]
           
        top_sizer = wx.BoxSizer(wx.VERTICAL)

        buttonsizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        self.Bind( wx.EVT_BUTTON, self._onOkButton, id=wx.ID_OK )
        self.Bind( wx.EVT_BUTTON, self._onCancelButton, id=wx.ID_CANCEL )
        
        linesettings_sizer = wx.FlexGridSizer(cols = 2, rows = 2, vgap = 5, hgap = 10)
        linesettings_sizer.Add(self._createLineControls(), 1, wx.EXPAND)
        linesettings_sizer.Add(self._createErrorBarsControls(), 1, wx.EXPAND)
        linesettings_sizer.Add(self._createLineMarkerControls(), 1, wx.EXPAND)
        
        top_sizer.Add(self._createLegendLabelControls(), 0, wx.ALL | wx.EXPAND, 10)
        top_sizer.Add(linesettings_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        top_sizer.Add(wx.StaticLine(self, -1), wx.EXPAND |wx.TOP | wx.BOTTOM, 3)
        top_sizer.Add(buttonsizer, 0, wx.CENTER | wx.BOTTOM, 10)
        
        self.SetSizer(top_sizer)
        self.Fit()
        self.CenterOnParent()
    
    
    def _createLegendLabelControls(self):
        topbox = wx.StaticBox(self, -1, 'Legend Label') 
        box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
        
        self.legend_label_text = wx.TextCtrl(self, -1, self.legend_label)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.legend_label_text, 1, wx.EXPAND)
        
        box.Add(sizer, 0, wx.EXPAND | wx.ALL, 5)
        return box
    
    def _createErrorBarsControls(self):
        topbox = wx.StaticBox(self, -1, 'Error Bars') 
        box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
        
        err_linewidth_label = wx.StaticText(self, -1, 'Width :')
        err_linestyle_label = wx.StaticText(self, -1, 'Style :')
        err_colour_label = wx.StaticText(self, -1, 'Line Colour :')
        
        self.err_linewidth = wx.SpinCtrl(self, -1, '1')
        self.err_linewidth.SetRange(1, 99)
        self.err_linewidth.SetValue(self._old_errlinewidth)
        self.err_linewidth.Bind(wx.EVT_SPINCTRL, self.updateLine)
        
        self.err_linestyle_list = wx.Choice(self, -1, choices = self.linestyle_list_choices)
        self.err_linestyle_list.Select(self.linestyle_list_choices.index(str(self._old_errlinestyle)))
        self.err_linestyle_list.Bind(wx.EVT_CHOICE, self.updateLine)
        
        self.err_colour = wx.Panel(self, -1, name = 'ErrColour', style = wx.RAISED_BORDER)
        self.err_colour.SetBackgroundColour(self._errcolour)
        self.err_colour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
      
        sizer = wx.FlexGridSizer(cols = 2, rows = 5, vgap = 5, hgap = 3)
        sizer.Add(err_linestyle_label, 0)
        sizer.Add(self.err_linestyle_list, 0, wx.EXPAND)
        sizer.Add(err_linewidth_label, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.err_linewidth, 0, wx.EXPAND)
        sizer.Add(err_colour_label, 0)
        sizer.Add(self.err_colour, 0, wx.EXPAND)
      
        box.Add(sizer, 0, wx.ALL, 5)
        
        return box
    
    def _onColourPress(self, event):
        
        colour_panel = event.GetEventObject()
        
        dlg = ColourChangeDialog(self, self.sasm, colour_panel.GetName())
        dlg.ShowModal()
        dlg.Destroy()
        
        if colour_panel.GetName() == 'LineColour':
            color = self.line.get_color()
        elif colour_panel.GetName() == 'ErrColour':
            color = self.sasm.err_line[0][0].get_color()
        elif colour_panel.GetName() == 'MarLineColour':
            color = self.line.get_markeredgecolor()
        elif colour_panel.GetName() == 'MarFillColour':
            color = self.line.get_markerfacecolor()
        
        conv = mplcol.ColorConverter()
        
        if color != "None": #Not transparent
            color = conv.to_rgb(color)
            color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
            colour_panel.SetBackgroundColour(color)
            colour_panel.Refresh()
    
    def _createLineMarkerControls(self):
        topbox = wx.StaticBox(self, -1, 'Data Point Marker') 
        box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
        
        mar_size_label = wx.StaticText(self, -1, 'Size :')
        self.mar_fillcolour_label = wx.StaticText(self, -1, 'Fill Colour :')
        self.mar_fillcolour_label.Enable(not self.hollow_marker)
        mar_linecolour_label = wx.StaticText(self, -1, 'Line Colour :')
        mar_linemarker_label = wx.StaticText(self, -1, 'Marker :')
        mar_hollow_label = wx.StaticText(self, -1, 'Hollow :')
        
        #self.mar_size = wx.SpinCtrl(self, -1, '1')
        self.mar_size = RAWCustomCtrl.FloatSpinCtrl(self, -1, '1.0', TextLength = 60, never_negative = True)
        self.mar_size.Bind(RAWCustomCtrl.EVT_MY_SPIN, self.updateLine)
        self.mar_size.SetValue(str(self._old_marsize))
        #self.mar_size.Bind(wx.EVT_SPINCTRL, self.updateLine)
        
        self.mar_fillcolour = wx.Panel(self, -1, name = 'MarFillColour', style = wx.RAISED_BORDER)
        self.mar_fillcolour.SetBackgroundColour(self._marcolour)
        self.mar_fillcolour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
        self.mar_fillcolour.Enable(not self.hollow_marker)
        
        self.mar_linecolour = wx.Panel(self, -1, name = 'MarLineColour', style = wx.RAISED_BORDER)
        self.mar_linecolour.SetBackgroundColour(self._marlinecolour)
        self.mar_linecolour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
        
        self.mar_linemarker_list = wx.Choice(self, -1, choices = self.linemarker_list_choices)
        self.mar_linemarker_list.Select(self.linemarker_list_choices.index(str(self._linemarker)))
        self.mar_linemarker_list.Bind(wx.EVT_CHOICE, self.updateLine)
        
        self.mar_hollow = wx.CheckBox(self, -1)
        self.mar_hollow.SetValue(self.hollow_marker)
        self.mar_hollow.Bind(wx.EVT_CHECKBOX, self._onHollowCheckBox)
      
        sizer = wx.FlexGridSizer(cols = 2, rows = 5, vgap = 5, hgap = 3)
        sizer.Add(mar_linemarker_label, 0)
        sizer.Add(self.mar_linemarker_list, 0, wx.EXPAND)
        sizer.Add(mar_size_label, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.mar_size, 0, wx.EXPAND)
        sizer.Add(mar_linecolour_label, 0)
        sizer.Add(self.mar_linecolour, 0, wx.EXPAND)
        sizer.Add(self.mar_fillcolour_label, 0)
        sizer.Add(self.mar_fillcolour, 0, wx.EXPAND)
        sizer.Add(mar_hollow_label, 0)
        sizer.Add(self.mar_hollow, 0, wx.EXPAND)
        
      
        box.Add(sizer, 0, wx.ALL, 5)
        
        return box
    
    def _onHollowCheckBox(self, event):
        
        chkbox = event.GetEventObject()
        
        if chkbox.GetValue() == True:
            self.line.set_markerfacecolor("None")
            self.sasm.plot_panel.canvas.draw()
            self.mar_fillcolour.Enable(False)
            self.mar_fillcolour_label.Enable(False)
        else:
            self.mar_fillcolour.Enable(True)
            self.mar_fillcolour_label.Enable(True)
            colour =  self.mar_fillcolour.GetBackgroundColour()
            colour =  (colour[0]/255.0, colour[1]/255.0, colour[2]/255.0)
            self.line.set_markerfacecolor(colour)
            self.sasm.plot_panel.canvas.draw()
    
    def _createLineControls(self):
        
        topbox = wx.StaticBox(self, -1, 'Line') 
        box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
        
        linewidth_label = wx.StaticText(self, -1, 'Width :')
        linestyle_label = wx.StaticText(self, -1, 'Style :')
        linecolour_label = wx.StaticText(self, -1, 'Line Colour :')
        
        self.linewidth = wx.SpinCtrl(self, -1, '1')
        self.linewidth.SetRange(1,99)
        self.linewidth.SetValue(self._old_linewidth)
        self.linewidth.Bind(wx.EVT_SPINCTRL, self.updateLine)
        
        self.linestyle_list = wx.Choice(self, -1, choices = self.linestyle_list_choices)
        self.linestyle_list.Select(self.linestyle_list_choices.index(str(self._linestyle)))
        self.linestyle_list.Bind(wx.EVT_CHOICE, self.updateLine)
        
        self.line_colour = wx.Panel(self, -1, name = 'LineColour', style = wx.RAISED_BORDER)
        self.line_colour.SetBackgroundColour(self._linecolour)
        self.line_colour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
              
        sizer = wx.FlexGridSizer(cols = 2, rows = 5, vgap = 5, hgap = 3)
        
        sizer.Add(linestyle_label, 0)
        sizer.Add(self.linestyle_list, 0, wx.EXPAND)
        sizer.Add(linewidth_label, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.linewidth, 0, wx.EXPAND)
        sizer.Add(linecolour_label, 0)
        sizer.Add(self.line_colour, 0, wx.EXPAND)
  
        box.Add(sizer, 0, wx.ALL, 5)
        
        return box
    
    def getLegendLabel(self):
        return self.legend_label_text.GetValue()
    
    def updateErrorLines(self, data):
        
        for each in self.sasm.err_line:
            for line in each:
                func, param = data
                getattr(line, func)(param)
                
        
    def updateLine(self, event):
        marker =  self.mar_linemarker_list.GetStringSelection()
        width =  self.linewidth.GetValue()
        style =  self.linestyle_list.GetStringSelection()
        
        mar_size = self.mar_size.GetValue()
        err_linewidth = self.err_linewidth.GetValue()
        err_linestyle = self.err_linestyle_list.GetStringSelection()
        
        self.line.set_marker(marker)
        
        colour =  self.mar_linecolour.GetBackgroundColour()
        colour =  (colour[0]/255.0, colour[1]/255.0, colour[2]/255.0)
        
        self.updateErrorLines(['set_linewidth', err_linewidth])
        
        each = self.sasm.err_line[1]
        if err_linestyle != "None":
            for line in each:
                line.set_linestyle(err_linestyle)
        
        self.line.set_markeredgecolor(colour)
        self.line.set_linewidth(float(width))
        self.line.set_linestyle(style)    
        #self.line.set_color(colour)
        self.line.set_markersize(float(mar_size))
        
        self.sasm.plot_panel.canvas.draw()
        
        if event != None:
            event.Skip()
        
    def _onCancelButton(self, event):
        self.line.set_linewidth(self._old_linewidth)
        self.line.set_linestyle(self._old_linestyle)
        self.line.set_color(self._old_linecolour)
        
        self.line.set_marker(self._old_linemarker)
        self.line.set_markeredgecolor(self._old_marlinecolour)
        self.line.set_markerfacecolor(self._old_marcolour)
        self.line.set_markersize(self._old_marsize)
        
        #Stupid errorbars:
        line1, line2 = self.sasm.err_line
        for each in line2:
            each.set_linestyle(self._old_errlinestyle)
            each.set_linewidth(self._old_errlinewidth)
            each.set_color(self._old_errcolour)   
        for each in line1:
            each.set_linewidth(self._old_errlinewidth)
            each.set_color(self._old_errcolour)
        
        self.EndModal(wx.ID_CANCEL)

    def _onOkButton(self, event):
        self.updateLine(None)
      
        self.EndModal(wx.ID_OK)


class SECMLinePropertyDialog(wx.Dialog):
    
    def __init__(self, parent, secm, legend_label, *args, **kwargs):

        if secm.line == None:
            wx.MessageBox('Unable to change line properties.\nNo plot has been made for this item.', 'No plot')
            return
            
        
        wx.Dialog.__init__(self, parent, -1, "Line Properties", *args, **kwargs)
        
        self.secm = secm
        self.line = secm.line
        self.calc_line = secm.calc_line
        self.legend_label = legend_label
        
        self.linewidth_combo_choices = ['1.0', '2.0', '3.0', '4.0', '5.0']
        self.linestyle_list_choices = ['None', '-', '--', '-.', ':']
        self.linemarker_list_choices = ['None', '+', '*', ',','.','1','2','3','4','<', '>', 'D', 'H', '^','_','d','h','o','p','s','v','x','|']
        
        self._linestyle = self.line.get_linestyle()
        self._linemarker = self.line.get_marker()
        self._linewidth = self.line.get_linewidth()

        self._calclinestyle = self.calc_line.get_linestyle()
        self._calclinemarker = self.calc_line.get_marker()
        self._calclinewidth = self.calc_line.get_linewidth()
        
        conv = mplcol.ColorConverter()
        color = conv.to_rgb(self.line.get_color())
        calc_color = conv.to_rgb(self.calc_line.get_color())
        self._old_linecolour = color
        self._old_calclinecolour = calc_color
        color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        calc_color = wx.Colour(int(calc_color[0]*255), int(calc_color[1]*255), int(calc_color[2]*255))
        self._linecolour = color
        self._calclinecolour = calc_color
        
        
        mfc = self.line.get_markerfacecolor()

        if mfc != "None":
            color = conv.to_rgb(mfc)
            self._marcolour = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
            self.hollow_marker = False
        else:
            color = conv.to_rgb(self.line.get_markeredgecolor())
            self._marcolour =  wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
            self.hollow_marker = True
        
        mfc_calc = self.calc_line.get_markerfacecolor()
        if mfc_calc != "None":
            color = conv.to_rgb(mfc_calc)
            self._calcmarcolour = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
            self.hollow_marker_calc = False
        else:
            color = conv.to_rgb(self.calc_line.get_markeredgecolor())
            self._calcmarcolour =  wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
            self.hollow_marker_calc = True

        color = conv.to_rgb(self.line.get_markeredgecolor())
        self._marlinecolour = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))

        color = conv.to_rgb(self.calc_line.get_markeredgecolor())
        self._calcmarlinecolour = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        # color = conv.to_rgb(self.secm.err_line[0][0].get_color())
        # self._errcolour = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
        self._old_linestyle = self.line.get_linestyle()
        self._old_linemarker = self.line.get_marker()
        self._old_linewidth = self.line.get_linewidth()
        self._old_marcolour = self.line.get_markerfacecolor()
        self._old_marlinecolour = self.line.get_markeredgecolor()
        self._old_marsize = self.line.get_markersize()

        self._old_calclinestyle = self.calc_line.get_linestyle()
        self._old_calclinemarker = self.calc_line.get_marker()
        self._old_calclinewidth = self.calc_line.get_linewidth()
        self._old_calcmarcolour = self.calc_line.get_markerfacecolor()
        self._old_calcmarlinecolour = self.calc_line.get_markeredgecolor()
        self._old_calcmarsize = self.calc_line.get_markersize()


        # self._old_errcolour = self.secm.err_line[0][0].get_color()
        # self._old_errlinewidth = self.secm.err_line[0][0].get_linewidth()

        # errstyle = self.secm.err_line[1][0].get_linestyle()
        # strange_errlinestyles = {(None, None) : '-',
        #                         (0,(6.0, 6.0))    : '--',
        #                         (0,(3.0, 5.0, 1.0, 5.0)) : '-.',
        #                         (0,(1.0, 3.0)) : ':'}
        
        # self._old_errlinestyle = strange_errlinestyles[errstyle[0]]
           
        top_sizer = wx.BoxSizer(wx.VERTICAL)

        buttonsizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        self.Bind( wx.EVT_BUTTON, self._onOkButton, id=wx.ID_OK )
        self.Bind( wx.EVT_BUTTON, self._onCancelButton, id=wx.ID_CANCEL )
        
        linesettings_sizer = wx.FlexGridSizer(cols = 2, rows = 2, vgap = 5, hgap = 10)
        linesettings_sizer.Add(self._createLineControls(), 1, wx.EXPAND)
        # linesettings_sizer.Add(self._createErrorBarsControls(), 1, wx.EXPAND)
        linesettings_sizer.Add(self._createLineMarkerControls(), 1, wx.EXPAND)

        calclinesettings_sizer = wx.FlexGridSizer(cols = 2, rows = 2, vgap = 5, hgap = 10)
        calclinesettings_sizer.Add(self._createLineControls(calc = True), 1, wx.EXPAND)
        # linesettings_sizer.Add(self._createErrorBarsControls(), 1, wx.EXPAND)
        calclinesettings_sizer.Add(self._createLineMarkerControls(calc = True), 1, wx.EXPAND)
        
        top_sizer.Add(self._createLegendLabelControls(), 0, wx.ALL | wx.EXPAND, 10)
        top_sizer.Add(linesettings_sizer, 0, wx.ALL | wx.EXPAND, 10)
        top_sizer.Add(calclinesettings_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        top_sizer.Add(wx.StaticLine(self, -1), wx.EXPAND |wx.TOP | wx.BOTTOM, 3)
        top_sizer.Add(buttonsizer, 0, wx.CENTER | wx.BOTTOM, 10)
        
        self.SetSizer(top_sizer)
        self.Fit()
        self.CenterOnParent()
    
    
    def _createLegendLabelControls(self):
        topbox = wx.StaticBox(self, -1, 'Legend Label') 
        box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
        
        self.legend_label_text = wx.TextCtrl(self, -1, self.legend_label)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.legend_label_text, 1, wx.EXPAND)
        
        box.Add(sizer, 0, wx.EXPAND | wx.ALL, 5)
        return box
    
    def _createErrorBarsControls(self):
        topbox = wx.StaticBox(self, -1, 'Error Bars') 
        box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
        
        err_linewidth_label = wx.StaticText(self, -1, 'Width :')
        err_linestyle_label = wx.StaticText(self, -1, 'Style :')
        err_colour_label = wx.StaticText(self, -1, 'Line Colour :')
        
        self.err_linewidth = wx.SpinCtrl(self, -1, '1')
        self.err_linewidth.SetRange(1, 99)
        self.err_linewidth.SetValue(self._old_errlinewidth)
        self.err_linewidth.Bind(wx.EVT_SPINCTRL, self.updateLine)
        
        self.err_linestyle_list = wx.Choice(self, -1, choices = self.linestyle_list_choices)
        self.err_linestyle_list.Select(self.linestyle_list_choices.index(str(self._old_errlinestyle)))
        self.err_linestyle_list.Bind(wx.EVT_CHOICE, self.updateLine)
        
        self.err_colour = wx.Panel(self, -1, name = 'ErrColour', style = wx.RAISED_BORDER)
        self.err_colour.SetBackgroundColour(self._errcolour)
        self.err_colour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
      
        sizer = wx.FlexGridSizer(cols = 2, rows = 5, vgap = 5, hgap = 3)
        sizer.Add(err_linestyle_label, 0)
        sizer.Add(self.err_linestyle_list, 0, wx.EXPAND)
        sizer.Add(err_linewidth_label, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.err_linewidth, 0, wx.EXPAND)
        sizer.Add(err_colour_label, 0)
        sizer.Add(self.err_colour, 0, wx.EXPAND)
      
        box.Add(sizer, 0, wx.ALL, 5)
        
        return box
    
    def _onColourPress(self, event):
        
        colour_panel = event.GetEventObject()
        
        dlg = ColourChangeDialog(self, self.secm, colour_panel.GetName())
        dlg.ShowModal()
        dlg.Destroy()
        
        if colour_panel.GetName() == 'LineColour':
            color = self.line.get_color()
        # elif colour_panel.GetName() == 'ErrColour':
            # color = self.secm.err_line[0][0].get_color()
        elif colour_panel.GetName() == 'MarLineColour':
            color = self.line.get_markeredgecolor()
        elif colour_panel.GetName() == 'MarFillColour':
            color = self.line.get_markerfacecolor()

        elif colour_panel.GetName() == 'CalcLineColour':
            color = self.calc_line.get_color()
        # elif colour_panel.GetName() == 'ErrColour':
            # color = self.secm.err_line[0][0].get_color()
        elif colour_panel.GetName() == 'CalcMarLineColour':
            color = self.calc_line.get_markeredgecolor()
        elif colour_panel.GetName() == 'CalcMarFillColour':
            color = self.calc_line.get_markerfacecolor()
        
        conv = mplcol.ColorConverter()
        
        if color != "None": #Not transparent
            color = conv.to_rgb(color)
            color = wx.Colour(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        
            colour_panel.SetBackgroundColour(color)
            colour_panel.Refresh()
    
    def _createLineMarkerControls(self, calc = False):

        if not calc:
            topbox = wx.StaticBox(self, -1, 'Data Point Marker') 
            box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
            
            mar_size_label = wx.StaticText(self, -1, 'Size :')
            self.mar_fillcolour_label = wx.StaticText(self, -1, 'Fill Colour :')
            self.mar_fillcolour_label.Enable(not self.hollow_marker)
            mar_linecolour_label = wx.StaticText(self, -1, 'Line Colour :')
            mar_linemarker_label = wx.StaticText(self, -1, 'Marker :')
            mar_hollow_label = wx.StaticText(self, -1, 'Hollow :')
            
            #self.mar_size = wx.SpinCtrl(self, -1, '1')
            self.mar_size = RAWCustomCtrl.FloatSpinCtrl(self, -1, '1.0', TextLength = 60, never_negative = True)
            self.mar_size.Bind(RAWCustomCtrl.EVT_MY_SPIN, self.updateLine)
            self.mar_size.SetValue(str(self._old_marsize))
            #self.mar_size.Bind(wx.EVT_SPINCTRL, self.updateLine)
            
            self.mar_fillcolour = wx.Panel(self, -1, name = 'MarFillColour', style = wx.RAISED_BORDER)
            self.mar_fillcolour.SetBackgroundColour(self._marcolour)
            self.mar_fillcolour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
            self.mar_fillcolour.Enable(not self.hollow_marker)
            
            self.mar_linecolour = wx.Panel(self, -1, name = 'MarLineColour', style = wx.RAISED_BORDER)
            self.mar_linecolour.SetBackgroundColour(self._marlinecolour)
            self.mar_linecolour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
            
            self.mar_linemarker_list = wx.Choice(self, -1, choices = self.linemarker_list_choices)
            self.mar_linemarker_list.Select(self.linemarker_list_choices.index(str(self._linemarker)))
            self.mar_linemarker_list.Bind(wx.EVT_CHOICE, self.updateLine)
            
            self.mar_hollow = wx.CheckBox(self, -1)
            self.mar_hollow.SetValue(self.hollow_marker)
            self.mar_hollow.Bind(wx.EVT_CHECKBOX, self._onHollowCheckBox)
          
            sizer = wx.FlexGridSizer(cols = 2, rows = 5, vgap = 5, hgap = 3)
            sizer.Add(mar_linemarker_label, 0)
            sizer.Add(self.mar_linemarker_list, 0, wx.EXPAND)
            sizer.Add(mar_size_label, 0, wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(self.mar_size, 0, wx.EXPAND)
            sizer.Add(mar_linecolour_label, 0)
            sizer.Add(self.mar_linecolour, 0, wx.EXPAND)
            sizer.Add(self.mar_fillcolour_label, 0)
            sizer.Add(self.mar_fillcolour, 0, wx.EXPAND)
            sizer.Add(mar_hollow_label, 0)
            sizer.Add(self.mar_hollow, 0, wx.EXPAND)
            
          
            box.Add(sizer, 0, wx.ALL, 5)

        else:
            topbox = wx.StaticBox(self, -1, 'Calc Data Point Marker') 
            box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
            
            mar_size_label = wx.StaticText(self, -1, 'Size :')
            self.calc_mar_fillcolour_label = wx.StaticText(self, -1, 'Fill Colour :')
            self.calc_mar_fillcolour_label.Enable(not self.hollow_marker_calc)
            mar_linecolour_label = wx.StaticText(self, -1, 'Line Colour :')
            mar_linemarker_label = wx.StaticText(self, -1, 'Marker :')
            mar_hollow_label = wx.StaticText(self, -1, 'Hollow :')
            
            #self.mar_size = wx.SpinCtrl(self, -1, '1')
            self.calc_mar_size = RAWCustomCtrl.FloatSpinCtrl(self, -1, '1.0', TextLength = 60, never_negative = True)
            self.calc_mar_size.Bind(RAWCustomCtrl.EVT_MY_SPIN, self.updateLine)
            self.calc_mar_size.SetValue(str(self._old_calcmarsize))
            #self.mar_size.Bind(wx.EVT_SPINCTRL, self.updateLine)
            
            self.calc_mar_fillcolour = wx.Panel(self, -1, name = 'CalcMarFillColour', style = wx.RAISED_BORDER)
            self.calc_mar_fillcolour.SetBackgroundColour(self._calcmarcolour)
            self.calc_mar_fillcolour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
            self.calc_mar_fillcolour.Enable(not self.hollow_marker_calc)
            
            self.calc_mar_linecolour = wx.Panel(self, -1, name = 'CalcMarLineColour', style = wx.RAISED_BORDER)
            self.calc_mar_linecolour.SetBackgroundColour(self._calcmarlinecolour)
            self.calc_mar_linecolour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
            
            self.calc_mar_linemarker_list = wx.Choice(self, -1, choices = self.linemarker_list_choices)
            self.calc_mar_linemarker_list.Select(self.linemarker_list_choices.index(str(self._calclinemarker)))
            self.calc_mar_linemarker_list.Bind(wx.EVT_CHOICE, self.updateLine)
            
            self.calc_mar_hollow = wx.CheckBox(self, -1)
            self.calc_mar_hollow.SetValue(self.hollow_marker_calc)
            self.calc_mar_hollow.Bind(wx.EVT_CHECKBOX, self._onHollowCheckBoxCalc)
          
            sizer = wx.FlexGridSizer(cols = 2, rows = 5, vgap = 5, hgap = 3)
            sizer.Add(mar_linemarker_label, 0)
            sizer.Add(self.calc_mar_linemarker_list, 0, wx.EXPAND)
            sizer.Add(mar_size_label, 0, wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(self.calc_mar_size, 0, wx.EXPAND)
            sizer.Add(mar_linecolour_label, 0)
            sizer.Add(self.calc_mar_linecolour, 0, wx.EXPAND)
            sizer.Add(self.calc_mar_fillcolour_label, 0)
            sizer.Add(self.calc_mar_fillcolour, 0, wx.EXPAND)
            sizer.Add(mar_hollow_label, 0)
            sizer.Add(self.calc_mar_hollow, 0, wx.EXPAND)
            
          
            box.Add(sizer, 0, wx.ALL, 5)
        
        return box
    
    def _onHollowCheckBox(self, event):
        
        chkbox = event.GetEventObject()
        
        if chkbox.GetValue() == True:
            self.line.set_markerfacecolor("None")
            self.secm.plot_panel.canvas.draw()
            self.mar_fillcolour.Enable(False)
            self.mar_fillcolour_label.Enable(False)
        else:
            self.mar_fillcolour.Enable(True)
            self.mar_fillcolour_label.Enable(True)
            colour =  self.mar_fillcolour.GetBackgroundColour()
            colour =  (colour[0]/255.0, colour[1]/255.0, colour[2]/255.0)
            self.line.set_markerfacecolor(colour)
            self.secm.plot_panel.canvas.draw()

    def _onHollowCheckBoxCalc(self, event):
        
        chkbox = event.GetEventObject()
        
        if chkbox.GetValue() == True:
            self.calc_line.set_markerfacecolor("None")
            self.secm.plot_panel.canvas.draw()
            self.calc_mar_fillcolour.Enable(False)
            self.calc_mar_fillcolour_label.Enable(False)
        else:
            self.calc_mar_fillcolour.Enable(True)
            self.calc_mar_fillcolour_label.Enable(True)
            colour =  self.calc_mar_fillcolour.GetBackgroundColour()
            colour =  (colour[0]/255.0, colour[1]/255.0, colour[2]/255.0)
            self.calc_line.set_markerfacecolor(colour)
            self.secm.plot_panel.canvas.draw()

    def _createLineControls(self, calc = False):
        
        if not calc:
            topbox = wx.StaticBox(self, -1, 'Line') 
            box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
            
            linewidth_label = wx.StaticText(self, -1, 'Width :')
            linestyle_label = wx.StaticText(self, -1, 'Style :')
            linecolour_label = wx.StaticText(self, -1, 'Line Colour :')
            
            self.linewidth = wx.SpinCtrl(self, -1, '1')
            self.linewidth.SetRange(1,99)
            self.linewidth.SetValue(self._old_linewidth)
            self.linewidth.Bind(wx.EVT_SPINCTRL, self.updateLine)
            
            self.linestyle_list = wx.Choice(self, -1, choices = self.linestyle_list_choices)
            self.linestyle_list.Select(self.linestyle_list_choices.index(str(self._linestyle)))
            self.linestyle_list.Bind(wx.EVT_CHOICE, self.updateLine)
            
            self.line_colour = wx.Panel(self, -1, name = 'LineColour', style = wx.RAISED_BORDER)
            self.line_colour.SetBackgroundColour(self._linecolour)
            self.line_colour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
                  
            sizer = wx.FlexGridSizer(cols = 2, rows = 5, vgap = 5, hgap = 3)
            
            sizer.Add(linestyle_label, 0)
            sizer.Add(self.linestyle_list, 0, wx.EXPAND)
            sizer.Add(linewidth_label, 0, wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(self.linewidth, 0, wx.EXPAND)
            sizer.Add(linecolour_label, 0)
            sizer.Add(self.line_colour, 0, wx.EXPAND)
      
            box.Add(sizer, 0, wx.ALL, 5)

        else:
            topbox = wx.StaticBox(self, -1, 'Calc Line') 
            box = wx.StaticBoxSizer(topbox, wx.VERTICAL)
            
            linewidth_label = wx.StaticText(self, -1, 'Width :')
            linestyle_label = wx.StaticText(self, -1, 'Style :')
            linecolour_label = wx.StaticText(self, -1, 'Line Colour :')
            
            self.calc_linewidth = wx.SpinCtrl(self, -1, '1')
            self.calc_linewidth.SetRange(1,99)
            self.calc_linewidth.SetValue(self._old_calclinewidth)
            self.calc_linewidth.Bind(wx.EVT_SPINCTRL, self.updateLine)
            
            self.calc_linestyle_list = wx.Choice(self, -1, choices = self.linestyle_list_choices)
            self.calc_linestyle_list.Select(self.linestyle_list_choices.index(str(self._calclinestyle)))
            self.calc_linestyle_list.Bind(wx.EVT_CHOICE, self.updateLine)
            
            self.calc_line_colour = wx.Panel(self, -1, name = 'CalcLineColour', style = wx.RAISED_BORDER)
            self.calc_line_colour.SetBackgroundColour(self._calclinecolour)
            self.calc_line_colour.Bind(wx.EVT_LEFT_DOWN, self._onColourPress)
                  
            sizer = wx.FlexGridSizer(cols = 2, rows = 5, vgap = 5, hgap = 3)
            
            sizer.Add(linestyle_label, 0)
            sizer.Add(self.calc_linestyle_list, 0, wx.EXPAND)
            sizer.Add(linewidth_label, 0, wx.ALIGN_CENTER_VERTICAL)
            sizer.Add(self.calc_linewidth, 0, wx.EXPAND)
            sizer.Add(linecolour_label, 0)
            sizer.Add(self.calc_line_colour, 0, wx.EXPAND)
      
            box.Add(sizer, 0, wx.ALL, 5)
        
        return box
    
    def getLegendLabel(self):
        return self.legend_label_text.GetValue()
    
    def updateErrorLines(self, data):
        
        for each in self.secm.err_line:
            for line in each:
                func, param = data
                getattr(line, func)(param)
                
        
    def updateLine(self, event):
        marker =  self.mar_linemarker_list.GetStringSelection()
        width =  self.linewidth.GetValue()
        style =  self.linestyle_list.GetStringSelection()
        
        mar_size = self.mar_size.GetValue()
        # err_linewidth = self.err_linewidth.GetValue()
        # err_linestyle = self.err_linestyle_list.GetStringSelection()
        
        self.line.set_marker(marker)
        
        colour =  self.mar_linecolour.GetBackgroundColour()
        colour =  (colour[0]/255.0, colour[1]/255.0, colour[2]/255.0)
        
        # self.updateErrorLines(['set_linewidth', err_linewidth])
        
        # each = self.secm.err_line[1]
        # if err_linestyle != "None":
        #     for line in each:
        #         line.set_linestyle(err_linestyle)
        
        self.line.set_markeredgecolor(colour)
        self.line.set_linewidth(float(width))
        self.line.set_linestyle(style)    
        #self.line.set_color(colour)
        self.line.set_markersize(float(mar_size))


        calc_marker =  self.calc_mar_linemarker_list.GetStringSelection()
        calc_width =  self.calc_linewidth.GetValue()
        calc_style =  self.calc_linestyle_list.GetStringSelection()
        
        calc_mar_size = self.calc_mar_size.GetValue()
        # err_linewidth = self.err_linewidth.GetValue()
        # err_linestyle = self.err_linestyle_list.GetStringSelection()
        
        self.calc_line.set_marker(calc_marker)
        
        calc_colour =  self.calc_mar_linecolour.GetBackgroundColour()
        calc_colour =  (calc_colour[0]/255.0, calc_colour[1]/255.0, calc_colour[2]/255.0)
        
        # self.updateErrorLines(['set_linewidth', err_linewidth])
        
        # each = self.secm.err_line[1]
        # if err_linestyle != "None":
        #     for line in each:
        #         line.set_linestyle(err_linestyle)
        
        self.calc_line.set_markeredgecolor(calc_colour)
        self.calc_line.set_linewidth(float(calc_width))
        self.calc_line.set_linestyle(calc_style)    
        #self.line.set_color(colour)
        self.calc_line.set_markersize(float(calc_mar_size))
        
        self.secm.plot_panel.canvas.draw()
        
        if event != None:
            event.Skip()
        
    def _onCancelButton(self, event):
        self.line.set_linewidth(self._old_linewidth)
        self.line.set_linestyle(self._old_linestyle)
        self.line.set_color(self._old_linecolour)
        
        self.line.set_marker(self._old_linemarker)
        self.line.set_markeredgecolor(self._old_marlinecolour)
        self.line.set_markerfacecolor(self._old_marcolour)
        self.line.set_markersize(self._old_marsize)


        self.calc_line.set_linewidth(self._old_calclinewidth)
        self.calc_line.set_linestyle(self._old_calclinestyle)
        self.calc_line.set_color(self._old_calclinecolour)
        
        self.calc_line.set_marker(self._old_linemarker)
        self.calc_line.set_markeredgecolor(self._old_calcmarlinecolour)
        self.calc_line.set_markerfacecolor(self._old_calcmarcolour)
        self.calc_line.set_markersize(self._old_calcmarsize)
        
        #Stupid errorbars:
        # line1, line2 = self.secm.err_line
        # for each in line2:
        #     each.set_linestyle(self._old_errlinestyle)
        #     each.set_linewidth(self._old_errlinewidth)
        #     each.set_color(self._old_errcolour)   
        # for each in line1:
        #     each.set_linewidth(self._old_errlinewidth)
        #     each.set_color(self._old_errcolour)
        
        self.EndModal(wx.ID_CANCEL)

    def _onOkButton(self, event):
        self.updateLine(None)
      
        self.EndModal(wx.ID_OK)
        
#--- ** Startup app **


class WelcomeDialog(wx.Dialog):
    def __init__(self, parent, *args, **kwargs):
        
        wx.Dialog.__init__(self,parent, -1, *args, **kwargs)
        
        self.ok_button = wx.Button(self, -1, 'OK')       
        self.ok_button.Bind(wx.EVT_BUTTON, self._onOKButton)
        self.ok_button.SetDefault()
        
        button_sizer = wx.BoxSizer()
        button_sizer.Add(self.ok_button,0, wx.RIGHT, 5) 
        
        raw_bitmap = raw_icon_embed.GetBitmap()
        rawimg = wx.StaticBitmap(self, -1, raw_bitmap)
        
        headline = wx.StaticText(self, -1, 'Welcome to RAW 1.0.0b!')
        
        text1 = 'Developers/Contributors:'
        text2 = '\nSoren S. Nielsen'
        text3 = 'Jesse B. Hopkins'
        text4 = 'Richard E. Gillilan'
        text5 = 'Jesper Nygaard'
        text6 = 'Kurt Andersen'
        
        text7 = '\nHelp this software become better by reporting bugs to: sskn@life.ku.dk'
        
        text8 = '\nIf you use this software for your SAXS data processing please cite:\n\n'
        text9 = '"BioXTAS RAW, a software program for high-throughput automated small-angle\nX-ray scattering data reduction and preliminary analysis", J. Appl. Cryst. (2009). 42, 959-964\n\n'


        all_text = [text1, text2, text3, text4, text5, text6, text7, text8, text9]
        
        final_sizer = wx.BoxSizer(wx.VERTICAL)
        final_sizer.Add(rawimg, 0, wx.TOP | wx.ALIGN_CENTER_HORIZONTAL, 10)
        final_sizer.Add(headline, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 15)
        
        for each in all_text:
            txt = wx.StaticText(self, -1, each)
            final_sizer.Add(txt, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.LEFT | wx.RIGHT, 15)

        #label = wx.StaticText(self, -1, ' ')
        
        #final_sizer.Add(label, 0, wx.ALL, 15)
        final_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        
        self.SetSizer(final_sizer)
        self.Fit()
        self.CenterOnParent()
        # self.ToggleWindowStyle(wx.STAY_ON_TOP)
    
    def _onOKButton(self, event):
        # mainworker_cmd_queue.put(['startup', sys.argv])
        wx.FutureCall(1, wx.FindWindowByName("MainFrame")._onStartup, sys.argv)
        self.EndModal(wx.ID_OK)
        
    def _onCancelButton(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def getFilename(self):
        return self._filename


class MyApp(wx.App):

    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        # This catches events when the app is asked to activate by some other
        # process on Mac
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate) 
    
    def OnInit(self):    
        MySplash = MySplashScreen()
        MySplash.Show()

        #On Mac, catch files asked to open
        # print sys.argv
        for f in  sys.argv[1:]:
            # self.OpenFileMessage(f)
            print f
        
        return True

    def BringWindowToFront(self):
        try: # it's possible for this event to come when the frame is closed
            self.GetTopWindow().Raise()
        except:
            pass
    
    def OnActivate(self, event):
        # if this is an activate event, rather than something else, like iconize.
        if event.GetActive():
            self.BringWindowToFront()
        event.Skip()

    #Mac specific
    def MacOpenFile(self, filename):
        """Called for files droped on dock icon, or opened via finders context menu"""
        if filename != 'RAW.py':
            print filename
            print "%s dropped on app"%(filename) #code to load filename goes here.
        # self.OpenFileMessage(filename)
    
    #Mac specific
    def MacReopenApp(self):
        """Called when the doc icon is clicked, and ???"""
        self.BringWindowToFront()

    #Mac specific
    def MacNewFile(self):
        pass
    
    #Mac specific
    def MacPrintFile(self, file_path):
        pass
    
class MySplashScreen(wx.SplashScreen):
    """
        Create a splash screen widget.
    """
    
    def __init__(self, parent = None):
        
        aBitmap = wx.Image(name = os.path.join(RAWWorkDir, "resources","logo_atom.gif")).ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 2000 # milliseconds
        
        wx.SplashScreen.__init__(self, aBitmap, splashStyle, splashDuration, parent)
        
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        wx.Yield()

        self.fc = wx.FutureCall(1, self.ShowMain)

    def OnExit(self, evt):
        if self.fc.IsRunning():
            self.fc.Stop()
            self.ShowMain()
        self.Hide()
        evt.Skip()
        
    def ShowMain(self):            
        frame = MainFrame('RAW 1.0.0b', -1)
        
        dlg = WelcomeDialog(frame, name = "WelcomeDialog")
        dlg.ShowModal()

        
    

        # The program will freeze without this line.


raw_icon_embed =PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAVlpVFh0"
    "WE1MOmNvbS5hZG9iZS54bXAAAAAAADx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0"
    "YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDUuNC4wIj4KICAgPHJkZjpSREYgeG1sbnM6cmRmPSJo"
    "dHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICAgICAgPHJk"
    "ZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgICAgICAgICAgeG1sbnM6dGlmZj0iaHR0"
    "cDovL25zLmFkb2JlLmNvbS90aWZmLzEuMC8iPgogICAgICAgICA8dGlmZjpPcmllbnRhdGlv"
    "bj4xPC90aWZmOk9yaWVudGF0aW9uPgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9y"
    "ZGY6UkRGPgo8L3g6eG1wbWV0YT4KTMInWQAABLRJREFUaAXtV1tMW2Uc/xVakFJKKyut3Mpg"
    "FCvrNtYZiHtwy1ymMV4SExNNTDRG46vxRY3vPvuCPuzJy4NOEnd5cIlkxgtlssoUSIUOhHLr"
    "KbBCKZRr6/f/u6+eWpLF1Hg8S//J6fed//32/b9TA16/kYGOwVhTadSx+4DxgN4DqLEUK6Bp"
    "C+r/DOj/EFtKNW2BQo0XW6jQDBYqX7wHCs1gofK6r4BhdzOj6485Q0ZAoWXUUr5ES+P/hm3d"
    "B7Dvp+ivwRsom53OSZDVfn/Ou5YvSVcdPJ52diHvDJDzE59+ggdHg0i7alESjfGqpcPSduNG"
    "nLchRwvw8mvo6upGXgDj42OIhEJS5q5rRXl5Hk9qaysPRwjJ+3e6xBOPpBGO9pJG+7Vvr3Fi"
    "660m9DUeQffb7yKnhRYUBQs3h+BOJUnXXWHPZse2wwHfcX+W97sLn8OpzGbf1ZuM9wgcvqMY"
    "HQjAvbLEpM3ECjKPnGId4fA40qERlK78mWliSNU3wXfmLKKxGCL910DOE9RtJllPTgCRqd9x"
    "4MoXcN4pFXOKn7nETlZQ4uQ69cY7cov+q1+zPLXdfpAe7Mfae++jyuXCdu/H3J5u4VBodgbR"
    "hkYYAt+j7vJnOaLULuEmN9OsQ0HgTgBzrgb4/cf+qgBlXxH9byXjkkk4Hjp5BtZjnZgTahOi"
    "Ou0Tw2yYrCRa22EXygmGfw7CePHLLI1wv3X4OVPWiTF6ZdrW1ctoev4lBFp98Eb7ODnkWOCj"
    "HtYtk0UrgTUxhtEPe+BZngGNTMKT3frHn4C7oZlxzLgoslAWvM57YmLGTj87X1tpzvaiOrvm"
    "h7xoa/OASj/f8wGko6SEnK86dRqUKYL4xg4/JaIKZIscIEcIT+D9sS8bfH91AyeOCeKHBora"
    "ruLrRFPzQSZnW2jq+gDui8WzCu1mExR3G3ZF1uuF8vVyG1zxRVB3Em268SBazj3FvUkZco6N"
    "M00arbw1gbR4LAIhnSTa6uQcFDHljr/1JoIiOMusIhgWpRiSdgeMTz+Hw14vJiOTsAq9alAe"
    "7kbHY2fxgNPJaA6AJs9eOAyLShFlx1wvsicemklmoUwamhHBbPu7UFVtw2DvBZCzEhLtHqSs"
    "uXfGOlpRkbiddcY5OICp/gEcfuFFdlLqJR3JE352niq7cO5JJEVSpV8UHFWV7ErgAGhsqp0g"
    "IrVH1zPPMt+0OCzh4E0kLvWyE6SwengIEf8JDnLtUCvIyYzNxq1xVJR3eyclbfD6y6UrUFSB"
    "lS4todlcztlWxHiU4BSznZwn8Dx6GgHhm3omUmVk9onHSNmnw2mutSMhHgLKoEWMNgl0WMpM"
    "FRicm8WtkVEcMpmwNzyCqp9+wG5bByCyQkAz2263Y211RYpm12aPBzGqqApWlSWeSFKeSEYh"
    "TwNBAgUk7wbCqbNP74b5aDRDBuPxOBuXq7yqiUnCNxe/Qvr8edH384xy1dZJ0n+yUnv5X32F"
    "p480mHcTS8J+K31m0GHXCmpaWnFSTC81/KMA1IL/l73uP6eLAWjdSsbb67ta+1CQfRHAXkEK"
    "tBY2Luu/AsUW0rSL7oVDrPMWWt7Q+RQq3gOaHmHx/0H3FbgHLrLiIdb0FPwBwjQD94YpSggA"
    "AAAASUVORK5CYII=")

class RawTaskbarIcon(wx.TaskBarIcon):
    TBMENU_RESTORE = wx.NewId()
    TBMENU_CLOSE   = wx.NewId()
    TBMENU_CHANGE  = wx.NewId()
    TBMENU_REMOVE  = wx.NewId()
 
    #----------------------------------------------------------------------
    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)
        self.frame = frame
 
        # Set the image
        self.tbIcon = raw_icon_embed.GetIcon()
 
        self.SetIcon(self.tbIcon, "Test")
 
        # bind some events
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeftClick)
 
    #----------------------------------------------------------------------
    def CreatePopupMenu(self, evt=None):
        """
        This method is called by the base class when it needs to popup
        the menu for the default EVT_RIGHT_DOWN event.  Just create
        the menu how you want it and return it from this function,
        the base class takes care of the rest.
        """
        menu = wx.Menu()
        menu.Append(self.TBMENU_RESTORE, "Open Program")
        menu.Append(self.TBMENU_CHANGE, "Show all the Items")
        menu.AppendSeparator()
        menu.Append(self.TBMENU_CLOSE,   "Exit Program")
        return menu
 
    #----------------------------------------------------------------------
    def OnTaskBarActivate(self, evt):
        """"""
        pass
 
    #----------------------------------------------------------------------
    def OnTaskBarClose(self, evt):
        """
        Destroy the taskbar icon and frame from the taskbar icon itself
        """
        self.frame.Close()
 
    #----------------------------------------------------------------------
    def OnTaskBarLeftClick(self, evt):
        """
        Create the right-click menu
        """
        menu = self.CreatePopupMenu()
        self.PopupMenu(menu)
        menu.Destroy()
       
if __name__ == '__main__':
    app = MyApp(0)   #MyApp(redirect = True)
    app.MainLoop()
        