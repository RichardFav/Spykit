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
from spykit.plotting.utils import PlotWidget, PlotLayout, UnitPlotLayout, dlg_width, dlg_height, info_width, x_gap

# pyqt6 module import
from PyQt6.QtWidgets import QWidget, QGraphicsPathItem
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPainterPath

# pyqtgraph module imports
import pyqtgraph as pg

# plot button fields
b_icon = ['save', 'close']
b_type = ['button', 'button']
tt_lbl = ['Save Figure', 'Close View']

# ----------------------------------------------------------------------------------------------------------------------

xy_pad = 0.02

lbl_font = cw.create_font_obj(9, is_bold=True, font_weight=QFont.Weight.Bold)
tick_font = cw.create_font_obj(8, is_bold=True, font_weight=QFont.Weight.Bold)

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMetricPlot:
"""


class UnitMetricPlot(PlotWidget):
    # fixed fields
    n_plot = 6

    # font objects
    font_title = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold, size=24)

    def __init__(self, session_info):
        # field initialisations
        self.is_updating = True
        self.i_unit = 1

        # creates the class object
        sz_layout = QSize(dlg_width - (info_width + x_gap), dlg_height)
        p_layout = PlotLayout(None, sz_hint=sz_layout)
        super(UnitMetricPlot, self).__init__(
            'unitmet', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl, p_layout=p_layout)
        p_layout.setParent(self)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # property class fields
        self.m_plot = None
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
        self.t_dur = self.session_info.session_props.t_dur

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

        # creates the title widget
        self.title_lbl = cw.create_text_label(None, 'TEST', font=self.font_title, align='center')
        self.title_lbl.setStyleSheet("QLabel { color: white; background-color: rgba(0, 0, 0, 0);}")
        self.plot_layout.addWidget(self.title_lbl)

        # sets up the plot widgets
        self.m_plot = np.empty(self.n_plot, dtype=object)
        self.m_plot[0] = TemplateTrace(self.unit_props, self.i_unit, False)
        self.m_plot[1] = TemplateTrace(self.unit_props, self.i_unit, True)
        self.m_plot[2] = SpatialDecayPlot(self.unit_props, self.i_unit)
        self.m_plot[3] = AutoCorrelPlot(self.unit_props, self.i_unit)
        self.m_plot[4] = SpikeActivityPlot(self.unit_props, self.i_unit, self.t_dur)
        self.m_plot[5] = SpikeAmplitudeHist(self.unit_props, self.i_unit)

        # adds the plot widgets
        for mp in self.m_plot:
            mp.update_unit_index(self.i_unit)
            # mp.setStyleSheet("border: 1px solid white;")
            self.plot_layout.addWidget(mp)

        # updates the plot title
        self.update_plot_config()
        self.update_plot_title()

    # ---------------------------------------------------------------------------
    # Parameter Update Functions
    # ---------------------------------------------------------------------------

    def plot_update(self, p_str):

        match p_str:
            case 'i_unit':
                # case is the unit index
                self.update_unit_index()

            case 'show_thresh':
                # case is showing the threshold markers
                self.update_show_thresh()

            case 'show_grid':
                # case is showing the plot grid
                self.update_show_grid()

    def update_plot_config(self):

        # hides all the current plot items
        for mp in self.m_plot:
            mp.hide()

        # sets up the new grid configuration
        c_id = deepcopy(self.unit_props.obj_rconfig.c_id)
        c_id[c_id > 0] += 1

        # updates the grid
        g_id = np.vstack((np.ones((1, c_id.shape[1]), dtype=int), c_id))

        # updates the plot layout
        self.plot_layout.updateID(g_id)
        self.plot_layout.activate()

    def update_unit_index(self):

        # updates the main plot fields
        self.update_plot_title()

        # updates the unit index for each plot
        for mp in self.m_plot:
            mp.update_unit_index(self.i_unit)

    def update_show_thresh(self):

        # updates the threshold marker visibility for each plot
        for mp in self.m_plot:
            hp.update_show_thresh(self.show_thresh)

    def update_show_grid(self):

        # updates the grid visibility for each plot
        for mp in self.m_plot:
            mp.update_axes_grid(self.show_grid)

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

        # histogram parameter fields
        self.is_updating = True
        self.i_unit = int(self.unit_props.get_para_value('i_unit'))
        self.show_grid = bool(self.unit_props.get_para_value('show_grid'))
        self.show_metric = bool(self.unit_props.get_para_value('show_metric'))
        self.is_updating = False

        # updates the plot view
        self.init_plot_view()

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_field(self, p_fld):

        return self.session_info.get_mem_map_field(p_fld)

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def para_update(p_str, _self):
        if _self.is_updating:
            return

        _self.plot_update(p_str)

    # property observer properties
    i_unit = cf.ObservableProperty(pfcn(para_update, 'i_unit'))
    show_grid = cf.ObservableProperty(pfcn(para_update, 'show_grid'))
    show_metric = cf.ObservableProperty(pfcn(para_update, 'show_metric'))


# ----------------------------------------------------------------------------------------------------------------------

"""
    TemplateTrace:
