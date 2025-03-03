'''
Created on Aug 16, 2010

@author: Nielsen

#******************************************************************************
# This file is part of RAW.
#
#    RAW is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
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
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import object, range, map, zip
from io import open

import os
import platform

import matplotlib
matplotlib.rcParams['backend'] = 'WxAgg'
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import wx
import numpy as np
import matplotlib.pyplot as plt

raw_path = os.path.abspath(os.path.join('.', __file__, '..', '..'))
if raw_path not in os.sys.path:
    os.sys.path.append(raw_path)

import bioxtasraw.RAWGlobals as RAWGlobals
import bioxtasraw.SASMask as SASMask
import bioxtasraw.SASCalib as SASCalib
import bioxtasraw.RAWCustomCtrl as RAWCustomCtrl
import bioxtasraw.SASUtils as SASUtils

class ImagePanelToolbar(NavigationToolbar2WxAgg):
    ''' The toolbar under the image in the image panel '''

    def __init__(self, parent, canvas):

        self.fig_axes = parent.fig.gca()
        self.parent = parent
        self.main_frame = wx.FindWindowByName('MainFrame')

        self._MTB_HDRINFO = self.NewControlId()
        self._MTB_IMGSET = self.NewControlId()
        self._MTB_PREVIMG = self.NewControlId()
        self._MTB_NEXTIMG = self.NewControlId()
        self._MTB_GOTO = self.NewControlId()


        self._tool_ids = {
            'hdrinfo'   : self._MTB_HDRINFO,
            'imgset'    : self._MTB_IMGSET,
            'previmg'   : self._MTB_PREVIMG,
            'nextimg'   : self._MTB_NEXTIMG,
            'goto'      : self._MTB_GOTO,
            }

        if (float(matplotlib.__version__.split('.')[0]) == 3 and
            float(matplotlib.__version__.split('.')[1]) >= 3 and
            float(matplotlib.__version__.split('.')[2]) >= 1 or
            float(matplotlib.__version__.split('.')[0]) > 3):
            NavigationToolbar2WxAgg.__init__(self, canvas, coordinates=False)
        else:
            NavigationToolbar2WxAgg.__init__(self, canvas)

        self._getIcons()

        if wx.version().split()[0].strip()[0] >= '4':
            self.AddSeparator()
            self.AddTool(self._MTB_HDRINFO, '', self._bitmaps['hdrinfo'], 
                shortHelp='Show Header Information')
            self.AddTool(self._MTB_IMGSET, '', self._bitmaps['imgset'], 
                shortHelp='Image Display Settings')
            self.AddSeparator()
            self.AddTool(self._MTB_PREVIMG, '', self._bitmaps['previmg'], 
                shortHelp='Previous Image')
            self.AddTool(self._MTB_NEXTIMG, '', self._bitmaps['nextimg'], 
                shortHelp='Next Image')
            self.AddTool(self._MTB_GOTO, '', self._bitmaps['goto'],
                shortHelp='Go To Image')
        else:
            self.AddSeparator()
            self.AddSimpleTool(self._MTB_HDRINFO, self._bitmaps['hdrinfo'], 
                'Show Header Information')
            self.AddSimpleTool(self._MTB_IMGSET, self._bitmaps['imgset'], 
                'Image Display Settings')
            self.AddSeparator()
            self.AddSimpleTool(self._MTB_PREVIMG, self._bitmaps['previmg'], 
                'Previous Image')
            self.AddSimpleTool(self._MTB_NEXTIMG, self._bitmaps['nextimg'], 
                'Next Image')
            self.AddSimpleTool(self._MTB_GOTO, '', self._bitmaps['goto'],
                'Go To Image')


        self.Bind(wx.EVT_TOOL, self.onHeaderInfoButton, id = self._MTB_HDRINFO)
        self.Bind(wx.EVT_TOOL, self.onImageSettingsButton, id = self._MTB_IMGSET)

        self.Bind(wx.EVT_TOOL, self.onPreviousImgButton, id = self._MTB_PREVIMG)
        self.Bind(wx.EVT_TOOL, self.onNextImgButton, id = self._MTB_NEXTIMG)
        self.Bind(wx.EVT_TOOL, self.onGoToImgButton, id = self._MTB_GOTO)


        self.Realize()

        self._current_tool = None

    def _getIcons(self):
        hdrInfoIcon = wx.Bitmap(self.main_frame.hdrInfoIcon)
        ImgSetIcon = wx.Bitmap(self.main_frame.ImgSetIcon)
        prevImgIcon = wx.Bitmap(self.main_frame.prevImgIcon)
        nextImgIcon = wx.Bitmap(self.main_frame.nextImgIcon)
        goToIcon = wx.Bitmap(self.main_frame.goToIcon)

        self._bitmaps = {
            'hdrinfo'   : hdrInfoIcon,
            'imgset'    : ImgSetIcon,
            'previmg'   : prevImgIcon,
            'nextimg'   : nextImgIcon,
            'goto'      : goToIcon,
            }

    def getCurrentTool(self):
        return self._current_tool

    def onPreviousImgButton(self, event):
        try:
            current_file = self.parent.current_sasm.getParameter('filename')
        except AttributeError:
            current_file = None
        RAWGlobals.mainworker_cmd_queue.put(['show_nextprev_img', [current_file,
            -1, self.parent.current_index, self.parent.total_frames]])

    def onNextImgButton(self, event):
        try:
            current_file = self.parent.current_sasm.getParameter('filename')
        except AttributeError:
            current_file = None
        RAWGlobals.mainworker_cmd_queue.put(['show_nextprev_img', [current_file,
            1, self.parent.current_index, self.parent.total_frames]])

    def onGoToImgButton(self, event):
        if self.parent.img is not None and self.parent.multi_image_file:
            frame = wx.GetNumberFromUser("Select an image in the current multi-image file",
                "Image #:", "Select Image", self.parent.current_index+1,
                min=1, max=self.parent.total_frames, parent=self.parent)

            if frame != -1:
                try:
                    current_file = self.parent.current_sasm.getParameter('filename')
                except AttributeError:
                    current_file = None

                if current_file is not None:
                    RAWGlobals.mainworker_cmd_queue.put(['show_goto_img', [current_file,
                        frame-1]])

    def onImageSettingsButton(self, event):
        self.parent.showImageSetDialog()

    def onHeaderInfoButton(self, event):
        self._deactivatePanZoom()
        self.parent.showHdrInfo()

    def _deactivateMaskTools(self):
        self.parent.stopMaskCreation()

    def _deactivatePanZoom(self):
        ''' Disable the zoon and pan buttons if they are pressed: '''

        if float(matplotlib.__version__[:3]) >= 1.2:
            wxid = self.wx_ids['Zoom']
        else:
            wxid = self._NTB2_ZOOM

        if self.GetToolState(wxid):
            self.ToggleTool(wxid, False)
            NavigationToolbar2WxAgg.zoom(self)

        if float(matplotlib.__version__[:3]) >= 1.2:
            wxid = self.wx_ids['Pan']
        else:
            wxid = self._NTB2_PAN

        if self.GetToolState(wxid):
            self.ToggleTool(wxid, False)
            NavigationToolbar2WxAgg.pan(self)

        self._current_tool = None

    ## Overridden functions:

    def home(self, *args, **kwargs):
        self.parent.fitAxis()
        self.parent.canvas.draw()

    def zoom(self, *args):
        masking_panel = wx.FindWindowByName('MaskingPanel')
        if masking_panel.IsShown():
            self._deactivateMaskTools()

        if float(matplotlib.__version__[:3]) >= 1.2:
            wxid = self.wx_ids['Pan']
        else:
            wxid = self._NTB2_PAN

        self.ToggleTool(wxid, False)
        NavigationToolbar2WxAgg.zoom(self, *args)

        if self.GetToolState(args[0].GetId()):
            self._current_tool = 'Zoom'
        else:
            self._current_tool = None

    def pan(self, *args):
        masking_panel = wx.FindWindowByName('MaskingPanel')
        if masking_panel.IsShown():
            self._deactivateMaskTools()

        if float(matplotlib.__version__[:3]) >= 1.2:
            wxid = self.wx_ids['Zoom']
        else:
            wxid = self._NTB2_ZOOM

        self.ToggleTool(wxid, False)
        NavigationToolbar2WxAgg.pan(self, *args)

        if self.GetToolState(args[0].GetId()):
            self._current_tool = 'Pan'
        else:
            self._current_tool = None

    def updateColors(self):
        self._getIcons()

        for name in ["hdrinfo", "imgset", "nextimg", "previmg"]:
            self.SetToolNormalBitmap(self._tool_ids[name],
                self._bitmaps[name])

class ImagePanel(wx.Panel):

    def __init__(self, parent, panel_id, name, *args, **kwargs):

        wx.Panel.__init__(self, parent, panel_id, *args, name = name, **kwargs)

        file_drop_target = RAWCustomCtrl.RawPlotFileDropTarget(self, 'image')
        self.SetDropTarget(file_drop_target)

        self.fig = matplotlib.figure.Figure((5,4), 75)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)

        self.toolbar = ImagePanelToolbar(self, self.canvas)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.LEFT|wx.TOP|wx.GROW)
        sizer.Add(self.toolbar, 0, wx.GROW)

        #color = parent.GetThemeBackgroundColour()
        #self.SetColor(color)

        self.fig.gca().set_visible(False)
        self.SetSizer(sizer)

        self.img = None
        self.current_sasm = None
        self.multi_image_file = False
        self.current_index = 0
        self.img_list = None

        self._canvas_cursor = None
        self._selected_patch = None
        self._first_mouse_pos = None      # Used to keep the mouse position at the same place
                                        # when moving a patch.

        self.current_tool = None

        self._polygon_guide_line = None
        self._rectangle_line = None
        self._circle_guide_line = None

        self._plotting_in_progress = False
        self._movement_in_progress = False
        self._right_click_on_patch = False

        self._chosen_points_x = []
        self._chosen_points_y = []
        self._plotted_patches = []
        self.center_patch = None
        self._resizing = False

        self.next_mask_number = 0

        self.center_click_mode = False
        self.pyfai_cent_mode = False
        self.pyfai_ring_num = 0

        self.multi_image_file = False
        self.current_index = 0
        self.total_frames = 1

        self.pyfai_color_cycle = ['y', 'c', 'g', 'b', 'k', 'w']

        self.plot_parameters = {'axesscale'         : 'linlin',
                                'storedMasks'       : [],
                                'UpperClim'         : None,
                                'LowerClim'         : None,
                                'ClimLocked'        : False,
                                'ImgScale'          : 'linear',
                                'ColorMap'          : matplotlib.cm.jet,
                                'Brightness'        : 100,
                                'Contrast'          : 100,
                                'maxImgval'         : None,
                                'minImgVal'         : None}

        self.canvas.draw()

        self.canvas.mpl_connect('motion_notify_event', self._onMouseMotion)
        self.canvas.mpl_connect('button_press_event', self._onMouseButtonPressEvent)
        self.canvas.mpl_connect('button_release_event', self._onMouseButtonReleaseEvent)
        self.canvas.mpl_connect('pick_event', self._onPickEvent)
        self.canvas.mpl_connect('key_press_event', self._onKeyPressEvent)
        self.canvas.mpl_connect('scroll_event', self._onMouseScroll)

        self.draw_cid = self.canvas.mpl_connect('draw_event', self.safe_draw)

    def updateColors(self):
        SASUtils.update_mpl_style()

        self.canvas.draw()

        self.toolbar.updateColors()

    def showHdrInfo(self):

        if self.current_sasm is not None:
            diag = HdrInfoDialog(self, self.current_sasm)
            diag.ShowModal()
            diag.Destroy()

    def addLine(self, xpoints, ypoints, color = 'red'):

        a = self.fig.gca()

        a.add_line(matplotlib.lines.Line2D(xpoints, ypoints, color = color))
        self.canvas.draw()

    def setTool(self, tool):
        self.current_tool = tool

        if tool in ['circle', 'rectangle', 'polygon']:
            self.toolbar._deactivatePanZoom()

    def getTool(self):
        return self.current_tool

    def safe_draw(self, event = None):
        self.canvas.mpl_disconnect(self.draw_cid)
        self.canvas.draw()
        self.draw_cid = self.canvas.mpl_connect('draw_event', self.safe_draw)

        if wx.FindWindowByName('CenteringPanel').IsShown() and self.img is not None:
            a = self.fig.gca()
            self.background = self.canvas.copy_from_bbox(a.bbox)

            self.canvas.restore_region(self.background)

            for patch in a.patches:
                if patch.get_animated():
                    a.draw_artist(patch)
            self.canvas.blit(a.bbox)

    def fitAxis(self):

        if self.img is None:
            return

        img_ydim, img_xdim = self.img.shape

        a = self.fig.gca()

        a.set_xlim((0, img_xdim))
        a.set_ylim((0, img_ydim))


    def untoggleAllToolButtons(self):
        self.masking_panel = wx.FindWindowByName('MaskingPanel')
        self.masking_panel.disableDrawButtons()
        self.setTool(None)

    def showImage(self, img, sasm, fnum=0, num_frames=1):
        ''' This function is the one that gets called when a new
        image is to be displayed '''

        if num_frames > 1:
            self.multi_image_file = True
            self.current_index = fnum
            self.total_frames = num_frames
        else:
            self.multi_image_file = False
            self.current_index = 0
            self.total_frames = 1

        if isinstance(img, list):
            img = img[0]

        if isinstance(sasm, list):
            sasm = sasm[0]

        self.current_sasm = sasm

        self.showNewImage(img)

    def showNewImage(self, img):
        self.img = np.flipud(img)

        a = self.fig.gca()
        xlims = a.get_xlim()
        ylims = a.get_ylim()

        self.fig.clear() #Important! or a memory leak will occur!

        a = self.fig.gca()

        img_ydim, img_xdim = self.img.shape
        extent = (0, img_xdim, 0, img_ydim)
        self.imgobj = a.imshow(self.img, interpolation = 'nearest', extent = extent)

        self.imgobj.cmap = self.plot_parameters['ColorMap']


        img_hdr = self.current_sasm.getParameter('imageHeader')

        if 'Meas.Description' in img_hdr:
            title_str = img_hdr['Meas.Description'] + '\n'
        else:
            title_str = ''
        if 'load_path' in self.current_sasm.getAllParameters():
            title_str = title_str + os.path.split(self.current_sasm.getParameter('load_path'))[-1]
        else:
            title_str = title_str + self.current_sasm.getParameter('filename')
        if self.multi_image_file:
            title_str = title_str + '  Image: %i of %i' %(self.current_index+1, self.total_frames)

        a.set_title(title_str)
        a.set_xlabel('x (pixels)')
        a.set_ylabel('y (pixels)')
        a.axis('image')

        self.plotStoredMasks(update=False)

        mainframe = wx.FindWindowByName('MainFrame')

        settings = mainframe.raw_settings

        mask_dict = settings.get('Masks')
        try:
            bs_mask = np.flipud(mask_dict['BeamStopMask'][0]) == 1
        except Exception:
            bs_mask = None

        if bs_mask is None:
            bs_mask = np.ones(self.img.shape) == 1

        try:
            if 'eiger2' in settings.get('Detector'):
                if settings.get('ExcludeMaskFromImageScale'):
                    self.plot_parameters['maxImgVal'] = self.img[np.logical_and(self.img<4294967295, bs_mask)].max()
                else:
                    self.plot_parameters['maxImgVal'] = self.img[self.img<4294967295].max()

            else:
                if settings.get('ExcludeMaskFromImageScale'):
                    self.plot_parameters['maxImgVal'] = self.img[bs_mask].max()
                else:
                    self.plot_parameters['maxImgVal'] = self.img.max()

            if 'pilatus' in settings.get('Detector'):
                if settings.get('ExcludeMaskFromImageScale'):
                    self.plot_parameters['minImgVal'] = self.img[np.logical_and(self.img>-1, bs_mask)].min()
                else:
                    self.plot_parameters['minImgVal'] = self.img[self.img>-1].min()

            else:
                if settings.get('ExcludeMaskFromImageScale'):
                    self.plot_parameters['minImgVal'] = self.img[bs_mask].min()
                else:
                    self.plot_parameters['minImgVal'] = self.img.min()

        except ValueError:
            self.plot_parameters['maxImgVal'] = self.img.max()
            self.plot_parameters['minImgVal'] = self.img.min()

        if self.plot_parameters['ClimLocked'] == False:
            clim = self.imgobj.get_clim()

            if clim[0] is not None and self.plot_parameters['minImgVal'] is not None:
                self.plot_parameters['LowerClim'] = max(clim[0], self.plot_parameters['minImgVal'])
            elif clim[0] is None:
                self.plot_parameters['LowerClim'] = self.plot_parameters['minImgVal']
            else:
                self.plot_parameters['LowerClim'] = clim[0]

            if clim[1] is not None and self.plot_parameters['maxImgVal'] is not None:
                self.plot_parameters['UpperClim'] = min(clim[1], self.plot_parameters['maxImgVal'])
            elif clim[1] is None:
                self.plot_parameters['UpperClim'] = self.plot_parameters['maxImgVal']
            else:
                self.plot_parameters['UpperClim'] = clim[1]
        else:
            clim = self.imgobj.set_clim(self.plot_parameters['LowerClim'],
                self.plot_parameters['UpperClim'])

        if self.plot_parameters['ImgScale'] == 'linear':
            norm = matplotlib.colors.Normalize(vmin=self.plot_parameters['LowerClim'],
                vmax=self.plot_parameters['UpperClim'])
        else:
            norm = matplotlib.colors.SymLogNorm(linthresh=1,
                vmin=self.plot_parameters['LowerClim'],
                vmax=self.plot_parameters['UpperClim'])

        self.imgobj.set_norm(norm)

        #Update figure:
        self.fig.gca().set_visible(True)
        if xlims[0] == 0 and xlims[1] == 1:     #Assume this means no previously loaded image
            a.set_xlim(0, img_xdim)
            a.set_ylim(0, img_ydim)
        else:
            a.set_xlim(xlims[0], xlims[1])
            a.set_ylim(ylims[0], ylims[1])
        self.safe_draw()

    def showImageSetDialog(self):
        if self.img is not None:
            diag = ImageSettingsDialog(self, self.current_sasm, self.imgobj)
            diag.ShowModal()
            diag.Destroy()

    def setPlotParameters(self, new_param):
        self.plot_parameters = new_param

    def getPlotParameters(self):
        return self.plot_parameters

    def enableCenterClickMode(self, state = True):
        self.center_click_mode = state

    def enableAutoCentMode(self, state = True):
        self.pyfai_cent_mode = state

    def _initOnNewImage(self, img, sasm):
        ''' Inserts information about the newly displayed image
        into the plot parameters '''

        # if not self._canvas_cursor:
        #     a = self.fig.gca()
        #     self._canvas_cursor = Cursor(a, useblit=True, color='red', linewidth=1 )

    def _onMouseScroll(self, event):

        if self._plotting_in_progress or self._movement_in_progress:
            return

        # get the current x and y limits
        ax = self.fig.gca()
#
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
#
        cur_xrange = (cur_xlim[1] - cur_xlim[0])
        cur_yrange = (cur_ylim[1] - cur_ylim[0])
#
        xdata = event.xdata # get event x location
        ydata = event.ydata # get event y location

        if event.button == 'up':
            # zoom in
            scale_factor = 1.15
        elif event.button == 'down':
            # zoom out
            scale_factor = 0.85
        else:
            # deal with something that should never happen
            scale_factor = 1
            print(event.button)

        if xdata is not None and ydata is not None:
            # MOVE AXIS
            zx_pix, zy_pix = ax.transAxes.transform((0,0))
            cx_pix, cy_pix = ax.transAxes.transform((0.5,0.5))
            mx_pix, my_pix = ax.transData.transform((xdata,ydata))

            dx = cx_pix - mx_pix
            dy = cy_pix - my_pix

            dist = np.sqrt(np.power(abs(dx),2)+np.power(abs(dy),2))

            step = 0.2
            new_dist = dist * step   #step = 0..1

            tanA = abs(dy) / abs(dx)
            A = np.arctan(tanA)

            new_dx = np.cos(A) * new_dist
            new_dy = tanA * new_dx

            zdx = zx_pix + new_dx
            zdy = zy_pix + new_dy

            inv = ax.transData.inverted()

            zxdata, zydata = inv.transform((zx_pix, zy_pix))
            zstpx, zstpy = inv.transform((zdx, zdy))

            dx_move = zstpx - zxdata
            dy_move = zstpy - zydata


            if dx >= 0:
                newxmin = cur_xlim[0] - dx_move
                newxmax = cur_xlim[1] - dx_move
            if dx < 0:
                newxmin = cur_xlim[0] + dx_move
                newxmax = cur_xlim[1] + dx_move

            try:
                newxlim = (newxmin, newxmax)
            except UnboundLocalError:
                return

            if dy >= 0:
                newymin = cur_ylim[0] - dy_move
                newymax = cur_ylim[1] - dy_move
            if dy < 0:
                newymin = cur_ylim[0] + dy_move
                newymax = cur_ylim[1] + dy_move

            newylim = (newymin, newymax)


            #ZOOM
            cur_xrange = (cur_xlim[1] - cur_xlim[0])
            cur_yrange = (cur_ylim[1] - cur_ylim[0])

            new_xrange = scale_factor * cur_xrange
            new_yrange = scale_factor * cur_yrange

            dxrange = cur_xrange - new_xrange
            dyrange = cur_yrange - new_yrange

            xmin, xmax = newxlim
            newxlim_zoom = (xmin - (dxrange/2.0), xmax + (dxrange/2.0))

            ymin,ymax = newylim
            newylim_zoom = (ymin - (dyrange/2.0), ymax + (dyrange/2.0))

            ax.set_xlim(newxlim_zoom)
            ax.set_ylim(newylim_zoom)

            self.canvas.draw() # force re-draw

    def _onMouseMotion(self, event):
        ''' handles mouse motions, updates the
        status panel with the coordinates and image value and
        draws the mask guide line.'''

        if event.inaxes:
            x, y = event.xdata, event.ydata

            mouseX = int(x)
            mouseY = int(y)

            try:
                z = self.img[mouseY,mouseX]
            except (IndexError, TypeError):
                z = 0

            try:
                mainframe = wx.FindWindowByName('MainFrame')
                mainframe.statusbar.SetStatusText('(x,y) = (' + str(mouseX) + ', ' + str(mouseY) + ')' + '   I = ' + str(z), 1)
                #mainframe.statusbar.SetStatusText('I = ' + str(z), 2)
            except:
                pass

            if len(self._chosen_points_x) > 0 and self._plotting_in_progress:
                self._drawMaskGuideLine(mouseX, mouseY)

            if self._movement_in_progress == True:
                self._movePatch(mouseX, mouseY)

    def _onMouseButtonPressEvent(self, event):
        ''' Handles matplotlib button press event and splits
        it up into right and left button functions '''

        xd, yd = event.xdata, event.ydata

        if event.button == 1:    # 1 = Left button
            wx.CallAfter(self._onLeftMouseButtonPress, xd, yd, event)

        if event.button == 3:    # 3 = Right button
            wx.CallAfter(self._onRightMouseButtonPress, xd, yd, event)

    def _onMouseButtonReleaseEvent(self, event):
        ''' Handles matplotlib button release event and splits
        it up into right and left button functions '''

        xd, yd = event.xdata, event.ydata

        if event.button == 1:    # 1 = Left button
            wx.CallAfter(self._onLeftMouseButtonRelease, xd, yd, event)

        if event.button == 3:    # 3 = Right button
            wx.CallAfter(self._onRightMouseButtonRelease, xd, yd, event)

    def _onLeftMouseButtonRelease(self, x, y, event):
        if self._movement_in_progress == True:
            self._selected_patch.set_animated(False)
            self._insertNewCoordsIntoMask()
            self._movement_in_progress = False
            self._first_mouse_pos = None

        if self.getTool() is None and self.toolbar.getCurrentTool() is None:
            self._toggleMaskSelection()

    def _onLeftMouseButtonPress(self, x, y, event):
        ''' take action on the click based on what tool is
        selected '''

        if event.inaxes is None: # If click is outside the canvas area
            return

        centering_panel = wx.FindWindowByName('CenteringPanel')
        a = self.fig.gca()

        tool = self.getTool()

        if tool == 'polygon':
            self._addPolygonPoint(x, y, event)

        elif tool == 'circle':
            self._addCirclePoint(x, y, event)

        elif tool == 'rectangle':
            self._addRectanglePoint(x, y, event)

        elif self.pyfai_cent_mode and self.toolbar.getCurrentTool() is None:
            points, centering_panel.c.points = SASCalib.new_grp(self.img, [int(x),
                int(y)], centering_panel.c.points, 200, self.pyfai_ring_num,
                centering_panel.bs_mask)

            if not points:
                if self.canvas.HasCapture():
                    self.canvas.ReleaseMouse()
                wx.CallAfter(wx.MessageBox, 'Failed to find any points in the calibrant ring. Try another location or, if no points in any ring can be found, cancel the auto centering.', 'Automatic Peak Search Failed', style = wx.ICON_ERROR | wx.OK)
                return


            for point in points:
                cir = matplotlib.patches.Circle((point[1], point[0]), radius = 1, alpha = 1, color = self.pyfai_color_cycle[int(self.pyfai_ring_num) % len(self.pyfai_color_cycle)])
                a.add_patch(cir)

            self.canvas.draw()

        elif self.center_click_mode == True:
            self.center_click_mode = False
            wx.CallAfter(centering_panel.setCenter, [int(x),int(y)])

    def _onRightMouseButtonPress(self, x, y, event):
        pass

    def _onRightMouseButtonRelease(self, x, y, event):

        if self.getTool() is None and self._right_click_on_patch == True:
            self._right_click_on_patch = False
            if int(wx.__version__.split('.')[0]) >= 3:
                wx.CallAfter(self._showPopupMenu)
            else:
                self._showPopupMenu()

        elif self.getTool() == 'polygon':

            if len(self._chosen_points_x) > 2:
                points = []
                for i in range(0, len(self._chosen_points_x)):
                    points.append( (self._chosen_points_x[i], self._chosen_points_y[i]) )

                masking_panel = wx.FindWindowByName('MaskingPanel')
                selected_mask = masking_panel.selector_choice.GetStringSelection()
                mask_key = masking_panel.mask_choices[selected_mask]
                masking_panel.mask_modified = True

                if mask_key == 'TransparentBSMask':
                    start_negative = True
                else:
                    start_negative = False

                mask = SASMask.PolygonMask(points, self._createNewMaskNumber(), self.img.shape, negative = start_negative)

                if self._resizing and self._resize_is_negative_mask:
                    mask.setAsNegativeMask()

                self.plot_parameters['storedMasks'].append(mask)

            self.stopMaskCreation()
            self.untoggleAllToolButtons()

    def _onKeyPressEvent(self, event):

        if event.key == 'escape':
            self.untoggleAllToolButtons()

            if self._plotting_in_progress == True:
                self._plotting_in_progress = False

            #self.agbeSelectedPoints = []
            self.stopMaskCreation()

        if event.key == 'delete' or event.key == 'backspace':

            for each in self._plotted_patches:
                if each.selected == 1:

                    for idx in range(0, len(self.plot_parameters['storedMasks'])):
                        if each.id == self.plot_parameters['storedMasks'][idx].getId():
                            self.plot_parameters['storedMasks'].pop(idx)
                            break

                    masking_panel = wx.FindWindowByName('MaskingPanel')
                    masking_panel.mask_modified = True

            self.plotStoredMasks()

    def _onPickEvent(self, event):
        ''' When a mask(patch) is clicked on, a pick event is thrown.
        This function marks the mask as selected when it
        is picked.

        _onPickEvent and _onLeftMouseButtonRelease are the
        two functions that handles selecting masks.
        '''
        mouseevent = event.mouseevent

        if mouseevent.button == 1: #Left click
            self._onPickLeftClick(event)
        elif mouseevent.button == 3: #right click
            self._onPickRightClick(event)

    def _onPickLeftClick(self, event):
        ''' when a patch is selected the move flag should be
        set until the mouse button is released
        see _onLeftMouseButtonRelease too. If it is not
        selected it should be. '''

        if self.getTool() is None:
            self._selected_patch = event.artist

            if event.artist.selected == 0:
                event.artist.selected = 1
            else:
                #If its already selected, set flag
                #to start moving the patch.
                self._movement_in_progress = True
                self._selected_patch.set_animated(True)
                self.canvas.draw()
                self.background = self.canvas.copy_from_bbox(self.fig.gca().bbox)
                self.fig.gca().draw_artist(self._selected_patch)
                self.canvas.blit(self.fig.gca().bbox)

    def _onPickRightClick(self, event):
        ''' If a patch (mask) is selected, then set the
        flag to indicate that a patch has been right clicked
        on so that a pop up menu is shown when the mouse button is
        released. See _onRightMouseButtonRelease. Otherwise
        select the patch and then set the flag.  '''

        self._selected_patch = event.artist
        if not event.artist.selected:
            event.artist.selected = 1
            self._toggleMaskSelection()
            self._selected_patch = event.artist

        self._right_click_on_patch = True

    def _showPopupMenu(self):
        ''' Show a popup menu that gives the user the
        option to toggle between a positive and negative
        mask. '''

        if self._selected_patch.mask is not None:
            menu = wx.Menu()

            menu.AppendRadioItem(1, 'Normal Mask')
            i2 = menu.AppendRadioItem(2, 'Inverted Mask')

            if not isinstance(self._selected_patch.mask, SASMask.PolygonMask):
                menu.Append(3, 'Resize')

            if self._selected_patch.mask.isNegativeMask() == True:
                i2.Check(True)

            self.Bind(wx.EVT_MENU, self._onPopupMenuChoice)

            self.PopupMenu(menu)

            self._selected_patch = None

            menu.Destroy()

    def _onPopupMenuChoice(self, evt):
        id = evt.GetId()

        if id == 1:
            self._selected_patch.mask.setAsPositiveMask()
            masking_panel = wx.FindWindowByName('MaskingPanel')
            masking_panel.mask_modified = True
        elif id == 2:
            self._selected_patch.mask.setAsNegativeMask()
            masking_panel = wx.FindWindowByName('MaskingPanel')
            masking_panel.mask_modified = True
        elif id == 3:
            self._resizeMask()


    #--- ** Mask Creation **

    def _resizeMask(self):
        self._resizing = True
        points = self._selected_patch.mask.getPoints()

        if isinstance(self._selected_patch.mask, SASMask.CircleMask):
            self.current_tool = 'circle'
            self._addCirclePoint(points[0][0], points[0][1], None)

        elif isinstance(self._selected_patch.mask, SASMask.RectangleMask):
            self.current_tool = 'rectangle'
            self._addRectanglePoint(points[0][0], points[0][1], None)

        for each in self._plotted_patches:
            if each.selected == 1:
                for idx in range(0, len(self.plot_parameters['storedMasks'])):
                    if each.id == self.plot_parameters['storedMasks'][idx].getId():
                        self._resize_is_negative_mask = self.plot_parameters['storedMasks'][idx].isNegativeMask()
                        self.plot_parameters['storedMasks'].pop(idx)
                        break

        self.plotStoredMasks()
        self._drawMaskGuideLine(points[1][0], points[1][1])

    def _getMaskFromId(self, mask_id):

        for each in self.plot_parameters['storedMasks']:
            if each.getId() == mask_id:
                return each

    def _movePatch(self, mouseX, mouseY):
        patch = self._selected_patch

        if patch is not None:

            if patch.get_facecolor() == 'yellow' or patch.get_facecolor() == (1.0, 1.0, 0.0, 0.5):
                self.canvas.restore_region(self.background)

                old_points = self._getMaskFromId(patch.id).getPoints()

                x = old_points[0][0]
                y = old_points[0][1]

                dX = mouseX - old_points[0][0]
                dY = mouseY - old_points[0][1]

                if self._first_mouse_pos is None:        # Is reset when mouse button is released
                    self._first_mouse_pos = (dX, dY)

                if isinstance(patch, matplotlib.patches.Circle):
                    patch.center = (x + dX - self._first_mouse_pos[0], y + dY - self._first_mouse_pos[1])

                elif isinstance(patch, matplotlib.patches.Rectangle):
                    patch.set_x(x + dX - self._first_mouse_pos[0])
                    patch.set_y(y + dY - self._first_mouse_pos[1])

                elif isinstance(patch, matplotlib.patches.Polygon):
                    new_points = []
                    for each in old_points:
                        new_points.append((each[0]+dX - self._first_mouse_pos[0], each[1] + dY - self._first_mouse_pos[1]))

                    new_points.append(new_points[0])
                    patch.set_xy(new_points)

                masking_panel = wx.FindWindowByName('MaskingPanel')
                masking_panel.mask_modified = True

                self.fig.gca().draw_artist(patch)
                self.canvas.blit(self.fig.gca().bbox)


    def _toggleMaskSelection(self):
        ''' Changes the colour of the patch when the patch is selected
        or deselected. '''
        update = False

        if self._selected_patch is not None:

            if self._selected_patch.selected == 1:
                if not self._selected_patch.get_facecolor()[:3] == matplotlib.colors.to_rgb('yellow'):
                    self._selected_patch.set_facecolor('yellow')
                    update = True

                id = self._selected_patch.id

                for each in self._plotted_patches:
                    if id != each.id:
                        if not each.mask.isNegativeMask():
                            if not each.get_facecolor()[:3] == matplotlib.colors.to_rgb('red'):
                                each.set_facecolor('red')
                                update = True
                            if not each.get_edgecolor()[:3] ==  matplotlib.colors.to_rgb('red'):
                                each.set_edgecolor('red')
                                update = True
                        else:
                            if not each.get_facecolor()[:3] == matplotlib.colors.to_rgb('green'):
                                each.set_facecolor('green')
                                update = True
                            if not each.get_edgecolor()[:3] ==  matplotlib.colors.to_rgb('green'):
                                each.set_edgecolor('green')
                                update = True
                        each.selected = 0

                self._selected_patch = None

        else:
            for each in self._plotted_patches:
                if not each.mask.isNegativeMask():
                    if not each.get_facecolor()[:3] == matplotlib.colors.to_rgb('red'):
                        each.set_facecolor('red')
                        update = True
                    if not each.get_edgecolor()[:3] ==  matplotlib.colors.to_rgb('red'):
                        each.set_edgecolor('red')
                        update = True
                else:
                    if not each.get_facecolor()[:3] == matplotlib.colors.to_rgb('green'):
                        each.set_facecolor('green')
                        update = True
                    if not each.get_edgecolor()[:3] ==  matplotlib.colors.to_rgb('green'):
                        each.set_edgecolor('green')
                        update = True
                each.selected = 0

            self._selected_patch = None

        if update:
            self.canvas.draw()

    def _insertNewCoordsIntoMask(self):
        patch = self._selected_patch
        mask = self._getMaskFromId(self._selected_patch.id)

        if isinstance(patch, matplotlib.patches.Circle):

            newCenter = patch.center

            #first point is center, next point is first on circle perferie
            mask.setPoints([newCenter, (newCenter[0]+mask.getRadius(), newCenter[1])])

        elif isinstance(patch, matplotlib.patches.Rectangle):

            x = patch.get_x()
            y = patch.get_y()

            dx = x - mask.getPoints()[0][0]
            dy = y - mask.getPoints()[0][1]

            mask.setPoints([(x, y),(mask.getPoints()[1][0] + dx, mask.getPoints()[1][1] + dy)])

        elif isinstance(patch, matplotlib.patches.Polygon):
            mask.setPoints(patch.get_xy()[:-1])

    def stopMaskCreation(self, untoggle = True):


        self.untoggleAllToolButtons()

        self._chosen_points_x = []
        self._chosen_points_y = []
        self._plotting_in_progress = False
        self._polygon_guide_line = None
        self._circle_guide_line = None
        self._rectangle_line = None
        self._resizing = False
        self._resize_is_negative_mask = False
        self.plotStoredMasks()

    def clearAllMasks(self):

        self.plot_parameters['storedMasks'] = []

        a = self.fig.gca()

        if a.lines:
            del(a.lines[:])     # delete plotted masks
        if a.patches:
            del(a.patches[:])
        if a.collections:
            del(a.collections[:])

        if self.center_patch:
            a.add_patch(self.center_patch)

        self.canvas.draw()

    def plotStoredMasks(self, update=True):

        a = self.fig.gca()        # Get current axis from figure
        stored_masks = self.plot_parameters['storedMasks']

        if a.lines:
            del(a.lines[:])     # delete plotted masks
        if a.patches:
            del(a.patches[:])
        if a.collections:
            del(a.collections[:])

        for mask_id, each in enumerate(stored_masks):
            each.setId(mask_id)

            if each.isNegativeMask() == True:
                col = 'green'
            else:
                col = 'red'

            if each.getType() == 'circle':
                self._drawCircle(each.getPoints(), mask_id, each, color=col)

            elif each.getType() == 'rectangle':
                self._drawRectangle(each.getPoints(), mask_id, each, color=col)

            elif each.getType() == 'polygon':
                self._drawPolygon(each.getPoints(), mask_id, each, color=col)

        if self.center_patch:
            a.add_patch(self.center_patch)

        if update:
            self.canvas.draw()

    def drawCenterPatch(self, x, style = 'circle'):
        a = self.fig.gca()
        self.center_patch = matplotlib.patches.Circle( x, radius = 3, alpha = 1, facecolor = 'red', edgecolor = 'red')
        a.add_patch(self.center_patch)
        self.canvas.draw()

    def removeCenterPatch(self):
        if self.center_patch:
            try:
                self.center_patch.remove()
            except ValueError:
                pass
            self.center_patch = None
            self.canvas.draw()

    def _drawMaskGuideLine(self, x, y):
        ''' Draws the guide lines for the different mask types '''

        tool = self.getTool()

        a = self.fig.gca()             # Get current axis from figure

        if tool == 'circle':
            radius_c = abs(x - self._chosen_points_x[-1])

            if self._circle_guide_line:
                self.canvas.restore_region(self.background)

                self._circle_guide_line.set_radius(radius_c)

                self.fig.gca().draw_artist(self._circle_guide_line)
                self.canvas.blit(self.fig.gca().bbox)
            else:
                self._circle_guide_line = matplotlib.patches.Circle((self._chosen_points_x[-1],
                    self._chosen_points_y[-1]), radius_c, color = 'r', fill = False,
                    linewidth = 2, animated = True)
                a.add_patch(self._circle_guide_line)
                self.canvas.draw()
                self.background = self.canvas.copy_from_bbox(self.fig.gca().bbox)
                self.fig.gca().draw_artist(self._circle_guide_line)
                self.canvas.blit(self.fig.gca().bbox)

        elif tool == 'rectangle':
            xPoints = [self._chosen_points_x[-1], x, x, self._chosen_points_x[-1], self._chosen_points_x[-1]]
            yPoints = [self._chosen_points_y[-1], self._chosen_points_y[-1], y, y, self._chosen_points_y[-1]]

            if self._rectangle_line:
                self.canvas.restore_region(self.background)
                self._rectangle_line[0].set_ydata(yPoints)
                self._rectangle_line[0].set_xdata(xPoints)

                self.fig.gca().draw_artist(self._rectangle_line[0])
                self.canvas.blit(self.fig.gca().bbox)
            else:
                self._rectangle_line = a.plot(xPoints, yPoints, 'r', animated = True)
                self.canvas.draw()
                self.background = self.canvas.copy_from_bbox(self.fig.gca().bbox)
                self.fig.gca().draw_artist(self._rectangle_line[0])
                self.canvas.blit(self.fig.gca().bbox)


        elif tool == 'polygon':
            xPoint = self._chosen_points_x[-1]
            yPoint = self._chosen_points_y[-1]

            if self._polygon_guide_line:

                self.canvas.restore_region(self.background)
                self._polygon_guide_line[0].set_ydata([yPoint, y])
                self._polygon_guide_line[0].set_xdata([xPoint, x])

                self.fig.gca().draw_artist(self._polygon_guide_line[0])
                self.canvas.blit(self.fig.gca().bbox)

            else:
                self._polygon_guide_line = a.plot([xPoint, x], [yPoint, y], 'r', animated = True)
                self.canvas.draw()
                self.background = self.canvas.copy_from_bbox(self.fig.gca().bbox)


        #self.canvas.draw()

    def _drawCircle(self, points, mask_id, mask, color, animated = False):

        a = self.fig.gca()

        radius_c = abs(points[1][0] - points[0][0])

        if animated:
            cir = matplotlib.patches.Circle( (points[0][0], points[0][1]),
                color = color, radius = radius_c, alpha = 0.5, picker = True,
                animated=True)
        else:
            cir = matplotlib.patches.Circle( (points[0][0], points[0][1]),
                color = color, radius = radius_c, alpha = 0.5, picker = True)
        cir.id = mask_id       # Creating a new parameter called id to distingush them!
        cir.mask = mask
        cir.selected = 0
        self._plotted_patches.append(cir)

        a.add_patch(cir)

        self._circle_guide_line = None

    def _drawRectangle(self, points, mask_id, mask, color, animated = False):
        a = self.fig.gca()

        xStart = points[0][0]
        yStart = points[0][1]

        xEnd = points[1][0]
        yEnd = points[1][1]

        width = xEnd - xStart
        height = yEnd - yStart
        if animated:
            rect = matplotlib.patches.Rectangle( (xStart, yStart), width,
                height, color = color, alpha = 0.5, picker = True, animated=True )
        else:
            rect = matplotlib.patches.Rectangle( (xStart, yStart), width,
                height, color = color, alpha = 0.5, picker = True)
        rect.mask = mask

        rect.id = mask_id
        rect.selected = 0
        self._plotted_patches.append(rect)

        a.add_patch(rect)

        self._rectangle_line = None

    def _drawPolygon(self, points, mask_id, mask, color, animated = False):
        a = self.fig.gca()

        if animated:
            poly = matplotlib.patches.Polygon(points, alpha = 0.5, picker = True ,
                color = color, animated=True)
        else:
            poly = matplotlib.patches.Polygon(points, alpha = 0.5, picker = True ,
                color = color)
        poly.mask = mask
        a.add_patch(poly)

        poly.id = mask_id
        poly.selected = 0
        self._plotted_patches.append(poly)

        self._polygon_guide_line = None

    def _drawCenteringRings(self, x, r_list):
        a = self.fig.gca()

        if self.img is not None:

            if len(a.patches)>len(r_list)+1:
                self.clearPatches()

            if not a.patches:
                cir = matplotlib.patches.Circle( x, radius = 3, alpha = 1,
                    facecolor = 'red', edgecolor = 'red', animated=True)
                a.add_patch(cir)

                for r in r_list:
                    cir = matplotlib.patches.Circle(x, radius = r, alpha = 1,
                        fill = False, linestyle = 'dashed', linewidth = 1.5,
                        edgecolor = 'red',animated=True)
                    a.add_patch(cir)

                self.canvas.draw()

            else:
                self.canvas.restore_region(self.background)

                for i, patch in enumerate(a.patches):
                    patch.center = x
                    if i>0:
                        patch.set_radius(r_list[i-1])
                    a.draw_artist(patch)

                self.canvas.blit(self.fig.gca().bbox)

    def drawCenteringPoints(self, points):

        a = self.fig.gca()

        for point in points:
            cir = matplotlib.patches.Circle((point[1], point[0]), radius = 1,
                alpha = 1, color = self.pyfai_color_cycle[int(point[2]) % len(self.pyfai_color_cycle)])
            a.add_patch(cir)

        self.canvas.draw()

    def _addCirclePoint(self, x, y, event):
        ''' Add point to chosen points list and create a circle
        patch if two points has been chosen '''
        self._plotting_in_progress = True

        self._chosen_points_x.append(round(x))
        self._chosen_points_y.append(round(y))

        if len(self._chosen_points_x) == 2:

            masking_panel = wx.FindWindowByName('MaskingPanel')
            selected_mask = masking_panel.selector_choice.GetStringSelection()
            mask_key = masking_panel.mask_choices[selected_mask]

            if mask_key == 'TransparentBSMask':
                start_negative = True
            else:
                start_negative = False

            if ((self._chosen_points_x[1]-self._chosen_points_x[0])**2+
                (self._chosen_points_y[1]-self._chosen_points_y[0])**2 > 0):
                self.create_circ_mask(self._chosen_points_x, self._chosen_points_y,
                    start_negative, False)

            self.untoggleAllToolButtons()
            self.stopMaskCreation()

    def _addRectanglePoint(self, x, y, event):
        ''' Add point to chosen points list and create a rectangle
        patch if two points has been chosen '''
        self._plotting_in_progress = True

        self._chosen_points_x.append(round(x))
        self._chosen_points_y.append(round(y))

        if len(self._chosen_points_x) == 2:

            masking_panel = wx.FindWindowByName('MaskingPanel')
            selected_mask = masking_panel.selector_choice.GetStringSelection()
            mask_key = masking_panel.mask_choices[selected_mask]

            if mask_key == 'TransparentBSMask':
                start_negative = True
            else:
                start_negative = False

            if ((self._chosen_points_x[1]-self._chosen_points_x[0])**2 > 0 and
                (self._chosen_points_y[1]-self._chosen_points_y[0])**2 > 0):
                self.create_rect_mask(self._chosen_points_x, self._chosen_points_y,
                    start_negative, False)

            self.untoggleAllToolButtons()
            self.stopMaskCreation()

    def _addPolygonPoint(self, x, y, event):
        ''' Add points to the polygon and draw lines
        between points if enough points are present '''

        if len(self._chosen_points_x) > 0:
            if event.inaxes is not None:

                new_line_x = [self._chosen_points_x[-1], round(x)]
                new_line_y = [self._chosen_points_y[-1], round(y)]

                self._chosen_points_x.append(round(x))
                self._chosen_points_y.append(round(y))

                if len(self._chosen_points_x) >= 2:
                    self.fig.gca().plot(new_line_x, new_line_y,'r')
                    self.canvas.draw()

                    #update blitz background region for guideline:
                    self.background = self.canvas.copy_from_bbox(self.fig.gca().bbox)
        else:
            self._chosen_points_x.append(round(x))
            self._chosen_points_y.append(round(y))
            self._plotting_in_progress = True

    def create_rect_mask(self, x_points, y_points, negative, plot=True):
        new_mask = SASMask.RectangleMask((x_points[0], y_points[0]),
            (x_points[1], y_points[1]), self._createNewMaskNumber(),
            self.img.shape, negative=negative)

        if self._resizing and self._resize_is_negative_mask:
            new_mask.setAsNegativeMask()

        self.plot_parameters['storedMasks'].append(new_mask)

        masking_panel = wx.FindWindowByName('MaskingPanel')
        masking_panel.mask_modified = True

        if plot:
            self.plotStoredMasks()

    def create_circ_mask(self, x_points, y_points, negative, plot=True):
        new_mask = SASMask.CircleMask((x_points[0], y_points[0]),
            (x_points[1], y_points[1]), self._createNewMaskNumber(),
            self.img.shape, negative=negative)

        if self._resizing and self._resize_is_negative_mask:
            new_mask.setAsNegativeMask()

        self.plot_parameters['storedMasks'].append(new_mask)

        masking_panel = wx.FindWindowByName('MaskingPanel')
        masking_panel.mask_modified = True

        if plot:
            self.plotStoredMasks()

    def _createNewMaskNumber(self):

        storedMasks = self.plot_parameters['storedMasks']

        if not(storedMasks):
            self.next_mask_number = 0
        else:
            self.next_mask_number = self.next_mask_number + 1

        return self.next_mask_number

    def showCenter(self):
        pass

    def _drawCenter(self):
        self.fig.gca()

    def clearPatches(self):
        a = self.fig.gca()

        if a.lines:
            del(a.lines[:])     # delete plotted masks
        if a.patches:
            del(a.patches[:])
        if a.texts:
            del(a.texts[:])

        self.canvas.draw()

    def clearFigure(self):
        self.fig.clear()
        self.fig.gca().set_visible(False)
        self.canvas.draw()

    def updateClim(self):

        upper = self.plot_parameters['UpperClim']
        lower = self.plot_parameters['LowerClim']

        if upper is not None and lower is not None and self.imgobj is not None:
            if lower < upper:
                self.imgobj.set_clim(lower, upper)
                self.canvas.draw()

    def updateImage(self):
        self.canvas.draw()

class HdrInfoDialog(wx.Dialog):

    def __init__(self, parent, sasm):

        wx.Dialog.__init__(self, parent, -1, 'Image Header',
            style = wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX)
        self.SetSize(self._FromDIP((500,500)))

        self.sasm = sasm

        final_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = self.createHdrInfoWindow()

        button = wx.Button(self, wx.ID_CLOSE, 'Close')
        button.Bind(wx.EVT_BUTTON, self.onClose)

        final_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, border=self._FromDIP(5))
        final_sizer.Add(button,0, wx.BOTTOM | wx.ALIGN_RIGHT | wx.RIGHT,
            border=self._FromDIP(5))

        self.SetSizer(final_sizer)

        SASUtils.set_best_size(self)

        self.CenterOnParent()

    def _FromDIP(self, size):
        # This is a hack to provide easy back compatibility with wxpython < 4.1
        try:
            return self.FromDIP(size)
        except Exception:
            return size

    def createHdrInfoWindow(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.text = wx.TextCtrl(self, -1, style = wx.TE_MULTILINE | wx.TE_READONLY)

        self.text.AppendText('#############################################\n')
        self.text.AppendText('                                 Header information\n')
        self.text.AppendText('#############################################\n\n')


        if self.sasm is not None:
            param = self.sasm.getAllParameters()

            for each in param:

                if each == 'imageHeader':
                    imghdr = param[each]
                    imghdr_keys = sorted(imghdr.keys())
                    self.text.AppendText(str(each) + ' : \n')
                    for eachkey in imghdr_keys:
                        self.text.AppendText(str(eachkey) + ' : ' + str(imghdr[eachkey])+'\n')

                else:
                    self.text.AppendText(str(each) + ' : ' + str(param[each])+'\n')

        sizer.Add(self.text, 1, wx.EXPAND)

        return sizer

    def onClose(self, event):
        self.EndModal(wx.ID_OK)


class ImageSettingsDialog(wx.Dialog):

    def __init__(self, parent, sasm, ImgObj):

        wx.Dialog.__init__(self, parent, -1, title = 'Image Display Settings')

        self.sasm = sasm
        self.ImgObj = ImgObj
        self.parent = parent

        self.newImg = self.parent.img.copy()

        sizer = wx.BoxSizer(wx.VERTICAL)

        if not parent.plot_parameters['UpperClim'] is None and not parent.plot_parameters['LowerClim'] is None:
            self.maxval = parent.plot_parameters['maxImgVal']
            self.minval = parent.plot_parameters['minImgVal']
        else:
            self.maxval = 100
            self.minval = 0

        self.sliderinfo = (
                           ################### ctrl,     slider #############
                           ('Upper limit:', self.NewControlId(), self.NewControlId(), 'UpperClim'),
                           ('Lower limit:', self.NewControlId(), self.NewControlId(), 'LowerClim'))
                           # ('Brightness:', self.NewControlId(), self.NewControlId(), 'Brightness'))

        box = wx.StaticBox(self, -1, 'Image parameters')
        finalfinal_sizer = wx.BoxSizer()

        slidersizer = self.createSettingsWindow(box)
        scalesizer = self.createScaleSelector()
        colormapsizer = self.createColormapSelector()

        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        sizer.Add(slidersizer, 1, wx.EXPAND | wx.TOP | wx.BOTTOM,
            border=self._FromDIP(5))

        self.okButton = wx.Button(self, -1, 'OK')
        self.okButton.Bind(wx.EVT_BUTTON, self.OnOk)

        finalSizer = wx.BoxSizer(wx.VERTICAL)
        finalSizer.Add(sizer, 0, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
            border=self._FromDIP(5))
        finalSizer.Add(scalesizer,0, wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=self._FromDIP(5))
        finalSizer.Add(colormapsizer,0, wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=self._FromDIP(5))
        finalSizer.Add(self.okButton, 0, wx.CENTER | wx.TOP,
            border=self._FromDIP(10))

        finalfinal_sizer.Add(finalSizer, 0, wx.ALL, border=self._FromDIP(10))

        self.SetSizer(finalfinal_sizer)
        self.Fit()

        SASUtils.set_best_size(self)

        try:
            file_list_ctrl = wx.FindWindowByName('FilePanel')
            pos = file_list_ctrl.GetScreenPosition()
            if wx.version().split()[0].strip()[0] == '4':
                self.Move(pos[0], pos[1])
            else:
                self.MoveXY(pos[0], pos[1])
        except:
            pass

    def _FromDIP(self, size):
        # This is a hack to provide easy back compatibility with wxpython < 4.1
        try:
            return self.FromDIP(size)
        except Exception:
            return size

    def OnOk(self, event):

        self.EndModal(1)

    def createColormapSelector(self):

        sizer = wx.BoxSizer()

        self.colorRadioList = ['Gray', 'Heat', 'Rainbow', 'Jet', 'Spectral']

        self.colormaps = [matplotlib.cm.gray,
                          matplotlib.cm.gist_heat,
                          matplotlib.cm.gist_rainbow,
                          matplotlib.cm.jet,
                          matplotlib.cm.nipy_spectral]

        rb = wx.RadioBox(self, label="Colormaps", choices=self.colorRadioList,
            style=wx.RA_SPECIFY_COLS)
        rb.Bind(wx.EVT_RADIOBOX, self.onColorMapsRadioBox)

        rb.SetSelection(self.colormaps.index(self.parent.plot_parameters['ColorMap']))

        sizer.Add(rb, 1, wx.EXPAND)

        return sizer

    def onColorMapsRadioBox(self, event):

        selection = event.GetSelection()

        if self.colorRadioList[selection] == 'Gray':
            self.parent.plot_parameters['ColorMap'] = matplotlib.cm.gray
        elif self.colorRadioList[selection] == 'Heat':
            self.parent.plot_parameters['ColorMap'] = matplotlib.cm.gist_heat
        elif self.colorRadioList[selection] == 'Rainbow':
            self.parent.plot_parameters['ColorMap'] = matplotlib.cm.gist_rainbow
        elif self.colorRadioList[selection] == 'Jet':
            self.parent.plot_parameters['ColorMap'] = matplotlib.cm.jet
        elif self.colorRadioList[selection] == 'Bone':
            self.parent.plot_parameters['ColorMap'] = matplotlib.cm.bone
        elif self.colorRadioList[selection] == 'Spectral':
            self.parent.plot_parameters['ColorMap'] = matplotlib.cm.nipy_spectral

        if self.ImgObj is not None:
            self.ImgObj.cmap = self.parent.plot_parameters['ColorMap']
            self.ImgObj.changed()
            self.parent.updateImage()

    def createScaleSelector(self):

        sizer = wx.BoxSizer()

        radioList = ['Linear', 'Logarithmic']
        rb = wx.RadioBox(self, label="Image scaling", choices=radioList,
            style=wx.RA_SPECIFY_COLS)
        rb.Bind(wx.EVT_RADIOBOX, self.onRadioBox)

        if self.parent.plot_parameters['ImgScale'] == 'linear':
            rb.SetSelection(0)
        else:
            rb.SetSelection(1)

        sizer.Add(rb, 1, wx.EXPAND)

        return sizer

    def onRadioBox(self, event):

        selection = event.GetSelection()

        upper_val = wx.FindWindowById(self.sliderinfo[0][1])
        upper_slider = wx.FindWindowById(self.sliderinfo[0][2])
        lower_val = wx.FindWindowById(self.sliderinfo[1][1])
        lower_slider = wx.FindWindowById(self.sliderinfo[1][2])

        if not self.parent.plot_parameters['ClimLocked']:
            minval = self.parent.plot_parameters['minImgVal']
            maxval = self.parent.plot_parameters['maxImgVal']

            self.parent.plot_parameters['UpperClim'] = maxval
            self.parent.plot_parameters['LowerClim'] = minval

            upper_slider.SetValue(min(2147483647,int(maxval)))
            lower_slider.SetValue(min(2147483647,int(minval)))

            upper_val.ChangeValue(str(maxval))
            lower_val.ChangeValue(str(minval))

        else:
            maxval = self.parent.plot_parameters['UpperClim']
            minval = self.parent.plot_parameters['LowerClim']

        if selection == 0:
            if self.parent.plot_parameters['ImgScale'] != 'linear':

                self.parent.plot_parameters['ImgScale'] = 'linear'

                norm = matplotlib.colors.Normalize(vmin = minval, vmax = maxval)

                self.ImgObj.set_norm(norm)
                self.ImgObj.changed()

                self.ImgObj.set_clim(minval, maxval)

                self.parent.updateImage()

        elif selection == 1:
            if self.parent.plot_parameters['ImgScale'] != 'logarithmic':

                self.parent.plot_parameters['ImgScale'] = 'logarithmic'

                norm = matplotlib.colors.SymLogNorm(vmin = minval, vmax = maxval,linthresh = 1)

                self.ImgObj.set_norm(norm)
                self.ImgObj.changed()

                self.ImgObj.set_clim(minval, maxval)

                self.parent.updateImage()

    def createSettingsWindow(self, parent):

        finalSizer = wx.BoxSizer(wx.VERTICAL)

        for each in self.sliderinfo:

            label = wx.StaticText(parent, -1, each[0])
            val = wx.TextCtrl(parent, each[1], size=self._FromDIP((60, 21)),
                style=wx.TE_PROCESS_ENTER)
            val.Bind(wx.EVT_TEXT_ENTER, self.OnTxtEnter)
            val.Bind(wx.EVT_KILL_FOCUS, self.OnTxtEnter)

            slider = wx.Slider(parent, each[2], style = wx.HORIZONTAL)

            if platform.system() == 'Darwin':
                slider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.OnSlider)
            else:
                slider.Bind(wx.EVT_SCROLL_CHANGED, self.OnSlider)

            if each[3] == 'Brightness' or each[3] == 'Contrast':
                slider.SetMin(0)
                slider.SetMax(200)
                slider.Enable(False)
            else:
                slider.SetMin(int(self.minval))
                slider.SetMax(min(int(self.maxval),2147483647))


            if self.parent.plot_parameters[each[3]] is not None:
                val.SetValue(str(self.parent.plot_parameters[each[3]]))
                slider.SetValue(min(int(self.parent.plot_parameters[each[3]]), 2147483647))

            hslider = wx.BoxSizer(wx.HORIZONTAL)

            hslider.Add(label, 0, wx.EXPAND | wx.RIGHT, border=self._FromDIP(5))
            hslider.Add(val, 0, wx.EXPAND|wx.RIGHT)
            hslider.Add(slider, 1, wx.EXPAND|wx.RIGHT)

            finalSizer.Add(hslider, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT,
                border=self._FromDIP(5))

        chkbox = wx.CheckBox(parent, -1, 'Lock values')
        chkbox.Bind(wx.EVT_CHECKBOX, self.onLockValues)
        chkbox.SetValue(self.parent.plot_parameters['ClimLocked'])

        finalSizer.Add(chkbox, 0, wx.EXPAND | wx.ALL, border=self._FromDIP(5))

        return finalSizer

    def resetSliders(self, maxval, minval):

        for each in self.sliderinfo:
            txtCtrl = wx.FindWindowById(each[1], self)
            slider = wx.FindWindowById(each[2], self)
            txtCtrl.SetValue(str(self.parent.plot_parameters[each[3]]))

            if each[3] == 'Brightness' or each[3] == 'Contrast':
                slider.SetMin(0)
                slider.SetMax(200)
            else:
                slider.SetMin(minval)
                slider.SetMax(min(maxval,2147483647))

            slider.SetValue(min(2147483647,int(self.parent.plot_parameters[each[3]])))

    def onLockValues(self, event):

        if event.GetEventObject().IsChecked():
            self.parent.plot_parameters['ClimLocked'] = True
        else:
            self.parent.plot_parameters['ClimLocked'] = False

    def OnTxtEnter(self, event):
        id = event.GetId()

        for each in self.sliderinfo:
            if each[1] == id:
                ctrl = wx.FindWindowById(id, self)
                slider = wx.FindWindowById(each[2], self)

                val = ctrl.GetValue()

                try:
                    int(val)
                except ValueError:
                    val = slider.GetMin()

                slider.SetValue(min(2147483647,int(val)))

                self.parent.plot_parameters[each[3]] = int(val)

                if each[3] == 'Brightness' or each[3] == 'Contrast':
                    self.setBrightnessAndContrastUINT16()
                else:
                    self.parent.updateClim()

        event.Skip()

    def OnSlider(self, event):
        id = event.GetId()

        for each in self.sliderinfo:
            if each[2] == id:
                slider = event.GetEventObject()
                val = slider.GetValue()

                wx.FindWindowById(each[1], self).ChangeValue(str(val))
                self.parent.plot_parameters[each[3]] = int(val)

                if each[3] == 'Brightness' or each[3] == 'Contrast':
                    self.setBrightnessAndContrastUINT16()
                else:
                    self.parent.updateClim()

        event.Skip()

#     def setBrightnessAndContrastUINT16(self):
#         print 'setting brightness'
#         brightness = self.parent.plot_parameters['Brightness'] - 100;
#         contrast = (self.parent.plot_parameters['Contrast'] - 100)/10;
#         max_value = 0;

#         print brightness
#         print contrast

#         lut = np.array(range(0,65536), int)

#     # The algorithm is by Werner D. Streidt
#     # (http://visca.com/ffactory/archives/5-99/msg00021.html)
#         if( contrast > 0 ):
#             delta = 32767.*contrast/100;
#             a = 65535./(65535. - delta*2);
#             b = a*(brightness - delta);
#         else:
#             delta = -32768.*contrast/100;
#             a = (65536.-delta*2)/65535.;
#             b = a*brightness + delta;

#         print a
#         print b

#         for i in range(65536):
#             v = round(a*i + b)

#             if( v < 0 ):
#                 v = 0

#             if( v > 65535 ):
#                 v = 65535

#             lut[i] = v

#         change = lambda x: lut[x]

#         print change(0)
#         print change(10)
#         print change(50)

#         newImg = change(self.parent.img)


#       #  if self.parent.plot_parameters['ImgScale'] != 'logarithmic':
#       #      newImg[where(newImg) == 0] = 1.0
#       #      newImg = log(self.parent.img)
#       #      newImg = uint16(self.newImg / self.newImg.max() * 65535)

#                 #self.ImgObj.set_data(self.newImg)
# #       newImg[where(newImg<1)] = 1
#         self.ImgObj.set_data(newImg)
#         self.parent.updateImage()

#--- ** FOR TESTING **
class ImageTestFrame(wx.Frame):
    ''' A Frame for testing the image panel '''

    def __init__(self, title, frame_id):
        wx.Frame.__init__(self, None, frame_id, title, name = 'MainFrame')

        self.SetSize((500,500))
        self.raw_settings = RAWSettings.RawGuiSettings()

        self.background_panel = wx.Panel(self, -1)

        sizer = wx.BoxSizer()

        self.image_panel = ImagePanel(self.background_panel, -1, 'RawPlotPanel')

        sizer.Add(self.image_panel, 1, wx.GROW)

        self.background_panel.SetSizer(sizer)

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(3)

        self.SetStatusBar(self.statusbar)

        self.loadTestImage()

    def loadTestImage(self):

        file = os.path.join(os.getcwd(), 'Tests', 'TestData', 'AgBe_Quantum.img')
        sasm, img = SASFileIO.loadFile(file, self.raw_settings)

        if isinstance(sasm, list):
            sasm = sasm[-1]
            img = img[-1]

        self.image_panel.showImage(img, sasm)


class ImageTestApp(wx.App):
    ''' A test app '''

    def OnInit(self):

        frame = ImageTestFrame('Options', -1)
        self.SetTopWindow(frame)
        frame.CenterOnScreen()
        frame.Show(True)
        return True

if __name__ == "__main__":
    import RAWSettings
    import SASFileIO

    app = ImageTestApp(0)   #MyApp(redirect = True)
    app.MainLoop()

