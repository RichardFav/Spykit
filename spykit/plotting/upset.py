# module import
import os
import time
import colorsys
import functools
import numpy as np
import pandas as pd
from copy import deepcopy

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.plotting.utils import PlotWidget

# pyqt6 module import
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import (QColor, QFont)

# pyqtgraph modules
from pyqtgraph import (BarGraphItem, PlotDataItem, ScatterPlotItem, mkBrush, mkPen, plot)

# plot button fields
b_icon = ['save', 'close']
b_type = ['button', 'button']
tt_lbl = ['Save Figure', 'Close View']

# ----------------------------------------------------------------------------------------------------------------------

"""
    UpSetPlot:
"""


class UpSetPlot(PlotWidget):
    # pyqtsignal functions
    hide_plot = pyqtSignal()
    reset_highlight = pyqtSignal(object)

    # parameters
    p_row = 60
    p_col = 30
    m_size = 10
    c_col1 = 220
    c_col2 = 200
    c_col3 = 175

    x_pad = 0.005
    y_pad = 0.02

    # pen/font objects
    plt_pen = mkPen('k', width=2)
    tick_font = cw.create_font_obj(size=10, is_bold=True, font_weight=QFont.Weight.Bold)

    # stripe colours
    c_stripe_1 = QColor(c_col1, c_col1, c_col1, 255)
    c_stripe_2 = QColor(c_col2, c_col2, c_col2, 255)
    c_dot = QColor(c_col3, c_col3, c_col3, 255)

    def __init__(self, session_info):
        super(UpSetPlot, self).__init__('upset', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # sets up the plot regions
        self.setup_subplots(n_r=2, n_c=2)
        self.plot_set = self.h_plot[0, 1].getPlotItem()
        self.plot_interact = self.h_plot[0, 1].getPlotItem()
        self.plot_details = self.h_plot[1, 1].getPlotItem()

        # initialises the other class fields
        self.init_class_fields()

        # other class fields
        self.has_plot = False
        # self.unit_type = 'MUA'
        self.unit_type = 'Noise'
        # self.unit_type = 'NonSoma'

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # resets the row stretch
        self.plot_layout.setRowStretch(0, self.p_row)
        self.plot_layout.setRowStretch(1, 100 - self.p_row)
        self.plot_layout.setColumnStretch(0, self.p_col)
        self.plot_layout.setColumnStretch(1, 100 - self.p_col)

        # hides the top-left plot region
        self.h_plot[0, 0].hide()

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = functools.partial(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

    # ---------------------------------------------------------------------------
    # PLot View Methods
    # ---------------------------------------------------------------------------

    def update_plot(self):

        # -----------------------------------------------------------------------
        # Pre-Calculations
        # -----------------------------------------------------------------------

        # clears the plot data
        self.clear_subplots()

        # field retrieval
        q_hdr = np.array(self.get_data_labels())
        q_data = np.array(self.get_data_array())
        n_unit, n_data = q_data.shape

        # determines the types of violations
        p_bool = cf.bool_perm_array(n_data)[1:, :]
        A = p_bool @ (1 - np.transpose(q_data))
        B = (1 - p_bool) @ np.transpose(q_data)
        p_pos = np.where(np.array(np.logical_or(A, B), dtype=int) == 0)[0]

        # returns the sorted total count/violation codes
        p_type, n_count = np.unique(p_pos, return_counts=True)
        ind_p = np.lexsort((np.array(range(len(n_count))), -n_count))
        p_type, n_count = p_type[ind_p], n_count[ind_p]

        # returns the sorted set size counts
        s_count = np.sum(q_data, axis=0)
        ind_s = np.argsort(-s_count)
        s_count, q_hdr, p_bool = s_count[ind_s], q_hdr[ind_s], p_bool[:, ind_s]

        # -----------------------------------------------------------------------
        # Interaction Size Subplot
        # -----------------------------------------------------------------------

        # plotting values
        x_int = np.array(range(len(n_count))) + 0.5
        t_str = '{0} Unit Classification Interactions'.format(self.unit_type)

        # creates the bar graph item
        bar_int = BarGraphItem(x=x_int, height=n_count, width=0.6)
        self.h_plot[0, 1].addItem(bar_int)
        self.h_plot[0, 1].setTitle(t_str, size='20pt', bold=True)
        self.v_box[0, 1].setYRange(0, n_count[0], padding=self.x_pad)
        self.v_box[0, 1].setXRange(0, len(n_count))

        # sets the x-axis properties
        x_axis_int = self.plot_interact.getAxis('bottom')
        x_axis_int.setTicks([])

        # y-axis properties
        y_axis_int = self.plot_interact.getAxis('left')
        y_axis_int.setStyle(tickLength=1, tickFont=self.tick_font)

        # determines the y-axis tick values
        v_rng_int = self.v_box[0, 1].viewRange()
        y_tick_int = y_axis_int.tickValues(v_rng_int[1][0], v_rng_int[1][1], y_axis_int.size().height())[0][1]
        y_tick_lbl = [(y_pos, str(int(y_pos))) for y_pos in y_tick_int]
        y_axis_int.setTicks([y_tick_lbl])

        # other axes properties
        self.h_plot[0, 1].showGrid(y=True)
        self.v_box[0, 1].setXRange(v_rng_int[0][0], v_rng_int[0][1], padding=0)

        # -----------------------------------------------------------------------
        # Set Size Subplot
        # -----------------------------------------------------------------------

        # plotting values
        y_set = np.array(range(n_data)) + 0.5

        # creates the bar plot
        bar_set = BarGraphItem(x0=0, y=y_set, height=0.6, width=s_count)
        self.h_plot[1, 0].addItem(bar_set)
        self.v_box[1, 0].setYRange(0, n_data, padding=self.x_pad)
        self.v_box[1, 0].setXRange(0, np.max(s_count), padding=self.y_pad)

        # y-axis properties
        y_axis_set = self.h_plot[1, 0].getAxis('left')
        y_ticks = [(y_pos, lbl) for y_pos, lbl in zip(y_set, q_hdr)]
        y_axis_set.setStyle(tickLength=1, tickFont=self.tick_font)
        y_axis_set.setTicks([y_ticks])

        # other axis properties
        self.h_plot[1, 0].invertX(True)
        self.h_plot[1, 0].showGrid(x=True)

        # -----------------------------------------------------------------------
        # Interaction Data Subplot
        # -----------------------------------------------------------------------

        # field retrieval
        x_lim = v_rng_int[0]
        y_lim_set = self.v_box[1, 0].viewRange()[1]

        # creates the fill markers
        for i in range(n_data):
            # sets the fill item lower limit
            y_fill, y0 = (i + 1) * np.ones(2), i
            if i == 0:
                y0 = y_lim_set[0]
            elif (i + 1) == n_data:
                y_fill[:] = y_lim_set[1]

            # creates the plot item based on type
            if (i % 2) == 0:
                p_item = PlotDataItem(x_lim, y_fill, fillLevel=y0, brush=mkBrush(self.c_stripe_1))
            else:
                p_item = PlotDataItem(x_lim, y_fill, fillLevel=y0, brush=mkBrush(self.c_stripe_2))

            # adds the plot item
            self.h_plot[1, 1].addItem(p_item)

        # creates the dot markers
        x_dot, y_dot = np.meshgrid(x_int, y_set)
        h_dot = ScatterPlotItem(x=x_dot.flatten(),
                                y=y_dot.flatten(), size=self.m_size, brush=mkBrush(self.c_dot))
        self.h_plot[1, 1].addItem(h_dot)

        # creates the detail type plot
        for i in range(len(p_type)):
            y_plt = y_set[p_bool[p_type[i]]]
            x_plt = x_int[i] * np.ones(len(y_plt))
            self.h_plot[1, 1].plot(x_plt, y_plt, pen=self.plt_pen, symbolBrush='k',
                                   symbol='o', symbolpen='k', symbolSize=self.m_size)

        # hides the plot axis
        self.plot_details.getAxis('left').setTextPen('k')
        self.plot_details.getAxis('bottom').setTextPen('k')
        self.v_box[1, 1].setBorder(color='k')

        # copies the data plot tick
        y_axis_details = self.h_plot[1, 1].getAxis('left')
        y_details = np.linspace(0, n_data, len(y_tick_int))
        y_tick_details = [(y_pos, str(int(lbl))) for y_pos, lbl in zip(y_details, y_tick_int)]
        y_axis_details.setTicks([y_tick_details])
        y_axis_details.setStyle(tickFont=self.tick_font)

        # resets the axes limits
        self.v_box[1, 1].setYRange(y_lim_set[0], y_lim_set[1], padding=0)
        self.v_box[1, 1].setXRange(x_lim[0], x_lim[1], padding=0)
        # self.v_box[1, 1].setXRange(0, len(n_count), padding=0.025)

    def get_data_array(self):

        # sets up the metric table
        p = self.get_field
        q_met = self.session_info.get_metric_table()

        match self.unit_type:
            case 'Noise':
                # case is the noisy units
                data_arr = [
                    np.isnan(q_met['nPeaks']) | (q_met['nPeaks'] > p('maxNPeaks')),
                    np.isnan(q_met['nTroughs']) | (q_met['nTroughs'] > p('maxNTroughs')),
                    q_met['waveformBaselineFlatness'] > p('maxWvBaselineFraction'),
                    q_met['scndPeakToTroughRatio'] > p('maxScndPeakToTroughRatio_noise'),
                    ((q_met['waveformDuration_peakTrough'] < p('minWvDuration')) |
                     (q_met['waveformDuration_peakTrough'] > p('maxWvDuration'))),
                ]

                # appends spatial decay specific metrics
                if self.get_field('spDecayLinFit'):
                    data_arr += [q_met.spatialDecaySlope > p('minSpatialDecaySlope')]
                else:
                    data_arr += [((q_met['spatialDecaySlope'] < p('minSpatialDecaySlopeExp')) |
                                  (q_met['spatialDecaySlope'] > p('maxSpatialDecaySlopeExp')))]

            case 'MUA':
                # case is the MUA units
                data_arr = [
                    q_met['percentageSpikesMissing_gaussian'] > p('maxPercSpikesMissing'),
                    q_met['nSpikes'] < p('minNumSpikes'),
                    q_met['fractionRPVs_estimatedTauR'] > p('maxRPVviolations'),
                    q_met['presenceRatio'] < p('minPresenceRatio')
                ]

                # appends distance metrics (if applicable)
                if p('computeDistanceMetrics') and (not np.isnan(p('isoDmin'))):
                    data_arr += [q_met['isoD'] < p('isoDmin'),
                                 q_met['Lratio'] > p('lratioMax')]

                # appends extracted raw waveform metrics (if applicable)
                if p('extractRaw'):
                    data_arr += [q_met['rawAmplitude'] < p('minAmplitude'),
                                 q_met['signalToNoiseRatio'] < p('minSNR')]

                # appends drift correction labels (if applicable)
                if p('computeDrift'):
                    data_arr += [q_met['maxDriftEstimate'] > p('maxDrift')]

                # keep only MUA and single units
                is_keep = np.isin(self.get_field('unit_type'), [1, 2]).flatten()
                data_arr = [x[is_keep] for x in data_arr]

            case 'NonSoma':
                # case is the non-soma units
                data_arr = [
                    ((q_met['troughToPeak2Ratio'] < p('minTroughToPeak2Ratio_nonSomatic')) &
                     (q_met['mainPeak_before_width'] < p('minWidthFirstPeak_nonSomatic')) &
                     (q_met['mainTrough_width'] < p('minWidthMainTrough_nonSomatic')) &
                     (q_met['peak1ToPeak2Ratio'] > p('maxPeak1ToPeak2Ratio_nonSomatic'))) ,
                    q_met['mainPeakToTroughRatio'] > p('maxMainPeakToTroughRatio_nonSomatic')
                ]

        # returns the label array
        return np.transpose(np.array(data_arr))

    def get_data_labels(self):

        p = self.get_field

        match self.unit_type:
            case 'Noise':
                # case is the noisy units
                lbl_arr = [
                    '# Peaks',
                    '# Troughs',
                    'Baseline Flatness',
                    '2nd Peak/Trough',
                    'Duration',
                    'Spatial Decay',
                ]

            case 'MUA':
                # case is the MUA units
                lbl_arr = [
                    '% Missing Spikes',
                    '# Spikes',
                    'Fraction RPVs',
                    'Presence Ratio'
                ]

                # appends distance metrics (if applicable)
                if p('computeDistanceMetrics') and (not np.isnan(p('isoDmin'))):
                    lbl_arr += ['Isolation Dist.', 'l-Ratio']

                # appends extracted raw waveform metrics (if applicable)
                if p('extractRaw'):
                    lbl_arr += ['Amplitude', 'SNR']

                # appends drift correction labels (if applicable)
                if p('computeDrift'):
                    lbl_arr += ['Max Drift']

            case 'NonSoma':
                # case is the non-soma units
                lbl_arr = [
                    '1st Peak/2nd Peak',
                    'Max Peak/Trough'
                ]

        # returns the label array
        return lbl_arr

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
    # Miscellaneous Methods
    # ---------------------------------------------------------------------------

    def get_field(self, p_fld):

        return self.session_info.get_mem_map_field(p_fld)

    def set_plot_view(self, plot_view_new):

        self.plot_view = plot_view_new

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_para(_self):
        _self.update_plot()

    # trace property observer properties
    unit_type = cf.ObservableProperty(update_para)