"""

class TemplateTrace(UnitPlotLayout):
    # static class fields
    n_plot = 20
    n_col = 4
    n_row = 5
    p_scl = 1.2
    y_ofs = 0.5

    # pen objects
    l_pen_path = pg.mkPen(color=(255, 0, 0), width=2)
    l_pen_wform = pg.mkPen(color=(0, 255, 0), width=4)

    def __init__(self, unit_props, i_unit, is_raw):
        super(TemplateTrace, self).__init__(unit_props, i_unit)

        # field initialisation
        self.pk_ch = None
        self.ch_pos = None
        self.is_raw = is_raw

        # initialises the plot widgets
        self.init_other_class_fields()
        self.init_plot_widgets()

    def init_other_class_fields(self):

        # field retrieval
        self.n_pts = self.unit_props.get_mem_map_field('n_pts')
        self.ch_pos = self.unit_props.get_mem_map_field('ch_pos')

        # sets the peak channel indices
        i_col_cmax = self.unit_props.get_metric_col_index('maxChannels')
        self.pk_ch = self.unit_props.get_mem_map_field('q_met')[:, i_col_cmax].astype(int)

        # memory allocation
        self.xi_plt = np.array(range(self.n_pts))
        self.x_plt = np.tile(self.xi_plt / self.xi_plt[-1], (self.n_plot, 1))

        # sets up the plot connection array
        self.c_plt = np.ones((self.n_plot, self.n_pts), dtype=bool)
        self.c_plt[:, -1] = False

    def init_plot_widgets(self):

        # creates the plot axes/metric legend
        self.create_plot_axes()
        self.create_metric_legend()

    # ---------------------------------------------------------------------------
    # PlotWidget Setup Functions
    # ---------------------------------------------------------------------------

    def create_plot_axes(self):

        # creates the plot path item
        self.plot_path = QGraphicsPathItem(QPainterPath())
        self.plot_path.setPen(self.l_pen_path)
        self.addItem(self.plot_path)

        # creates the template waveform plot
        self.plot_wform = self.plot(
            self.xi_plt,
            np.zeros(self.n_pts),
            pen = self.l_pen_wform,
        )

        # resets the axis tick marks
        self.plotItem.getAxis('left').setTicks([[]])
        self.plotItem.getAxis('bottom').setTicks([[]])

        # creates the sub-plot title
        t_str = 'Mean Raw Waveform' if self.is_raw else 'Template Waveform'
        self.setTitle(t_str, bold=True)

    def create_metric_legend(self):

        pass

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_unit_index(self, i_unit_new):

        # updates the unit index
        self.i_unit = i_unit_new

        # retrieves the trace coordinates
        x_sig, y_sig, i_ch_w, is_ok = self.get_trace_coords()

        # updates the plot paths/traces
        unit_path = pg.arrayToQPath(
            x_sig[is_ok, :].flatten(),
            y_sig[is_ok, :].flatten(),
            self.c_plt[is_ok, :].flatten())
        self.plot_path.setPath(unit_path)

        # updates the waveform trace
        ii = is_ok[np.where(is_ok == i_ch_w)[0][0]]
        self.plot_wform.setData(x_sig[ii, :], y_sig[ii, :])

        # resets the axes limits
        self.v_box.setXRange(self.x_lim[0], self.x_lim[1], padding=xy_pad)
        self.v_box.setYRange(self.y_lim[0], self.y_lim[1], padding=xy_pad)

    def update_show_metric(self, show_metric):

        pass

    def update_axes_grid(self, show_grid):

        pass

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_channel_waveforms(self, i_ch):

        # pre-calculations
        i_unit_f = self.i_unit - 1

        # returns the waveforms based on unit/channel indices
        if self.is_raw:
            return self.unit_props.get_mem_map_field('avg_sig')[i_unit_f, i_ch, :]
        else:
            return self.unit_props.get_mem_map_field('t_wform')[i_unit_f, :, i_ch]

    def get_neighbouring_channels(self, i_pk_ch):

        # calculates the distance from the max channel to all others
        D = np.sum(np.abs(self.ch_pos - self.ch_pos[i_pk_ch, :]) ** 2, axis=1) ** 0.5

        return np.sort(np.argsort(D)[:self.n_plot])

    def get_trace_coords(self):

        # determines channels closest to likely location
        i_unit_f = self.i_unit - 1
        i_pk_ch = self.pk_ch[i_unit_f] - 1

        # determines the neighbouring channels
        i_ch_n = self.get_neighbouring_channels(i_pk_ch)
        i_ch_w = np.where(i_ch_n == i_pk_ch)[0][0]
        y_sig = self.get_channel_waveforms(i_ch_n)

        # calculates the x/y axis scale factors
        ch_pos_n = self.ch_pos[i_ch_n, :]
        ch_x, i_x = np.unique(ch_pos_n[:, 0], return_inverse=True)
        ch_y, i_y = np.unique(ch_pos_n[:, 1], return_inverse=True)

        # calculates the trace width/height scale factors
        w_pos = np.min(np.diff(ch_x)) if (len(ch_x) > 1) else 1
        h_pos = np.min(np.diff(ch_y)) if (len(ch_y) > 1) else 1

        # calculates the channel position range
        self.x_lim = np.array([ch_x[0], ch_x[-1]]) + (self.p_scl * w_pos / 2) * np.array([-1, 1])
        self.y_lim = np.array([ch_y[0], ch_y[-1]]) + (self.p_scl * h_pos / 2) * np.array([-1, 1])

        # scales the waveforms to the unit channel signal amplitude
        y_wform = y_sig[i_ch_w, :]
        y_min, y_max = np.min(y_wform), np.max(y_wform)
        y_sig = (y_sig - y_min) / (y_max - y_min)
        is_ok = np.where((np.min(y_sig, axis=1) > -self.y_ofs) &
                         (np.max(y_sig, axis=1) < (1 + self.y_ofs)))[0]

        # returns the scaled waveform signals
        x_wform = self.p_scl * (self.x_plt - 1 / 2) * w_pos + ch_pos_n[:, 0].reshape(-1, 1)
        y_wform = self.p_scl * (y_sig - 1 / 2) * h_pos + ch_pos_n[:, 1].reshape(-1, 1)
        return x_wform, y_wform, i_ch_w, is_ok

# ----------------------------------------------------------------------------------------------------------------------

"""
    SpatialDecayPlot:
