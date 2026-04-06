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
from spykit.plotting.utils import PlotWidget, setup_default_layout

# pyqt6 module import
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, Qt

# pyqtgraph modules
import pyqtgraph as pg
from pyqtgraph.Qt.QtWidgets import QGraphicsPathItem

# plot button fields
b_icon = ['save', 'close']
b_type = ['button', 'button']
tt_lbl = ['Save Figure', 'Close View']

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    WaveFormPlot:
"""


class WaveFormPlot(PlotWidget):
    # font sizes
    title_size0 = 22

    # pen objects
    l_pen_sel = pg.mkPen(color=(255, 0, 0), width=4)

    def __init__(self, session_info):
        # creates the class object
        p_layout = setup_default_layout()
        super(WaveFormPlot, self).__init__(
            'waveform', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl, p_layout=p_layout)
        p_layout.setParent(self)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # field initialisations
        self.is_updating = True
        self.i_unit = 1

        # other class fields
        self.has_plot = False
        self.show_grid = False
        self.i_type_sel = None
        self.bg_widget = QWidget()
        self.tr_col = cf.get_colour_value('g')

        # initialises the other class fields
        self.init_class_fields()
        self.init_plot_view()
        self.update_plot()

        # resets the initialisation flag
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # field retrieval
        self.l_size = self.plot_layout.sizeHint()
        self.title_size = '{0}pt'.format(self.title_size0)
        self.t0 = np.array(range(self.get_field('n_pts')))

        # field initialisations
        if self.get_field('splitGoodAndMua_NonSomatic'):
            self.unit_lbl = ['Noise', 'Somatic Good', 'Somatic MUA', 'Non-somatic Good', 'Non-somatic MUA']
        else:
            self.unit_lbl = ['Noise', 'Good', 'MUA', 'Non-Somatic']

        # memory allocation
        self.n_plt = len(self.unit_lbl)
        self.unit_type = np.ones(self.n_plt, dtype=bool)
        self.h_pen_tr = pg.mkPen(self.tr_col, width=1)

        # background widget properties
        self.bg_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.plot_layout.addWidget(self.bg_widget)

        # creates the background widget
        self.plot_layout.setSpacing(5)
        self.plot_layout.setDimOffset(36, 1)

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = pfcn(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)
            pb.raise_()

    def init_plot_view(self):

        # memory allocation
        d_val = np.zeros(1)
        self.h_plot = np.empty(self.n_plt, dtype=object)
        self.h_plot_sel = np.empty(self.n_plt, dtype=object)

        # creates the waveform subplots
        for i_type in range(self.n_plt):
            # creates the waveform plot widget
            self.h_plot[i_type] = pg.PlotWidget()
            self.h_plot[i_type].hideButtons()
            self.plot_layout.addWidget(self.h_plot[i_type])

            # creates the unit waveform traces
            h_path = pg.arrayToQPath(d_val, d_val)
            h_item = QGraphicsPathItem(h_path)
            self.h_plot[i_type].addItem(h_item)

            # creates the unit selection trace
            h_path_sel = pg.arrayToQPath(d_val, d_val)
            h_item_sel = QGraphicsPathItem(h_path_sel)
            self.h_plot[i_type].addItem(h_item_sel)

            # sets the axes properties
            h_plt_item = self.h_plot[i_type].getPlotItem()
            h_plt_item.showAxes(True, False)
            h_plt_item.layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
            h_plt_item.vb.setXRange(0, self.t0[-1])

            for ax_t in ['left', 'bottom', 'right', 'top']:
                # resets the axes properties
                self.h_plot[i_type].getAxis(ax_t).setStyle(tickLength=0)

                # shows the right/top axes
                if ax_t in ['right', 'top']:
                    h_plt_item.showAxis(ax_t)

        # creates the unit type traces
        self.reset_unit_traces()

    def reset_unit_traces(self):

        # field retrieval
        u_type = np.array(self.get_field('unit_type'))
        y_spike = np.array(self.get_field('y_spike_unit'))

        # creates the waveform traces
        for i_type in range(self.n_plt):
            # sets the waveform plot points
            is_unit = u_type[:, 0] == i_type
            t_plt = np.tile(self.t0, sum(is_unit))
            y_plt = y_spike[is_unit, :].flatten()

            # sets up the connectivity array
            c_arr = np.ones((sum(is_unit), len(self.t0)), dtype=np.ubyte)
            c_arr[:, -1] = 0

            # creates the unit waveform traces
            hp = self.h_plot[i_type].plotItem.items[0]
            hp.setPath(pg.arrayToQPath(t_plt, y_plt, c_arr.flatten()))

            # sets the axes properties
            if len(y_plt):
                h_plt_item = self.h_plot[i_type].getPlotItem()
                h_plt_item.vb.setYRange(np.min(y_plt), np.max(y_plt))

    # ---------------------------------------------------------------------------
    # PLot View Methods
    # ---------------------------------------------------------------------------

    def update_plot(self):

        # updates the axes grids
        self.update_plot_config()
        self.update_selected_trace()
        self.update_trace_colour()
        self.update_axes_grid()

    def update_selected_trace(self):

        # hides the unit (if one is already selected)
        if self.i_type_sel is not None:
            self.h_plot[self.i_type_sel].plotItem.items[1].hide()

        # field retrieval
        u_type = np.array(self.get_field('unit_type'))
        y_spike = np.array(self.get_field('y_spike_unit'))

        # resets the class fields
        self.i_type_sel = u_type[self.i_unit - 1][0]

        # resets the selected trace plot
        hp = self.h_plot[self.i_type_sel].plotItem.items[1]
        hp.setPath(pg.arrayToQPath(self.t0, y_spike[self.i_unit - 1, :]))
        hp.setPen(self.l_pen_sel)
        hp.show()

    def update_plot_config(self):

        # determines the unit configuration
        i_unit = np.where(self.unit_type)[0]
        n_row, n_col = self.get_plot_config(len(i_unit))

        # hides all plots
        for hp in self.h_plot:
            hp.hide()

        # sets/clears the subplot regions
        g_id = np.zeros((n_row, n_col), dtype=int)
        for i, id in enumerate(i_unit):
            i_row, i_col = int(i / n_col), i % n_col
            g_id[i_row, i_col] = id + 1

        # updates the plot layout
        self.plot_layout.updateID(g_id)
        self.plot_layout.activate()

    def update_trace_colour(self):

        # resets the pen colour
        self.h_pen_tr = pg.mkPen(self.tr_col, width=1)

        for hp in self.h_plot:
            hp.plotItem.items[0].setPen(self.h_pen_tr)

    def update_axes_grid(self):

        # updates the grid visibility
        for hp in self.h_plot:
            hp_item = hp.getPlotItem()
            hp_item.showGrid(x=self.show_grid, y=self.show_grid)

    def update_plot_title(self, i_type):

        t_str = '{0} Unit Waveforms'.format(self.unit_lbl[i_type])
        self.h_plot[i_type].setTitle(t_str, size=self.title_size, bold=True)

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

    @staticmethod
    def get_plot_config(n_plt):

        match n_plt:
            case 1:
                return 1, 1
            case 2:
                return 1, 2
            case _:
                return 2, int(np.ceil(n_plt / 2))

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
        self.scale_font_sizes(p_wid, p_hght)

        # resets the plot titles
        for i in range(self.n_plt):
            self.update_plot_title(i)

    def scale_font_sizes(self, p_wid, p_hght):

        # calculates the new scale factor
        p_scl = np.min([p_wid, p_hght])
        f_sz_title = int(np.ceil(self.title_size0 * p_scl))

        # resets the title string
        self.title_size = '{0}pt'.format(f_sz_title)

    # ---------------------------------------------------------------------------
    # Parameter Field Update Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_para(p_str, _self):
        if _self.is_updating:
            return

        match p_str:
            case 'show_grid':
                _self.update_axes_grid()

            case 'tr_col':
                _self.update_trace_colour()

            case 'i_unit':
                _self.update_selected_trace()

            case _:
                _self.update_plot()

    # trace property observer properties
    i_unit = cf.ObservableProperty(pfcn(update_para, 'i_unit'))
    show_grid = cf.ObservableProperty(pfcn(update_para, 'show_grid'))
    unit_type = cf.ObservableProperty(pfcn(update_para, 'unit_type'))
    tr_col = cf.ObservableProperty(pfcn(update_para, 'tr_col'))
