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
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QFont

# pyqtgraph module imports
import pyqtgraph as pg

# plot button fields
b_icon = ['save', 'close']
b_type = ['button', 'button']
tt_lbl = ['Save Figure', 'Close View']

# ----------------------------------------------------------------------------------------------------------------------

xy_pad = 0.02

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMetricPlot:
"""


class UnitMetricPlot(PlotWidget):
    # fixed fields
    n_plot = 5

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
        self.m_plot[0] = TemplateTrace(self.unit_props, self.i_unit, True)
        self.m_plot[1] = TemplateTrace(self.unit_props, self.i_unit, False)
        self.m_plot[2] = SpatialDecayPlot(self.unit_props, self.i_unit)
        self.m_plot[3] = AutoCorrelPlot(self.unit_props, self.i_unit)
        self.m_plot[4] = SpikeActivityPlot(self.unit_props, self.i_unit)

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
    def __init__(self, unit_props, i_unit, is_mean):
        super(TemplateTrace, self).__init__(unit_props, i_unit)

        # field initialisation
        self.is_mean = is_mean
        self.is_updating = True

        # initialises the plot widgets
        self.init_plot_widgets()

        # resets the update flag
        self.is_updating = False

    def init_plot_widgets(self):

        # creates the plot axes/metric legend
        self.create_plot_axes()
        self.create_metric_legend()

    # ---------------------------------------------------------------------------
    # PlotWidget Setup Functions
    # ---------------------------------------------------------------------------

    def create_plot_axes(self):

        pass

    def create_metric_legend(self):

        pass

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_unit_index(self, i_unit_new):

        # updates the unit index
        self.i_unit = i_unit_new

    def update_show_metric(self, show_metric):

        pass

    def update_axes_grid(self, show_grid):

        self.plotItem.showGrid(x=show_grid, y=show_grid)

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
        self.getAxis('bottom').setLabel('Distance (um)')
        self.getAxis('left').setLabel('Amplitude')

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

    def init_plot_widgets(self):

        # creates the plot axes/metric legend
        self.create_plot_axes()
        self.create_metric_legend()

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
            self.cc_gram[i_unit_f] = cc_g[0][(self.n_bin - 1):]

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
        y_max_h = np.floor(math.log10(y_max) - 1)
        y_max_f = cf.round_up(y_max, -y_max_h)
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
        self.getAxis('bottom').setLabel('Time (ms)')
        self.getAxis('left').setLabel('Freq.')

# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeActivityPlot:
"""

class SpikeActivityPlot(UnitPlotLayout):
    def __init__(self, unit_props, i_unit):
        super(SpikeActivityPlot, self).__init__(unit_props, i_unit)

        # field initialisation
        self.is_updating = True

        # initialises the plot widgets
        self.init_plot_widgets()

        # resets the update flag
        self.is_updating = False

    def init_plot_widgets(self):

        # creates the plot axes/metric legend
        self.create_plot_axes()
        self.create_metric_legend()

    # ---------------------------------------------------------------------------
    # PlotWidget Setup Functions
    # ---------------------------------------------------------------------------

    def create_plot_axes(self):

        pass

    def create_metric_legend(self):

        pass

    # ---------------------------------------------------------------------------
    # Class Object Update Functions
    # ---------------------------------------------------------------------------

    def update_unit_index(self, i_unit_new):

        # updates the unit index
        self.i_unit = i_unit_new

    def update_show_metric(self, show_metric):

        pass

    def update_axes_grid(self, show_grid):

        self.plotItem.showGrid(x=show_grid, y=show_grid)