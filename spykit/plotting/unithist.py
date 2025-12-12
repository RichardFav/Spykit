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
    UnitHistPlot:
"""


class UnitHistPlot(PlotWidget):

    def __init__(self, session_info):
        super(UnitHistPlot, self).__init__('unithist', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_info = session_info
        s_props = self.session_info.session_props

        # other class fields
        self.is_init = True
        self.show_met = True

        # initialises the other class fields
        self.init_class_fields()
        self.update_plot()

        # resets the initialisation flag
        self.is_init = False

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = functools.partial(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

    # ---------------------------------------------------------------------------
    # PLot View Methods
    # ---------------------------------------------------------------------------

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
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

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
