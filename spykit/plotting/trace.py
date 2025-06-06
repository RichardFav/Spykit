# module import
import os
import time
import colorsys
import functools
from copy import deepcopy

import numpy as np

# pyqtgraph modules
from pyqtgraph import (exporters, mkPen, mkColor, TextItem, ImageItem, PlotCurveItem, LinearRegionItem,
                       colormap, RectROI, PlotItem)
from pyqtgraph.Qt import QtGui

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.plotting.utils import PlotWidget, PlotPara
from spikeinterface.preprocessing import depth_order

# pyqt6 module import
from PyQt6.QtWidgets import (QWidget)
from PyQt6.QtCore import pyqtSignal, Qt, QObject, QPointF

# plot button fields
b_icon = ['datatip', 'save', 'close']
b_type = ['toggle', 'button', 'button']
tt_lbl = ['Show Channel Labels', 'Save Figure', 'Close TraceView']

# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceLabelMixin:
"""


class TraceLabelMixin:
    # parameters
    n_lbl_max = 50
    lbl_col = mkColor((128, 128, 128, 255))

    def setup_trace_labels(self):

        for i in range(self.n_lbl_max):
            # creates the label object
            label = TextItem(f'Test', color='#FFFFFF', anchor=(0, 0.5), border=None, fill=self.lbl_col)
            label.hide()

            # adds the label to the plot item and stores it
            self.plot_item.addItem(label)
            self.labels.append(label)

    def update_labels(self, force_hide=False):

        # determines the indices of the traces within the view
        if force_hide:
            n_trace = 0

        else:
            self.get_view_trace_indices()
            n_trace = len(self.i_trace)

        if (n_trace == 0) or (n_trace > self.n_lbl_max):
            # if no/too many traces, then hide the labels
            self.hide_labels()

        else:
            # show/hides the labels based on how many are being displayed
            if n_trace < self.n_show:
                self.hide_labels(range(self.n_show, self.n_lbl_max))

            # updates the locations of the labels so they overlap with the traces
            tr_id = self.plot_id[self.i_trace]
            # tr_id = self.session_info.get_selected_channels()[self.i_trace]
            for i_tr in range(n_trace):
                self.labels[i_tr].setPos(self.t_lim[0], self.y_trace[i_tr])
                self.labels[i_tr].setText('#ID: {0}'.format(tr_id[i_tr]))

            # shows all the required labels
            self.show_labels(range(n_trace))

            # update the trace count flag
            self.n_show = n_trace

    def get_view_trace_indices(self):

        # determines the location of the label spots
        y_lim = np.array(self.v_box[0, 0].viewRange()[1])
        y_pos = np.array([self.calc_vert_loc(x) for x in range(self.n_plt)])

        # returns the indices of the traces within the range
        self.i_trace = np.where([self.is_in_range(y_lim, x) for x in y_pos])[0]
        self.y_trace = y_pos[self.i_trace]

    def hide_labels(self, i_lbl=None):

        # hide all label if indices not provided
        if i_lbl is None:
            i_lbl = range(self.n_lbl_max)

        for i in i_lbl:
            self.labels[i].hide()

    def show_labels(self, i_lbl=None):

        # show all label if indices not provided
        if i_lbl is None:
            i_lbl = range(self.n_lbl_max)

        for i in i_lbl:
            self.labels[i].show()

    def calc_vert_loc(self, i_lvl):

        return (i_lvl * self.y_gap + 1.) - self.y_ofs

    @staticmethod
    def is_in_range(y_lim, y_pos):

        return int(np.prod(np.sign(y_lim - y_pos))) == -1


# ----------------------------------------------------------------------------------------------------------------------

class TracePlot(TraceLabelMixin, PlotWidget):
    # pyqtsignal functions
    hide_plot = pyqtSignal()
    reset_highlight = pyqtSignal(object)

    # parameters
    pw_y = 1.05
    pw_x = 1.05
    n_frm_plt = 10000
    y_gap = 2
    y_ofs = 0.2
    p_gap = 0.05
    n_lvl = 100
    n_col_img = 1000
    n_row_yscl = 100
    t_dur_max0 = 0.1
    n_plt_max = 64
    c_lim_hi = 200
    c_lim_lo = -200
    p_zoom0 = 0.2
    eps = 1e-6

    # list class fields
    lbl_tt_str = ['Show Channel Labels', 'Hide Channel Labels']

    # pen widgets
    l_pen = mkPen(width=3, color='y')
    l_pen_hover = mkPen(width=3, color='g')
    l_pen_trace = mkPen(color=cf.get_colour_value('g'), width=1)
    l_pen_inset = mkPen(color=cf.get_colour_value('r'), width=1)
    l_pen_high = mkPen(color=cf.get_colour_value('y'), width=1)

    def __init__(self, session_info):
        TraceLabelMixin.__init__(self)
        super(TracePlot, self).__init__('trace', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # experiment properties
        self.t_dur = s_props.get_value('t_dur')
        self.s_freq = s_props.get_value('s_freq')
        self.n_channels = s_props.get_value('n_channels')
        self.n_samples = s_props.get_value('n_samples')

        # plot item mouse event functions
        self.enter_fcn = None
        self.leave_fcn = None
        self.release_fcn = None
        self.double_click_fcn = None

        # trace fields
        self.x_tr = None
        self.y_tr = None
        self.c_tr = None
        self.gen_props = None
        self.trace_props = None
        self.inset_id = None
        self.inset_tr = []

        # axes limits
        self.y_lim = []
        self.y_lim_tr = self.y_ofs / 2
        self.x_window = np.min([self.t_dur, self.t_dur_max0])
        self.t_lim = np.array([0, self.x_window])
        self.pt_lim = np.array([0, 1])
        self.t_lim_prev = deepcopy(self.t_lim)

        # axes zoom class fields
        self.iz_lvl = -1
        self.zx_full = None
        self.zy_full = None
        self.pz_lvl = None
        self.p_zoom = [1 - self.p_zoom0, 1 + self.p_zoom0]

        # trace label class fields
        self.n_plt = 0
        self.n_show = 0
        self.t_start_ofs = 0
        self.labels = []
        self.l_pen_status = {}
        self.i_trace = None
        self.y_trace = None
        self.is_show = False

        # class widgets
        self.c_map = None
        self.l_reg_x = None
        self.l_reg_y = None
        self.i_sel_tr = None
        self.frame_img = None
        self.plot_id = None
        self.image_item = ImageItem()
        self.ximage_item = ImageItem()
        self.yimage_item = ImageItem()

        # creates the label object
        self.hm_label = TextItem(
            f'Test',
            color='#FFFFFF',
            anchor=(0, 0.0),
            border=None,
            fill=self.lbl_col)
        self.hm_roi = RectROI(
            [0, 0],
            [0, self.x_window],
            movable=False,
            rotatable=False,
            resizable=False,)

        # removes the ROI handles
        for h in self.hm_roi.getHandles():
            self.hm_roi.removeHandle(h)

        # trace items
        self.main_trace = PlotCurveItem(pen=self.l_pen_trace, skipFiniteCheck=False)
        self.inset_trace = PlotCurveItem(pen=self.l_pen_inset, skipFiniteCheck=False)
        self.highlight_trace = PlotCurveItem(pen=self.l_pen_high, skipFiniteCheck=False)

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

        for ps in cw.p_col_status:
            self.l_pen_status[ps] = mkPen(cw.p_col_status[ps], width=3)

        # ---------------------------------------------------------------------------
        # Trace Subplot Setup
        # ---------------------------------------------------------------------------

        # creates the image transform
        tr_map = QtGui.QTransform()
        tr_map.scale(self.x_window / self.n_col_img, 1.0)

        # sets the plot item properties
        self.plot_item.setMouseEnabled()
        self.plot_item.hideAxis('left')
        self.plot_item.hideButtons()
        # self.plot_item.setDownsampling(ds=1000)
        self.plot_item.setDownsampling(auto=True)
        self.plot_item.setClipToView(True)

        # sets the axis limits
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
        self.v_box[0, 0].setLimits(xMin=0, xMax=self.session_info.session_props.t_dur, yMin=0, yMax=self.y_lim_tr)
        self.v_box[0, 0].setMouseMode(self.v_box[0, 0].RectMode)
        self.v_box[0, 0].wheelEvent = self.mouse_wheel_move

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = functools.partial(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

        # adds the traces to the main plot
        self.h_plot[0, 0].addItem(self.main_trace)
        self.h_plot[0, 0].addItem(self.inset_trace)
        self.h_plot[0, 0].addItem(self.highlight_trace)
        self.h_plot[0, 0].addItem(self.hm_label)
        self.h_plot[0, 0].addItem(self.hm_roi)

        # hides the heatmap ROI objects
        self.hm_roi.hide()
        self.hm_label.hide()
        self.hm_roi.setZValue(9)
        self.hm_label.setZValue(10)

        # adds the image frame
        self.image_item.setTransform(tr_map)
        self.image_item.setImage(None)
        self.image_item.setLevels([self.c_lim_lo, self.c_lim_hi])
        self.image_item.hide()
        self.h_plot[0, 0].addItem(self.image_item)

        # retrieves the original event methods
        self.enter_fcn = self.h_plot[0, 0].enterEvent
        self.leave_fcn = self.h_plot[0, 0].leaveEvent
        self.release_fcn = self.h_plot[0, 0].mouseReleaseEvent
        self.double_click_fcn = self.h_plot[0, 0].mouseDoubleClickEvent

        # sets the signal trace plot event functions
        self.h_plot[0, 0].enterEvent = self.heatmap_enter
        self.h_plot[0, 0].leaveEvent = self.heatmap_leave
        self.h_plot[0, 0].mouseReleaseEvent = self.trace_mouse_release
        self.h_plot[0, 0].mouseDoubleClickEvent = self.trace_double_click
        self.h_plot[0, 0].scene().sigMouseMoved.connect(self.heatmap_mouse_move)

        # # sets up the trace label widgets
        # self.setup_trace_labels()

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
        self.ximage_item.setImage(self.setup_frame_image('x'))
        self.h_plot[1, 0].addItem(self.ximage_item)

        # creates the linear region
        self.l_reg_x = LinearRegionItem([0, self.x_window], bounds=[0, self.t_dur], span=[0, 1],
                                        pen=self.l_pen, hoverPen=self.l_pen_hover, swapMode='None')
        self.l_reg_x.sigRegionChanged.connect(self.xframe_region_move)
        self.l_reg_x.sigRegionChangeFinished.connect(self.xframe_region_finished)
        self.l_reg_x.mouseDoubleClickEvent = self.xframe_region_double_click
        self.l_reg_x.setZValue(10)
        self.h_plot[1, 0].addItem(self.l_reg_x)

        # disables the viewbox pan/zooming on the frame selection panel
        self.v_box[1, 0].setMouseEnabled(False, False)

        # ---------------------------------------------------------------------------
        # Y-Axis Range Finder Setup
        # ---------------------------------------------------------------------------

        # creates the image transform
        tr_y = QtGui.QTransform()
        tr_y.scale(1 / self.n_row_yscl, 1.0)

        # disables the viewbox pan/zooming on the frame selection panel
        self.v_box[0, 1].setMouseEnabled(False, False)

        # sets the plot item properties
        self.yframe_item.setMouseEnabled(x=False)
        self.yframe_item.hideAxis('left')
        self.yframe_item.getAxis('bottom').setGrid(False)
        self.yframe_item.getAxis('bottom').setTextPen('black')
        self.yframe_item.getAxis('bottom').setTickPen(mkPen(style=Qt.PenStyle.NoPen))
        self.yframe_item.hideButtons()
        self.yframe_item.setDefaultPadding(0.0)

        # adds the image frame
        self.yimage_item.setTransform(tr_y)
        self.yimage_item.setColorMap(cw.setup_colour_map(self.n_lvl))
        self.yimage_item.setImage(self.setup_frame_image('y'))
        self.h_plot[0, 1].addItem(self.yimage_item)

        # creates the linear region
        self.l_reg_y = LinearRegionItem([0, self.n_row_yscl], bounds=[0, self.n_row_yscl], span=[0, 1],
                                        pen=self.l_pen, hoverPen=self.l_pen_hover, orientation='horizontal',
                                        swapMode='block')
        self.l_reg_y.sigRegionChanged.connect(self.yframe_region_move)
        self.l_reg_y.sigRegionChangeFinished.connect(self.yframe_region_finished)
        self.l_reg_y.mouseDoubleClickEvent = self.yframe_region_double_click
        self.l_reg_y.setZValue(10)
        self.h_plot[0, 1].addItem(self.l_reg_y)

        # makes the bottom right plot invisible
        self.h_plot[1, 1].setVisible(False)

        # resets the zoom limits
        self.reset_zoom_limits()

    def setup_frame_image(self, axis):

        if axis == 'x':
            return np.linspace(0, 1, self.n_col_img).reshape(-1, 1)

        else:
            return np.linspace(0, 1, self.n_row_yscl).reshape(1, -1)

    # ---------------------------------------------------------------------------
    # Property Reset/Update Functions
    # ---------------------------------------------------------------------------

    def reset_trace_props(self, p_str):

        # field retrieval
        reset_type = 0
        t_lim_p = self.get_prop_xlimits()

        # parameter specific updates
        match p_str:
            case 't_span':
                # case is the window time-span

                # updates the signal limits
                t_span0, t_span1 = deepcopy(self.x_window), self.trace_props.get('t_span')
                dt_span = (t_span1 - t_span0) / 2.
                if self.t_lim[0] < dt_span:
                    # limits exceed the experiment start
                    self.t_lim = np.array([0, t_span1])

                elif self.t_lim[1] > (self.t_dur - dt_span):
                    # limits exceed the experiment finish
                    self.t_lim = np.array([(self.t_dur - t_span1), self.t_dur])

                else:
                    # otherwise, update the limits as per normal
                    self.t_lim += + dt_span * np.array([-1., 1.])

                # rounds the values to reasonable values
                self.t_lim = np.round(self.t_lim, cf.n_dp)

                # resets the trace properties
                reset_type = 0
                self.x_window = t_span1
                self.zx_full = deepcopy(self.t_lim)

                # updates the start/finish parameters
                t_lim_p = np.round(self.get_prop_xlimits(), cf.n_dp)
                self.trace_props.reset_para_field('t_start', t_lim_p[0])
                self.trace_props.reset_para_field('t_finish', t_lim_p[1])

            # case p_str if p_str in ['t_start', 't_finish']:
            #     # case is the start/finish time
            #     p_val0 = getattr(self, p_str)
            #     setattr(self, p_str, self.trace_props.get(p_str))

            case p_str if p_str in ['c_lim_lo', 'c_lim_hi']:
                # case is lower/upper colour limits
                setattr(self, p_str, self.trace_props.get(p_str))

        # resets the zoom/previous limit fields
        self.t_lim_prev = deepcopy(t_lim_p)

        # resets the plot view axis
        self.v_box[0, 0].setXRange(t_lim_p[0], t_lim_p[1], padding=0)
        self.reset_trace_view(0)

        if self.hm_roi is not None:
            self.hm_roi.setPos(t_lim_p)

        # resets the plot item visibility
        self.reset_colour_map()
        self.plot_button_clicked('datatip')
        self.reset_plot_items()

        # resets the linear region
        self.is_updating = True
        self.l_reg_x.setRegion((t_lim_p[0], t_lim_p[1]))
        self.is_updating = False

    def reset_gen_props(self):

        # calculates the change in start time
        t_start_ofs_new = self.gen_props.get('t_start')
        dt_start_ofs = t_start_ofs_new - self.t_start_ofs

        # class field updates
        self.t_dur = self.gen_props.get('t_dur')
        self.t_start_ofs = t_start_ofs_new

        # ensures the limits are correct
        self.t_lim -= dt_start_ofs
        if self.t_lim[0] < 0:
            self.t_lim = np.array([0, self.x_window])

        elif self.t_lim[1] > self.t_dur:
            self.t_lim = self.t_dur - np.asarray([self.x_window, 0])

        # resets the plot view axis
        t_lim_p = self.get_prop_xlimits()
        self.v_box[0, 0].setLimits(xMin=0, xMax=self.t_dur)
        self.v_box[1, 0].setLimits(xMin=0, xMax=self.t_dur)
        self.v_box[0, 0].setXRange(t_lim_p[0], t_lim_p[1], padding=0)
        self.reset_trace_view()
        self.update_trace_props()

        # resets the x-axis linear item transform
        tr_x = QtGui.QTransform()
        tr_x.scale(self.t_dur / self.n_col_img, 1.0)
        self.ximage_item.setTransform(tr_x)

        # resets the linear region
        self.is_updating = True
        self.l_reg_x.setRegion((t_lim_p[0], t_lim_p[1]))
        self.is_updating = False

    def update_trace_props(self):

        if self.trace_props is None:
            return

        # indicate that manual updating is taking place
        t_lim_p = self.get_prop_xlimits()
        self.trace_props.is_updating = True

        # resets the start time
        t_start = t_lim_p[0]
        self.trace_props.set_n('t_start', t_start)
        self.trace_props.edit_start.setText('{0:.4f}'.format(t_start))

        # resets the finish time
        t_finish = t_lim_p[1]
        self.trace_props.set_n('t_finish', t_finish)
        self.trace_props.edit_finish.setText('{0:.4f}'.format(t_finish))

        # print('Start/Finish = {0}/{1}'.format(t_start, t_finish))

        # resets the update flag
        self.trace_props.is_updating = False

    def reset_colour_map(self):

        c_map_name = self.trace_props.get('c_map')
        self.c_map = colormap.get(c_map_name, source="matplotlib", skipCache=False)
        self.image_item.setColorMap(self.c_map)

    # ---------------------------------------------------------------------------
    # Other Reset Functions
    # ---------------------------------------------------------------------------

    def reset_trace_view(self, reset_type=0):

        # retrieves the currently selected channels
        depth_sort = self.trace_props.get('sort_by') == 'Depth'
        i_channel = self.session_info.get_selected_channels()
        is_map = self.get_plot_mode(len(i_channel))
        self.n_plt = len(i_channel)
        self.reset_plot_items()

        # case is there are no plots (collapse y-axis range)
        self.y_lim_tr = (2 + (self.n_plt - 1) * self.y_gap) if self.n_plt else (self.y_ofs / 2.)

        # flag that manual updating is taking place
        self.is_updating = True

        # runs the axis reset type
        match reset_type:
            case 1:
                # case is resetting x-axis only
                self.reset_xaxis_limits()
                self.reset_zoom_limits()

            case 2:
                # case is resetting the y-axis only
                self.reset_yaxis_limits()

            case 3:
                # case is resetting the both axis

                # resets the time limit markers
                self.t_lim = np.array([0, self.x_window])
                self.zx_full = self.t_lim
                self.t_lim_prev = self.t_lim

                # resets the axes and zoom limits
                self.reset_xaxis_limits()
                self.reset_yaxis_limits()
                self.reset_zoom_limits()

        # resets the update flag
        self.is_updating = False

        if self.n_plt:
            # field retrieval
            use_diff = self.use_diff_signal()
            plot_id_orig = deepcopy(self.plot_id)
            s_freq = self.session_info.session_props.s_freq

            # sets the frame range indices
            t_lim_p = self.get_prop_xlimits()
            i_frm0 = int((self.t_lim[0] + self.t_start_ofs) * s_freq)
            i_frm1 = int((self.t_lim[1] + self.t_start_ofs) * s_freq)
            n_frm = (i_frm1 - i_frm0) - int(use_diff)
            if n_frm == 0:
                return

            # retrieves the plot indices
            channel_id, self.plot_id = self.session_info.get_channel_ids(i_channel, depth_sort)
            if not np.array_equal(self.plot_id, plot_id_orig):
                # if there is a change, then update the inset trace indices
                self.reset_inset_traces_indices()

            # sets up the y-data array
            y0 = self.session_info.get_traces(
                start_frame=i_frm0,
                end_frame=i_frm1,
                channel_ids=channel_id,
                return_scaled=self.trace_props.get('scale_signal'),
            )

            # calculates the signal difference (if using difference calc)
            if use_diff:
                y0 = np.diff(y0, axis=0)

            # sets up the heatmap/trace items
            if is_map:
                # removes the signal median value (help to better visualise raw signals)
                # y0 = y0 - np.median(y0)

                # resets the image item
                x_scl = self.x_window / n_frm
                self.image_item.setImage(np.clip(y0, self.c_lim_lo, self.c_lim_hi))
                self.image_item.setLevels([self.c_lim_lo, self.c_lim_hi])
                self.image_item.show()

                # creates the image transform
                tr_map = QtGui.QTransform()
                tr_map.scale(x_scl, self.y_lim_tr / self.n_plt)
                tr_map.translate(self.t_lim[0] / x_scl, 0)
                self.image_item.setTransform(tr_map)

            else:
                self.y_tr = np.empty((self.n_plt, n_frm))
                self.x_tr = np.empty((self.n_plt, n_frm))
                self.x_tr[:] = np.linspace(self.t_lim[0], self.t_lim[1], n_frm)

                for i in range(self.n_plt):
                    # determines the signal range values
                    y_min, y_max = np.min(y0[:, i]), np.max(y0[:, i])
                    if y_min == y_max:
                        y_scl = 0.5 * np.ones(n_frm, dtype=float)

                    else:
                        y_scl = (y0[:, i] - y_min) / (y_max - y_min)

                    # calculates the scaled traces
                    self.y_tr[i, :] = (i * self.y_gap + self.y_ofs) + (1 - self.y_ofs) * y_scl

                # sets up the connection array
                self.c_tr = np.ones((self.n_plt, n_frm), dtype=np.ubyte)
                self.c_tr[:, -1] = False

                # resets the curve data
                if self.inset_id is None:
                    self.inset_trace.clear()
                    self.update_trace(self.main_trace)

                else:
                    self.update_trace(self.main_trace, ~self.inset_tr)
                    self.update_trace(self.inset_trace, self.inset_tr)

        else:
            # resets the zoom limits
            self.reset_xaxis_limits()
            self.reset_yaxis_limits()
            self.reset_zoom_limits()

            # resets the plot id fields
            self.plot_id = None

            # removes the heatmap image (if mapping)
            if is_map:
                self.image_item.hide()

        # resets the maximum y-axis trace range
        self.v_box[0, 0].setLimits(yMax=self.y_lim_tr)

        # resets the other plot properties
        self.plot_item.setDownsampling(auto=True)
        self.plot_item.setClipToView(True)

        # # resets the y-axis range
        # if reset_type == 0:
        #     self.reset_yaxis_limits()

        # # updates the plot labels
        # if self.is_show and (not is_map):
        #     self.update_labels()

    def reset_frame_image(self):

        a = 1

    def reset_plot_items(self):

        is_map = self.get_plot_mode()

        self.image_item.show() if is_map else self.image_item.hide()
        self.main_trace.hide() if is_map else self.main_trace.show()
        self.inset_trace.hide() if is_map else self.inset_trace.show()

    def update_trace(self, h_trace, is_tr=None):

        # clears the trace
        h_trace.clear()

        if is_tr is None:
            h_trace.setData(
                self.x_tr.flatten(),
                self.y_tr.flatten(),
                connect=self.c_tr.flatten()
            )

        elif np.any(is_tr):
            h_trace.setData(
                self.x_tr[is_tr, :].flatten(),
                self.y_tr[is_tr, :].flatten(),
                connect=self.c_tr[is_tr, :].flatten(),
            )

    # ---------------------------------------------------------------------------
    # Mouse Movement Functions
    # ---------------------------------------------------------------------------

    def mouse_wheel_move(self, evnt):

        # field retrieval
        is_zoom_out = np.sign(evnt.delta()) > 0
        is_shift = evnt.modifiers() & cf.key_flag['Shift']

        # resets the
        if is_shift:
            # case is vertical zooming
            s_scale = [None, self.p_zoom[is_zoom_out]]

        else:
            # case is horizontal zooming
            s_scale = [self.p_zoom[is_zoom_out], None]

        # resets the axis limits
        self.v_box[0, 0].scaleBy(s_scale)
        self.is_updating = True

        # retrieves the new viewbox range
        x_range, y_range = self.v_box[0, 0].viewRange()
        if is_shift:
            # resets the y-axis linear regions
            y_range_scl = 100 * np.array(y_range) / self.y_lim_tr
            self.l_reg_y.setRegion(y_range_scl)

        else:
            # resets the x-axis linear regions
            reset_range = False

            dx_range = np.diff(x_range)
            if dx_range < cw.t_span_min:
                reset_range = True
                x_range = np.mean(x_range) + np.array([-1, 1]) * (cw.t_span_min / 2.)

            else:
                # ensures the lower limit is within the time range
                if x_range[0] < self.t_lim[0]:
                    reset_range, x_range[0] = True, self.t_lim[0]

                # ensures the upper limit is within the time range
                if x_range[1] > self.t_lim[1]:
                    reset_range, x_range[1] = True, self.t_lim[1]

            # resets the x-region (if required)
            self.t_lim_prev = x_range
            self.l_reg_x.setRegion(x_range)
            if reset_range:
                self.v_box[0, 0].setXRange(x_range[0], x_range[1], padding=0)

        # stores the current zoom limits
        self.store_zoom_limits()

        # updates the heatmap marker
        self.heatmap_mouse_move(evnt.pos())

        # continues running the event function
        evnt.accept()

        # resets the update flag
        self.is_updating = False

    def trace_double_click(self, evnt=None) -> None:

        # flag that updating is taking place
        self.is_updating = True

        # runs the original mouse event function
        if evnt is not None:
            # self.double_click_fcn(evnt)

            # resets the y-axis range
            self.restore_zoom_limits()
            # self.reset_yaxis_limits()

            # # determines if the time axis needs resetting
            # if (self.x_window - np.diff(self.t_lim)[0]) > self.eps:
            #     if (self.t_dur - self.t_lim[0]) < self.x_window:
            #         self.t_lim = [self.t_dur - self.x_window, self.t_dur]
            #     else:
            #         self.t_lim[1] = self.t_lim[0] = self.x_window
            #
            #     # resets the trace view
            #     self.reset_xaxis_limits()
            #     self.reset_trace_view(True)

            # updates the heatmap marker
            self.heatmap_mouse_move(evnt.position())

        # # updates the labels (if currently displaying)
        # if self.is_show:
        #     self.update_labels()

        # resets the update flag
        self.is_updating = False

    def trace_mouse_release(self, evnt) -> None:

        # runs the original mouse event function
        self.release_fcn(evnt)

        # flag that updating is taking place
        self.is_updating = True

        # retrieves the new axis limit
        if self.n_plt == 0:
            # uses the default x/y axis limits
            x_lim_zoom, self.y_lim = self.zx_full, self.zy_full

        else:
            # retrieves the x/y axis limits
            x_lim_zoom0, self.y_lim = self.v_box[0, 0].viewRange()

            # ensures the x-limits are feasible
            x_lim_zoom = [np.max([x_lim_zoom0[0], self.t_lim[0]]),
                          np.min([x_lim_zoom0[1], self.t_lim[1]])]
            dx_lim_zoom = np.diff(x_lim_zoom)[0]
            if dx_lim_zoom < cw.t_span_min:
                # if the time span is too small then expand it
                if (x_lim_zoom[0] < cw.t_span_min / 2.):
                    x_lim_zoom = np.array([0, cw.t_span_min], dtype=float)

                elif x_lim_zoom[1] > (self.t_dur - cw.t_span_min / 2.):
                    x_lim_zoom = self.t_dur - np.array([cw.t_span_min, 0], dtype=float)

                else:
                    x_lim_zoom = np.mean(x_lim_zoom) + np.array([-1, 1], dtype=float) * (cw.t_span_min / 2.)

            # updates the heatmap marker
            self.heatmap_mouse_move(QPointF(evnt.pos()))

        # resets the x-axis linear regions and plot axis limits
        self.l_reg_x.setRegion(x_lim_zoom)
        self.h_plot[0, 0].setXRange(x_lim_zoom[0], x_lim_zoom[1], padding=0)

        # resets the y-axis linear region
        self.l_reg_y.setRegion(100 * np.array(self.y_lim) / self.y_lim_tr)

        # resets the zoomed limits
        self.store_zoom_limits()

        # if self.hm_roi is not None:
        #     self.hm_roi.setPos([0, self.t_lim[0]])

        # # updates the labels (if currently displaying)
        # if self.is_show:
        #     self.update_labels()

        # resets the update flag
        self.is_updating = False

    def heatmap_mouse_move(self, p_pos):

        if (self.session_info.session is None) or (not self.is_show):
            return

        # determines the selected channels
        i_channel = self.session_info.get_selected_channels()
        n_channel = len(i_channel)

        # if not in heatmap mode, or no channels are selected, then exit
        # if (not self.get_plot_mode(n_channel)) or (n_channel == 0):
        if n_channel == 0:
            return

        # calculates the mapped coordinates
        m_pos = self.v_box[0, 0].mapSceneToView(p_pos)
        if ((m_pos.x() < self.t_lim[0]) or (m_pos.x() > self.t_lim[1]) or
            (m_pos.y() < 0) or (m_pos.y() > self.y_lim_tr)):
            return

        # updates the crosshair position
        y_mlt = self.n_plt / self.y_lim_tr
        i_row = np.min([int(np.floor(m_pos.y() * y_mlt)), len(i_channel) - 1])

        # updates the text label
        self.reset_heatmap_label(m_pos, self.plot_id[i_row])

        # resets the ROI position
        t_lim_p = self.get_prop_xlimits()
        self.hm_roi.setPos(t_lim_p[0], i_row / y_mlt)
        self.hm_roi.setSize(QPointF(self.x_window, self.y_lim_tr / self.n_plt))

    # ---------------------------------------------------------------------------
    # Axes Zoom Functions
    # ---------------------------------------------------------------------------

    def reset_zoom_limits(self):

        # resets the zoom label fields
        self.iz_lvl = -1
        self.pz_lvl = np.empty((2, 2), dtype=object)

        # stores the zoom limits
        self.zx_full, self.zy_full = self.t_lim, [0, self.y_lim_tr]
        self.update_trace_props()

    def store_zoom_limits(self):

        # retrieves the current viewbox range
        px_range, py_range = self.calc_prop_time_limits()
        # print(py_range)

        # increments the zoom level count (if not full zoom)
        match self.iz_lvl:
            case -1:
                # case is the first zoom level
                self.iz_lvl = 0

            case 0:
                # case is the second zoom level

                # calculates the change in view range
                if self.is_view_change(self.pz_lvl[0, :], px_range, py_range):
                    # if there is a change, then store the new limits
                    self.iz_lvl = 1

                else:
                    # otherwise, exit the function
                    return

            case 1:
                # case is the third zoom level

                # calculates the change in view range
                if self.is_view_change(self.pz_lvl[1, :], px_range, py_range):
                    # if there is a change, then store the new limits
                    self.pz_lvl[0, :] = deepcopy(self.pz_lvl[1, :])

                else:
                    # otherwise, exit the function
                    return

        # resets the main zoom range
        self.pz_lvl[self.iz_lvl, 0], self.pz_lvl[self.iz_lvl, 1] = px_range, py_range
        self.update_trace_props()

    def restore_zoom_limits(self):

        if self.iz_lvl < 0:
            return

        # field retrieval
        self.iz_lvl -= 1

        # flag that manual updating is taking place
        self.is_updating = True

        # resets the plot x-range/linear region
        px_range = self.get_prop_xlimits()
        self.h_plot[0, 0].setXRange(px_range[0], px_range[1], padding=0)
        self.l_reg_x.setRegion(px_range)
        self.t_lim_prev = px_range

        # resets the plot y-range/linear region
        py_range = self.get_prop_ylimits()
        self.h_plot[0, 0].setYRange(py_range[0], py_range[1], padding=0)
        self.l_reg_y.setRegion(py_range)

        # resets the manual update flag
        self.is_updating = False

        # resets the trace view
        self.update_trace_props()
        self.reset_trace_view()

        # resets the zoom level field
        self.pz_lvl[self.iz_lvl + 1, :] = None

    # ---------------------------------------------------------------------------
    # Signal Trace Plot Event Functions
    # ---------------------------------------------------------------------------

    def reset_heatmap_label(self, m_pos, i_channel):

        # updates the label text
        self.hm_label.setText(self.setup_label_text(i_channel))
        self.hm_label.update()

        # resets the probe view highlight
        self.reset_highlight.emit(i_channel)

        # calculates the label x/y-offsets
        dx_pos, dy_pos = self.convert_coords()

        # resets the y-label offset (if near the top)
        if (m_pos.y() + self.pw_y * dy_pos) > self.y_lim_tr:
            dy_pos = 0

        # resets the x-label offset (if near the right-side)
        x_lim_m = self.get_xlimit_prop()
        if (m_pos.x() - self.pw_x * dx_pos) < x_lim_m[0]:
            dx_pos = 0

        # resets the label position
        y_ofs = float(self.get_plot_mode())
        self.hm_label.setPos(m_pos + QPointF(-dx_pos, dy_pos-y_ofs))

    def convert_coords(self):

        lbl_bb = self.hm_label.boundingRect()
        bb_rect = self.v_box[0, 0].mapSceneToView(lbl_bb).boundingRect()
        return bb_rect.width(), bb_rect.height()

    def setup_label_text(self, i_channel):

        loc_ch = self.session_info.get_channel_location(i_channel)
        status_ch = self.session_info.get_channel_status(i_channel)

        self.hm_roi.setPen(self.l_pen_status[status_ch])

        return "Channel #{0}\nDepth = {1}\nStatus = {2}".format(i_channel, loc_ch[1], status_ch)

    def heatmap_leave(self, evnt):

        if self.session_info.session is None:
            return

        self.leave_fcn(evnt)

        self.hm_roi.hide()
        self.hm_label.hide()

        # resets the probe view highlight
        self.reset_highlight.emit(-1)

    def heatmap_enter(self, evnt):

        if self.session_info.session is None:
            return

        self.enter_fcn(evnt)

        # if not in heatmap mode, or no channels are selected, then exit
        n_channel = self.get_channel_count()
        # if (not self.get_plot_mode(n_channel)) or (n_channel == 0) or (not self.is_show):
        if (n_channel == 0) or (not self.is_show):
            return

        self.hm_roi.show()
        self.hm_label.show()

    # ---------------------------------------------------------------------------
    # Axis Limit Reset Functions
    # ---------------------------------------------------------------------------

    def reset_yaxis_limits(self):

        # resets the y-axis limits and region position
        self.h_plot[0, 0].setYRange(0, (1 + self.p_gap) * self.y_lim_tr, padding=0)
        self.l_reg_y.setRegion((0, 100))

        # resets the y-axis zoom-limits
        self.zy_full = [0, self.y_lim_tr]
        if self.iz_lvl >= 0:
            self.pz_lvl[self.iz_lvl, 0] = np.array([0, 1], dtype=float)

    def reset_xaxis_limits(self):

        # updates the time limits
        self.h_plot[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
        self.l_reg_x.setRegion(self.t_lim)

        # resets the y-axis zoom-limits
        if self.iz_lvl >= 0:
            self.pz_lvl[self.iz_lvl, 1] = np.array([0, 1], dtype=float)

        # updates the trace properties
        self.update_trace_props()

    # ---------------------------------------------------------------------------
    # Frame Region Event Functions
    # ---------------------------------------------------------------------------

    def xframe_region_move(self):

        if self.is_updating:
            return

        # retrieves the current region limits
        t_lim_p0 = self.get_prop_xlimits()
        t_lim_reg0 = np.array(self.l_reg_x.getRegion())
        dt_reg_p = t_lim_reg0 - t_lim_p0

        # determines if the region has resized
        i_side = np.argmax(np.abs(dt_reg_p))
        self.t_lim += dt_reg_p[i_side]

        if self.t_lim[0] < 0:
            # case is the left side is before the expt start
            self.t_lim -= self.t_lim[0]

        elif self.t_lim[1] > self.t_dur:
            # case is the right side is after the expt finish
            self.t_lim -= (self.t_lim[1] - self.t_dur)

        # resets the full x-limit field
        self.zx_full = self.t_lim
        t_lim_reg = self.get_prop_xlimits()

        # resets the x-linear region view size
        self.is_updating = True
        self.l_reg_x.setRegion((t_lim_reg[0], t_lim_reg[1]))
        self.v_box[0, 0].setXRange(t_lim_reg[0], t_lim_reg[1], padding=0)
        self.is_updating = False

        # updates the previous region limit field
        self.t_lim_prev = t_lim_reg

        # updates the view range
        self.update_trace_props()
        self.reset_trace_view()

        if self.hm_roi is not None:
            self.hm_roi.setPos([0, self.t_lim[0]])

    def xframe_region_finished(self):

        # stores the zoomed limits
        if not self.is_updating:
            self.zx_full = self.t_lim

            self.store_zoom_limits()
            self.update_trace_props()

    def xframe_region_double_click(self, evnt=None) -> None:

        # resets the y-linear region
        self.t_lim = self.zx_full
        self.l_reg_x.setRegion((self.t_lim[0], self.t_lim[1]))

        # resets the zoom limits
        self.iz_lvl = -1
        self.pz_lvl[:] = None

    def yframe_region_move(self):

        if self.is_updating:
            return

        y_lim_nw = np.array(self.l_reg_y.getRegion()) * (self.y_lim_tr / 100)
        y_pad_nw = self.p_gap * np.diff(y_lim_nw)[0]
        self.v_box[0, 0].setYRange(y_lim_nw[0], y_lim_nw[1] + y_pad_nw, padding=0)

    def yframe_region_finished(self):

        # stores the zoomed limits
        if not self.is_updating:
            self.store_zoom_limits()

        # # updates the labels (if currently displaying)
        # if self.is_show:
        #     self.update_labels()

    def yframe_region_double_click(self, evnt=None) -> None:

        # resets the y-linear region
        self.l_reg_y.setRegion(100 * np.array(self.zy_full) / self.y_lim_tr)

        # resets the zoom limits
        self.iz_lvl = -1
        self.pz_lvl[:] = None

    # ---------------------------------------------------------------------------
    # Plot Button Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'datatip':
                # case is the label toggle button
                is_map = self.get_plot_mode()
                obj_but = self.findChild(cw.QPushButton, name=b_str)

                # updates the tooltip string
                self.is_show = obj_but.isChecked()
                obj_but.setToolTip(self.lbl_tt_str[int(self.is_show)])

                # # updates the plot labels (depending on toggle value)
                # if self.is_show and (not is_map):
                #     self.update_labels()
                #
                # else:
                #     self.hide_labels()

            case 'save':
                # case is the figure save button

                # outputs the current trace to file
                f_path = cf.setup_image_file_name(cw.figure_dir, 'TraceTest.png')       # CHANGE THIS TO
                exp_obj = exporters.ImageExporter(self.h_plot[0, 0].getPlotItem())
                exp_obj.export(f_path)

            case 'close':
                # case is the close button
                self.hide_plot.emit()

    def reset_trace_highlight(self, is_on=False, i_contact=None):

        # removes any current trace highlight
        if self.i_sel_tr is not None:
            # resets the trace colours
            self.highlight_trace.setVisible(False)

            # resets the trace highlight flag
            self.i_sel_tr = None

        # highlights the required trace (if turning on highlight)
        if is_on and (not self.get_plot_mode()):
            # ensures the trace is visible
            if not self.highlight_trace.isVisible():
                self.highlight_trace.setVisible(True)

            # determines the index of the curve that corresponds to the contact ID
            i_sel_ch = self.session_info.get_selected_channels()
            if i_contact in i_sel_ch:
                i_sort_plt = np.argsort(np.argsort(self.session_info.channel_data.i_sort_rev[i_sel_ch]))
                self.i_sel_tr = i_sort_plt[i_sel_ch == i_contact][0]
                self.highlight_trace.setData(self.x_tr[0, :], self.y_tr[self.i_sel_tr, :])

    def reset_inset_highlight(self, inset_id=None):

        # if there is no change in inset ids, then exit
        if np.array_equal(self.inset_id, inset_id):
            return

        # resets the contact inset id
        self.inset_id = inset_id
        self.reset_inset_traces_indices()

        # updates the trace plot (if
        if self.n_plt:
            self.reset_trace_view()

    def reset_inset_traces_indices(self):

        if (self.plot_id is None) or (self.inset_id is None):
            self.inset_tr = None

        else:
            self.inset_tr = np.array([x in self.inset_id for x in self.plot_id])

    # ---------------------------------------------------------------------------
    # Parameter Object Setter Functions
    # ---------------------------------------------------------------------------

    def set_gen_props(self, gen_props_new):

        self.gen_props = gen_props_new
        gen_props_new.set_trace_view(self)

    def set_trace_props(self, trace_props_new):

        self.trace_props = trace_props_new
        self.reset_colour_map()
        trace_props_new.set_trace_view(self)

    # ---------------------------------------------------------------------------
    # Other Getter Functions
    # ---------------------------------------------------------------------------

    def get_plot_mode(self, n_channel=None):

        if n_channel is None:
            n_channel = self.get_channel_count()

        p_type = self.trace_props.get('plot_type')
        return (p_type == 'Heatmap') or ((p_type == 'Auto') and (n_channel >= self.n_plt_max))

    def use_diff_signal(self):

        return self.trace_props.get('sig_type') == 'Difference'

    def get_channel_count(self):

        return len(self.session_info.get_selected_channels())

    def get_run_index(self):

        return self.session_info.session.get_run_index(self.session_info.current_run)

    # ---------------------------------------------------------------------------
    # Other Plot View Functions
    # ---------------------------------------------------------------------------

    def clear_plot_view(self):

        # clears the selection flags
        self.reset_trace_view()

    def show_view(self):

        pass

    def hide_view(self):

        pass

    # ---------------------------------------------------------------------------
    # Plot Property Functions
    # ---------------------------------------------------------------------------

    def get_prop_xlimits(self):

        if self.iz_lvl < 0:
            if self.zx_full is None:
                return self.t_lim

            else:
                return self.zx_full

        else:
            return self.zx_full[0] + np.diff(self.zx_full) * self.pz_lvl[self.iz_lvl, 0]

    def get_prop_ylimits(self):

        if self.iz_lvl < 0:
            if self.zy_full is None:
                return [0, self.y_lim_tr]

            else:
                return self.zy_full

        else:
            return self.zy_full[0] + np.diff(self.zy_full) * self.pz_lvl[self.iz_lvl, 1]

    def get_xlimit_prop(self):

        if self.iz_lvl < 0:
            return np.array([0, 1], dtype=float)

        else:
            return self.pz_lvl[self.iz_lvl, 0]

    def calc_prop_time_limits(self, x_only=False):

        x_range, y_range = self.v_box[0, 0].viewRange()

        px_range = (np.array(x_range) - self.zx_full[0])/np.diff(self.zx_full)
        py_range = (np.array(y_range) - self.zy_full[0])/np.diff(self.zy_full)

        return np.maximum(0., px_range), np.maximum(0., py_range)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def det_moved_side(self, t_lim_reg):

        return np.abs(t_lim_reg - self.t_lim_prev[1]) > self.eps

    def det_moved_direction(self, t_lim_reg):

        return np.sign(t_lim_reg - self.t_lim_prev[1])

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def is_view_change(pXY, pX, pY):

        if pXY[0] is None:
            return False

        else:
            eps = 1e-10
            dpX, dpY = np.abs(pXY[0] - pX), np.abs(pXY[1] - pY)
            return not np.all([np.all(dpX < eps), np.all(dpY < eps)])
