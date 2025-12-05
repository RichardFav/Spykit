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



# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMetricProps:
"""


class UnitMetricProps(PropWidget):
    # field properties
    type = 'unit'

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

            # 'sig_type': self.create_para_field('Signal Type', 'combobox', self.sig_list[0], p_list=self.sig_list),
            # 't_start': self.create_para_field('Start Time (s)', 'edit', 0),
            # 'scale_signal': self.create_para_field('Scale Signals', 'checkbox', True),
            # 'c_map': self.create_para_field('Colormap', 'colormapchooser', 'RdBu'),
        }

        # updates the class field
        self.p_info = {'name': 'Metrics', 'type': 'v_panel', 'ch_fld': p_tmp}