# module import
import os
import time
import colorsys
import functools
import numpy as np
from copy import deepcopy

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.plotting.utils import PlotWidget

# pyqtgraph modules
from pyqtgraph import exporters, mkPen, mkBrush, ImageItem, PlotCurveItem, LinearRegionItem, ColorMap
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
    l_brush = mkBrush(color=cf.get_colour_value('k', alpha=200))

    def __init__(self, session_info):
        super(TriggerPlot, self).__init__('trigger', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # experiment properties
        self.t_start_ofs = 0
        self.i_run_reg = self.get_run_index()
        self.t_dur = s_props.get_value('t_dur')
        self.s_freq = s_props.get_value('s_freq')
        self.n_samples = s_props.get_value('n_samples')
        self.n_run = self.session_info.session.get_run_count()
        self.t_lim = [0, self.t_dur]

        # field retrieval
        self.gen_props = None
        self.trig_props = None
        self.x_tr = np.arange(self.n_samples) / self.s_freq
        self.y_tr = self.session_info.session.sync_ch

        # plot item mouse event functions
        self.trace_release_fcn = None
        self.trace_dclick_fcn = None

        # linear region objects
        self.l_reg_x = None
        self.l_reg_xs = np.empty(self.n_run, dtype=object)
        self.n_reg_xs = np.zeros(self.n_run, dtype=int)

        # class widgets
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
        self.v_box[0, 0].setLimits(xMin=0, xMax=self.session_info.session_props.t_dur, yMin=0.01, yMax=0.99)
        self.v_box[0, 0].setMouseMode(self.v_box[0, 0].RectMode)

        # adds the traces to the main plot
        self.h_plot[0, 0].addItem(self.trig_trace)
        self.update_trigger_trace()

        # sets the signal trace plot event functions
        self.trace_dclick_fcn = self.h_plot[0, 0].mousePressEvent
        self.h_plot[0, 0].mouseDoubleClickEvent = self.trace_double_click
        self.h_plot[1, 0].mouseDoubleClickEvent = self.trace_double_click

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

    def update_trigger_trace(self, reset_run=False):

        # sets up the trace plot
        i_run = self.get_run_index()

        if reset_run:
            # hides the current linear regions
            if self.n_reg_xs[self.i_run_reg]:
                [x.hide() for x in self.l_reg_xs[self.i_run_reg]]

            # hides the current linear regions
            if self.n_reg_xs[i_run]:
                [x.show() for x in self.l_reg_xs[i_run]]

            # resets the run index
            self.i_run_reg = i_run
            self.reset_gen_props(False)

        # sets up the scaled trigger trace
        i_frm0 = int(self.t_start_ofs * self.s_freq)
        i_frm1 = int((self.t_start_ofs + self.t_dur) * self.s_freq)
        y_tr_new = self.p_ofs + (1 - 2 * self.p_ofs) * cf.normalise_trace(self.y_tr[i_run][i_frm0:i_frm1])

        # resets the trigger trace data
        self.trig_trace.clear()
        self.trig_trace.setData(self.x_tr[i_frm0:i_frm1] - self.t_start_ofs, y_tr_new)

    def setup_frame_image(self):

        return np.linspace(0, 1, self.n_col_img).reshape(-1, 1)

    # ---------------------------------------------------------------------------
    # Suppression Region Functions
    # ---------------------------------------------------------------------------

    def add_region(self, nw_row):

        # creates the linear region
        l_reg = LinearRegionItem([nw_row[1], nw_row[2]], bounds=[0, self.t_dur], span=[0, 1],
                                 pen=self.l_pen, hoverPen=self.l_pen_hover, brush=self.l_brush)
        l_reg.sigRegionChanged.connect(functools.partial(self.xtrig_region_move, l_reg))
        l_reg.sigRegionChangeFinished.connect(functools.partial(self.xtrig_region_moved, l_reg))
        l_reg.setZValue(10)

        # stores the linear region object
        i_run = self.get_run_index()
        if self.n_reg_xs[i_run] == 0:
            # case is this is the first linear region
            self.l_reg_xs[i_run] = [l_reg]

        else:
            # case is there are multiple linear regions
            self.l_reg_xs[i_run].append(l_reg)

        # increments the linear region count
        self.n_reg_xs[i_run] += 1

        # adds the region to the trigger trace
        self.h_plot[0, 0].addItem(l_reg)

    def delete_region(self, i_reg):

        # removes the linear item from the list/plot item
        i_run = self.get_run_index()
        l_reg_del = self.l_reg_xs[i_run].pop(i_reg)
        self.h_plot[0, 0].removeItem(l_reg_del)

        # decrements the linear region count
        self.n_reg_xs[i_run] -= 1

    def update_region(self, i_reg):

        # removes the linear item from the list/plot item
        i_run = self.get_run_index()
        t_row = self.trig_props.get_table_row(i_reg)
        l_reg = self.l_reg_xs[i_run][i_reg]

        # resets the region position
        self.is_updating = True
        l_reg.setRegion((t_row[1], t_row[2]))
        self.is_updating = False

        # updates the region limits
        self.xtrig_region_moved(l_reg)

    def hide_regions(self, i_run=None):

        if i_run is None:
            i_run = self.get_run_index()

        [x.hide() for x in self.l_reg_xs[i_run]]

    def show_regions(self, i_run=None):

        if i_run is None:
            i_run = self.get_run_index()

        [x.show() for x in self.l_reg_xs[i_run]]

    # ---------------------------------------------------------------------------
    # Frame Region Event Functions
    # ---------------------------------------------------------------------------

    def xframe_region_move(self):

        if self.is_updating:
            return

        self.t_lim = list(self.l_reg_x.getRegion())
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)

    def xtrig_region_move(self, l_reg):

        if self.is_updating:
            return

        # field retrieval
        i_run = self.get_run_index()
        x_reg = list(l_reg.getRegion())
        i_reg = next((i for i, x in enumerate(self.l_reg_xs[i_run]) if l_reg == x))

        # updates the trigger table cells
        self.trig_props.set_table_cell(i_reg, 1, np.round(x_reg[0], 4))
        self.trig_props.set_table_cell(i_reg, 2, np.round(x_reg[1], 4))

    def xtrig_region_moved(self, l_reg):

        if self.is_updating:
            return

        # field retrieval
        i_run = self.get_run_index()
        i_reg = self.get_region_index(l_reg, i_run)

        if i_reg > 0:
            # if not the left-most region, then reset limits with previous region
            self.reset_region_limits(i_run, i_reg - 1, i_reg)

        if (i_reg + 1) < self.n_reg_xs[i_run]:
            # if not the right-most region, then reset limits with next region
            self.reset_region_limits(i_run, i_reg, i_reg + 1)

    def reset_region_limits(self, i_run, i_reg0, i_reg1):

        # retrieves the previous region object/region
        l_reg0 = self.l_reg_xs[i_run][i_reg0]
        x_reg0 = l_reg0.getRegion()

        # retrieves the next region object/region
        l_reg1 = self.l_reg_xs[i_run][i_reg1]
        x_reg1 = l_reg1.getRegion()

        # resets the previous region limits
        if i_reg0 == 0:
            # previous region is the first region
            l_reg0.setBounds([0, x_reg1[0]])

        else:
            # otherwise, reset regions based on region preceeding previous
            x_reg0_pre = self.l_reg_xs[i_run][i_reg0 - 1].getRegion()
            l_reg0.setBounds([x_reg0_pre[1], x_reg1[0]])

        # resets the region limits
        if (i_reg1 + 1) == self.n_reg_xs[i_run]:
            # next region is the last region
            l_reg1.setBounds([x_reg0[1], self.t_dur])

        else:
            # otherwise, reset regions based on region proceeding next
            x_reg1_post = self.l_reg_xs[i_run][i_reg1 + 1].getRegion()
            l_reg1.setBounds([x_reg0[1], x_reg1_post])

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
            # runs the mouse event
            PlotWidget.mousePressEvent(self, evnt)

            # updates the time limits
            self.t_lim = [0, self.t_dur]
            self.h_plot[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
            self.l_reg_x.setRegion(self.t_lim)

        # resets the update flag
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Property Object Functions
    # ---------------------------------------------------------------------------

    def reset_gen_props(self, shift_time=True):

        # calculates the change in start time
        t_start_ofs_new = self.gen_props.get('t_start')
        dt_start_ofs = t_start_ofs_new - self.t_start_ofs

        # class field updates
        self.t_start_ofs = t_start_ofs_new
        self.t_dur = self.gen_props.get('t_dur')

        # ensures the limits are correct
        if shift_time:
            self.t_lim = cf.list_add(self.t_lim, -dt_start_ofs)
            if self.t_lim[0] < 0:
                self.t_lim[0] = 0

            if self.t_lim[1] > self.t_dur:
                self.t_lim[1] = self.t_dur

            # resets the region times
            self.trig_props.reset_region_timing(self.t_dur)

        else:
            self.t_lim = [0, self.t_dur]

        # resets the plot view axis
        self.v_box[0, 0].setLimits(xMin=0, xMax=self.t_dur)
        self.v_box[1, 0].setLimits(xMin=0, xMax=self.t_dur)
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
        self.v_box[1, 0].setXRange(0, self.t_dur, padding=0)
        self.update_trigger_trace()

        # resets the linear region
        self.is_updating = True
        self.l_reg_x.setRegion((self.t_lim[0], self.t_lim[1]))
        self.is_updating = False

    def set_gen_props(self, gen_props_new):

        self.gen_props = gen_props_new
        gen_props_new.set_trig_view(self)

    def set_trig_props(self, trig_props_new):

        self.trig_props = trig_props_new
        trig_props_new.set_trig_view(self)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def get_run_index(self):

        return self.session_info.session.get_run_index(self.session_info.current_run)

    def get_region_index(self, l_reg, i_run):

        return next((i for i, x in enumerate(self.l_reg_xs[i_run]) if l_reg == x))