"""

class SpatialDecayPlot(UnitPlotLayout):
    # widget dimensions
    n_fit = 100

    # plot properties
    sym = 'o'
    sym_size = 10

    # pen/brush objects
    l_pen_loc = 'g'
    l_pen_trend = pg.mkPen('r', width=2)
    l_brush_loc = (100, 255, 100, 100)

    def __init__(self, unit_props, i_unit):
        super(SpatialDecayPlot, self).__init__(unit_props, i_unit)

        # plot data fields
        self.x_plt = None
        self.y_plt = None

        # initialises the plot widgets
        self.init_other_class_fields()
        self.init_plot_widgets()

    def init_other_class_fields(self):

        # field retrieval
        i_col_sp = self.unit_props.get_metric_col_index('spatialDecaySlope')

        # field retrieval
        self.x_decay_sp = self.unit_props.get_mem_map_field('x_decay_sp')
        self.y_decay_sp = self.unit_props.get_mem_map_field('y_decay_sp')
        self.k_decay_sp = self.unit_props.get_mem_map_field('k_decay_sp')
        self.h_decay_sp = self.unit_props.get_mem_map_field('q_met')[:, i_col_sp]
        self.is_lin_fit = bool(self.unit_props.get_mem_map_field('spDecayLinFit'))

        # memory allocation
        n_unit = len(self.k_decay_sp)
        self.x_fit = np.empty(n_unit, dtype=object)
        self.y_fit = np.empty(n_unit, dtype=object)
        self.has_fit = np.zeros(n_unit, dtype=bool)

        # other field initialisations
        self.x_lim = [0, np.max(self.y_decay_sp[:, -1])]
        self.y_lim = [0, 1.0]

    def init_plot_widgets(self):

        # creates the plot axes/metric legend
        self.create_plot_axes()
        self.create_metric_legend()

    # ---------------------------------------------------------------------------
    # PlotWidget Setup Functions
    # ---------------------------------------------------------------------------

    def create_plot_axes(self):

        # creates the plot line
        self.plot_loc = self.plot(
            [0],
            [0],
            pen=None,
            symbol=self.sym,
            symbolSize=self.sym_size,
            symbolPen=self.l_pen_loc,
            symbolBrush=self.l_brush_loc
        )

        # creates the trend line
        self.plot_trend = self.plot(
            [0],
            [0],
            pen=self.l_pen_trend
        )

        # updates the axis font properties
        self.getAxis('left').label.setFont(lbl_font)
        self.getAxis('bottom').label.setFont(lbl_font)
        self.getAxis("left").setTickFont(tick_font)
        self.getAxis("bottom").setTickFont(tick_font)

    def create_metric_legend(self):

        pass

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_unit_index(self, i_unit):

        # field update
        self.i_unit = i_unit

        # field retrieval
        self.x_plt = self.y_decay_sp[self.i_unit - 1, :]
        self.y_plt = self.x_decay_sp[self.i_unit - 1, :]

        # updates the plot markers
        self.update_scatter_plot()
        self.update_trend_line()
        self.update_plot_title()

        # updates the other plot properties
        self.update_axes_grid(bool(self.unit_props.get_para_value('show_grid')))

    def update_scatter_plot(self):

        # updates the plot data
        self.plot_loc.setData(x=self.x_plt, y=self.y_plt)

        # resets the axes limits
        self.v_box.setXRange(self.x_lim[0], self.x_lim[1],padding=xy_pad)
        self.v_box.setYRange(self.y_lim[0], self.y_lim[1],padding=4 * xy_pad)

    def update_trend_line(self):

        i_unit_f = self.i_unit - 1

        if not self.has_fit[i_unit_f]:
            # sets up the x fit data values
            A, m = self.k_decay_sp[i_unit_f], self.h_decay_sp[i_unit_f]
            self.x_fit[i_unit_f] = np.linspace(self.x_plt[0], self.x_plt[-1], self.n_fit)

            if self.is_lin_fit:
                # case is a linear fit
                self.y_fit[i_unit_f] = A + m * self.x_fit[i_unit_f]
            else:
                self.y_fit[i_unit_f] = A * np.exp(-m * self.x_fit[i_unit_f])

        # updates the plot data
        self.plot_trend.setData(x=self.x_fit[i_unit_f], y=self.y_fit[i_unit_f])

    def update_plot_title(self):

        # sets the axis labels
        self.setTitle('Spatial Decay', bold=True)
        self.plotItem.getAxis('bottom').setLabel('Distance (um)')
        self.plotItem.getAxis('left').setLabel('Amplitude')

    def update_show_metric(self, show_metric):

        pass

    def update_axes_grid(self, show_grid):

        self.plotItem.showGrid(x=show_grid, y=show_grid)

# ----------------------------------------------------------------------------------------------------------------------

"""
    AutoCorrelPlot:
