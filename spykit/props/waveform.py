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
    def _edit_update(p_str, _self):

        if not _self.is_updating:
            _self.edit_update.emit(p_str)

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
    i_unit = cf.ObservableProperty(pfcn(_edit_update, 'i_unit'))
    unit_type = cf.ObservableProperty(pfcn(_checklist_update, 'unit_type'))
    show_grid = cf.ObservableProperty(pfcn(_check_update, 'show_grid'))
    trace_col = cf.ObservableProperty(pfcn(_colorpick_update, 'trace_col'))
    unit_col = cf.ObservableProperty(pfcn(_colorpick_update, 'unit_col'))


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
        self.p_props.check_update.connect(self.check_update)
        self.p_props.checklist_update.connect(self.checklist_update)
        self.p_props.colorpick_update.connect(self.colorpick_update)

    def setup_prop_fields(self):

        # field retrieval
        self.n_unit, _ = self.get_mem_map_field('q_met').shape

        # field retrieval
        unit_lbl = self.get_unit_label()
        trace_col0 = cf.get_colour_value('g')
        unit_col0 = cf.get_colour_value('r')
        show_unit = np.ones(len(unit_lbl), dtype=bool)

        # sets up the subgroup fields
        p_tmp = {
            'i_unit': self.create_para_field('Cluster ID#', 'edit', 1),
            'unit_type': self.create_para_field('Waveform Unit Type', 'checklist', show_unit, p_list=unit_lbl),
            'trace_col': self.create_para_field('Waveform Colour', 'colorpick', trace_col0),
            'unit_col': self.create_para_field('Selected Unit Colour', 'colorpick', unit_col0),
            'show_grid': self.create_para_field('Show Plot Gridlines', 'checkbox', False),
        }

        # updates the class field
        self.p_info = {'name': 'Waveforms', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def edit_update(self, p_str):

        # if force updating, then exit the function
        if self.is_updating:
            return

        # field retrieval
        h_edit = self.findChild(cw.QLineEdit,name=p_str)
        nw_val = h_edit.text()

        match p_str:
            case 'i_unit':
                min_val, max_val = 1, self.n_unit

        # determines if the new value is valid
        chk_val = cf.check_edit_num(nw_val, min_val=min_val, max_val=max_val, is_int=True)
        if chk_val[1] is None:
            # updates the parameter value
            setattr(self, p_str, int(chk_val[0]))

            # parameter specific updates
            match p_str:
                case 'i_unit':
                    # case is the cluster index
                    unit_tab = self.main_obj.main_obj.main_obj.info_manager.get_info_tab('unit')
                    unit_tab.reset_selected_cell(chk_val[0] - 1)

            # updates the histogram view
            if self.plot_view is not None:
                setattr(self.plot_view, p_str, int(chk_val[0]))

        else:
            # otherwise, reset the previous value
            p_val_pr = getattr(self, p_str)
            h_edit.setText('%g' % p_val_pr)
            self.reset_para_value(p_str, p_val_pr)

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

    def set_para_value(self, p_fld, p_val):

        setattr(self.p_props, p_fld, p_val)

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

    def get_mem_map_field(self, p_fld):

        return self.main_obj.main_obj.session_obj.get_mem_map_field(p_fld)

    # ---------------------------------------------------------------------------
    # Miscellaneous Methods
    # ---------------------------------------------------------------------------

    def post_process_change(self):

        # field retrieval
        self.is_updating = True
        u_lbl = self.get_unit_label()
        h_chklist = self.findChild(cw.QLabelCheckCombo, name='unit_type')

        # retrieves the current selected units
        is_sel = h_chklist.get_selected_states()
        if len(u_lbl) != len(is_sel):
            # if this doesn't match, then reset the array
            is_sel = np.ones(len(u_lbl), dtype=bool)

        # clears and resets the unit-types
        h_chklist.clear()
        for i, t in enumerate(self.get_unit_label()):
            h_chklist.add_item(t, is_sel[i])

        # resets the waveform traces
        self.plot_view.reset_unit_traces()
        self.plot_view.update_selected_trace()

        # field retrieval
        self.is_updating = False

    def reset_para_value(self, p_fld, p_val):

        # resets the parameter value (without activating callback)
        self.p_props.is_updating = True
        setattr(self.p_props, p_fld, p_val)
        self.p_props.is_updating = False