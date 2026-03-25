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

# pyqtgraph modules
from pyqtgraph import (arrayToQPath, mkBrush, mkPen, plot)
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

    def __init__(self, session_info):
        super(WaveFormPlot, self).__init__('waveform', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # other class fields
        self.is_init = True
        self.has_plot = False
        self.show_grid = False
        self.tr_col = cf.get_colour_value('g')

        # initialises the other class fields
        self.init_class_fields()
        self.update_plot()

        # resets the initialisation flag
        self.is_init = False

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets up the unit type fields
        if self.get_field('splitGoodAndMua_NonSomatic'):
            self.unit_lbl = ['Noise', 'Somatic Good', 'Somatic MUA', 'Non-somatic Good', 'Non-somatic MUA']
        else:
            self.unit_lbl = ['Noise', 'Good', 'MUA', 'Non-Somatic']

        # memory allocation
        self.n_plt = len(self.unit_lbl)
        self.unit_type = np.ones(self.n_plt, dtype=bool)

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = pfcn(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

    # ---------------------------------------------------------------------------
    # PLot View Methods
    # ---------------------------------------------------------------------------

    def update_plot(self):

        # field retrieval
        t0 = np.array(range(self.get_field('n_pts')))
        u_type = np.array(self.get_field('unit_type'))
        y_spike = np.array(self.get_field('y_spike_unit'))

        # determines the unit configuration
        i_unit = np.where(self.unit_type)[0]
        n_unit = len(i_unit)

        # if no units are selected, then delete the subplots and exit
        if n_unit == 0:
            self.delete_subplots()
            return

        # sets/clears the subplot regions
        n_row, n_col = self.get_plot_config(n_unit)
        if len(self.h_plot):
            # clears the subplots
            if (n_row, n_col) == self.h_plot.shape:
                # case is the configuration is the same (clear plots only)
                self.clear_subplots()
            else:
                # case is config has changed (delete/re-setup plot vlews)
                self.delete_subplots()
                self.setup_subplots(n_r=n_row, n_c=n_col)

        else:
            # sets up the subplots
            self.setup_subplots(n_r=n_row, n_c=n_col)

        if not isinstance(self.h_plot, np.ndarray):
            self.h_plot = np.array(self.h_plot).reshape(1, -1)

        # hides the extransoue subplots
        for i_sub in range(len(i_unit), n_row * n_col):
            i_row, i_col = i_sub // n_col, i_sub % n_col
            self.h_plot[i_row, i_col].hide()

        # creates the waveform subplots
        for i_sub, i_type in enumerate(i_unit):
            # row/column indices
            i_row, i_col = i_sub // n_col, i_sub % n_col
            self.h_plot[i_row, i_col].show()

            # trace plotting
            is_unit = u_type[:, 0] == i_type

            # sets the waveform plot points
            t_plt = np.matlib.repmat(t0, sum(is_unit), 1).flatten()
            y_plt = y_spike[is_unit, :].flatten()

            # sets up the connectivity array
            c_arr = np.ones((sum(is_unit), len(t0)), dtype=np.ubyte)
            c_arr[:, -1] = 0

            # creates the unit traces
            h_unit = arrayToQPath(t_plt, y_plt, c_arr.flatten())
            h_item = QGraphicsPathItem(h_unit)
            h_item.setPen(mkPen(self.tr_col, width=1))

            # plot title
            t_str = '{0} Unit Waveforms'.format(self.unit_lbl[i_type])
            self.h_plot[i_row, i_col].setTitle(t_str, size='20pt', bold=True)
            self.h_plot[i_row, i_col].addItem(h_item)

            # hides the plot axis
            h_plt_item = self.h_plot[i_row, i_col].getPlotItem()
            for ax_t in ['left', 'bottom', 'right', 'top']:
                h_plt_item.showAxes(True, False)
                h_plt_item.layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
                self.h_plot[i_row, i_col].getAxis(ax_t).setStyle(tickLength=0)

                if ax_t in ['right', 'top']:
                    h_plt_item.showAxis(ax_t)

        # updates the axes grids
        self.update_axes_grid()

    def update_axes_grid(self):

        for hp in self.h_plot.flatten():
            # updates the grid visibility
            hp_item = hp.getPlotItem()
            hp_item.showGrid(x=self.show_grid, y=self.show_grid)

    def clear_current_plot(self):

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
    # Parameter Field Update Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_para(p_str, _self):
        if _self.is_init:
            return

        match p_str:
            case 'show_grid':
                _self.update_axes_grid()

            case _:
                _self.update_plot()

    # trace property observer properties
    show_grid = cf.ObservableProperty(pfcn(update_para, 'show_grid'))
    unit_type = cf.ObservableProperty(pfcn(update_para, 'unit_type'))
    tr_col = cf.ObservableProperty(pfcn(update_para, 'tr_col'))
