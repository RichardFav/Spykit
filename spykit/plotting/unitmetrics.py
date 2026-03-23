# module import
import os
import time
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
            mp.setStyleSheet("border: 1px solid white;")
            self.plot_layout.addWidget(mp)

        # updates the plot title
        self.update_plot_config()
        self.update_plot_title()

    # ---------------------------------------------------------------------------
    # Parameter Update Functions
    # ---------------------------------------------------------------------------

    def plot_update(self, p_str):

        pass

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
        self.is_init = True
        self.i_unit = int(self.unit_props.get_para_value('i_unit'))
        self.show_grid = bool(self.unit_props.get_para_value('show_grid'))
        self.show_metric = bool(self.unit_props.get_para_value('show_metric'))
        self.is_init = False

        # updates the plot view
        self.init_plot_view()

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------



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

        pass


# ----------------------------------------------------------------------------------------------------------------------

"""
    SpatialDecayPlot:
"""

class SpatialDecayPlot(UnitPlotLayout):
    def __init__(self, unit_props, i_unit):
        super(SpatialDecayPlot, self).__init__(unit_props, i_unit)

        # field initialisation
        self.is_updating = True

        # initialises the plot widgets
        self.init_plot_widgets()

        # resets the update flag
        self.is_updating = False

    def init_plot_widgets(self):

        pass


# ----------------------------------------------------------------------------------------------------------------------

"""
    AutoCorrelPlot:
"""

class AutoCorrelPlot(UnitPlotLayout):
    def __init__(self, unit_props, i_unit):
        super(AutoCorrelPlot, self).__init__(unit_props, i_unit)

        # field initialisation
        self.is_updating = True

        # initialises the plot widgets
        self.init_plot_widgets()

        # resets the update flag
        self.is_updating = False

    def init_plot_widgets(self):

        pass


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

        pass
