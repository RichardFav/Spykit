# module import
import os
import numpy as np
from copy import deepcopy
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
    WaveFormPara:
"""


class WaveFormPara(PropPara):
    # pyqtSignal functions
    check_update = pyqtSignal(str)
    checklist_update = pyqtSignal(str)
    colorpick_update = pyqtSignal(str)

    def __init__(self, p_info):

        # initialises the class parameters
        self.is_updating = True
        super(WaveFormPara, self).__init__(p_info)
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

    @staticmethod
    def _colorpick_update(p_str, _self):

        if not _self.is_updating:
            _self.colorpick_update.emit(p_str)

    # trace property observer properties
    unit_type = cf.ObservableProperty(pfcn(_checklist_update, 'unit_type'))
    show_grid = cf.ObservableProperty(pfcn(_check_update, 'show_grid'))
    tr_col = cf.ObservableProperty(pfcn(_colorpick_update, 'tr_col'))


# ----------------------------------------------------------------------------------------------------------------------

"""
    WaveFormProps:
"""


class WaveFormProps(PropWidget):
    # field properties
    type = 'waveform'

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # initialises the property widget
        self.setup_prop_fields()
        super(WaveFormProps, self).__init__(self.main_obj, 'waveform', self.p_info)

        # sets up the parameter fields
        self.p_props = WaveFormPara(self.p_info['ch_fld'])

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # connects the slot functions
        self.p_props.check_update.connect(self.check_update)
        self.p_props.checklist_update.connect(self.checklist_update)
        self.p_props.colorpick_update.connect(self.colorpick_update)

    def setup_prop_fields(self):

        # field retrieval
        unit_lbl = self.get_unit_label()
        tr_col0 = cf.get_colour_value('g')
        show_unit = np.ones(len(unit_lbl), dtype=bool)

        # sets up the subgroup fields
        p_tmp = {
            'unit_type': self.create_para_field('Waveform Unit Type', 'checklist', show_unit, p_list=unit_lbl),
            'tr_col': self.create_para_field('Plot Trace Colour', 'colorpick', tr_col0),
            'show_grid': self.create_para_field('Show Plot Gridlines', 'checkbox', False),
        }

        # updates the class field
        self.p_info = {'name': 'Waveforms', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def check_update(self, p_str):

        # updates the plot view parameter value
        if self.plot_view is not None:
            setattr(self.plot_view, p_str, getattr(self.p_props, p_str))

    def checklist_update(self, p_str):

        match p_str:
            case 'unit_type':
                # case is the display unit type
                unit_type = self.get_para_value(p_str)
                if np.sum(unit_type) == 0:
                    # if there are no plots selected, then output an error
                    e_str = "At least one unit type must be selected."
                    cf.show_error(e_str, "Invalid Configuration")

                    # determines the index of the
                    i_unit_type = np.where(unit_type)[0]
                    g_id = deepcopy(self.plot_view.plot_layout.g_id)
                    i_met_chg = g_id.flatten()[0] - 1

                    # resets the parameter field
                    unit_type[i_met_chg] = True
                    self.reset_para_value('hist_type', unit_type)

                    # resets the checklist marker
                    self.is_updating = True
                    h_chklist = self.findChild(cw.QLabelCheckCombo, name=p_str)
                    h_chklist.set_checked(i_met_chg, True)
                    self.is_updating = False

        # updates the plot view parameter value
        if self.plot_view is not None:
            setattr(self.plot_view, p_str, getattr(self.p_props, p_str))

    def colorpick_update(self, p_str):

        # updates the plot view parameter value
        if self.plot_view is not None:
            setattr(self.plot_view, p_str, getattr(self.p_props, p_str))

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_plot_view(self, plot_view_new):

        self.plot_view = plot_view_new

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_unit_label(self):

        # sets up the unit type fields
        if self.main_obj.get_field('splitGoodAndMua_NonSomatic'):
            return ['Noise', 'Somatic Good', 'Somatic MUA', 'Non-somatic Good', 'Non-somatic MUA']
        else:
            return ['Noise', 'Good', 'MUA', 'Non-Somatic']

    def get_para_value(self, p_str):

        return getattr(self.p_props, p_str)

    # ---------------------------------------------------------------------------
    # Miscellaneous Methods
    # ---------------------------------------------------------------------------

    def post_process_change(self):

        # field retrieval
        self.is_updating = True
        h_combo = self.findChild(QComboBox, name='unit_type')

        # clears and resets the unit-types
        h_combo.clear()
        for t in self.get_unit_label():
            h_combo.addItem(t)

        # field retrieval
        self.is_updating = False

    def reset_para_value(self, p_fld, p_val):

        # resets the parameter value (without activating callback)
        self.p_props.is_updating = True
        setattr(self.p_props, p_fld, p_val)
        self.p_props.is_updating = False