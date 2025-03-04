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
from PyQt6.QtCore import pyqtSignal


# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceParaClass:
"""


class TraceParaClass(PlotPara):
    def __init__(self):
        super(TraceParaClass, self).__init__('Trace')
        a = 1


# ----------------------------------------------------------------------------------------------------------------------

"""
    TracePlotWidget:
"""


class TracePlotWidget(PlotWidget):
    def __init__(self):
        super(TracePlotWidget, self).__init__('trace')
        a = 1


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
    y_gap = 4

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

        # parameters
        self.frame_img = None
        self.t_trace = np.min([self.t_dur, self.t_trace0])
        self.t_lim = [0, self.t_trace]

        # class widgets
        self.l_reg = None
        self.trace_curves = []
        self.image_item = pg.ImageItem()

        # sets up the plot regions
        self.setup_subplots(n_r=2, n_c=1)
        self.plot_item = self.h_plot[0, 0].getPlotItem()
        self.frame_item = self.h_plot[1, 0].getPlotItem()

        # initialises the other class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # resets the row stretch
        self.plot_layout.setRowStretch(0, 19)
        self.plot_layout.setRowStretch(1, 1)

        # ---------------------------------------------------------------------------
        # Trace Subplot Setup
        # ---------------------------------------------------------------------------

        # sets the plot item properties
        self.plot_item.setMouseEnabled(y=False)
        self.plot_item.hideAxis('left')
        self.plot_item.hideButtons()
        self.plot_item.setDownsampling(auto=True)

        # sets the axis limits
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
        self.v_box[0, 0].setLimits(xMin=0, xMax=self.session_info.session_props.t_dur)
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

        # ---------------------------------------------------------------------------
        # Frame Image Setup
        # ---------------------------------------------------------------------------

        # creates the image transform
        tr = pg.QtGui.QTransform()
        tr.scale(self.t_dur / self.n_col_img, 1.0)

        # pen widgets
        l_pen = pg.mkPen(width=3, color='y')
        l_pen_h = pg.mkPen(width=3, color='g')

        # sets the plot item properties
        self.frame_item.setMouseEnabled(y=False)
        self.frame_item.hideAxis('left')
        self.frame_item.hideAxis('bottom')
        self.frame_item.hideButtons()
        self.frame_item.setDefaultPadding(0.0)

        # adds the image frame
        self.image_item.setTransform(tr)
        self.image_item.setColorMap(self.setup_colour_map())
        self.image_item.setImage(self.setup_frame_image())
        self.h_plot[1, 0].addItem(self.image_item)

        # sets up the linear region
        self.l_reg = pg.LinearRegionItem(
            [0, self.t_trace], bounds=[0, self.t_dur], span=[0, 1], pen=l_pen, hoverPen=l_pen_h)
        self.l_reg.sigRegionChangeFinished.connect(self.frame_region_move)
        self.l_reg.setZValue(10)
        self.h_plot[1, 0].addItem(self.l_reg)

        # disables the viewbox pan/zooming on the frame selection panel
        self.v_box[1, 0].setMouseEnabled(False, False)

    def setup_colour_map(self):

        p_rgb = []
        for i_lvl in range(self.n_lvl):
            p_hsv = (0.5 - (i_lvl / (2 * self.n_lvl)), 0.5, 0.5)
            p_rgb.append([int(255 * x) for x in list(colorsys.hsv_to_rgb(*p_hsv))])

        return pg.ColorMap(pos=np.linspace(0.0, 1.0, self.n_lvl), color=p_rgb)

    def setup_frame_image(self):

        return np.linspace(0, 1, self.n_col_img).reshape(-1, 1)

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
            self.h_plot[0, 0].setYRange(0, 1 + (n_plt - 1) * self.y_gap)

        else:
            # case is there are no plots (collapse y-axis range)
            self.h_plot[0, 0].setYRange(0, self.y_ofs / 2.)

    def reset_frame_image(self):

        a = 1

    # ---------------------------------------------------------------------------
    # Frame Region Event Functions
    # ---------------------------------------------------------------------------

    def frame_region_move(self):

        self.t_lim = list(self.l_reg.getRegion())
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)

        self.reset_trace_view()

    # ---------------------------------------------------------------------------
    # Plot Button Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'new':
                # case is the new button
                cf.show_error('Finish Me!')

            case 'open':
                # case is the open button
                cf.show_error('Finish Me!')

            case 'save':
                # case is the save button
                cf.show_error('Finish Me!')

            case 'close':
                # case is the close button
                self.hide_plot.emit()
