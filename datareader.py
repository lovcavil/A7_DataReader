#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import numpy, matplotlib,pandas
import glob
import wx
import matplotlib_GUI
import os
import matplotlib_canvas
import matplotlib.backend_managers
import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d.axes3d import get_test_data
from mpl_toolkits.mplot3d import Axes3D
import winsound
import progressbar

if matplotlib.__version__ < '2.2':
    raise ValueError("Minimum Matplotlib version required: 2.2")
prog_i = 0

class MyFrame(matplotlib_GUI.MyFrame):
    # set up datastructure used by get_axes() method -------------------------------------------------------------------
    # where to place plots? map user choice to subplot: (row, col, position)
    # e.g. "top left" for 2x2 plots -> (2,2,1)
    # this will be the argument to self.canvas.figure.add_subplot(...)
    _SUBPLOT_CHOICES = [((1,1),("center",)),
                        ((1,2),("left","right")),
                        ((2,1),("top","bottom")),
                        ((2,2),("top left","top right","bottom left","bottom right")),
                        ((2,3),("top left","top center","top right","bottom left","bottom center","bottom right"))]
    _SUBPLOT_POSITIONS = {}
    for ((rows,cols), choices) in _SUBPLOT_CHOICES:
        _SUBPLOT_POSITIONS[rows,cols] = {}
        i = 0
        for row in range(1,rows+1):
            for col in range(1,cols+1):
                if choices:
                    _SUBPLOT_POSITIONS[rows,cols][choices[i]] = (rows,cols,i+1)
                i += 1
    del rows, cols, choices, i

    # ------------------------------------------------------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        self.result = {}

        matplotlib_GUI.MyFrame.__init__(self, *args, **kwargs)
        self.figure = self.canvas.figure

        self.init_toolmanager()
        self.init_events()
        # where to save figures by default?
        matplotlib.rcParams['savefig.directory'] = "" # defaults to current directory

        self.Bind(wx.EVT_CLOSE, self.OnClose)


        # initialize values from control values; so the .wxg file needs to have correct initialization values!
        self.on_choice_line_style()
        self.on_combo_colour()
        self.on_combo_line_width()

        self.on_choice_subplots()
        self.set_history_buttons()
        self.on_button_plot()

        self.multicursor = None

    def init_toolmanager(self):
        self.toolmanager = matplotlib.backend_managers.ToolManager(self.canvas.figure)

        self.toolmanager.add_tool('viewpos', 'ToolViewsPositions')  # required for pan/zoom/home/back/forward
        self.toolmanager.add_tool('pan', 'ToolPan')  # pan w. mouse and zoom w. wheel with 'p' key
        self.toolmanager.add_tool('zoom', 'ToolZoom') # zoom to rect with 'o' key
        self.toolmanager.add_tool('home', 'ToolHome') # 'h', 'r', 'home'
        if hasattr(matplotlib.backend_managers, "ToolHelp"):
            self.toolmanager.add_tool('help', 'ToolHelp') # 'F1'
        self.toolmanager.add_tool('back', 'ToolBack') # 'left', 'c', 'backspace'
        self.toolmanager.add_tool('forward', 'ToolForward') # 'right', 'v'
        self.toolmanager.add_tool('save', 'ToolSaveFigure') # 's', 'ctrl+s'
        self.toolmanager.add_tool('grid', 'ToolGrid')              # toggle throug major h/v grids with 'g' key
        self.toolmanager.add_tool('grid_minor', 'ToolMinorGrid')   # toggle throug major/minor grids with 'G' key
        
        self.toolmanager.add_tool('yscale', 'ToolYScale')          # toggle lin/log scaling with 'l' key
        self.toolmanager.add_tool('xscale', 'ToolXScale')          # toggle lin/log scaling with 'k','L' keys

        # some tools will only be available with matplotlib 3.0:
        if hasattr(matplotlib.backend_managers, "ToolCopyToClipboard"):
            self.toolmanager.add_tool('copy', 'ToolCopyToClipboard')

        self.toolmanager.add_tool('rubberband', 'ToolRubberband')
        self.toolmanager.add_tool('setcursor', 'ToolSetCursor')

        self.toolmanager.toolmanager_connect("tool_trigger_home", self.set_history_buttons)
        self.toolmanager.toolmanager_connect("tool_trigger_back", self.set_history_buttons)
        self.toolmanager.toolmanager_connect("tool_trigger_forward", self.set_history_buttons)

    def init_events(self):
        # connect to matplotlib events

        # for picking elements
        self.canvas.mpl_connect( 'pick_event', self.on_pick)
        self._last_pick_mouseevent = None  # store info, as we will act only once per pick event

        # for displaying cursor position
        self.canvas.mpl_connect( 'motion_notify_event', self.on_mouse_move)

        # button_release_event may be the end of a zoom; use CallAfter as we may receive the event too early
        self.canvas.mpl_connect("button_release_event", lambda event: wx.CallAfter(self.set_history_buttons))

        # register a handler for all canvas events except 'motion_notify_event', which would cause too much traffic
        for event in ('button_press_event', 'button_release_event', 'key_press_event', 'key_release_event',
                          'draw_event', 'pick_event', 'resize_event', 'scroll_event',
                          'figure_enter_event', 'figure_leave_event', 'axes_enter_event', 'axes_leave_event'):
            self.canvas.mpl_connect(event, self.on_canvas_event)
        # in addition, there are events from the axes: 'xlim_changed', 'ylim_changed' (see self.get_axes())

    ###################################################################################################################
    # print messages
    def on_canvas_event(self, event):
        print("canvas event:", event)

    ###################################################################################################################
    # global actions: add plot or clear plots or all
    def get_axes(self):
        # return the axes that are selected acc. to "Subplots" and "Subplot position"
        subplots = self._SUBPLOT_POSITIONS[self.subplots][self.subplot]
        # subplots = (row, col, position), e.g. (2,2,1) for the top left of 2x2 plots
        ret = self.figure.add_subplot(*subplots)
        # we could register event handlers when x or y limits are changing:
        #ret.callbacks.connect( 'xlim_changed', lambda evt: print("callback xlim_changed:", evt) )
        return ret

    def on_button_clear(self, types):
        if self.multicursor:
            self.multicursor.disconnect()
            self.multicursor = None
            self.button_multicursor.SetValue(False)

        if types=="plots":
            for axes in self.figure.axes:
                axes.clear()
        elif types in ("figures","all"):
            self.figure.clear()
        self.canvas.draw()

        if types in ("plots","all"):
            # reset zoom history
            self.toolmanager.get_tool("viewpos").clear(self.canvas.figure)
            self.set_history_buttons()

    def on_button_multicursor(self, event):
        from matplotlib.widgets import MultiCursor

        axes = self.canvas.figure.axes
        if event.IsChecked() and not self.multicursor and axes:
            # add multicursor
            self.multicursor = MultiCursor(self.canvas, axes, color='r', lw=1, horizOn=True, vertOn=True)
        elif self.multicursor:
            # remove multicursor
            self.multicursor.disconnect()
            self.multicursor = None
        self.canvas.draw()
        event.Skip()

    ####################################################################################################################
    # draw elements on canvas plot areas / axes (by coordinates)
    def on_button_plot(self, event=None):
        # plot a function
        xmin, xmax, step = self._get_floats("text_plot_", ("xmin","xmax","xstep"))
        if None in (xmin, xmax, step):
            # one of the values is invalid
            return
        x = numpy.arange(xmin, xmax, step)
        
        # build globals with some functions for eval(...)
        g = {}
        for name in ["sin","cos","tan","ufunc","square"]:
            g[name] = getattr(numpy, name)
        y = eval(self.text_function.GetValue(), g, {"numpy":numpy, "x":x})

        axes = self.get_axes()
        colour, width, style = self._get_styles()
        
        axes.plot(x,y, picker=5,  # enable picking, i.e. the user can select this with the mouse
                  color=colour, linewidth=width, linestyle=style)

        # show the updates
        self.canvas.draw()
        self.set_history_buttons()

    ####################################################################################################################
    # helpers
    def _get_floats(self, prefix, names):
        ret = []
        for name in names:
            full_name = prefix+name
            f = self._get_float(getattr(self, full_name))
            ret.append(f)
        return ret

    def _get_float(self, control):
        # returns a float or None if not a valid float
        try:
            ret = float( control.GetValue() )
            colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
            control.SetBackgroundColour(colour)
        except:
            control.SetBackgroundColour(wx.RED)
            wx.Bell()
            ret = None
        control.Refresh()
        return ret

    ####################################################################################################################
    # mouse actions
    def on_pick(self, event):
        # pick: when the user clicked an item on the canvas that has picking enabled ( see above: line.set_picker(5) )

        if id(event.mouseevent)==self._last_pick_mouseevent:
            # it's reasonable that we have received this one already for another element
            print("skipping pick event")
            return
        self._last_pick_mouseevent = id(event.mouseevent)

        delete = self.checkbox_pick_delete.GetValue()

        artist = event.artist

        s = ""
        if isinstance(artist, matplotlib.lines.Line2D):
            s = "line"
        elif isinstance(artist, matplotlib.patches.Rectangle):
            s = "rectangle"
        elif isinstance(artist, matplotlib.patches.Circle):
            s = "circle"

        if artist.axes:
            # data plotted on axes
            if hasattr(artist, "get_data"):
                xdata, ydata = artist.get_data()
                ind = event.ind[0]
                s = 'plot: %s, %s'%( xdata[ind], ydata[ind] )
            elif hasattr(artist, "get_xy"):
                xdata, ydata = artist.get_xy()
            if delete: artist.remove()
        else:
            # no axes -> drawn directly on figure by pixel coordinates
            if delete: self.canvas.figure.patches.remove(artist)
        self.text_picked.SetValue(s)
        self.canvas.draw()

    def on_mouse_move(self, event):
        # display mouse pointer coordinates; based on code from NavigationToolbar2
        s = ""
        if event.inaxes and event.inaxes.get_navigate():
            try:
                xs = event.inaxes.format_xdata(event.xdata).strip()
                ys = event.inaxes.format_ydata(event.ydata).strip()
                s = "%s / %s"%(xs,ys)
            except (ValueError, OverflowError):
                pass
            else:
                artists = [a for a in event.inaxes.mouseover_set if a.contains(event) and a.get_visible()]

                if artists:
                    a = cbook._topmost_artist(artists)
                    if a is not event.inaxes.patch:
                        data = a.get_cursor_data(event)
                        if data is not None:
                            s += ' [%s]' % a.format_cursor_data(data)

        self.text_cursor_xy_value.SetValue(s)
        self.text_cursor_xy_pixel.SetValue( "%s / %s px"%(event.x, event.y))

    ####################################################################################################################
    # canvas size and layout (number of plots)
    def on_choice_canvas_size(self, event):
        # this partially relies on a modification of FigureCanvas in matplotlib_compat.py
        value = event.GetString()
        sz = canvas.GetParent().Sizer
        si = sz.GetItem(canvas)
        if "x" in value:
            si.SetProportion(0)
            si.SetFlag( si.GetFlag() & ~wx.EXPAND ) # clear the expand bit
            size = value.split("x")
            size = int(size[0]), int(size[1])
            si.SetMinSize(size)
            canvas.SetSize(size)
            canvas.SetMinSize(size)
        else:
            # variable size
            si.SetProportion(3)
            si.SetFlag( si.GetFlag() | wx.EXPAND ) # clear the expand bit
            si.SetMinSize( (100,100) )
        sz.Layout()

    def on_choice_subplots(self, event=None):
        # clear the canvas if required; set the "Subplot" choices
        if event is None:
            rows_cols = self.choice_subplots.GetStringSelection()
            update_subplot_choices = True
        else:
            rows_cols = event.GetString()
            update_subplot_choices = False
        rows, cols = rows_cols.split("x") # e.g. "2x1"
        subplots = int(rows), int(cols)
        if hasattr(self, "subplots") and subplots!=self.subplots:
            # changed -> clear existing plots
            #self.on_button_clear("plots")
            self.on_button_clear("all")
            update_subplot_choices = True
        if update_subplot_choices:
            for SUBPLOTS,CHOICES in self._SUBPLOT_CHOICES:
                if SUBPLOTS==subplots:
                    if CHOICES is None:
                        self.choice_subplot.Clear()
                        self.choice_subplot.Disable()
                        self.subplot = (1,1)
                    else:
                        self.choice_subplot.Set(CHOICES)
                        self.choice_subplot.SetSelection(0)
                        self.choice_subplot.Enable(len(CHOICES)>1)
                        self.subplot = CHOICES[0]

        self.subplots = subplots

    def on_choice_subplot(self, event):
        self.subplot = event.GetString()

    ####################################################################################################################
    # plot styles: maintain properties for colour, line width, line style
    def _get_styles(self):
        ret = (self._line_colour, self._line_width, self._line_style)
        n = self.combo_box_colour.GetSelection() + 1
        n = n % self.combo_box_colour.GetCount()
        self.combo_box_colour.Select(n)
        self.on_combo_colour()
        return ret

    def on_combo_colour(self, event=None):
        self._line_colour = self.combo_box_colour.GetValue() or "black"

    def on_combo_line_width(self, event=None):
        self._line_width  = float(self.combo_box_line_width.GetValue())

    def on_choice_line_style(self, event=None):
        line_style = self.choice_line_style.GetItems()[self.choice_line_style.GetSelection()]
        self._line_style  = line_style.split()[0].strip()

    ####################################################################################################################
    # some actions to be forwarded to the tool manager
    def on_button_zoom_history(self, action):
        if action=="home":
            self.toolmanager.trigger_tool("home")
        elif action=="back":
            self.toolmanager.trigger_tool("back")
        elif action=="forward":
            self.toolmanager.trigger_tool("forward")
        self.canvas.draw()
        self.set_history_buttons()

    def on_button_autoscale(self, event):
        if not self.canvas.figure.axes: return
        for axes in self.canvas.figure.axes:
            axes.autoscale(True, 'both', True)
        self.canvas.draw()
        viewpos_tool = self.toolmanager.get_tool("viewpos")
        viewpos_tool.clear(self.canvas.figure)
        if self.canvas.figure in viewpos_tool.views:
            self.toolmanager.get_tool("viewpos").push_current()
        self.set_history_buttons()

    def set_history_buttons(self, event=None):
        # enable or disable buttons: zoom/scale, clear
        vp = self.toolmanager.get_tool("viewpos")
        if vp.views:
            view_stack = vp.views[self.canvas.figure]
            view_stack._pos
            
            can_backward = view_stack._pos > 0
            can_forward  = view_stack._pos < len(view_stack._elements) - 1
        else:
            can_backward = can_forward = False
        self.button_zoom_hist_back.Enable(can_backward)
        self.button_zoom_hist_forward.Enable(can_forward)
        # enable the autoscale button as well
        can_autoscale = bool(self.canvas.figure.axes)
        self.button_autoscale.Enable(can_autoscale)
        # and the clear buttons
        can_clear_plots = False
        for axes in self.canvas.figure.axes:
            if axes.has_data():
                can_clear_plots = True
                break
        can_clear_all   = len(self.canvas.figure.get_children()) > 1
        self.button_clear_plots.Enable(can_clear_plots)
        self.button_clear_all.Enable(can_clear_all)

    def on_choice_mouse_action(self, event):
        selection = self.choice_mouse_action.GetStringSelection()
        if selection == "Pan/Zoom":
            self.toolmanager.trigger_tool("pan")
        elif selection=="Zoom":
            self.toolmanager.trigger_tool("zoom")
        else:
            # deactivate by triggering the currently selected tool
            # when pan and zoom are inactive, the mouse will pick elements
            toggled = self.toolmanager.active_toggle.get("default")
            if toggled=="pan":
                self.toolmanager.trigger_tool("pan")
            elif toggled=="zoom":
                self.toolmanager.trigger_tool("zoom")

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    def readfun(self, f, bar):
        global prog_i
        bar.update(prog_i)
        prog_i = prog_i + 1
        return pandas.read_csv(f, index_col=False)

    def on_button_adddata(self, event):
        global prog_i
        prog_i=0
        self.list_box_currentdata.Append(self.list_box_data_folder.GetStringSelection())
        self.list_box_currentdata.SetSelection(self.list_box_currentdata.FindString(self.list_box_data_folder.GetStringSelection()))
        picklefolder = "F:\\A7data\\p\\"
        folder = self.list_box_data_folder.GetStringSelection()
        files = glob.glob("D:\Project\ODEA7\PTrun\\"+folder+'\\a\\allMyNumbers*.csv')
        bar = progressbar.ProgressBar(max_value=len(files))

        if os.path.exists(picklefolder + folder):
            print("read pickle")
            self.result[folder] = pandas.read_pickle(picklefolder + folder)
        else:
            print("read raw csv")
            self.result[folder] = pandas.concat([self.readfun(f, bar) for f in files], ignore_index=True)
            self.result[folder].to_pickle(picklefolder + folder)

        self.slider_length.SetRange(1, self.result[self.list_box_data_folder.GetStringSelection()].shape[0])
        self.slider_length.SetValue(self.result[self.list_box_data_folder.GetStringSelection()].shape[0])
        self.slider_startpoint.SetRange(1, self.result[self.list_box_data_folder.GetStringSelection()].shape[0])
        self.slider_startpoint.SetValue(1)
        winsound.Beep(2500, 300)
        print("_add data'!")

    def on_button_update_folder(self, event):
        runlist = os.listdir('D:\Project\ODEA7\PTrun')
        self.list_box_data_folder.Set(runlist)
        # self.listBox.SetSelection(2)
        print("update'!")

    def on_button_removedata(self, event):
        self.result.pop(self.list_box_currentdata.GetSelection()) # obvious logic error in delete an item added more than once but can be avoided by restricted ops
        self.list_box_currentdata.Delete(self.list_box_currentdata.GetSelection())
        print("_rmdata'!")

    def on_button_draw(self, event):

        x = self.result[self.list_box_currentdata.GetStringSelection()].loc[:, self.list_box_parax.GetStringSelection()]
        y = self.result[self.list_box_currentdata.GetStringSelection()].loc[:,  self.list_box_paray.GetStringSelection()]
        endpoint = self.slider_startpoint.GetValue()+self.slider_length.GetValue()-1
        if endpoint > self.slider_startpoint.GetMax()-1:
            endpoint = self.slider_startpoint.GetMax()-1
        x = x.iloc[self.slider_startpoint.GetValue():endpoint]
        y = y.iloc[self.slider_startpoint.GetValue():endpoint]
        axes = self.get_axes()
        colour, width, style = self._get_styles()

        axes.plot(x, y, picker=5,  # enable picking, i.e. the user can select this with the mouse
                  color=colour, linewidth=width, linestyle=style)

        # show the updates
        self.canvas.draw()

    def on_button_popupdraw1(self, event):
        startPer = self.slider_startpoint.GetValue() / self.slider_startpoint.GetMax()
        endPer = (self.slider_startpoint.GetValue() + self.slider_length.GetValue() - 1) / self.slider_startpoint.GetMax()
        paraList = [self.list_box_parax.GetStringSelection(), self.list_box_paray.GetStringSelection()]
        fig = plt.figure()
        axes = fig.add_subplot(1, 1, 1)
        self.draw_on_request(ax=axes,startPer=startPer,endPer=endPer,paraList=paraList)
        plt.show()

    def on_button_popupdraw2(self, event):
        fig = plt.figure()
        axes = fig.add_subplot(2, 3, 1)
        self.draw_on_request(ax=axes, paraList = ['time','xb1'])
        axes = fig.add_subplot(2, 3, 2)
        self.draw_on_request(ax=axes, paraList = ['time','yb1'])
        axes = fig.add_subplot(2, 3, 3)
        self.draw_on_request(ax=axes, paraList = ['time','zb1'])
        axes = fig.add_subplot(2, 3, 4, projection='3d')
        self.draw_on_request(ax=axes, paraList = ['time','xb1','yb1'], dim=3)
        axes = fig.add_subplot(2, 3, 5,  projection='3d')
        self.draw_on_request(ax=axes, paraList=['xb1', 'yb1','zb1'], dim=3)
        axes = fig.add_subplot(2, 3, 6)
        #self.draw_on_request(ax=axes, paraList = ['time','xb1'])
        plt.show()

    def on_button_popupdraw3(self, event):
        fig = plt.figure()
        paraLists = [['time','xb1'],['time','yb1'],['time','zb1']]
        index=1
        for paraList in paraLists:
            axes = fig.add_subplot(2, 2, index)
            self.draw_on_request(ax=axes, paraList = paraList)
            index=index+1

        fig = plt.figure()
        paraLists = [['time','xb2'],['time','yb2'],['time','zb2']]
        index=1
        for paraList in paraLists:
            axes = fig.add_subplot(2, 2, index)
            self.draw_on_request(ax=axes, paraList = paraList)
            index=index+1

        fig = plt.figure()
        paraLists = [['time','xb3'],['time','yb3'],['time','zb3']]
        index=1
        for paraList in paraLists:
            axes = fig.add_subplot(2, 2, index)
            self.draw_on_request(ax=axes, paraList = paraList)
            index=index+1

        fig = plt.figure()
        paraLists = [['time','xb4'],['time','yb4'],['time','zb4']]
        index=1
        for paraList in paraLists:
            axes = fig.add_subplot(2, 2, index)
            self.draw_on_request(ax=axes, paraList = paraList)
            index=index+1

        fig = plt.figure()
        paraLists = [['time','x1'],['time','y1'],['time','z1'],['time','theta1x'],['time','theta1y'],['time','theta1z']]
        index=1
        for paraList in paraLists:
            axes = fig.add_subplot(2, 3, index)
            self.draw_on_request(ax=axes, paraList = paraList)
            index=index+1
        fig = plt.figure()
        paraLists = [['time','x2'],['time','y2'],['time','z2'],['time','theta2x'],['time','theta2y'],['time','theta2z']]
        index=1
        for paraList in paraLists:
            axes = fig.add_subplot(2, 3, index)
            self.draw_on_request(ax=axes, paraList = paraList)
            index=index+1
        fig = plt.figure()
        paraLists = [['time','thetap'],['time','thetag'],['time','theta1z'],['time','theta2z']]
        index=1
        for paraList in paraLists:
            axes = fig.add_subplot(2, 2, index)
            self.draw_on_request(ax=axes, paraList = paraList)
            index=index+1

        plt.show()

    def draw_on_request(self, ax, startPer = 0, endPer = 1,
                        dim = 2,
                        paraList = ['time','thetap'] ):
        drawdata = {}
        for obj in self.result.items():
            #firstPara = self.list_box_parax.GetStringSelection()
            # = self.list_box_paray.GetStringSelection()
            key, data = obj
            drawdata[key] = self.getdrawdata(data, paraList)
            total_len = drawdata[key].shape[0] # length in dim 0
            startPoint = int(total_len * startPer)
            endPoint = int(total_len * endPer)
            drawdata[key] = drawdata[key][startPoint:endPoint, :]
            if dim==2:
                drawn=self.drawPlot2d(ax, drawdata[key][:, 0], drawdata[key][:, 1],label=key)
                ax.set_xlabel(paraList[0])
                ax.set_ylabel(paraList[1])
            if dim==3:
                drawn=self.drawPlot3d(ax, drawdata[key][:, 0], drawdata[key][:, 1],drawdata[key][:, 2],label=key)
                ax.set_xlabel(paraList[0])
                ax.set_ylabel(paraList[1])
                ax.set_zlabel(paraList[2])
            ax.legend()


    def getdrawdata(self, data, paraList):
        nd = numpy.array(data[paraList])
        return nd

    def drawPlot2d(self,ax,x,y,label):
        drawn=ax.plot(x, y, picker=5,  # enable picking, i.e. the user can select this with the mouse
        label=label)
        return drawn


    def drawPlot3d(self,ax,x,y,z,label):
        drawn =ax.plot(x, y,z, picker=5,  # enable picking, i.e. the user can select this with the mouse
        label=label)
        return drawn

    def on_button_openfolder(self, event):
        start_directory = r'D:\Project\ODEA7\PTrun\\' + self.list_box_data_folder.GetStringSelection()
        os.startfile(start_directory)

    def on_button_opencfg(self, event):
        start_directory = r'D:\Project\ODEA7\PTrun\\' + self.list_box_data_folder.GetStringSelection() + '\cfg.ini'
        os.startfile(start_directory)

    def on_file_save(self, event):
        # save figure as bitmap or PDF
        self.toolmanager.trigger_tool("save")

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    
    def on_file_exit(self, event):
        self.Close()

    def OnClose(self, event):
        # delete graphics context to avoid crash
        self.canvas.cleanup()
        event.Skip()


class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
