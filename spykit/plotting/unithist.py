# module import
import os
import time
import math
import colorsys
import numpy as np
from copy import deepcopy
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.plotting.utils import PlotWidget

# pyqt6 module import
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGraphicsRectItem, QLabel
from PyQt6.QtGui import QFont

# pyqtgraph module imports
import pyqtgraph as pg

# plot button fields
b_icon = ['save', 'close']
b_type = ['button', 'button']
tt_lbl = ['Save Figure', 'Close View']

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitHistPlot:
"""


class UnitHistPlot(PlotWidget):
    # widget dimensions
    p_row0 = 5

    # font
    font_title = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold, size=24)

    def __init__(self, session_info):
        self.is_init = True
        super(UnitHistPlot, self).__init__('unithist', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # property class fields
        self.i_unit = 1
        self.q_hdr = None
        self.q_met = None
        self.unit_props = None
        self.is_init = False

        # initialises the other class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = pfcn(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

    # ---------------------------------------------------------------------------
    # PLot View Methods
    # ---------------------------------------------------------------------------

    def init_plot_view(self, is_view_init=True):

        # plot view initialisations (only required once)
        if is_view_init:
            # field retrieval
            n_met = np.sum(self.unit_props.can_plot)
            self.hist = np.empty(n_met, dtype=object)
            self.q_met_hist = np.empty(n_met, dtype=object)

            # memory allocation
            for i_met in range(n_met):
                self.q_met_hist[i_met] = self.get_hist_metrics(i_met)

        # sets up the plot regions
        self.setup_subplots(n_r=self.n_r + 1, n_c=self.n_c)

        # resets the row stretch
        self.plot_layout.setRowStretch(0, self.n_r * self.p_row0)
        for i_r in range(self.plot_layout.rowCount() - 1):
            # resets the minimum row height
            self.plot_layout.setRowMinimumHeight(i_r + 1, 0)

            # updates the grid row stretch
            if i_r < self.n_r:
                self.plot_layout.setRowStretch(i_r + 1, 100 - self.p_row0)
            else:
                self.plot_layout.setRowStretch(i_r + 1, 0)

        # creates the title widget
        self.title_lbl = cw.create_text_label(None, 'TEST', font=self.font_title, align='center')
        self.title_lbl.setStyleSheet("QLabel { color: white; }")
        self.plot_layout.addWidget(self.title_lbl, 0, 0, 1, self.n_c)

        # hides the first (title) row
        for hp_0 in self.h_plot[0, :]:
            hp_0.hide()

        # retrieves the initial subplot configuration
        self.i_met = np.where(self.hist_type)[0]

        # creates the subplots for each row
        for i_row in range(self.n_r):
            # resets the row stretch
            self.plot_layout.setRowStretch(i_row + 1, self.n_r * (100 - self.p_row0))

            # sets up the histogram widget
            for i_col in range(self.n_c):
                i_glob = i_row * self.n_c + i_col
                if i_glob < len(self.hist):
                    # if a valid plot index, then create the histogram object
                    self.hist[i_glob] = UnitHist(
                        self.h_plot[i_row + 1, i_col],
                        self.unit_props,
                        self.i_unit,
                    )

                    if i_glob < len(self.i_met):
                        # updates the figure with the plot metric data (if available)
                        i_met_new = self.i_met[i_glob]
                        self.hist[i_glob].update_hist_metric(
                            self.q_met_hist[i_met_new], i_met_new
                        )

                    else:
                        # otherwise, hide the subplot
                        self.hist[i_glob].set_plot_visibility(False)

                else:
                    # otherwise, hide the plot object
                    self.h_plot[i_row + 1, i_col].hide()

        # updates the plot title
        self.update_plot_title()

    # ---------------------------------------------------------------------------
    # Parameter Update Functions
    # ---------------------------------------------------------------------------

    def plot_update(self, p_str):

        match p_str:
            case p_str if p_str in ['opt_config', 'n_r', 'n_c']:
                # case is altering a configuration parameter
                self.update_hist_config()

            case 'hist_type':
                # case is histogram types
                self.update_hist_type()

            case 'i_unit':
                # case is the unit index
                self.update_unit_index()

            case 'n_bin':
                # case is the bin count
                self.update_bin_count()

            case 'show_thresh':
                # case is showing the threshold markers
                self.update_show_thresh()

            case 'show_grid':
                # case is showing the plot grid
                self.update_show_grid()

    def update_hist_config(self):

        # if there is no change in configuration, then exit
        if np.array_equal(self.h_plot.shape, [self.n_r + 1, self.n_c]):
            return

        # clears and deletes the subplots
        cf.clear_layout(self.plot_layout)

        # re-initialises the plot view
        self.init_plot_view(False)

    def update_hist_type(self):

        # field retrieval
        i_met_new = np.where(self.hist_type)[0]
        n_prev, n_new = len(self.i_met), len(i_met_new)

        for i_hist in range(np.min([n_prev, n_new])):
            # only update if the metric
            if i_met_new[i_hist] != self.hist[i_hist].i_met:
                self.hist[i_hist].update_hist_metric(
                    self.q_met_hist[i_met_new[i_hist]], i_met_new[i_hist]
                )

        # sets the final plot visibility (based on selection)
        if n_new > n_prev:
            # updates and shows the last plot (from the new configuration)
            self.hist[n_new - 1].update_hist_metric(
                self.q_met_hist[i_met_new[n_new - 1]], i_met_new[n_new - 1]
            )
            self.hist[n_new - 1].set_plot_visibility(True)

        else:
            # hides the last plot (from the previous configuration)
            self.hist[n_prev - 1].set_plot_visibility(False)

        # resets the metric fields
        self.i_met = i_met_new

    def update_unit_index(self):

        # updates the main plot fields
        self.update_plot_title()

        # updates the unit index for each plot
        for i in range(len(self.i_met)):
            self.hist[i].update_unit_index(self.i_unit)

    def update_bin_count(self):

        # updates the bin count for each plot
        for hp in self.hist:
            hp.update_bin_count()

    def update_show_thresh(self):

        # updates the threshold marker visibility for each plot
        for hp in self.hist:
            hp.update_show_thresh(self.show_thresh)

    def update_show_grid(self):

        # updates the grid visibility for each plot
        for hp in self.hist:
            hp.update_axes_grid(self.show_grid)

    # ---------------------------------------------------------------------------
    # Plot Button Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'save':
                # case is the figure save button

                # outputs the current trace to file
                f_path = cf.setup_image_file_name(cw.figure_dir, 'TraceTest.png')       # CHANGE THIS TO
                exp_obj = exporters.ImageExporter(self.h_plot[0, 0].getPlotItem())
                exp_obj.export(f_path)

            case 'close':
                # case is the close button
                self.hide_plot.emit()

    # ---------------------------------------------------------------------------
    # Other Plot View Functions
    # ---------------------------------------------------------------------------

    def clear_plot_view(self):

        pass

    def show_view(self):

        pass

    def hide_view(self):

        pass

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_hist_props(self, unit_props_new):

        # sets the histogram property/view tabs
        self.unit_props = unit_props_new
        unit_props_new.set_plot_view(self)

        # field retrieval
        self.q_met = self.unit_props.get_mem_map_field('q_met')
        self.q_hdr = self.unit_props.get_mem_map_field('q_hdr')

        # histogram parameter fields
        self.is_init = True
        self.hist_type = self.unit_props.get_para_value('hist_type')
        self.opt_config = bool(self.unit_props.get_para_value('opt_config'))
        self.n_r = int(self.unit_props.get_para_value('n_r'))
        self.n_c = int(self.unit_props.get_para_value('n_c'))
        self.n_bin = int(self.unit_props.get_para_value('n_bin'))
        self.show_grid = bool(self.unit_props.get_para_value('show_grid'))
        self.show_thresh = bool(self.unit_props.get_para_value('show_thresh'))
        self.i_unit = int(self.unit_props.get_para_value('i_unit'))
        self.is_init = False

        # updates the plot view
        self.init_plot_view()

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_hist_metrics(self, i_glob):

        p_str = cf.get_dict_key(cw.hist_map, str(self.unit_props.p_met_fin[i_glob]))
        return self.q_met[:, np.where(self.q_hdr[0, :] == p_str)[0][0]]

    def get_field(self, p_fld):

        return self.session_info.get_mem_map_field(p_fld)

    def get_subplot_config_id(self):

        # memory allocation
        i_met = np.where(self.hist_type)[0]
        c_id = np.nan * np.ones((self.n_r, self.n_c), dtype=int)

        # sets the sub-plot indices into the full array
        for i, i_m in enumerate(i_met):
            # i_r, i_c = self.get_grid_indices(i)
            # c_id[i_r, i_c] = i_m
            c_id[self.get_grid_indices(i)] = i_m

        return c_id

    def get_grid_indices(self, ind):

        return int(np.floor(ind / self.n_c)), ind % self.n_c

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def update_plot_title(self):

        # updates the plot super-title
        t_str_nw = "Unit #{0} Quality Metrics".format(self.i_unit)
        self.title_lbl.setText(t_str_nw)

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def para_update(p_str, _self):
        if _self.is_init:
            return

        _self.plot_update(p_str)

    # property observer properties
    hist_type = cf.ObservableProperty(pfcn(para_update, 'hist_type'))
    opt_config = cf.ObservableProperty(pfcn(para_update, 'opt_config'))
    n_r = cf.ObservableProperty(pfcn(para_update, 'n_r'))
    n_c = cf.ObservableProperty(pfcn(para_update, 'n_c'))
    n_bin = cf.ObservableProperty(pfcn(para_update, 'n_bin'))
    show_grid = cf.ObservableProperty(pfcn(para_update, 'show_grid'))
    show_thresh = cf.ObservableProperty(pfcn(para_update, 'show_thresh'))
    i_unit = cf.ObservableProperty(pfcn(para_update, 'i_unit'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitHist:
"""


