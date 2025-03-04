# module import
import colorsys
import functools
import time

import numpy as np
import pyqtgraph as pg

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.plotting.utils import PlotWidget, PlotPara

# pyqt6 module import
from PyQt6.QtWidgets import (QWidget)
from PyQt6.QtCore import pyqtSignal, Qt

# plot button fields
b_icon = ['datatip', 'save', 'close']
b_type = ['toggle', 'button', 'button']


# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceParaClass:
"""


class TraceParaClass(PlotPara):
    def __init__(self):
        super(TraceParaClass, self).__init__('Trace')


# ----------------------------------------------------------------------------------------------------------------------

"""
    TracePlotWidget:
"""


class TracePlotWidget(PlotWidget):
    def __init__(self):
        super(TracePlotWidget, self).__init__('trace', b_icon=b_icon, b_type=b_type)

# ----------------------------------------------------------------------------------------------------------------------

"""
    TracePlot:
"""


class TracePlot(TraceParaClass, TracePlotWidget):
    # pyqtsignal functions
    hide_plot = pyqtSignal()

    # parameters
    y_ofs = 0.2
    t_trace0 = 2
    n_lvl = 100
    n_col_img = 1000
    n_row_yscl = 100
    y_gap = 4

    # pen widgets
    l_pen = pg.mkPen(width=3, color='y')
    l_pen_h = pg.mkPen(width=3, color='g')

    def __init__(self, session_info):
        TracePlotWidget.__init__(self)
        TraceParaClass.__init__(self)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # experiment properties
        self.t_dur = s_props.get_value('t_dur')
        self.s_freq = s_props.get_value('s_freq')
        self.n_channels = s_props.get_value('n_channels')
        self.n_samples = s_props.get_value('n_samples')

        # plot item mouse event functions
        self.trace_release_fcn = None
        self.trace_dclick_fcn = None

        # parameters
        self.y_lim_tr = self.y_ofs / 2
        self.t_trace = np.min([self.t_dur, self.t_trace0])
        self.t_lim = [0, self.t_trace]

        # class widgets
        self.l_reg_x = None
        self.l_reg_y = None
        self.frame_img = None
        self.trace_curves = []
        self.ximage_item = pg.ImageItem()
        self.yimage_item = pg.ImageItem()

        # sets up the plot regions
        self.setup_subplots(n_r=2, n_c=2)
        self.plot_item = self.h_plot[0, 0].getPlotItem()
        self.xframe_item = self.h_plot[1, 0].getPlotItem()
        self.yframe_item = self.h_plot[0, 1].getPlotItem()

        # initialises the other class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # resets the row stretch
        self.plot_layout.setRowStretch(0, 19)
        self.plot_layout.setRowStretch(1, 1)
        self.plot_layout.setColumnStretch(0, 19)
        self.plot_layout.setColumnStretch(1, 1)

        # ---------------------------------------------------------------------------
        # Trace Subplot Setup
        # ---------------------------------------------------------------------------

        # sets the plot item properties
        self.plot_item.setMouseEnabled()
        self.plot_item.hideAxis('left')
        self.plot_item.hideButtons()
        self.plot_item.setDownsampling(auto=True)

        # sets the axis limits
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
        self.v_box[0, 0].setLimits(xMin=0, xMax=self.session_info.session_props.t_dur, yMin=0, yMax=self.y_lim_tr)
        self.v_box[0, 0].setMouseMode(self.v_box[0, 0].RectMode)

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = functools.partial(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

        # creates the trace curves
        l_pen_tr = pg.mkPen(color=cf.get_colour_value('g'), width=1)
        for i_ch in range(self.n_channels):
            curve = pg.PlotCurveItem(pen=l_pen_tr, skipFiniteCheck=True)
            curve.setPos(0, i_ch * self.y_gap)
            self.h_plot[0, 0].addItem(curve)
            self.trace_curves.append(curve)

        # sets the signal trace plot event functions
        self.trace_dclick_fcn = self.h_plot[0, 0].mousePressEvent
        self.trace_release_fcn = self.h_plot[0, 0].mouseReleaseEvent
        self.h_plot[0, 0].mouseReleaseEvent = self.trace_mouse_release
        self.h_plot[0, 0].mouseDoubleClickEvent = self.trace_double_click

        # ---------------------------------------------------------------------------
        # X-Axis Range Finder Setup
        # ---------------------------------------------------------------------------

        # creates the image transform
        tr_x = pg.QtGui.QTransform()
        tr_x.scale(self.t_dur / self.n_col_img, 1.0)

        # sets the plot item properties
        self.xframe_item.setMouseEnabled(y=False)
        self.xframe_item.hideAxis('left')
        self.xframe_item.hideAxis('bottom')
        self.xframe_item.hideButtons()
        self.xframe_item.setDefaultPadding(0.0)

        # adds the image frame
        self.ximage_item.setTransform(tr_x)
        self.ximage_item.setColorMap(self.setup_colour_map())
        self.ximage_item.setImage(self.setup_frame_image('x'))
        self.h_plot[1, 0].addItem(self.ximage_item)

        # creates the linear region
        self.l_reg_x = pg.LinearRegionItem([0, self.t_trace], bounds=[0, self.t_dur], span=[0, 1],
                                           pen=self.l_pen, hoverPen=self.l_pen_h)
        self.l_reg_x.sigRegionChangeFinished.connect(self.xframe_region_move)
        self.l_reg_x.setZValue(10)
        self.h_plot[1, 0].addItem(self.l_reg_x)

        # disables the viewbox pan/zooming on the frame selection panel
        self.v_box[1, 0].setMouseEnabled(False, False)

        # ---------------------------------------------------------------------------
        # Y-Axis Range Finder Setup
        # ---------------------------------------------------------------------------

        # creates the image transform
        tr_y = pg.QtGui.QTransform()
        tr_y.scale(1 / self.n_row_yscl, 1.0)

        # disables the viewbox pan/zooming on the frame selection panel
        self.v_box[0, 1].setMouseEnabled(False, False)

        # sets the plot item properties
        self.yframe_item.setMouseEnabled(x=False)
        self.yframe_item.hideAxis('left')
        self.yframe_item.getAxis('bottom').setGrid(False)
        self.yframe_item.getAxis('bottom').setTextPen('black')
        self.yframe_item.getAxis('bottom').setTickPen(pg.mkPen(style=Qt.PenStyle.NoPen))
        self.yframe_item.hideButtons()
        self.yframe_item.setDefaultPadding(0.0)

        # adds the image frame
        self.yimage_item.setTransform(tr_y)
        self.yimage_item.setColorMap(self.setup_colour_map())
        self.yimage_item.setImage(self.setup_frame_image('y'))
        self.h_plot[0, 1].addItem(self.yimage_item)

        # creates the linear region
        self.l_reg_y = pg.LinearRegionItem([0, self.n_row_yscl], bounds=[0, self.n_row_yscl], span=[0, 1],
                                           pen=self.l_pen, hoverPen=self.l_pen_h, orientation='horizontal')
        self.l_reg_y.sigRegionChangeFinished.connect(self.yframe_region_move)
        self.l_reg_y.setZValue(10)
        self.h_plot[0, 1].addItem(self.l_reg_y)

        # makes the bottom right plot invisible
        self.h_plot[1, 1].setVisible(False)

    def setup_colour_map(self):

        p_rgb = []
        for i_lvl in range(self.n_lvl):
            p_hsv = (0.5 - (i_lvl / (2 * self.n_lvl)), 0.5, 0.5)
            p_rgb.append([int(255 * x) for x in list(colorsys.hsv_to_rgb(*p_hsv))])

        return pg.ColorMap(pos=np.linspace(0.0, 1.0, self.n_lvl), color=p_rgb)

    def setup_frame_image(self, axis):

        if axis == 'x':
            return np.linspace(0, 1, self.n_col_img).reshape(-1, 1)

        else:
            return np.linspace(0, 1, self.n_row_yscl).reshape(1, -1)

    # ---------------------------------------------------------------------------
    # Plot Update/Reset Functions
    # ---------------------------------------------------------------------------

    def reset_trace_view(self):

        # retrieves the currently selected channels
        i_channel = self.session_info.get_selected_channels()
        n_plt = len(i_channel)

        if n_plt:
            # sets the frame range indices
            s_freq = self.session_info.session_props.s_freq
            i_frm0 = int(self.t_lim[0] * s_freq)
            i_frm1 = int(self.t_lim[1] * s_freq)

            # sets up the x-data array
            x = np.linspace(self.t_lim[0], self.t_lim[1], i_frm1 - i_frm0)

            # sets up the y-data array
            ch_ids = self.session_info.get_channel_ids(i_channel)
            y0 = self.session_info.get_traces(start_frame=i_frm0, end_frame=i_frm1, channel_ids=ch_ids)
            for i in range(n_plt):
                y_min, y_max = np.min(y0[:, i]), np.max(y0[:, i])
                y_scl = self.y_ofs + (1 - self.y_ofs) * (y0[:, i] - y_min) / (y_max - y_min)
                self.trace_curves[i].setData(x, y_scl)

            # sets the y-axis range
            self.y_lim_tr = 1 + (n_plt - 1) * self.y_gap

        else:
            # case is there are no plots (collapse y-axis range)
            self.y_lim_tr = self.y_ofs / 2.

        # resets the y-axis range
        self.v_box[0, 0].setLimits(yMax=self.y_lim_tr)
        self.v_box[0, 0].setYRange(0, self.y_lim_tr, padding=0)
        self.trace_double_click()

    def reset_frame_image(self):

        a = 1

    # ---------------------------------------------------------------------------
    # Signal Trace Plot Event Functions
    # ---------------------------------------------------------------------------

    def trace_double_click(self, evnt=None) -> None:

        # flag that updating is taking place
        self.is_updating = True

        # runs the original mouse event function
        if evnt is not None:
            self.trace_release_fcn(evnt)
            self.h_plot[0, 0].setYRange(0, self.y_lim_tr, padding=0)

        # resets the y-range
        self.l_reg_y.setRegion((0, 100))

        # resets the update flag
        self.is_updating = False

    def trace_mouse_release(self, evnt) -> None:

        # flag that updating is taking place
        self.is_updating = True

        # runs the original mouse event function
        self.trace_release_fcn(evnt)

        # retrieves the new axis limit
        y_lim = self.v_box[0, 0].viewRange()[1]
        self.t_lim = self.v_box[0, 0].viewRange()[0]

        # resets the x/y-axis linear regions
        self.l_reg_x.setRegion(self.t_lim)
        self.l_reg_y.setRegion(100 * np.array(y_lim) / self.y_lim_tr)

        # resets the update flag
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Frame Region Event Functions
    # ---------------------------------------------------------------------------

    def xframe_region_move(self):

        if self.is_updating:
            return

        self.t_lim = list(self.l_reg_x.getRegion())
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
        self.reset_trace_view()

    def yframe_region_move(self):

        if self.is_updating:
            return

        y_lim_nw = np.array(self.l_reg_y.getRegion()) * (self.y_lim_tr / 100)
        self.v_box[0, 0].setYRange(y_lim_nw[0], y_lim_nw[1], padding=0)

    # ---------------------------------------------------------------------------
    # Plot Button Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'datatip':
                # case is the save button
                pass

            case 'save':
                # case is the save button
                cf.show_error('Finish Me!')

            case 'close':
                # case is the close button
                self.hide_plot.emit()
