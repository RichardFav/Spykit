# module import
import os
import time
import colorsys
import functools
import numpy as np

# pyqtgraph modules
from pyqtgraph import exporters, mkPen, mkColor, TextItem, ImageItem, PlotCurveItem, LinearRegionItem, ColorMap
from pyqtgraph.Qt import QtGui

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.plotting.utils import PlotWidget, PlotPara

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

    def update_labels(self):

        # determines the indices of the traces within the view
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
            tr_id = self.session_info.get_selected_channels()[self.i_trace]
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

"""
    TracePlot:
"""


class TracePlot(TraceLabelMixin, PlotWidget):
    # pyqtsignal functions
    hide_plot = pyqtSignal()

    # parameters
    n_frm_plt = 10000
    y_gap = 2
    y_ofs = 0.2
    p_gap = 0.05
    n_lvl = 100
    n_col_img = 1000
    n_row_yscl = 100
    t_dur_max0 = 0.1
    n_plt_max = 64

    # pen widgets
    l_pen = mkPen(width=3, color='y')
    l_pen_hover = mkPen(width=3, color='g')
    l_pen_trace = mkPen(color=cf.get_colour_value('g'), width=1)
    l_pen_high = mkPen(color=cf.get_colour_value('y'), width=1)
    l_pen_bad = mkPen(color=cf.get_colour_value('r'), width=1)

    lbl_tt_str = ['Hide Channel Labels', 'Show Channel Labels']

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
        self.trace_release_fcn = None
        self.trace_dclick_fcn = None

        # trace fields
        self.x_tr = None
        self.y_tr = None
        self.gen_props = None
        self.trace_props = None

        # axes limits
        self.y_lim = []
        self.x_window = np.min([self.t_dur, self.t_dur_max0])
        self.y_lim_tr = self.y_ofs / 2
        self.t_lim = np.array([0, self.x_window])

        # trace label class fields
        self.n_plt = 0
        self.n_show = 0
        self.labels = []
        self.i_trace = None
        self.y_trace = None
        self.is_show = False

        # class widgets
        self.l_reg_x = None
        self.l_reg_y = None
        self.i_sel_tr = None
        self.frame_img = None
        self.ximage_item = ImageItem()
        self.yimage_item = ImageItem()

        # trace items
        self.main_trace = PlotCurveItem(pen=self.l_pen_trace, skipFiniteCheck=False)
        self.highlight_trace = PlotCurveItem(pen=self.l_pen_high, skipFiniteCheck=False)
        self.bad_trace = PlotCurveItem(pen=self.l_pen_bad, skipFiniteCheck=False)

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
        # self.plot_item.setDownsampling(ds=1000)
        self.plot_item.setDownsampling(auto=True)
        self.plot_item.setClipToView(True)

        # sets the axis limits
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
        self.v_box[0, 0].setLimits(xMin=0, xMax=self.session_info.session_props.t_dur, yMin=0, yMax=self.y_lim_tr)
        self.v_box[0, 0].setMouseMode(self.v_box[0, 0].RectMode)

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = functools.partial(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

        # adds the traces to the main plot
        self.h_plot[0, 0].addItem(self.main_trace)
        self.h_plot[0, 0].addItem(self.highlight_trace)
        self.h_plot[0, 0].addItem(self.bad_trace)

        # sets the signal trace plot event functions
        self.trace_dclick_fcn = self.h_plot[0, 0].mousePressEvent
        self.trace_release_fcn = self.h_plot[0, 0].mouseReleaseEvent
        self.h_plot[0, 0].mouseReleaseEvent = self.trace_mouse_release
        self.h_plot[0, 0].mouseDoubleClickEvent = self.trace_double_click

        # sets up the trace label widgets
        self.setup_trace_labels()

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
                                        pen=self.l_pen, hoverPen=self.l_pen_hover)
        self.l_reg_x.sigRegionChanged.connect(self.xframe_region_move)
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
                                        pen=self.l_pen, hoverPen=self.l_pen_hover, orientation='horizontal')
        self.l_reg_y.sigRegionChangeFinished.connect(self.yframe_region_move)
        self.l_reg_y.setZValue(10)
        self.h_plot[0, 1].addItem(self.l_reg_y)

        # makes the bottom right plot invisible
        self.h_plot[1, 1].setVisible(False)

    def setup_frame_image(self, axis):

        if axis == 'x':
            return np.linspace(0, 1, self.n_col_img).reshape(-1, 1)

        else:
            return np.linspace(0, 1, self.n_row_yscl).reshape(1, -1)

    # ---------------------------------------------------------------------------
    # Plot Update/Reset Functions
    # ---------------------------------------------------------------------------

    def update_trace_props(self):

        # resets the start time
        t_start = self.t_lim[0]
        self.trace_props.set_n('t_start', t_start)
        self.trace_props.edit_start.setText('{0:.4f}'.format(t_start))

        # resets the finish time
        t_finish = self.t_lim[1]
        self.trace_props.set_n('t_finish', t_finish)
        self.trace_props.edit_finish.setText('{0:.4f}'.format(t_finish))

    def reset_trace_view(self, reset_limits=True):

        # retrieves the currently selected channels
        i_channel = self.session_info.get_selected_channels()
        self.n_plt = len(i_channel)

        if self.n_plt:
            # sets the frame range indices
            s_freq = self.session_info.session_props.s_freq
            i_frm0 = int(self.t_lim[0] * s_freq)
            i_frm1 = int(self.t_lim[1] * s_freq)
            n_frm = i_frm1 - i_frm0

            # sets up the x-data array
            self.y_tr = np.empty((self.n_plt, n_frm))
            self.x_tr = np.empty((self.n_plt, n_frm))
            self.x_tr[:] = np.linspace(self.t_lim[0], self.t_lim[1], n_frm)

            # sets up the y-data array
            ch_ids = self.session_info.get_channel_ids(i_channel)
            y0 = self.session_info.get_traces(start_frame=i_frm0, end_frame=i_frm1, channel_ids=ch_ids)

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
            c = np.ones((self.n_plt, n_frm), dtype=np.ubyte)
            c[:, -1] = False

            # resets the curve data
            self.main_trace.clear()
            self.main_trace.setData(self.x_tr.flatten(), self.y_tr.flatten(), connect=c.flatten())

            # sets the maximum y-axis trace range
            self.y_lim_tr = 1 + (self.n_plt - 1) * self.y_gap

        else:
            # case is there are no plots (collapse y-axis range)
            self.y_lim_tr = self.y_ofs / 2.

        # resets the maximum y-axis trace range
        self.v_box[0, 0].setLimits(yMax=self.y_lim_tr)

        # resets the other plot properties
        self.plot_item.setDownsampling(auto=True)
        self.plot_item.setClipToView(True)

        if reset_limits:
            # resets the y-axis range
            self.reset_yaxis_limits()

        # updates the plot labels
        if self.is_show:
            self.update_labels()

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
            self.trace_dclick_fcn(evnt)

            # resets the y-axis range
            self.reset_yaxis_limits()

            # determines if the time axis needs resetting
            if np.diff(self.t_lim)[0] < self.x_window:
                if (self.t_dur - self.t_lim[0]) < self.x_window:
                    self.t_lim = [self.t_dur - self.x_window, self.t_dur]
                else:
                    self.t_lim[1] = self.t_lim[0] = self.x_window

                # resets the trace view
                self.reset_xaxis_limits()
                self.reset_trace_view(True)

        # updates the labels (if currently displaying)
        if self.is_show:
            self.update_labels()

        # resets the update flag
        self.is_updating = False

    def trace_mouse_release(self, evnt) -> None:

        # flag that updating is taking place
        self.is_updating = True

        # runs the original mouse event function
        self.trace_release_fcn(evnt)

        # retrieves the new axis limit
        self.y_lim = self.v_box[0, 0].viewRange()[1]
        self.t_lim = self.v_box[0, 0].viewRange()[0]

        # resets the x/y-axis linear regions
        self.l_reg_x.setRegion(self.t_lim)
        self.l_reg_y.setRegion(100 * np.array(self.y_lim) / self.y_lim_tr)

        # updates the labels (if currently displaying)
        if self.is_show:
            self.update_labels()

        # resets the update flag
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Axis Limit Reset Functions
    # ---------------------------------------------------------------------------

    def reset_yaxis_limits(self):

        self.h_plot[0, 0].setYRange(0, (1 + self.p_gap) * self.y_lim_tr, padding=0)
        self.l_reg_y.setRegion((0, 100))

    def reset_xaxis_limits(self):

        # updates the time limits
        self.h_plot[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
        self.l_reg_x.setRegion(self.t_lim)

    # ---------------------------------------------------------------------------
    # Frame Region Event Functions
    # ---------------------------------------------------------------------------

    def xframe_region_move(self):

        if self.is_updating:
            return

        # retrieves the current region limits
        t_lim_nw = np.array(self.l_reg_x.getRegion())
        t_lim_half = np.mean(t_lim_nw)

        # case is the window size need to be fixed
        if t_lim_half < self.x_window / 2:
            t_lim_nw = [0, self.x_window]

        elif t_lim_half > (self.t_dur - self.x_window / 2):
            t_lim_nw = [self.t_dur - self.x_window, self.t_dur]

        else:
            t_lim_nw = t_lim_half + (self.x_window / 2) * np.array([-1, 1])

        # resets the x-linear region view size
        self.is_updating = True
        self.l_reg_x.setRegion((t_lim_nw[0], t_lim_nw[1]))
        self.is_updating = False

        # updates the view range
        self.t_lim = t_lim_nw
        self.v_box[0, 0].setXRange(self.t_lim[0], self.t_lim[1], padding=0)
        self.update_trace_props()
        self.reset_trace_view()

        # updates the labels (if currently displaying)
        if self.is_show:
            self.update_labels()

    def yframe_region_move(self):

        if self.is_updating:
            return

        y_lim_nw = np.array(self.l_reg_y.getRegion()) * (self.y_lim_tr / 100)
        y_pad_nw = self.p_gap * np.diff(y_lim_nw)[0]
        self.v_box[0, 0].setYRange(y_lim_nw[0], y_lim_nw[1] + y_pad_nw, padding=0)

        # updates the labels (if currently displaying)
        if self.is_show:
            self.update_labels()

    # ---------------------------------------------------------------------------
    # Plot Button Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'datatip':
                # case is the label toggle button
                obj_but = self.findChild(cw.QPushButton, name=b_str)

                # updates the tooltip string
                self.is_show = obj_but.isChecked()
                obj_but.setToolTip(self.lbl_tt_str[int(self.is_show)])

                # updates the plot labels (depending on toggle value)
                if self.is_show:
                    self.update_labels()
                else:
                    self.hide_labels()

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
        if is_on:
            # ensures the trace is visible
            if not self.highlight_trace.isVisible():
                self.highlight_trace.setVisible(True)

            # determines the index of the curve that corresponds to the contact ID
            i_sel_ch = self.session_info.get_selected_channels()
            self.i_sel_tr = np.where(i_sel_ch == i_contact)[0][0]
            self.highlight_trace.setData(self.x_tr[0, :], self.y_tr[self.i_sel_tr, :])

    # ---------------------------------------------------------------------------
    # Parameter Object Setter Functions
    # ---------------------------------------------------------------------------

    def set_gen_props(self, gen_props_new):

        self.gen_props = gen_props_new
        gen_props_new.set_trace_view(self)

    def set_trace_props(self, trace_props_new):

        self.trace_props = trace_props_new
        trace_props_new.set_trace_view(self)
