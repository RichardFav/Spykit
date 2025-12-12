# module import
import os
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMetricPara:
"""


class UnitMetricPara(PropPara):
    # pyqtSignal functions
    combo_update = pyqtSignal(str)
    edit_update = pyqtSignal(str)
    check_update = pyqtSignal(str)

    def __init__(self, p_info):

        # initialises the class parameters
        self.is_updating = True
        super(UnitMetricPara, self).__init__(p_info)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def _check_update(p_str, _self):

        if not _self.is_updating:
            _self.check_update.emit(p_str)

    # trace property observer properties
    show_grid = cf.ObservableProperty(pfcn(_check_update, 'show_grid'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMetricProps:
"""


class UnitMetricProps(PropWidget):
    # field properties
    type = 'unitmet'

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # initialises the property widget
        self.setup_prop_fields()
        super(UnitMetricProps, self).__init__(self.main_obj, 'unitmet', self.p_info)

        # sets up the parameter fields
        self.p_props = UnitMetricPara(self.p_info['ch_fld'])

    def setup_prop_fields(self):

        # sets up the subgroup fields
        p_tmp = {
            'show_grid': self.create_para_field('Show Plot Gridlines', 'checkbox', True),
        }

        # updates the class field
        self.p_info = {'name': 'Metrics', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def check_update(self, p_str):

        pass

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_plot_view(self, plot_view_new):

        self.plot_view = plot_view_new