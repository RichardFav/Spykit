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
        self.reset_mmap()

    def reset_mmap(self):

        # updates the current memory map
        print('Initialising Complete!')
        self.mmap = self.session_info.get_current_mem_map()

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

        print('Updating UpSet Plot')

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
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_mmap(_self):
        _self.update_plot()

    # trace property observer properties
    mmap = cf.ObservableProperty(update_mmap)