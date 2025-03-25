# module import
import os
import time
import colorsys
import functools
import numpy as np

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.props.utils import PropWidget

# pyqt imports
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    ConfigProps:
"""


class ConfigProps(PropWidget):
    # pyqtsignal functions
    config_reset = pyqtSignal()

    # other class fields
    init_plot_types = ['Trace', 'Probe']

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # field initialisation
        self.p_info = None
        self.obj_rconfig = None

        # initialises the property widget
        self.setup_prop_fields()
        super(ConfigProps, self).__init__(self.main_obj, 'config', self.p_info)

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # widget retrieval
        self.obj_rconfig = self.findChild(cw.QRegionConfig)

    def setup_prop_fields(self):

        # sets up the subgroup fields
        p_tmp = {
            'r_config': self.create_para_field('Region Configuration', 'rconfig', None),
        }

        # updates the class field
        self.p_info = {'name': 'Configuration', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Region Configuration Functions
    # ---------------------------------------------------------------------------

    def get_region_config(self):

        return self.obj_rconfig.c_id

    def set_region_config(self, c_id):

        self.obj_rconfig.reset_selector_widgets(c_id)

    def add_config_view(self, v_type):

        self.obj_rconfig.is_updating = True
        self.obj_rconfig.obj_lbl_combo.obj_cbox.addItem(v_type)
        self.obj_rconfig.is_updating = False
