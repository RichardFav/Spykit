# module import
import os
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitHistPara:
"""


class UnitHistPara(PropPara):
    # pyqtSignal functions
    combo_update = pyqtSignal(str)
    edit_update = pyqtSignal(str)
    check_update = pyqtSignal(str)
    checklist_update = pyqtSignal(str)

    def __init__(self, p_info):

        # initialises the class parameters
        self.is_updating = True
        super(UnitHistPara, self).__init__(p_info)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def _check_update(p_str, _self):

        if not _self.is_updating:
            _self.check_update.emit(p_str)

    @staticmethod
    def _checklist_update(p_str, _self):

        if not _self.is_updating:
            _self.checklist_update.emit(p_str)

    # trace property observer properties
    hist_type = cf.ObservableProperty(pfcn(_checklist_update, 'hist_type'))
    show_grid = cf.ObservableProperty(pfcn(_check_update, 'show_grid'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitHistProps:
"""


class UnitHistProps(PropWidget):
    # field properties
    type = 'unithist'

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # initialises the property widget
        self.setup_prop_fields()
        super(UnitHistProps, self).__init__(self.main_obj, 'unithist', self.p_info)

        # sets up the parameter fields
        self.p_props = UnitHistPara(self.p_info['ch_fld'])

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # resets the object sizes
        h_chklist = self.findChild(cw.QLabelCheckCombo)
        h_chklist.h_lbl.setFixedWidth(70)
        h_chklist.h_combo.setFixedWidth(200)

        # connects the slot functions
        self.p_props.check_update.connect(self.check_update)
        self.p_props.checklist_update.connect(self.checklist_update)

    def setup_prop_fields(self):

        # field retrieval
        p_list_met = list(cw.hist_map.values())
        show_hist = np.ones(len(p_list_met), dtype=bool)

        # sets up the subgroup fields
        p_tmp = {
            'hist_type': self.create_para_field('Plot Metric', 'checklist', show_hist, p_list=p_list_met),
            'show_grid': self.create_para_field('Show Plot Gridlines', 'checkbox', True),
        }

        # updates the class field
        self.p_info = {'name': 'Histograms', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def check_update(self, p_str):

        pass

    def checklist_update(self, p_str):

        match p_str:
            case 'hist_type':
                # case is updating the unit type
                self.plot_view.hist_type = getattr(self.p_props, p_str)

   # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_plot_view(self, plot_view_new):

        self.plot_view = plot_view_new