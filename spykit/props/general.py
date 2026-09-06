# module import
import os
import time
import numpy as np
from copy import deepcopy
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara

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

        # initialises the class parameters
        self.is_updating = False
        super(GeneralPara, self).__init__(p_info, n_run)
        self.is_updating = False

    def reset_prop_para(self, p_info, n_run):

        # re-initialises the class parameters
        self.is_updating = True

        # # loops through each of the class parameters
        # for k in p_info.keys():
        #     # retrieves the class parameter field
        #     pv = np.empty(n_run, dtype=object)
        #
        #     # updates the parameter fields
        #     for i_run in range(n_run):
        #         pv[i_run] = p_info[k]['value']
        #
        #     # updates the class parameter field
        #     setattr(self, k, pv)

        super(GeneralPara, self).__init__(p_info, n_run)

        # resets the update flag
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
    # field properties
    type = 'general'

    def __init__(self, prop_manager):

        # field initialisation
        self.trig_view = None
        self.trace_view = None
        self.t_dur = np.round(prop_manager.session_obj.session_props.t_dur, cf.n_dp)
        self.n_run = prop_manager.session_obj.session.get_run_count()

        # initialises the property widget
        self.setup_prop_fields()
        super(GeneralProps, self).__init__(prop_manager, 'general', self.p_info)

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
        self.reset_slot_functions()

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

    def reset_prop_fields(self):

        a = 1

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def check_update(self, run_change=False):

        # field retrieval
        use_full = self.get('use_full')

        # updates the editbox properties
        self.set_edit_props(use_full)

        # updates the time manager field
        if run_change:
            self.time_manager.field_update('i_run')

        elif self.is_init:
            self.time_manager.set('use_full', use_full)

        # if self.is_init:
        #     # resets the start/finish duration fields
        #     self.p_props.is_updating = True
        #     if use_full:
        #         # case is using the entire experiment
        #         self.set_n('t_start', 0., i_run)
        #         self.set_n('t_finish', self.t_dur, i_run)
        #
        #     else:
        #         # case is using the partial experiment
        #         self.set_n('t_start', float(self.edit_start.text()), i_run)
        #         self.set_n('t_finish', float(self.edit_finish.text()), i_run)
        #
        #     # updates the duration flag
        #     t_dur = np.round(self.get('t_finish', i_run) - self.get('t_start', i_run), cf.n_dp)
        #     self.set_n('t_dur', t_dur, i_run)
        #     self.p_props.is_updating = False
        #
        #     # resets the plot views
        #     if reset_view:
        #         self.reset_plot_views()

    def edit_update(self, p_str):

        # updates the dependent field(s)
        match p_str:
            case p_str if p_str in ['t_start', 't_finish']:
                # case is resetting the start/finish time
                fld_update = ['t_dur']
                fld_value = [np.round(self.get('t_finish') - self.get('t_start'), cf.n_dp)]

            case 't_dur':
                # case is resetting the run duration
                fld_update = ['t_finish']
                fld_value = [np.round(self.get('t_start') + self.get('t_dur'), cf.n_dp)]

        # resets the parameter fields
        for pf, pv in zip(fld_update, fld_value):
            self.set_n(pf, pv)
            self.time_manager.set(pf, pv, False)
            self.set_edit_value(pf)

        # updates the time manager field
        self.time_manager.set(p_str, self.get(p_str))

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_edit_value(self, pf):

        edit_obj = self.findChild(cw.QLineEdit, name=pf)
        edit_obj.setText(str(self.get(pf)))

    def set_trig_view(self, trig_view_new):

        self.trig_view = trig_view_new

    def set_trace_view(self, trace_view_new):

        self.trace_view = trace_view_new

    def set_edit_props(self, use_full):

        self.edit_start.setEnabled(not use_full)
        self.edit_finish.setEnabled(not use_full)
        self.edit_dur.setEnabled(not use_full)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def update_prop_fields(self, p_str):

        match p_str:
            case p_str if p_str in ['update_all', 'pp_change']:
                # case updating all parameter fields
                p_fld_update = ['t_dur', 't_start', 't_finish']

                # re-calculates experimental timing (if post-processing complete)
                if (p_str == 'pp_change') and self.time_manager.has_pp_fcn():
                    self.reset_pp_timing()

            case _:
                # case is the other parameter fiels
                p_fld_update = [p_str]

        # resets the parameter fields
        for pf in p_fld_update:
            # resets the edit parameter value
            pv = self.time_manager.get(pf)
            self.set_n(pf, np.round(pv, cf.n_dp))
            self.set_edit_value(pf)

        # resets the checkbox fields
        if p_str in ['update_all', 'pp_change']:
            self.is_init = False
            use_full = self.time_manager.get('use_full')
            self.check_use_full.setCheckState(cf.chk_state[use_full])
            self.set_edit_props(use_full)
            self.is_init = True

    def reset_slot_functions(self):

        self.p_props.edit_update.connect(self.edit_update)
        self.p_props.check_update.connect(self.check_update)

    def reset_pp_timing(self):

        # field retrieval
        tm = self.time_manager
        t_dur_raw = deepcopy(tm.get('t_dur', True)[0])
        t_run_raw = deepcopy(tm.get('t_run', True)[0])

        # resets the durations of full experimental runs
        for i_uf, uf in enumerate(tm.get('use_full', True)[0]):
            if uf:
                t_dur_raw[i_uf] = t_run_raw[i_uf]

        if self.time_manager.concat_fcn():
            # case is runs are concatenated
            td = np.array([np.sum(t_dur_raw)])
            ts, uf = np.array([0.0]), np.array([True])

        else:
            # case is runs are seperated
            td = deepcopy(t_dur_raw)
            uf = np.ones(len(t_dur_raw), dtype=bool)
            ts = np.zeros(len(t_dur_raw), dtype=float)

        # updates the class fields
        tm.t_start[1], tm.use_full[1] = ts, uf
        tm.t_dur[1], tm.t_run[1], tm.t_finish[1] = (deepcopy(td) for _ in range(3))