"""

class AutoCorrelPlot(UnitPlotLayout):
    # fixed scalar values
    t_win = 50
    b_sz = 1
    t_win_mu = 1e3
    b_sz_mu = 100

    # pen objects
    l_pen_marker = pg.mkPen(color=(255, 0, 0), width=2, style=cf.pen_style['Dash'])

    def __init__(self, unit_props, i_unit):
        super(AutoCorrelPlot, self).__init__(unit_props, i_unit)

        # field initialisations
        self.cc_gram = None
        self.x_cc_gram = None

        # initialises the plot widgets
        self.init_other_class_fields()
        self.init_plot_widgets()

    def init_other_class_fields(self):

        # memory allocation
        self.cc_gram = np.empty(self.unit_props.n_unit, dtype=object)
        self.cc_gram_mu = np.zeros(self.unit_props.n_unit, dtype=float)

        # retrieves the
        q_met = self.unit_props.get_mem_map_field('q_met')
        self.i_tauR = q_met[:, self.unit_props.get_metric_col_index('RPV_tauR_estimate')].astype(int)
        self.y_tauR = q_met[:, self.unit_props.get_metric_col_index('fractionRPVs_estimatedTauR')]

        # ccg bin counts
        self.n_bin = int(self.t_win / self.b_sz)
        self.n_bin_mu = int(self.t_win_mu / self.b_sz_mu)

        # resets the axes limits
        self.v_box.setXRange(0, self.n_bin, padding=xy_pad)

    def init_plot_widgets(self):

        # creates the plot axes/metric legend
        self.create_plot_axes()
        self.create_metric_legend()

    # ---------------------------------------------------------------------------
    # PlotWidget Setup Functions
    # ---------------------------------------------------------------------------

    def create_plot_axes(self):

        # field retrieval
        xi_bg = np.array(range(self.n_bin))
        y_bg = np.zeros(self.n_bin, dtype=int)

        # creates the bar-graph object
        self.bg_item = pg.BarGraphItem(
            x=xi_bg,
            height=y_bg,
            width=1,
            pen='w',
            brush=(0,0,255,150),
        )

        # updates the plot widget item/title
        self.addItem(self.bg_item)

        # creates the horizontal marker line
        self.plot_horz = self.plot(
            [0, self.n_bin],
            [0, 0],
            pen=self.l_pen_marker
        )

        # creates the horizontal marker line
        self.plot_vert = self.plot(
            [0, 0],
            [0, 0],
            pen=self.l_pen_marker
        )

        # updates the axis font properties
        self.getAxis('left').label.setFont(lbl_font)
        self.getAxis('bottom').label.setFont(lbl_font)
        self.getAxis("left").setTickFont(tick_font)
        self.getAxis("bottom").setTickFont(tick_font)

    def create_metric_legend(self):

        pass

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_unit_index(self, i_unit_new):

        # updates the unit index
        self.i_unit = i_unit_new

        # updates the plot markers
        self.update_cc_gram()
        self.update_plot_title()

        # updates the other plot properties
        self.update_axes_grid(bool(self.unit_props.get_para_value('show_grid')))

    def update_cc_gram(self):

        # field retrieval
        i_unit_f = self.i_unit - 1

        # ensures the unit cc-gram values are calculated
        if self.cc_gram[i_unit_f] is None:
            # retrieves the spike time for the current unit
            t_spike = self.unit_props.get_mem_map_field('t_spike')
            spk_cluster = self.unit_props.get_mem_map_field('spk_cluster')
            t_unit = t_spike[spk_cluster == self.i_unit] * 1000

            # calculates the fine unit cc-gram
            cc_g = cf.calc_ccgram(t_unit, t_unit, win_sz0=self.n_bin, bin_size=self.b_sz)
            self.cc_gram[i_unit_f] = np.flip(cc_g[0][:self.n_bin])

            # calculates the asymptotic cc-gram value
            cc_g_mu = cf.calc_ccgram(t_unit, t_unit, win_sz0=self.n_bin_mu, bin_size=self.b_sz_mu)
            self.cc_gram_mu[i_unit_f] = np.nanmean(cc_g_mu[0][(self.n_bin_mu - 1):])

            # calculates the mean
            if self.x_cc_gram is None:
                self.x_cc_gram = cc_g[1][(self.n_bin - 1):] + 0.5

        # updates the histogram values
        self.bg_item.setOpts(
            x = self.x_cc_gram,
            height = self.cc_gram[i_unit_f],
        )

        # resets the upper limit
        y_max = np.max(self.cc_gram[i_unit_f])
        if y_max > 0:
            y_max_h = np.floor(math.log10(y_max) - 1)
            y_max_f = cf.round_up(y_max, -y_max_h)
        else:
            y_max_f = 1

        # updates the y-axes range
        self.v_box.setYRange(0., y_max_f, padding=4 * xy_pad)

        # updates the asymptotic marker
        self.plot_horz.setData(x=[0, self.n_bin], y=self.cc_gram_mu[i_unit_f] * np.ones(2))
        self.plot_vert.setData(x=self.x_cc_gram[self.i_tauR[i_unit_f]] * np.ones(2), y=[0, y_max_f])

    def update_show_metric(self, show_metric):

        pass

    def update_axes_grid(self, show_grid):

        self.plotItem.showGrid(x=show_grid, y=show_grid)

    def update_plot_title(self):

        # sets the axis labels
        self.setTitle('Auto-Correlogram', bold=True)
        self.plotItem.getAxis('bottom').setLabel('Time (ms)')
        self.plotItem.getAxis('left').setLabel('Frequency')

# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeActivityPlot:
"""

