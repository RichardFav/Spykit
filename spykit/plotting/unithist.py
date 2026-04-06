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
from spykit.plotting.utils import PlotWidget, PlotLayout, UnitPlotLayout, setup_default_layout, x_gap

# pyqt6 module import
from PyQt6.QtWidgets import QWidget, QGraphicsRectItem, QLabel, QGridLayout
from PyQt6.QtCore import pyqtSignal, QSize
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

    def __init__(self, session_info):
        # field initialisations
        self.is_updating = True
        self.i_unit = 1

        # creates the class object
        p_layout = setup_default_layout()
        super(UnitHistPlot, self).__init__(
            'unithist', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl, p_layout=p_layout)
        p_layout.setParent(self)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # property class fields
        self.q_hdr = None
        self.q_met = None
        self.unit_props = None
        self.is_updating = False
        self.bg_widget = QWidget()

        # initialises the other class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # field retrieval
        self.l_size = self.plot_layout.sizeHint()

        # creates the background widget
        self.bg_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.plot_layout.addWidget(self.bg_widget)

        # sets the plot layout properties
        self.plot_layout.setSpacing(10)
        self.plot_layout.setDimOffset(15, 1)
        self.plot_layout.setRowStretch([0, 0.05])

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = pfcn(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)
            pb.raise_()

    def init_plot_view(self):

        # field retrieval
        n_met = np.sum(self.unit_props.can_plot)
        self.hist = np.empty(n_met, dtype=object)
        self.q_met_hist = np.empty(n_met, dtype=object)

        # memory allocation
        for i_met in range(n_met):
            self.q_met_hist[i_met] = self.get_hist_metrics(i_met)

        # creates the title widget
        self.title_lbl = cw.create_text_label(
            None, 'TEST', font=self.unit_props.title_main_font, align='center')
        self.title_lbl.setStyleSheet("QLabel { color: white; background-color: rgba(0, 0, 0, 0);}")
        self.plot_layout.addWidget(self.title_lbl)

        # creates the subplots for each row
        for i_row in range(self.n_r):
            # sets up the histogram widget
            for i_col in range(self.n_c):
                i_glob = i_row * self.n_c + i_col
                if i_glob < len(self.hist):
                    # if a valid plot index, then create the histogram object
                    self.hist[i_glob] = UnitHist(
                        self.unit_props,
                        self.i_unit,
                    )

                    # updates the figure with the plot metric data (if available)
                    if i_glob < n_met:
                        self.hist[i_glob].update_hist_metric(
                            self.q_met_hist[i_glob], i_glob
                        )

                    # adds the widget to the plot layout (initialisation only)
                    self.plot_layout.addWidget(self.hist[i_glob])

        # updates the plot title
        self.update_hist_config()
        self.update_plot_title()

    # ---------------------------------------------------------------------------
    # Parameter Update Functions
    # ---------------------------------------------------------------------------

    def update_plot(self, p_str='reset'):

        match p_str:
            case 'reset':
                # case is resetting the entire plot
                self.reset_all_histograms()

            case p_str if p_str in ['opt_config', 'n_r', 'n_c', 'hist_type']:
                # case is altering a configuration parameter
                self.update_hist_config(p_str != 'hist_type')

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

    def reset_all_histograms(self):

        # updates the unit index for each plot
        for hp in self.hist:
            hp.update_thresh_markers(True)
            hp.update_unit_index(self.i_unit)

    def update_hist_config(self, check_dim=True):

        # if there is no change in configuration, then exit
        if check_dim and (self.plot_layout.g_id is not None):
            if np.array_equal(self.plot_layout.g_id.shape, [self.n_r + 1, self.n_c]):
                return

        # memory allocation
        n_plt = (self.n_r + 1) * self.n_c
        xi_g = np.zeros(n_plt, dtype=int)
        self.i_met = np.where(self.hist_type)[0]

        # sets up the grid ID array
        xi_g[self.n_c:(self.n_c + len(self.i_met))] = self.i_met + 2
        g_id = xi_g.reshape(self.n_r + 1, self.n_c)
        g_id[0, :] = 1

        # updates the plot layout
        self.plot_layout.updateID(g_id)
        self.plot_layout.activate()

    def update_unit_index(self):

        # updates the main plot fields
        self.update_plot_title()

        # updates the unit index for each plot
        for hp in self.hist:
            hp.update_unit_index(self.i_unit)

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

    def update_plot_title(self):

        # updates the plot super-title
        u_type = self.unit_props.get_unit_type(self.i_unit - 1)
        t_str_nw = "Unit #{0} Quality Metrics ({1})".format(self.i_unit, u_type)
        self.title_lbl.setText(t_str_nw)

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

    def set_unit_props(self, unit_props_new):

        # sets the histogram property/view tabs
        self.unit_props = unit_props_new
        unit_props_new.set_plot_view(self)

        # field retrieval
        self.q_met = self.unit_props.get_mem_map_field('q_met')
        self.q_hdr = self.unit_props.get_mem_map_field('q_hdr')

        # histogram parameter fields
        self.is_updating = True
        self.hist_type = self.unit_props.get_para_value('hist_type')
        self.opt_config = bool(self.unit_props.get_para_value('opt_config'))
        self.n_r = int(self.unit_props.get_para_value('n_r'))
        self.n_c = int(self.unit_props.get_para_value('n_c'))
        self.n_bin = int(self.unit_props.get_para_value('n_bin'))
        self.show_grid = bool(self.unit_props.get_para_value('show_grid'))
        self.show_thresh = bool(self.unit_props.get_para_value('show_thresh'))
        self.i_unit = int(self.unit_props.get_para_value('i_unit'))
        self.is_updating = False

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

    # ---------------------------------------------------------------------------
    # Widget Event Callback Functions
    # ---------------------------------------------------------------------------

    def resizeEvent(self, event):

        # field retrieval
        new_size = event.size()

        # calculates the proportional height/width
        p_wid = new_size.width() / self.l_size.width()
        p_hght = new_size.height() / self.l_size.height()

        # resets the font object sizes
        self.unit_props.scale_font_sizes(p_wid, p_hght)

        # resets the title/label fonts
        self.title_lbl.setFont(self.unit_props.title_main_font)
        for hp in self.hist:
            hp.update_view_range()

        # updates the plot layout
        self.plot_layout.activate()

        # Call the base class implementation
        super().resizeEvent(event)

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def para_update(p_str, _self):
        if _self.is_updating:
            return

        _self.update_plot(p_str)

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


