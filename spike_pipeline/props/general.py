# module import
import os
import time
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    GeneralPara:
"""


class GeneralPara(PropPara):
    # pyqtSignal functions
    check_update = pyqtSignal()
    edit_update = pyqtSignal(str)

    def __init__(self, p_info):
        self.is_updating = True
        super(GeneralPara, self).__init__(p_info)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def _check_update(_self):

        if not _self.is_updating:
            _self.check_update.emit()

    @staticmethod
    def _edit_update(p_str, _self):

        if not _self.is_updating:
            _self.edit_update.emit(p_str)

    # trace property observer properties
    use_full = cf.ObservableProperty(_check_update)
    t_start = cf.ObservableProperty(pfcn(_edit_update, 't_start'))
    t_finish = cf.ObservableProperty(pfcn(_edit_update, 't_finish'))
    t_dur = cf.ObservableProperty(pfcn(_edit_update, 't_dur'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    GeneralProps:
"""


class GeneralProps(PropWidget):
    # pyqtsignal functions
    config_reset = pyqtSignal()

    def __init__(self, main_obj):

        # sets the input arguments
        self.main_obj = main_obj

        # field initialisation
        self.t_dur = self.main_obj.session_obj.session_props.t_dur

        # initialises the property widget
        self.setup_prop_fields()
        super(GeneralProps, self).__init__(self.main_obj, 'general', self.p_info)

        # sets up the parameter fields
        self.p_props = GeneralPara(self.p_info['ch_fld'])

        # widget retrieval
        self.check_use_full = self.findChild(QCheckBox, name='use_full')
        self.edit_start = self.findChild(cw.QLineEdit, name='t_start')
        self.edit_finish = self.findChild(cw.QLineEdit, name='t_finish')
        self.edit_dur = self.findChild(cw.QLineEdit, name='t_dur')

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # connects the slot functions
        self.p_props.edit_update.connect(self.edit_update)
        self.p_props.check_update.connect(self.check_update)

        # updates the editbox values
        self.check_update()

        # flag initialisation is complete
        self.is_init = True

    def setup_prop_fields(self):

        # sets up the subgroup fields
        p_tmp = {
            'use_full': self.create_para_field('Use Full Experiment', 'checkbox', True),
            't_start': self.create_para_field('Start Time (s)', 'edit', 0),
            't_finish': self.create_para_field('Finish Time (s)', 'edit', self.t_dur),
            't_dur': self.create_para_field('Duration (s)', 'edit', self.t_dur),
        }

        # updates the class field
        self.p_info = {'name': 'General', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def check_update(self):

        # updates the editbox properties
        self.edit_start.setEnabled(not self.p_props.use_full)
        self.edit_finish.setEnabled(not self.p_props.use_full)
        self.edit_dur.setEnabled(not self.p_props.use_full)

        if self.is_init:
            # resets the start/finish duration fields
            self.p_props.is_updating = True
            if self.get('use_full'):
                # case is using the entire experiment
                self.set('t_start', 0)
                self.set('t_finish', self.t_dur)

            else:
                # case is using the partial experiment
                self.set('t_start', float(self.edit_start.text()))
                self.set('t_finish', float(self.edit_finish.text()))

            # updates the duration flag
            self.set('t_dur', self.get('t_finish') - self.get('t_start'))
            self.p_props.is_updating = False

            # resets the plot views
            self.reset_plot_views()

    def edit_update(self, p_str):

        # flag that property values are being updated manually
        self.p_props.is_updating = True

        # updates the dependent field(s)
        fld_update = []
        match p_str:
            case p_str if p_str in ['t_start', 't_finish']:
                fld_update = ['t_dur']
                self.set('t_dur', self.get('t_finish') - self.get('t_start'))

            case 't_dur':
                fld_update = ['t_finish']
                self.set('t_finish', self.get('t_start') + self.get('t_dur'))

        # resets the parameter fields
        for pf in fld_update:
            edit_obj = self.findChild(cw.QLineEdit, name=pf)
            edit_obj.setText(str(self.get(pf)))

        # resets the property check flag
        self.p_props.is_updating = False

        # resets the plot views
        if self.is_init:
            self.reset_plot_views()

    # ---------------------------------------------------------------------------
    # Plot View Update Functions
    # ---------------------------------------------------------------------------

    def reset_plot_views(self):

        a = 1