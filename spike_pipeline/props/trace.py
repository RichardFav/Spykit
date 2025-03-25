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
    TraceProp:
"""


class TraceProps(PropWidget):
    # pyqtsignal functions
    config_reset = pyqtSignal()

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # field initialisation
        self.p_info = None
        self.obj_rconfig = None

        # initialises the property widget
        self.setup_prop_fields()
        super(TraceProps, self).__init__(self.main_obj, 'trace', self.p_info)

    def setup_prop_fields(self):
        # sets up the subgroup fields
        pass