class SpikeActivityPlot(UnitPlotLayout):
    # pen/brush objects
    rpv_col = '#FFFF00'
    freq_col = '#008000'
    spike_col = (0, 0, 255)
    l_pen_rpv = pg.mkPen(color=rpv_col, width=1)
    l_pen_freq = pg.mkPen(color=freq_col, width=3)
    l_brush_spike = pg.mkBrush(color=spike_col)

    # plot properties
    sym = 'o'
    sym_size = 6

    # other fixed scalars
    py_max = 1.1
    n_bin_min = 30

    def __init__(self, unit_props, i_unit, t_dur):
        super(SpikeActivityPlot, self).__init__(unit_props, i_unit)

        # input arguments
        self.t_dur = np.floor(t_dur)

        # initialises the plot widgets
        self.init_other_class_fields()
        self.init_plot_widgets()

    def init_other_class_fields(self):

        # histogram bin size
        self.n_bin = self.n_bin_min if (self.t_dur < self.n_bin_min) else int(self.t_dur)
        self.xi_freq = np.linspace(0, self.t_dur, self.n_bin + 1)

        # other class fields
        self.s_freq = np.empty((self.unit_props.n_unit, 2), dtype=object)
        self.t_spike = np.empty((self.unit_props.n_unit, 3), dtype=object)

    def init_plot_widgets(self):

        # creates the plot axes/metric legend
        self.create_plot_axes()
        self.create_metric_legend()

    # ---------------------------------------------------------------------------
    # PlotWidget Setup Functions
    # ---------------------------------------------------------------------------

    def create_plot_axes(self):

        # creates the spike plot markers
        self.plot_spike = self.plot(
            [0],
            [0.25],
            pen=None,
            symbol=self.sym,
            symbolSize=self.sym_size,
            symbolPen=None,
            symbolBrush=self.l_brush_spike
        )

        # creates the rpv plot markers
        self.plot_rpv = self.plot(
            [0],
            [0.5],
            pen=None,
            symbol=self.sym,
            symbolSize=self.sym_size,
            symbolPen=self.l_pen_rpv,
            symbolBrush=self.l_brush_spike
        )

        # creates the 2nd plot axes
        self.v_box2 = pg.ViewBox()

        # sets the left axes properties
        self.plotItem.showAxis('right')
        self.plotItem.scene().addItem(self.v_box2)
        self.plotItem.getAxis('right').linkToView(self.v_box2)
        self.v_box2.setXLink(self.plotItem)

        # creates the spiking frequency plot
        self.plot_freq = self.plot(
            [0, 1],
            [0, 1],
            pen = self.l_pen_freq,
        )
        self.v_box2.addItem(self.plot_freq)

        # sets the view resize function
        self.plotItem.vb.sigResized.connect(self.update_view_range)

        # updates the axis font properties
        self.getAxis('left').label.setFont(lbl_font)
        self.getAxis('right').label.setFont(lbl_font)
        self.getAxis('bottom').label.setFont(lbl_font)
        self.getAxis("left").setTickFont(tick_font)
        self.getAxis("right").setTickFont(tick_font)
        self.getAxis("bottom").setTickFont(tick_font)

    def create_metric_legend(self):

        pass

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_unit_index(self, i_unit_new):

        # updates the unit index
        self.i_unit = i_unit_new

        # updates the plot data/title
        self.update_unit_spikes()
        self.update_spike_freq()
        self.update_plot_title()

    def update_unit_spikes(self):

        # field retrieval
        i_unit_f = self.i_unit - 1

        if self.t_spike[i_unit_f, 0] is None:
            # retrieves the units spike
            t_spike = self.unit_props.get_mem_map_field('t_spike')
            is_unit = self.unit_props.get_mem_map_field('spk_cluster') == self.i_unit
            self.t_spike[i_unit_f, 0] = t_spike[is_unit]
            self.t_spike[i_unit_f, 1] = self.unit_props.get_mem_map_field('t_amp')[is_unit]

            # determines the spike feasibility
            t_spike_isi = np.diff(self.t_spike[i_unit_f, 0])
            self.t_spike[i_unit_f, 2] = np.ones(len(self.t_spike[i_unit_f, 0]), dtype=bool)
            self.t_spike[i_unit_f, 2][:-1] = t_spike_isi >= self.unit_props.get_mem_map_field('tauR_valuesMin')

            # calculates the spiking frequency
            n_count, x = np.histogram(
                self.t_spike[i_unit_f, 0], bins=self.n_bin, range=[0, self.t_dur])
            self.s_freq[i_unit_f, 0] = (x[1:] + x[:-1]) / 2
            self.s_freq[i_unit_f, 1] = self.n_bin * n_count / self.t_dur

        # updates the feasible plot spikes
        x, y, is_ok = self.t_spike[i_unit_f, :]
        self.plot_spike.setData(x[is_ok], y[is_ok])
        self.plot_rpv.setData(x[~is_ok], y[~is_ok])

        # resets the axes view range
        self.v_box.setXRange(0., self.t_dur, padding=xy_pad)
        self.v_box.setYRange(0., self.py_max * np.max(y), padding=2 * xy_pad)

    def update_spike_freq(self):

        # field retrieval
        i_unit_f = self.i_unit - 1

        # resets the plot data
        x, y = self.get_step_data(self.s_freq[i_unit_f, 0], self.s_freq[i_unit_f, 1])
        self.plot_freq.setData(x, y)

        # resets the axes view range
        self.v_box2.setYRange(0., self.py_max * np.max(y), padding=2 * xy_pad)

    def update_show_metric(self, show_metric):

        pass

    def update_axes_grid(self, show_grid):

        self.plotItem.showGrid(x=show_grid, y=show_grid)

    def update_view_range(self):

        self.v_box2.setGeometry(self.plotItem.vb.sceneBoundingRect())
        self.v_box2.linkedViewChanged(self.plotItem.vb, self.v_box2.XAxis)

    def update_plot_title(self):

        # sets the axis labels
        self.setTitle('Spike Activity', bold=True)
        self.plotItem.getAxis('bottom').setLabel('Time (s)')
        self.plotItem.getAxis('left').setLabel('Spike Amplitude', color=self.rpv_col)
        self.plotItem.getAxis('right').setLabel('Firing Rate (Hz)', color=self.freq_col)

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_step_data(self, x, y):

        # resets the x-data values
        x_new = np.zeros(2 * len(x))
        x_new[0::2] = x
        x_new[1:-1:2] = x[1:]
        x_new[-1] = x[-1]

        # resets the y-data values
        y_new = np.zeros(2 * len(x))
        y_new[0::2] = y
        y_new[1:-1:2] = y[:-1]
        y_new[-1] = y[-1]

        return x_new - (x[1] - x[0]) / 2, y_new

# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeAmplitudeHist:
"""

class SpikeAmplitudeHist(UnitPlotLayout):
    # pen objects
    l_pen_fit = pg.mkPen(color=(0, 255, 0), width=3)
    l_brush_hist = pg.mkBrush(color=(0, 0, 255))

    def __init__(self, unit_props, i_unit):
        super(SpikeAmplitudeHist, self).__init__(unit_props, i_unit)

        # initialises the plot widgets
        self.init_plot_widgets()

    def init_plot_widgets(self):

        # creates the plot axes/metric legend
        self.create_plot_axes()
        self.create_metric_legend()

    # ---------------------------------------------------------------------------
    # PlotWidget Setup Functions
    # ---------------------------------------------------------------------------

    def create_plot_axes(self):

        # creates the bar-graph object
        self.bg_item = pg.BarGraphItem(
            x0=0,
            height=1,
            width=1,
            pen='w',
            brush=self.l_brush_hist,
        )

        # updates the plot widget item/title
        self.addItem(self.bg_item)

        # creates the template waveform plot
        self.plot_fit = self.plot(
            [0],
            [0],
            pen = self.l_pen_fit,
        )

        # updates the axis font properties
        self.getAxis('left').label.setFont(lbl_font)
        self.getAxis('bottom').label.setFont(lbl_font)
        self.getAxis("left").setTickFont(tick_font)
        self.getAxis("bottom").setTickFont(tick_font)

    def create_metric_legend(self):

        pass

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_unit_index(self, i_unit_new):

        # updates the unit index
        self.i_unit = i_unit_new

        # updates the plot data/title
        self.update_plot_data()
        self.update_plot_title()

    def update_plot_data(self):

        # retrieves the plot values
        x_bin, y_bin, y_fit = self.get_plot_value()

        # updates the histogram values
        if len(x_bin):
            # case is there are valid values to plot
            self.bg_item.setOpts(
                y = x_bin,
                height = x_bin[1] - x_bin[0],
                width = y_bin,
            )

            # updates the plot values
            self.plot_fit.setData(y_fit, x_bin)

            # updates the y-axes range
            x_max = np.max([np.max(y_fit), np.max(y_bin)])
            self.v_box.setXRange(0., 1.05 * x_max, padding=xy_pad)
            self.v_box.setYRange(0., x_bin[-1], padding=2 * xy_pad)

        else:
            # case is there are valid values to plot
            self.bg_item.setOpts(
                y = [np.nan],
                width = [np.nan],
            )

            # updates the plot values
            self.plot_fit.setData([np.nan], [np.nan])

            # updates the y-axes range
            self.v_box.setXRange(0., 1, padding=xy_pad)
            self.v_box.setYRange(0., 1, padding=2 * xy_pad)

    def update_show_metric(self, show_metric):

        pass

    def update_axes_grid(self, show_grid):

        self.plotItem.showGrid(x=show_grid, y=show_grid)

    def update_plot_title(self):

        # sets the axis labels
        self.setTitle('Spike Amplitude', bold=True)
        self.getAxis('bottom').setLabel('Count')
        self.getAxis('left').setLabel('Amplitude')

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_plot_value(self):

        # field retrieval
        i_unit_f = self.i_unit - 1

        # retrieves the plot values
        x_bin = self.unit_props.get_mem_map_field('x_bin_amp')[i_unit_f, :]
        y_bin = self.unit_props.get_mem_map_field('y_bin_amp')[i_unit_f, :]
        y_fit = self.unit_props.get_mem_map_field('y_gauss_amp')[i_unit_f, :]

        # returns the non-NaN values
        ii = ~np.isnan(x_bin)
        return x_bin[ii], y_bin[ii], y_fit[ii]