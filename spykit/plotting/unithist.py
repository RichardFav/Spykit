# module import
import os
import time
import colorsys
import functools
import numpy as np
from copy import deepcopy

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
        super(UnitHistPlot, self).__init__('unithist', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # property class fields
        self.i_unit = 1
        self.q_hdr = None
        self.q_met = None
        self.unit_props = None

        # other class fields
        self.is_init = True
        self.show_met = True

        # initialises the other class fields
        self.init_class_fields()
        # self.update_plot()

        # resets the initialisation flag
        self.is_init = False

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # creates the title widget
        self.title_lbl = cw.create_text_label(None, 'TEST', font=self.font_title, align='center')
        self.title_lbl.setStyleSheet("QLabel { color: white; }")

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = functools.partial(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

    # ---------------------------------------------------------------------------
    # PLot View Methods
    # ---------------------------------------------------------------------------

    def init_plot_view(self):

        # field retrieval
        n_met = np.sum(self.unit_props.can_plot)
        n_row = int(self.unit_props.get_para_value('n_row'))
        n_col = int(self.unit_props.get_para_value('n_col'))

        # memory allocation
        self.hist = np.empty(n_met, dtype=object)
        self.q_met_hist = np.empty(n_met, dtype=object)
        self.i_hist = -np.ones((n_row, n_col), dtype=int)

        # sets up the plot regions
        self.setup_subplots(n_r=n_row + 1, n_c=n_col)

        # resets the row stretch
        self.plot_layout.setRowStretch(0, n_row * self.p_row0)
        self.plot_layout.addWidget(self.title_lbl, 0, 0, 1, n_col)

        # hides the first (title) row
        for hp_0 in self.h_plot[0, :]:
            hp_0.hide()

        # creates the subplots for each row
        for i_row in range(n_row):
            # resets the row stretch
            self.plot_layout.setRowStretch(i_row + 1, n_row * (100 - self.p_row0))

            # sets up the histogram widget
            for i_col in range(n_col):
                i_glob = i_row * n_col + i_col
                if i_glob < n_met:
                    # if a valid plot index, then create the histogram object
                    self.q_met_hist[i_glob] = self.get_hist_metrics(i_glob)
                    self.hist[i_glob] = UnitHist(
                        self.h_plot[i_row + 1, i_col],
                        self.unit_props,
                        self.q_met_hist[i_glob],
                        i_glob
                    )

                else:
                    # otherwise, hide the plot object
                    self.h_plot[i_row + 1, i_col].hide()

        # updates the plot title
        self.update_plot_title()

    def update_hist_view(self, reset_config=True):

        # updates the histogram configuration (if required)
        if reset_config:
            self.reset_hist_config()

    def update_plot_title(self):

        # updates the plot super-title
        t_str_nw = "Unit #{0} Quality Metrics".format(self.i_unit)
        self.title_lbl.setText(t_str_nw)

    def reset_hist_config(self):

        pass

    def update_plot(self):

        pass

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
    # Parameter Object Setter Functions
    # ---------------------------------------------------------------------------

    def set_hist_props(self, unit_props_new):

        # sets the histogram property/view tabs
        self.unit_props = unit_props_new
        unit_props_new.set_plot_view(self)

        # field retrieval
        self.q_met = self.unit_props.get_mem_map_field('q_met')
        self.q_hdr = self.unit_props.get_mem_map_field('q_hdr')

        # updates the plot view
        self.init_plot_view()

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def get_hist_metrics(self, i_glob):

        p_str = cf.get_dict_key(cw.hist_map, str(self.unit_props.p_met_fin[i_glob]))
        return self.q_met[:, np.where(self.q_hdr[0, :] == p_str)[0][0]]

    def get_field(self, p_fld):

        return self.session_info.get_mem_map_field(p_fld)

    # ---------------------------------------------------------------------------
    # Parameter Field Update Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_para(_self):
        if _self.is_init:
            return

        _self.update_plot()

    # trace property observer properties
    hist_type = cf.ObservableProperty(update_para)

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitHist:
"""


class UnitHist(object):
    # widget dimensions
    py_gap = 0.15
    py_thresh = 0.9
    grid_alpha = 0.25

    # pen/brush objects
    l_brush_thresh = pg.mkBrush('r')
    l_pen_unit = pg.mkPen('y', width=3)
    l_pen_thresh = pg.mkPen('k', width=1)

    def __init__(self, h_plot, unit_props, q_met, i_glob, i_unit=0):
        super(UnitHist, self).__init__()

        # field initialisation
        self.is_updating = True

        # field initialisations
        self.i_glob = i_glob
        self.i_unit = i_unit
        self.h_plot = h_plot
        self.unit_props = unit_props

        # metric fields
        self.v_box = self.h_plot.getViewBox()
        self.set_quantity_metrics(q_met)
        self.set_metric_info(self.unit_props.p_met_fin[i_glob])

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

        # sets the default plot properties
        self.h_plot.getAxis('left').setStyle(tickLength=0)
        self.h_plot.getAxis('bottom').setStyle(tickLength=0)

    def init_plot_widgets(self):

        # creates the metric histogram/markers
        self.create_metric_histogram()
        self.create_threshold_markers()

        # updates the other plot properties
        self.update_plot_labels()
        self.update_axes_grid()

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

        # updates the threshold markers
        self.update_thresh_markers()

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

        # updates the histogram range
        self.update_histogram_values()

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_axes_grid(self):

        show_grid = bool(self.unit_props.get_para_value('show_grid'))
        self.h_plot.plotItem.showGrid(x=show_grid, y=show_grid)

    def update_thresh_markers(self):

        # retrieves the
        _, y_lim = self.v_box.viewRange()
        x_lim = [self.x_plt[0], self.x_plt[-1]]
        rect_hght = [0.025, (-y_lim[0] / np.diff(y_lim)[0] - 0.01)]

        # sets the threshold rectangle y-coordinate
        dy_lim = np.diff(y_lim)[0]
        y_rect = y_lim[0] + (rect_hght[0] - 0.005) * dy_lim

        # updates the infeasible threshold marker
        out_wid = np.diff(x_lim)[0]
        self.thresh_reg.setBounds(x_lim)
        self.thresh_reg.setSpan(rect_hght[0], rect_hght[1])
        self.thresh_rect.setRect(x_lim[0], y_rect, out_wid, np.diff(rect_hght)[0] * dy_lim)

        # resets the marker location
        x_met = self.q_met[self.i_unit]
        self.unit_plot.setData([x_met, x_met], [0, y_lim[1]])

        # sets the lower bound limit
        dx_lim = np.diff(self.x_plt[:2])[0] / 2 if self.is_fixed_bin else 0
        if not np.isnan(self.p_met[0]):
            x_lim[0] = np.max([self.p_met[0] - dx_lim, x_lim[0]])

        if not np.isnan(self.p_met[1]):
            x_lim[1] = np.min([self.p_met[1] + dx_lim, x_lim[1]])

        # resets the axis limits
        self.thresh_reg.setRegion(x_lim)

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

        # retrieves the current subplot axes limits
        self.v_box.autoRange()
        y_lim = self.v_box.viewRange()[1]

        # sets the y-axes multiplier
        show_thresh = bool(self.unit_props.get_para_value('show_thresh'))
        py_lim = self.py_gap if show_thresh else -y_lim[0] / y_lim[1]

        # updates the y-axes limits
        self.v_box.setYRange(-py_lim * y_lim[1], y_lim[1], padding=0)

        if self.is_fixed_bin:
            x_ticks = [(x + 1, str(x + 1)) for x in range(self.n_bin)]
            self.h_plot.getAxis('bottom').setTicks([x_ticks])

    def update_plot_labels(self):

        # field retrieval
        lbl_col = 'w' if self.is_met_within_limits() else 'r'

        # sets up the histogram title string
        if self.is_int_met():
            q_met_str = f"({self.q_met[self.i_unit]:.0f})"
        else:
            q_met_str = f"({self.q_met[self.i_unit]:.3f})"

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
                self.is_fixed_bin = False
                self.n_bin = int(self.unit_props.get_para_value('n_bin'))

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def is_int_met(self):

        # determines if all metrics are
        return next((False for x in self.q_met if (x % 1 != 0)), True)

    def is_met_within_limits(self):

        # field retrieval
        q_val = self.q_met[self.i_unit]
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

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    # @staticmethod
    # def _check_update(_self):
    #
    #     if not _self.is_updating:
    #         _self.check_update.emit()

    # # trace property observer properties
    # use_full = cf.ObservableProperty(_check_update)