class UnitHist(UnitPlotLayout):
    # widget dimensions
    py_gap = 0.15
    px_gap = 0.02
    py_thresh = 0.9
    grid_alpha = 0.25
    py_title = 5

    # pen/brush objects
    l_brush_thresh = pg.mkBrush('r')
    l_pen_unit = pg.mkPen('y', width=3)
    l_pen_thresh = pg.mkPen('k', width=1)

    def __init__(self, unit_props, i_unit):
        super(UnitHist, self).__init__(unit_props, i_unit)

        # field initialisation
        self.is_updating = True

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
        self.init_plot_widgets()

        # resets the update flag
        self.is_updating = False

    def init_plot_widgets(self):

        # subplot layout setup
        self.sp_layout = QGridLayout()
        self.sp_layout.setRowStretch(0, self.py_title)
        self.sp_layout.setRowStretch(1, 100 - self.py_title)
        self.setLayout(self.sp_layout)

        # creates a temporary plot widget for the bar graph
        self.p_widget = pg.PlotWidget()
        self.sp_layout.addWidget(self.p_widget, 1, 0, 1, 1)
        self.p_widget.hideButtons()

        # creates the metric histogram/markers
        self.create_metric_histogram()
        self.create_threshold_markers()
        self.create_subplot_title()

        # sets the view range change function
        self.p_widget.plotItem.vb.sigResized.connect(self.update_view_range)

        # hides the wrapper plot widget axes
        self.plotItem.getAxis('left').hide()
        self.plotItem.getAxis('bottom').hide()

    # ---------------------------------------------------------------------------
    # Plot/Bar Graph Widget Setup Functions
    # ---------------------------------------------------------------------------

    def create_subplot_title(self):

        # creates the title label
        self.title_lbl = cw.create_text_label(
            None, 'TEST', font=self.unit_props.title_sub_font, align='center')
        self.sp_layout.addWidget(self.title_lbl, 0, 0, 1, 1)
        self.title_lbl.raise_()

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
        self.p_widget.addItem(self.bg_item)

    def create_threshold_markers(self):

        # creates the plot line
        self.unit_plot = self.plot([0], [0], pen=self.l_pen_unit)
        self.p_widget.addItem(self.unit_plot);

        # creates the threshold rectangle widget
        self.thresh_rect = QGraphicsRectItem(0, 0, 1, 1)
        self.thresh_rect.setBrush(self.l_brush_thresh);
        self.thresh_rect.setPen(self.l_pen_thresh);
        self.p_widget.addItem(self.thresh_rect);

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
        self.p_widget.addItem(self.thresh_reg)
        self.p_widget.plotItem.showGrid(alpha=self.grid_alpha)

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_hist_metric(self, q_met, i_met):

        # updates the metric fields
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
        vb = self.p_widget.plotItem.vb
        vb.setYRange(self.y_lim[0], self.y_lim[1], padding=0)
        vb.setXRange(self.x_lim[0], self.x_lim[1], padding=0)

        ax_bottom = self.p_widget.getAxis('bottom')
        if self.is_fixed_bin:
            x_ticks = [(x + 1, str(x + 1)) for x in range(self.n_bin)]
            ax_bottom.setTicks([x_ticks])

        else:
            ax_bottom.setTicks(None)

    def update_thresh_markers(self, reset_threshold=False):

        if reset_threshold:
            self.get_metric_thresholds()

        # retrieves the
        if self.p_str in ['presenceRatio']:
            x_lim = [0, 1]
        else:
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
        q_met_unit = self.q_met[self.i_unit - 1]
        self.lbl_col = 'white' if self.is_met_within_limits() else 'red'

        # sets up the histogram title string
        if np.isnan(q_met_unit):
            q_met_str = '(N/A)'
        elif self.is_int_met():
            q_met_str = f"({q_met_unit:.0f})"
        else:
            q_met_str = f"({q_met_unit:.3f})"

        # resets the title string
        self.t_str_plt = "{0}\n{1}".format(self.t_str, q_met_str)
        self.update_plot_title()

        # updates the axes colour
        h_pen_lbl = pg.mkPen(color=self.lbl_col[0])
        for ax_t in ['left', 'bottom']:
            h_ax = self.p_widget.getAxis(ax_t)
            h_ax.setPen(h_pen_lbl)
            h_ax.setTextPen(h_pen_lbl)
            h_ax.setZValue(-10)

    def update_plot_title(self):

        # sets the sub-plot title
        self.title_lbl.setFont(self.unit_props.title_sub_font)
        self.title_lbl.setText(self.t_str_plt)
        self.title_lbl.setStyleSheet("color: {0};".format(self.lbl_col))

        # updates the axis font properties
        self.p_widget.getAxis("left").setTickFont(self.unit_props.tick_font)
        self.p_widget.getAxis("bottom").setTickFont(self.unit_props.tick_font)

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

        self.p_widget.plotItem.showGrid(x=show_grid, y=show_grid)

    def update_view_range(self):

        self.update_plot_title()

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

        self.q_met = q_met_new

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
        q_met_hist = self.q_met[~np.isnan(self.q_met)]
        n_count, self.x_plt = np.histogram(q_met_hist, bins=self.n_bin, range=self.h_range)
        self.y_plt = n_count / np.sum(n_count)

        # calculates the upper limit
        if np.all(np.isnan(self.y_plt)):
            y_max = 1.0
        else:
            y_max = np.max(self.y_plt)

        # sets the overall y-axis max limit
        y_max_h = np.floor(math.log10(y_max) - 1)
        self.y_lim_max = cf.round_up(y_max, -y_max_h)
        self.y_lim_min = [self.get_max_lim_value(0.01),
                          self.get_max_lim_value(self.py_gap)]

        if self.p_str == ['presenceRatio']:
            x_rng = [0, 1]
        else:
            x_rng = [self.x_plt[0], self.x_plt[-1]]

        # calculates the upper limit
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

        pass