# module import
import os
import time
import numpy as np
from copy import deepcopy
from functools import partial as pfcn

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import pyqtSignal

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

    def __init__(self, p_info, n_run):
        self.n_run = n_run

        self.is_updating = True
        super(GeneralPara, self).__init__(p_info, n_run)
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
    def __init__(self, main_obj):

        # sets the input arguments
        self.main_obj = main_obj

        # field initialisation
        self.trig_view = None
        self.trace_view = None
        self.t_dur = self.main_obj.session_obj.session_props.t_dur
        self.n_run = self.main_obj.session_obj.session.get_run_count()

        # initialises the property widget
        self.setup_prop_fields()
        super(GeneralProps, self).__init__(self.main_obj, 'general', self.p_info)

        # sets up the parameter fields
        self.p_props = GeneralPara(self.p_info['ch_fld'], self.n_run)

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
            't_start': self.create_para_field('Start Time (s)', 'edit', 0.),
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
        i_run = self.get_run_index()
        self.edit_start.setEnabled(not self.p_props.use_full[i_run])
        self.edit_finish.setEnabled(not self.p_props.use_full[i_run])
        self.edit_dur.setEnabled(not self.p_props.use_full[i_run])

        if self.is_init:
            # resets the start/finish duration fields
            self.p_props.is_updating = True
            if self.get('use_full', i_run):
                # case is using the entire experiment
                self.set_n('t_start', 0., i_run)
                self.set_n('t_finish', self.t_dur, i_run)

            else:
                # case is using the partial experiment
                self.set_n('t_start', float(self.edit_start.text()), i_run)
                self.set_n('t_finish', float(self.edit_finish.text()), i_run)

            # updates the duration flag
            self.set_n('t_dur', self.get('t_finish', i_run) - self.get('t_start', i_run), i_run)
            self.p_props.is_updating = False

            # resets the plot views
            self.reset_plot_views()

    def edit_update(self, p_str):

        # flag that property values are being updated manually
        i_run = self.get_run_index()
        self.p_props.is_updating = True

        # updates the dependent field(s)
        fld_update = []
        match p_str:
            case p_str if p_str in ['t_start', 't_finish']:
                fld_update = ['t_dur']
                self.set_n('t_dur', self.get('t_finish', i_run) - self.get('t_start', i_run), i_run)

            case 't_dur':
                fld_update = ['t_finish']
                self.set_n('t_finish', self.get('t_start', i_run) + self.get('t_dur', i_run), i_run)

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
    # Plot View Setter Functions
    # ---------------------------------------------------------------------------

    def set_trig_view(self, trig_view_new):

        self.trig_view = trig_view_new

    def set_trace_view(self, trace_view_new):

        self.trace_view = trace_view_new

    # ---------------------------------------------------------------------------
    # Plot View Update Functions
    # ---------------------------------------------------------------------------

    def reset_plot_views(self):

        if self.trace_view is not None:
            self.trace_view.reset_gen_props()

        if self.trig_view is not None:
            self.trig_view.reset_gen_props()
