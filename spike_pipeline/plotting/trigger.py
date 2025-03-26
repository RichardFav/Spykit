# module import
import os
import time
import colorsys
import functools
import numpy as np

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.plotting.utils import PlotWidget

# pyqtgraph modules
from pyqtgraph import exporters, mkPen, mkColor, ImageItem, PlotCurveItem, LinearRegionItem, ColorMap
from pyqtgraph.Qt import QtGui

# pyqt6 module import
from PyQt6.QtWidgets import (QWidget)
from PyQt6.QtCore import pyqtSignal, Qt, QObject

# plot button fields
b_icon = ['save', 'close']
b_type = ['button', 'button']
tt_lbl = ['Save Figure', 'Close TriggerView']

# ----------------------------------------------------------------------------------------------------------------------

"""
    TriggerPlot:
"""


class TriggerPlot(PlotWidget):
    # parameters
    p_ofs = 0.05
    n_lvl = 100
    n_col_img = 1000

    # pen widgets
    l_pen = mkPen(width=3, color='y')
    l_pen_hover = mkPen(width=3, color='g')
    l_pen_trig = mkPen(color=cf.get_colour_value('g'), width=1)

    def __init__(self, session_info):
        super(TriggerPlot, self).__init__('trigger', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # experiment properties
        self.t_dur = s_props.get_value('t_dur')
        self.s_freq = s_props.get_value('s_freq')
        self.n_samples = s_props.get_value('n_samples')
        self.t_lim = [0, self.t_dur]

        # field retrieval
        self.gen_props = None
        self.trig_props = None
        self.x_tr = np.arange(self.n_samples) / self.s_freq
        self.y_tr = self.session_info.session.sync_ch

        # plot item mouse event functions
        self.trace_release_fcn = None
        self.trace_dclick_fcn = None

        # class widgets
        self.l_reg_x = None
        self.i_sel_tr = None
        self.frame_img = None
        self.ximage_item = ImageItem()

        # trace items
        self.trig_trace = PlotCurveItem(pen=self.l_pen_trig, skipFiniteCheck=False)

        # sets up the plot regions
        self.setup_subplots(n_r=2, n_c=1)
        self.plot_item = self.h_plot[0, 0].getPlotItem()
        self.xframe_item = self.h_plot[1, 0].getPlotItem()

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
        self.plot_item.setMouseEnabled()
        self.plot_item.hideAxis('left')
        self.plot_item.hideButtons()
        # self.plot_item.setDownsampling(ds=1000)
        self.plot_item.setDownsampling(auto=True)
        self.plot_item.setClipToView(True)

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = functools.partial(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

        # sets the axis limits
        self.v_box[0, 0].setLimits(xMin=0, xMax=self.session_info.session_props.t_dur, yMin=0, yMax=1)
        self.v_box[0, 0].setMouseMode(self.v_box[0, 0].RectMode)

        # adds the traces to the main plot
        self.h_plot[0, 0].addItem(self.trig_trace)
        self.update_trigger_trace()

        # sets the signal trace plot event functions
        self.trace_dclick_fcn = self.h_plot[0, 0].mousePressEvent
        self.h_plot[0, 0].mouseDoubleClickEvent = self.trace_double_click

        # ---------------------------------------------------------------------------
        # X-Axis Range Finder Setup
        # ---------------------------------------------------------------------------

        # creates the image transform
        tr_x = QtGui.QTransform()
        tr_x.scale(self.t_dur / self.n_col_img, 1.0)

        # sets the plot item properties
        self.xframe_item.setMouseEnabled(y=False)
        self.xframe_item.hideAxis('left')
        self.xframe_item.hideAxis('bottom')
        self.xframe_item.hideButtons()
        self.xframe_item.setDefaultPadding(0.0)

        # adds the image frame
        self.ximage_item.setTransform(tr_x)
        self.ximage_item.setColorMap(cw.setup_colour_map(self.n_lvl))
        self.ximage_item.setImage(self.setup_frame_image())
        self.h_plot[1, 0].addItem(self.ximage_item)

        # creates the linear region
        self.l_reg_x = LinearRegionItem([0, self.t_dur], bounds=[0, self.t_dur], span=[0, 1],
                                        pen=self.l_pen, hoverPen=self.l_pen_hover)
        self.l_reg_x.sigRegionChangeFinished.connect(self.xframe_region_move)
        self.l_reg_x.setZValue(10)
        self.h_plot[1, 0].addItem(self.l_reg_x)

        # disables the viewbox pan/zooming on the frame selection panel
        self.v_box[1, 0].setMouseEnabled(False, False)

    def update_trigger_trace(self):

        # sets up the trace plot
        i_tr = self.session_info.session.get_run_index(self.session_info.current_run)
        y_tr_new = self.p_ofs + (1 - 2 * self.p_ofs) * cf.normalise_trace(self.y_tr[i_tr])

        # resets the trigger trace data
        self.trig_trace.clear()
        self.trig_trace.setData(self.x_tr, y_tr_new)

    def setup_frame_image(self):

        return np.linspace(0, 1, self.n_col_img).reshape(-1, 1)

    # ---------------------------------------------------------------------------
    # Frame Region Event Functions
    # ---------------------------------------------------------------------------

    def xframe_region_move(self):

        if self.is_updating:
            return

        self.t_lim = list(self.l_reg_x.getRegion())
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)

    # ---------------------------------------------------------------------------
    # Plot Button Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'save':
                # case is the figure save button

                # outputs the current trace to file
                f_path = cf.setup_image_file_name(cw.figure_dir, 'TraceTest.png')  # CHANGE THIS TO
                exp_obj = exporters.ImageExporter(self.h_plot[0, 0].getPlotItem())
                exp_obj.export(f_path)

            case 'close':
                # case is the close button
                self.hide_plot.emit()

    # ---------------------------------------------------------------------------
    # Signal Trace Plot Event Functions
    # ---------------------------------------------------------------------------

    def trace_double_click(self, evnt=None) -> None:

        # flag that updating is taking place
        self.is_updating = True

        # runs the original mouse event function
        if evnt is not None:
            self.trace_dclick_fcn(evnt)

            # updates the time limits
            self.t_lim = [0, self.t_dur]
            self.h_plot[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
            self.l_reg_x.setRegion(self.t_lim)

        # resets the update flag
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Parameter Object Setter Functions
    # ---------------------------------------------------------------------------

    def set_gen_props(self, gen_props_new):

        self.gen_props = gen_props_new
        gen_props_new.set_trig_view(self)

    def set_trig_props(self, trig_props_new):

        self.trig_props = trig_props_new
        trig_props_new.set_trig_view(self)
