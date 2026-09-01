# module import
import os
import time
import colorsys
import numpy as np
from copy import deepcopy
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.plotting.utils import PlotWidget

# pyqtgraph modules
from pyqtgraph import (ImageItem, PlotCurveItem, LinearRegionItem, ColorMap,
                       exporters, mkPen, mkBrush, arrayToQPath)
from pyqtgraph.Qt.QtWidgets import QGraphicsPathItem
from pyqtgraph.Qt import QtGui

# pyqt6 module import
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, Qt, QObject
from PyQt6.QtGui import QPainterPath

# plot button fields
b_icon = ['save', 'close']
b_type = ['button', 'button']
tt_lbl = ['Save Figure', 'Close View']

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

    def __init__(self, sp_main):
        super(TriggerPlot, self).__init__(sp_main, 'trigger', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_obj = sp_main.session_obj

        # linear region objects
        self.l_reg_x = None
        self.l_reg_xs = None
        self.n_reg_xs = None
        self.t_start_ofs = 0

        # trace fields
        self.y_tr = None
        self.n_run = None
        self.i_run_reg = None

        # plot item mouse event functions
        self.trace_release_fcn = None
        self.trace_dclick_fcn = None
        self.release_fcn = None

        # other class fields
        self.t_lim = None
        self.s_props = None
        self.l_reg_x = None
        self.i_sel_tr = None
        self.frame_img = None
        self.gen_props = None
        self.trig_props = None

        # class widgets
        self.ximage_item = ImageItem()
        self.trig_trace = QGraphicsPathItem()

        # sets up the plot regions
        self.setup_subplots(n_r=2, n_c=1)
        self.plot_item = self.h_plot[0, 0].getPlotItem()
        self.xframe_item = self.h_plot[1, 0].getPlotItem()

        # initialises the other class fields
        self.init_class_fields()
        self.reset_session_fields()

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

        # resets the mouse release event function
        self.release_fcn = self.h_plot[0, 0].mouseReleaseEvent
        self.h_plot[0, 0].mouseReleaseEvent = self.trace_mouse_release

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = pfcn(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

        # sets the axis limits
        self.v_box[0, 0].setMouseMode(self.v_box[0, 0].RectMode)

        # adds the traces to the main plot
        self.h_plot[0, 0].addItem(self.trig_trace)
        self.trig_trace.setPen(self.l_pen_trig)

        # sets the signal trace plot event functions
        self.trace_dclick_fcn = self.h_plot[0, 0].mousePressEvent
        self.h_plot[0, 0].mouseDoubleClickEvent = self.trace_double_click
        self.h_plot[1, 0].mouseDoubleClickEvent = self.trace_double_click

        # ---------------------------------------------------------------------------
        # X-Axis Range Finder Setup
        # ---------------------------------------------------------------------------

        # sets the plot item properties
        self.xframe_item.setMouseEnabled(y=False)
        self.xframe_item.hideAxis('left')
        self.xframe_item.hideAxis('bottom')
        self.xframe_item.hideButtons()
        self.xframe_item.setDefaultPadding(0.0)

        # adds the image frame
        self.ximage_item.setColorMap(cw.setup_colour_map(self.n_lvl))
        self.ximage_item.setImage(self.setup_frame_image())
        self.h_plot[1, 0].addItem(self.ximage_item)

        # creates the linear region
        self.l_reg_x = LinearRegionItem([0, 1], bounds=[0, 1], span=[0, 1],
                                        pen=self.l_pen, hoverPen=self.l_pen_hover)
        self.l_reg_x.sigRegionChangeFinished.connect(self.xframe_region_move)
        self.l_reg_x.setZValue(10)
        self.h_plot[1, 0].addItem(self.l_reg_x)

        # disables the viewbox pan/zooming on the frame selection panel
        self.v_box[1, 0].setMouseEnabled(False, False)

    def reset_session_fields(self):

        # field retrieval
        get_fcn = self.time_manager.get
        self.s_props = self.session_obj.session_props

        if get_fcn('use_full'):
            self.t_lim = np.array([0, get_fcn('t_run')])
        else:
            self.t_lim = np.array([get_fcn('t_start'), get_fcn('t_finish')])

        # experiment properties
        if self.time_manager.is_concat():
            self.n_run, self.i_run_reg = 1, 1
        else:
            self.i_run_reg = self.get_run_index()
            self.n_run = self.session_obj.session.get_run_count()

        # resets the trace values
        self.reset_trace_values()

        # linear region objects
        self.l_reg_xs = np.empty(self.n_run, dtype=object)
        self.n_reg_xs = np.zeros(self.n_run, dtype=int)

        # resets main trace x-axis limits
        self.v_box[0, 0].setLimits(xMin=0, xMax=self.t_lim[1], yMin=0.01, yMax=0.99)
        self.update_trigger_trace()

        # creates the image transform
        self.reset_ximage_scale()

        # linear region position update
        self.l_reg_x.setPos(0, self.t_lim[1])
        self.l_reg_x.setBounds(self.t_lim)

    def setup_frame_image(self):

        return np.linspace(0, 1, self.n_col_img).reshape(-1, 1)

    def update_trigger_trace(self, reset_run=False, reset_time_limits=False):

        # field retrieval
        get_fcn = self.time_manager.get
        is_concat = self.time_manager.is_concat()
        i_run = self.get_run_index(is_concat)

        # time range values
        if get_fcn('use_full'):
            t_start, t_finish = 0, get_fcn('t_run')
        else:
            t_start, t_finish = get_fcn('t_start'), get_fcn('t_finish')

        # resets the time limits
        if reset_time_limits:
            self.t_lim = [t_start, t_finish]

        # trigger trace values
        y_tr_run = self.y_tr[i_run]

        if reset_run:
            # hides the current linear regions
            self.hide_regions(self.i_run_reg)
            self.show_regions(i_run)

            # resets the run index
            self.i_run_reg = i_run

        # sets up the scaled trigger trace
        s_freq = self.get_sample_freq()
        trig_path = arrayToQPath(y_tr_run[:, 0] / s_freq, y_tr_run[:, 1], connect='all')
        self.trig_trace.setPath(trig_path)

        # updates the other axes properties
        self.is_updating = True
        self.h_plot[0, 0].setXRange(t_start, t_finish)
        self.v_box[0, 0].setLimits(xMin=t_start, xMax=t_finish)
        self.l_reg_x.setBounds(self.t_lim)
        self.l_reg_x.setRegion(self.t_lim)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Suppression Region Functions
    # ---------------------------------------------------------------------------

    def add_region(self, nw_row, i_run=None):

        if i_run is None:
            i_run = self.get_run_index()

        # creates the linear region
        l_reg = LinearRegionItem([nw_row[1], nw_row[2]], bounds=self.t_lim, span=[0, 1],
                                 pen=self.l_pen, hoverPen=self.l_pen_hover, brush=self.l_brush)
        l_reg.sigRegionChanged.connect(pfcn(self.xtrig_region_move, l_reg))
        l_reg.sigRegionChangeFinished.connect(pfcn(self.xtrig_region_moved, l_reg))
        l_reg.setZValue(10)

        # stores the linear region object
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
        self.xtrig_region_moved(l_reg)

    def delete_region(self, i_reg, i_run=None):

        if i_run is None:
            i_run = self.get_run_index()

        # removes the linear item from the list/plot item
        l_reg_del = self.l_reg_xs[i_run].pop(i_reg)
        self.h_plot[0, 0].removeItem(l_reg_del)

        # decrements the linear region count
        self.n_reg_xs[i_run] -= 1

    def delete_all_regions(self):

        for i_run, n_reg in enumerate(self.n_reg_xs):
            for i_reg in range(n_reg):
                self.delete_region(0, i_run)

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

    def reset_regions(self, p_fld):

        # field retrieval
        i_run = self.get_run_index()
        reset_limits, reset_row_count = False, False

        # exit if there are no regions for the current run
        if self.n_reg_xs[i_run] == 0:
            return

        # region upper bound limit check
        for i_reg in reversed(range(self.n_reg_xs[i_run])):
            t_arr = self.trig_props.get_table_row(i_reg)
            if t_arr[1] > self.t_lim[1]:
                # case is the region is no longer feasible
                self.trig_props.delete_region(i_run, i_reg, True)
                reset_limits = True

            elif t_arr[2] > self.t_lim[1]:
                # case is the upper bound is no longer feasible
                self.reset_region_pos(self.l_reg_xs[i_run][i_reg], t_arr[1], self.t_lim[1])
                self.trig_props.set_table_cell(i_reg, 2, self.t_lim[1])
                reset_limits = True
                break

            else:
                # otherwise, current region is feasible
                break

        # region lower bound limit check
        for i_reg in range(self.n_reg_xs[i_run]):
            t_arr = self.trig_props.get_table_row(0)
            if self.t_lim[0] > t_arr[2]:
                # case is the region is no longer feasible
                self.trig_props.delete_region(i_run, 0, True)
                reset_limits, reset_row_count = True, True

            elif self.t_lim[0] > t_arr[1]:
                # case is the lower bound is no longer feasible
                self.reset_region_pos(self.l_reg_xs[i_run][0], self.t_lim[0], t_arr[2])
                self.trig_props.set_table_cell(0, 1, self.t_lim[0])
                reset_limits = True
                break

            else:
                # otherwise, current region is feasible
                break

        # resets the table row count
        if reset_row_count:
            for i_row in range(self.n_reg_xs[i_run]):
                self.trig_props.set_table_cell(i_row, 0, i_row + 1)

        # updates the region limits (if a change was made)
        if reset_limits:
            self.update_region_limits(i_run)

    def hide_regions(self, i_run=None):

        if i_run is None:
            i_run = self.get_run_index()

        if self.n_reg_xs[i_run]:
            [x.hide() for x in self.l_reg_xs[i_run]]

    def show_regions(self, i_run=None):

        if i_run is None:
            i_run = self.get_run_index()

        if self.n_reg_xs[i_run]:
            [x.show() for x in self.l_reg_xs[i_run]]

    # ---------------------------------------------------------------------------
    # Frame Region Event Functions
    # ---------------------------------------------------------------------------

    def xframe_region_move(self):

        if self.is_updating:
            return

        self.t_lim = np.array(self.l_reg_x.getRegion())
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)

    def xtrig_region_move(self, l_reg):

        if self.is_updating:
            return

        # field retrieval
        i_run = self.get_run_index()
        x_reg = list(l_reg.getRegion())
        i_reg = next((i for i, x in enumerate(self.l_reg_xs[i_run]) if l_reg == x))

        # updates the trigger table cells
        self.trig_props.set_table_cell(i_reg, 1, np.round(x_reg[0], cf.n_dp_trig))
        self.trig_props.set_table_cell(i_reg, 2, np.round(x_reg[1], cf.n_dp_trig))

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
            l_reg0.setBounds([self.t_lim[0], x_reg1[0]])

        else:
            # otherwise, reset regions based on region preceeding previous
            x_reg0_pre = self.l_reg_xs[i_run][i_reg0 - 1].getRegion()
            l_reg0.setBounds([x_reg0_pre[1], x_reg1[0]])

        # resets the region limits
        if (i_reg1 + 1) == self.n_reg_xs[i_run]:
            # next region is the last region
            l_reg1.setBounds([x_reg0[1], self.t_lim[1]])

        else:
            # otherwise, reset regions based on region proceeding next
            x_reg1_post = self.l_reg_xs[i_run][i_reg1 + 1].getRegion()
            l_reg1.setBounds([x_reg0[1], x_reg1_post[0]])

    def reset_ximage_scale(self):

        tr_x = QtGui.QTransform()
        tr_x.translate(self.t_lim[0], 0.0)
        tr_x.scale(np.diff(self.t_lim) / self.n_col_img, 1.0)
        self.ximage_item.setTransform(tr_x)

    # ---------------------------------------------------------------------------
    # Plot Button Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'save':
                # case is the figure save button

                # prompts the user for the file name
                f_path = cw.get_image_file_name(cw.get_def_dir("figure"), 'Trigger')
                if f_path is not None:
                    # saves the image to file
                    exp_obj = exporters.ImageExporter(self.h_plot[0, 0].getPlotItem())
                    exp_obj.export(f_path)

            case 'close':
                # case is the close button
                self.hide_plot.emit()

    # ---------------------------------------------------------------------------
    # Signal Trace Plot Event Functions
    # ---------------------------------------------------------------------------

    def trace_mouse_release(self, evnt) -> None:

        # runs the original mouse event function
        self.release_fcn(evnt)

        # flag that updating is taking place
        self.is_updating = True

        # retrieves the x/y axis limits
        self.t_lim = self.v_box[0, 0].viewRange()[0]

        # resets the x-axis linear regions and plot axis limits
        self.l_reg_x.setRegion(self.t_lim)
        self.h_plot[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)

        # resets the update flag
        self.is_updating = False

    def trace_double_click(self, evnt=None) -> None:

        # flag that updating is taking place
        self.is_updating = True

        # runs the original mouse event function
        if evnt is not None:
            # runs the mouse event
            PlotWidget.mousePressEvent(self, evnt)

            # updates the time limits
            get_fcn = self.time_manager.get
            self.t_lim = np.array([get_fcn('t_start'), get_fcn('t_finish')])
            self.h_plot[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
            self.l_reg_x.setRegion(self.t_lim)

        # resets the update flag
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Property Object Functions
    # ---------------------------------------------------------------------------

    def update_prop_fields(self, p_fld):

        # class field updates
        i_run = self.get_run_index()
        get_fcn = self.time_manager.get

        # time range values
        if get_fcn('use_full'):
            self.t_lim = [0, get_fcn('t_run')]
        else:
            self.t_lim = [get_fcn('t_start'), get_fcn('t_finish')]

        # resets the trigger regions (if post-processing completed)
        if (p_fld == 'pp_change'):
            # deletes all regions
            self.delete_all_regions()

            # resets the region indices
            self.reset_region_indices()
            self.reset_sync_channels()

            # resets the suppression region objects
            self.trig_props.p_props.reset_table_array(self.n_run)
            self.trig_props.reset_table_data()
            self.trig_props.readd_all_regions(True)

            # re-shows the regions
            self.show_regions(0)

        # resets the image scale/suppression regions
        self.reset_ximage_scale()
        self.reset_regions(p_fld)

        # resets the plot view properties
        self.v_box[0, 0].setLimits(yMin=-0.1, yMax=100.1)
        self.v_box[0, 0].setLimits(xMin=self.t_lim[0], xMax=self.t_lim[1])
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)

        # updates the time linear region properties
        self.v_box[1, 0].setLimits(xMin=self.t_lim[0], xMax=self.t_lim[1])

        # updates the trigger trace
        self.update_trigger_trace(p_fld in ['i_run', 'concat_run'], False)
        self.update_region_limits(i_run)

        # resets the linear region
        self.is_updating = True
        self.l_reg_x.setRegion((self.t_lim[0], self.t_lim[1]))
        self.is_updating = False

    def set_trig_props(self, trig_props_new):

        self.trig_props = trig_props_new
        trig_props_new.set_trig_view(self)

    # ---------------------------------------------------------------------------
    # Trigger Channel Functions
    # ---------------------------------------------------------------------------

    def reset_sync_channels(self):

        # field retrieval
        sync_ch_raw = self.get_raw_sync_channels()

        if self.time_manager.has_pp_fcn():
            # combines the trigger channel (if pre-processing)
            sync_ch_new = self.combine_sync_channels(sync_ch_raw)
            self.session_obj.reset_sync_channel(sync_ch_new)

        else:
            # reverts back to the raw trigger channel (if clearing pre-processing)
            self.session_obj.reset_sync_channel(sync_ch_raw)

        # resets the trigger trace values
        self.reset_trace_values()

    def combine_sync_channels(self, sync_ch):

        # field retrieval
        tm = self.time_manager
        t_s = tm.get('t_start', True)[0]
        t_f = tm.get('t_finish', True)[0]
        u_f = tm.get('use_full', True)[0]

        # retrieves the sync channel slices
        for i_run in range(len(sync_ch)):
            if not u_f[i_run]:
                sync_ch[i_run] = self.get_sync_channel_slice(sync_ch[i_run], t_s[i_run], t_f[i_run])

        if tm.concat_fcn():
            # case is experimental runs are concatenated
            return np.array([np.hstack(sync_ch)])

        else:
            # case is experimental runs are separated
            return sync_ch

    def get_sync_channel_slice(self, sync_ch, t_s, t_f):

        # start/end frame indices
        s_freq = self.session_obj.session_props.get_value('s_freq')
        ind_s, ind_f = int(t_s * s_freq), int(np.min([t_f * s_freq, len(sync_ch) - 1]))

        return sync_ch[ind_s:ind_f]

    def get_raw_sync_channels(self):

        return deepcopy(self.session_obj.session.sync_ch_raw)

    # ---------------------------------------------------------------------------
    # Trigger Channel Region Indices Functions
    # ---------------------------------------------------------------------------

    def reset_region_indices(self):

        if self.time_manager.has_pp_fcn():
            # combines the region indices (if pre-processing)
            reg_index_raw = deepcopy(self.trig_props.p_props.region_index)
            self.trig_props.p_props.region_index_raw = deepcopy(reg_index_raw)
            reg_index_new = self.combine_region_indices(reg_index_raw)

        else:
            # reverts back to the raw region indices (if clearing pre-processing)
            reg_index_new = deepcopy(self.trig_props.p_props.region_index_raw)

        # resets the region indices
        self.trig_props.p_props.region_index = deepcopy(reg_index_new)

    def combine_region_indices(self, reg_index):

        # field retrieval
        tm = self.time_manager
        t_dur = tm.get('t_dur', True)[0]
        t_start = tm.get('t_start', True)[0]

        # case is session is preprocessed
        if tm.concat_fcn():
            # case is runs are concatenated

            # combines the region indices over all runs
            ii = [(len(ri) > 0) for ri in reg_index]
            t_ofs = np.insert(np.cumsum(t_dur)[:-1], 0, 0)
            t_index = np.vstack([(ri[:, 1:] + to - ts) for ri, ts, to in zip(reg_index[ii], t_start[ii], t_ofs[ii])])

            # sets up the full region index array
            n_row = t_index.shape[0]
            reg_index = [np.hstack([np.array(range(n_row)).reshape(n_row, -1) + 1, t_index])]

        else:
            # case is runs are seperated

            # removes the start time from all non-empty region indices
            for ri, ts in zip(reg_index, t_start):
                if len(ri):
                    ri[:, 1:] -= ts

        return reg_index

    # ---------------------------------------------------------------------------
    # Other Plot View Functions
    # ---------------------------------------------------------------------------

    def clear_plot_view(self):

        self.trig_trace.setPath(QPainterPath())
        self.trig_trace.update()

    def show_view(self):

        pass

    def hide_view(self):

        pass

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def get_sample_freq(self):

        if self.s_props is None:
            return self.session_obj.session_props.get_value('s_freq')

        else:
            return self.s_props.get_value('s_freq')

    def get_run_index(self, is_concat=None):

        if is_concat is None:
            is_concat = self.time_manager.is_concat()

        if is_concat:
            return 0
        else:
            return self.session_obj.session.get_run_index(self.session_obj.current_run)

    def get_region_index(self, l_reg, i_run):

        return next((i for i, x in enumerate(self.l_reg_xs[i_run]) if l_reg == x))

    def reset_trace_values(self):

        # field retrieval
        is_concat = self.time_manager.is_concat()
        sync_ch = self.session_obj.session.sync_ch

        # memory allocation
        n_tr, n_run = [len(sc) for sc in sync_ch], len(sync_ch)
        self.y_tr = np.empty(n_run, dtype=object)

        for i_run in range(n_run):
            # sets the start end values
            y_tr_0 = np.array([0, sync_ch[i_run][0]])
            y_tr_1 = np.array([(n_tr[i_run]-1), sync_ch[i_run][-1]])

            # determines the points where the trigger channel changes
            i_ch = np.where(np.diff(sync_ch[i_run]) != 0)[0]
            if len(i_ch):
                # case is there is a trigger for this run
                x_tr_m = np.vstack((i_ch, i_ch)).transpose().flatten()
                y_tr_m = np.vstack((sync_ch[i_run][i_ch], sync_ch[i_run][i_ch+1])).transpose().flatten()
                xy_tr_m = np.vstack((x_tr_m, y_tr_m)).transpose()
                self.y_tr[i_run] = np.vstack((y_tr_0, xy_tr_m, y_tr_1))

            else:
                # case is there is no trigger channel signal for this run
                self.y_tr[i_run] = np.vstack((y_tr_0, y_tr_1))

        # # sets the concatenated run change indices (if multi-run)
        # if is_concat:
        #     # initialisations
        #     i_ofs = 0.
        #     A = np.empty(n_run, dtype=object)
        #
        #     # combines the trigger channel change indices over all runs
        #     for i_run in range(n_run):
        #         # updates the change indices
        #         A[i_run] = deepcopy(self.y_tr[i_run]) + np.array([i_ofs, 0.])
        #         i_ofs += n_tr[i_run]
        #
        #     # combines the sub arrays over all runs
        #     A = np.vstack(A)
        #
        #     # removes any repeated value rows
        #     is_keep = np.hstack((np.ones(1, dtype=bool), np.diff(A[:, 1]) != 0))
        #     is_keep[-1] = True
        #     self.y_tr[1] = [A[is_keep, :]]

    def reset_region_pos(self, l_reg, t_min, t_max):

        self.is_updating = True
        l_reg.setRegion([t_min, t_max])
        self.is_updating = False

    def update_region_limits(self, i_run):

        if self.n_reg_xs[i_run] == 1:
            # case is there is one region
            self.xtrig_region_moved(self.l_reg_xs[i_run][0])

        elif self.n_reg_xs[i_run] > 1:
            # case is there are multiple regions
            self.xtrig_region_moved(self.l_reg_xs[i_run][0])
            self.xtrig_region_moved(self.l_reg_xs[i_run][-1])