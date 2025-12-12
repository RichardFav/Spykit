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
    WaveFormPara:
"""


class WaveFormPara(PropPara):
    # pyqtSignal functions
    combo_update = pyqtSignal(str)
    edit_update = pyqtSignal(str)
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
    def _combo_update(p_str, _self):

        if not _self.is_updating:
            _self.combo_update.emit(p_str)

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
        self.p_props.edit_update.connect(self.edit_update)
        self.p_props.combo_update.connect(self.combo_update)
        self.p_props.check_update.connect(self.check_update)
        self.p_props.checklist_update.connect(self.checklist_update)
        self.p_props.colorpick_update.connect(self.colorpick_update)

    def setup_prop_fields(self):

        # field retrieval
        tr_col0 = cf.get_colour_value('g')
        unit_lbl = self.get_unit_label()
        show_unit = np.ones(len(unit_lbl), dtype=bool)

        # sets up the subgroup fields
        p_tmp = {
            'unit_type': self.create_para_field('Unit Type', 'checklist', show_unit, p_list=unit_lbl),
            'show_grid': self.create_para_field('Show Plot Gridlines', 'checkbox', True),
            'tr_col': self.create_para_field('Trace Colour', 'colorpick', tr_col0),
            # 'sig_type': self.create_para_field('Signal Type', 'combobox', self.sig_list[0], p_list=self.sig_list),
            # 't_start': self.create_para_field('Start Time (s)', 'edit', 0),
            # 'scale_signal': self.create_para_field('Scale Signals', 'checkbox', True),
            # 'c_map': self.create_para_field('Colormap', 'colormapchooser', 'RdBu'),
        }

        # updates the class field
        self.p_info = {'name': 'Waveforms', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def edit_update(self, p_str):

        pass

    def combo_update(self, p_str):

        pass

    def check_update(self, p_str):

        pass

    def checklist_update(self, p_str):

        match p_str:
            case 'unit_type':
                # case is updating the unit type
                self.plot_view.show_plt = getattr(self.p_props, p_str)

    def colorpick_update(self, p_str):

        match p_str:
            case 'tr_col':
                # case is updating the unit type
                self.plot_view.tr_col = getattr(self.p_props, p_str)

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

    def set_plot_view(self, plot_view_new):

        self.plot_view = plot_view_new

    def get_unit_label(self):

        # sets up the unit type fields
        if self.main_obj.get_field('splitGoodAndMua_NonSomatic'):
            return ['Noise', 'Somatic Good', 'Somatic MUA', 'Non-somatic Good', 'Non-somatic MUA']
        else:
            return ['Noise', 'Good', 'MUA', 'Non-Somatic']