class UnitHist(object):
    # widget dimensions
    py_gap = 0.15
    px_gap = 0.02
    py_thresh = 0.9
    grid_alpha = 0.25

    # pen/brush objects
    l_brush_thresh = pg.mkBrush('r')
    l_pen_unit = pg.mkPen('y', width=3)
    l_pen_thresh = pg.mkPen('k', width=1)

    def __init__(self, h_plot, unit_props, i_unit):
        super(UnitHist, self).__init__()

        # field initialisation
        self.is_updating = True

        # field initialisations
        self.i_unit = i_unit
        self.h_plot = h_plot
        self.unit_props = unit_props

        # metric specific fields
        self.q_met = None
        self.i_met = None

        # histogram property class fields
        self.n_bin = None
        self.py_lim = None
        self.h_range = None
        self.bg_item = None
        self.is_fixed_bin = False
        self.x_lim, self.y_lim = None, None
        self.x_plt, self.y_plt = None, None

        # threshold marker class fields
        self.thresh_reg = None

        # initialises the class fields
        self.init_class_fields()
        self.init_plot_widgets()

        # resets the update flag
        self.is_updating = False

    def init_class_fields(self):

        # metric fields
        self.v_box = self.h_plot.getViewBox()
        self.v_box.setMouseEnabled(False, False)

        # sets the default plot properties
        self.h_plot.getAxis('left').setStyle(tickLength=0)
        self.h_plot.getAxis('bottom').setStyle(tickLength=0)

    def init_plot_widgets(self):

        # creates the metric histogram/markers
        self.create_metric_histogram()
        self.create_threshold_markers()

    # ---------------------------------------------------------------------------
    # Plot/Bar Graph Widget Setup Functions
    # ---------------------------------------------------------------------------

    def create_threshold_markers(self):

        # creates the plot line
        self.unit_plot = self.h_plot.plot([0], [0], pen=self.l_pen_unit)

        # creates the threshold rectangle widget
        self.thresh_rect = QGraphicsRectItem(0, 0, 1, 1)
        self.thresh_rect.setBrush(self.l_brush_thresh);
        self.thresh_rect.setPen(self.l_pen_thresh);
        self.h_plot.addItem(self.thresh_rect);

        # creates the linear region
        self.thresh_reg = pg.LinearRegionItem(
            [0, 1],
            span=[0, 1],
            bounds=[0, 1],
            movable=False,
            pen=None,
            brush=(0, 255, 0, 255),
            orientation='vertical',
        )

        # adds the threshold marker to the plot item
        self.thresh_reg.setZValue(20)
        self.h_plot.addItem(self.thresh_reg)
        self.h_plot.plotItem.showGrid(alpha=self.grid_alpha)

    def create_metric_histogram(self):

        # creates the bar-graph object
        self.bg_item = pg.BarGraphItem(
            x0=[0],
            x1=[1],
            height=[1],
            pen='w',
            brush=(0,0,255,150),
        )

        # updates the plot widget item/title
        self.h_plot.addItem(self.bg_item)

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_hist_metric(self, q_met, i_met):

        # updates the metric fields
        self.i_met = i_met
        self.set_quantity_metrics(q_met)
        self.set_metric_info(self.unit_props.p_met_fin[i_met])

        # updates the histogram range
        self.update_histogram_values()
        self.update_thresh_markers()

        # updates the other plot properties
        self.update_plot_labels()
        self.update_axes_grid(bool(self.unit_props.get_para_value('show_grid')))

    def update_histogram_values(self):

        # retrieves the plot data
        self.get_hist_plot_data()

        # updates the histogram values
        self.bg_item.setOpts(
            x0 = self.x_plt[:-1],
            x1 = self.x_plt[1:],
            height = self.y_plt,
        )

        # updates the histogram range
        self.update_histogram_range()

    def update_histogram_range(self):

        # sets the y-axes multiplier
        show_thresh = bool(self.unit_props.get_para_value('show_thresh'))
        self.y_lim = [self.y_lim_min[show_thresh], self.y_lim_max]
        self.dx_lim = np.diff(self.x_plt[:2])[0] / 2 if self.is_fixed_bin else 0

        # updates the y-axes limits
        self.v_box.setYRange(self.y_lim[0], self.y_lim[1], padding=0)
        self.v_box.setXRange(self.x_lim[0], self.x_lim[1], padding=0)

        ax_bottom = self.h_plot.getAxis('bottom')
        if self.is_fixed_bin:
            x_ticks = [(x + 1, str(x + 1)) for x in range(self.n_bin)]
            ax_bottom.setTicks([x_ticks])

        else:
            ax_bottom.setTicks(None)

    def update_thresh_markers(self):

        # retrieves the
        x_lim = [self.x_plt[0], self.x_plt[-1]]

        # sets the threshold rectangle y-coordinate
        dy_lim = np.diff(self.y_lim)[0]
        rect_hght = [0.025, (-self.y_lim[0] / dy_lim - 0.01)]
        y_rect = self.y_lim[0] + (rect_hght[0] - 0.005) * dy_lim

        # updates the infeasible threshold marker
        out_wid = np.diff(x_lim)[0]
        self.thresh_reg.setBounds(x_lim)
        self.thresh_reg.setSpan(rect_hght[0], rect_hght[1])
        self.thresh_rect.setRect(x_lim[0], y_rect, out_wid, np.diff(rect_hght)[0] * dy_lim)

        # resets the marker location
        self.update_metric_marker()

        # sets the lower bound limit
        if not np.isnan(self.p_met[0]):
            x_lim[0] = np.max([self.p_met[0] - self.dx_lim, x_lim[0]])

        if not np.isnan(self.p_met[1]):
            x_lim[1] = np.min([self.p_met[1] + self.dx_lim, x_lim[1]])

        # resets the axis limits
        self.thresh_reg.setRegion(x_lim)

    def update_metric_marker(self):

        # field retrieval
        x_met = self.q_met[self.i_unit - 1]

        # updates the metric marker location
        self.unit_plot.setData([x_met, x_met], [0, self.y_lim[1]])

    def update_plot_labels(self):

        # field retrieval
        lbl_col = 'w' if self.is_met_within_limits() else 'r'

        # sets up the histogram title string
        if self.is_int_met():
            q_met_str = f"({self.q_met[self.i_unit - 1]:.0f})"
        else:
            q_met_str = f"({self.q_met[self.i_unit - 1]:.3f})"

        # resets the title string
        t_str_nw = "{0} {1}".format(self.t_str, q_met_str)
        self.h_plot.plotItem.setTitle(
            t_str_nw,
            bold = True,
            size='10pt',
            color=lbl_col,
        )

        # updates the axes colour
        h_pen_lbl = pg.mkPen(color=lbl_col)
        for ax_t in ['left', 'bottom']:
            h_ax = self.h_plot.getAxis(ax_t)
            h_ax.setPen(h_pen_lbl)
            h_ax.setTextPen(h_pen_lbl)
            h_ax.setZValue(-10)

    def update_bin_count(self):

        # updates the unit index
        self.update_histogram_values()
        self.update_thresh_markers()

    def update_unit_index(self, i_unit_new):

        # updates the unit index
        self.i_unit = i_unit_new

        # updates the plot
        self.update_plot_labels()
        self.update_metric_marker()

    def update_show_thresh(self, show_thresh):

        # sets the threshold widget visibility flags
        self.thresh_reg.setVisible(show_thresh)
        self.thresh_rect.setVisible(show_thresh)
        self.unit_plot.setVisible(show_thresh)

        # resets the histogram x/y-axes ranges
        self.update_histogram_range()

    def update_axes_grid(self, show_grid):

        self.h_plot.plotItem.showGrid(x=show_grid, y=show_grid)

    # ---------------------------------------------------------------------------
    # Setter Methods
    # ---------------------------------------------------------------------------

    def set_metric_info(self, t_str_new):

        # update the title string
        self.t_str = t_str_new

        # updates the parameter string/quality metric thresholds
        self.p_str = cf.get_dict_key(cw.hist_map, self.t_str)
        self.get_metric_thresholds()

    def set_quantity_metrics(self, q_met_new):

        self.q_met = q_met_new[~np.isnan(q_met_new)]

    def set_plot_visibility(self, state):

        self.h_plot.show() if state else self.h_plot.hide()

    # ---------------------------------------------------------------------------
    # Getter Methods
    # ---------------------------------------------------------------------------

    def get_metric_thresholds(self):

        # initialisations
        self.p_met = [np.nan, np.nan]

        match self.p_str:
            case 'nPeaks':
                # case is the peak count
                self.p_met[1] = self.unit_props.get_mem_map_field('maxNPeaks')

            case 'nTroughs':
                # case is the trough count
                self.p_met[1] = self.unit_props.get_mem_map_field('maxNTroughs')

            case 'scndPeakToTroughRatio':
                # case is the 2nd peak/trough ratio
                self.p_met[1] = self.unit_props.get_mem_map_field('maxScndPeakToTroughRatio_noise')

            case 'peak1ToPeak2Ratio':
                # case is the 1st peak/2nd peak ratio
                self.p_met[1] = self.unit_props.get_mem_map_field('maxPeak1ToPeak2Ratio_nonSomatic')

            case 'mainPeakToTroughRatio':
                # case is the main peak/trough ratio
                self.p_met[1] = self.unit_props.get_mem_map_field('maxMainPeakToTroughRatio_nonSomatic')

            case 'fractionRPVs_estimatedTauR':
                # case is the RPV tauR estimate fraction
                self.p_met[1] = self.unit_props.get_mem_map_field('maxRPVviolations')

            case 'percentageSpikesMissing_gaussian':
                # case is the % spike missings (gaussian)
                self.p_met[1] = self.unit_props.get_mem_map_field('maxPercSpikesMissing')

            case 'nSpikes':
                # case is the spike count
                self.p_met[0] = self.unit_props.get_mem_map_field('minNumSpikes')

            case 'rawAmplitude':
                # case is the raw amplitude
                self.p_met[0] = self.unit_props.get_mem_map_field('minAmplitude')

            case 'spatialDecaySlope':
                # case is the spatial decay slope
                if self.unit_props.get_mem_map_field('spDecayLinFit'):
                    # case is linear spatial decay fit
                    self.p_met[0] = self.unit_props.get_mem_map_field('minSpatialDecaySlope')

                else:
                    # case is non-linear spatial decay fit
                    self.p_met[0] = self.unit_props.get_mem_map_field('minSpatialDecaySlopeExp')
                    self.p_met[1] = self.unit_props.get_mem_map_field('maxSpatialDecaySlopeExp')

            case 'waveformDuration_peakTrough':
                # case is the waveform duration peak/trough ratio
                self.p_met[0] = self.unit_props.get_mem_map_field('minWvDuration')
                self.p_met[1] = self.unit_props.get_mem_map_field('maxWvDuration')

            case 'waveformBaselineFlatness':
                # case is the waveform baseline flatness
                self.p_met[1] = self.unit_props.get_mem_map_field('maxWvBaselineFraction')

            case 'presenceRatio':
                # case is the presence ratio
                self.p_met[0] = self.unit_props.get_mem_map_field('minPresenceRatio')

            case 'signalToNoiseRatio':
                # case is the signal-to-noise ratio
                self.p_met[0] = self.unit_props.get_mem_map_field('minSNR')

            case 'maxDriftEstimate':
                # case is the maximum drift estimate
                self.p_met[1] = self.unit_props.get_mem_map_field('maxDrift')

            case 'isoD':
                # case is the iso-distance
                self.p_met[1] = self.unit_props.get_mem_map_field('isoDmin')

            case 'Lratio':
                # case is the l-Ratio
                self.p_met[0] = self.unit_props.get_mem_map_field('lratioMax')

    def get_hist_plot_data(self):

        # retrieves the histogram bin count
        self.get_bin_count()

        # calculates the histogram
        n_count, self.x_plt = np.histogram(self.q_met, bins=self.n_bin, range=self.h_range)
        self.y_plt = n_count / np.sum(n_count)

        # calculates the upper limit
        y_max = np.max(self.y_plt)
        y_max_h = np.floor(math.log10(y_max) - 1)
        self.y_lim_max = cf.round_up(y_max, -y_max_h)
        self.y_lim_min = [self.get_max_lim_value(0.01),
                          self.get_max_lim_value(self.py_gap)]

        # calculates the upper limit
        x_rng = [self.x_plt[0], self.x_plt[-1]]
        dx_rng = np.diff(x_rng)[0]
        self.x_lim = np.array(x_rng) + dx_rng * np.array([-1, 1]) * self.px_gap

    def get_bin_count(self):

        match self.p_str:
            case self.p_str if self.p_str in ['nPeaks','nTroughs']:
                # case is peak/trough counts
                self.is_fixed_bin = True
                self.n_bin = int(np.max(self.q_met))
                self.h_range = (0.5, self.n_bin+0.5)

            # case 'presenceRatio':
            #     # case is the presence ratio
            #     self.is_fixed_bin = True
            #     self.n_bin = 10
            #     self.h_range = (-1 / 18, 1 + 1 / 18)

            case _:
                # case is the other quality metrics
                self.h_range = None
                self.n_bin = int(self.unit_props.get_para_value('n_bin'))
                self.is_fixed_bin = False

    def get_max_lim_value(self, x):

        return -(x * self.y_lim_max) / (1 - x)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def is_int_met(self):

        # determines if all metrics are
        return next((False for x in self.q_met if (x % 1 != 0)), True)

    def is_met_within_limits(self):

        # field retrieval
        q_val = self.q_met[self.i_unit - 1]
        has_lim = ~np.isnan(self.p_met)

        if np.all(has_lim):
            # both limits are specified
            return (q_val >= self.p_met[0]) and (q_val <= self.p_met[1])

        elif has_lim[0]:
            # only lower limit is specified
            return q_val >= self.p_met[0]

        elif has_lim[1]:
            # only upper limit is specified
            return q_val <= self.p_met[1]

        else:
            # no limit is specified
            return True