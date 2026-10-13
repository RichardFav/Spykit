# module import
import re
import os
import time
import docker
import shutil
import logging
import platform
import numpy as np
import pandas as pd
from pathlib import Path
from copy import deepcopy
from textwrap import dedent
from functools import partial as pfcn

# spykit module imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.threads.utils import ThreadWorker

# spike interface module imports
from spikeinterface.sorters import (available_sorters, installed_sorters, get_sorter_params_description,
                                    get_sorter_description, get_default_sorter_params)

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QWidget, QFrame, QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLineEdit, QCheckBox, QTabWidget, QSizePolicy, QProgressBar, QTreeWidget, QTreeWidgetItem,
                             QHeaderView, QComboBox, QPushButton, QDialog, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QTimeLine, Qt, QObject, QThread
from PyQt6.QtGui import QColor, QFont

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    Common Functions:  
"""


def convert_string(p_val_str, isint):
    if isint:
        # case is an integer string
        try:
            return int(p_val_str)
        except:
            return np.nan

    else:
        # case is a float string
        try:
            return float(p_val_str)
        except:
            return np.nan


# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeSortingDialog:  
"""


class SpikeSortingDialog(QMainWindow):
    # pyqtsignal functions
    prop_updated = pyqtSignal()
    close_spike_sorting = pyqtSignal(bool)

    # widget dimensions
    n_prog = 2
    gap_sz = 5
    dlg_width = 480
    dlg_height = 600
    but_height = 20
    p_row = np.array([20, 1, 2, 1])

    # array class fields
    sort_str = ['Start Spike Sorting', 'Cancel Spike Sorting']

    # sorter tab groupings
    sorter_groups = {
        'Local': 'local',
        'Docker Images': 'image',
        'Repositories': 'other',
        'Custom': 'custom',
    }

    # sorter group descriptions
    sorter_group_desc = {
        'local': 'Spikewrap Sorters',
        'image': 'Locally Stored Docker Images',
        'other': 'Available Docker Images',
        'custom': 'Custom Sorters',
    }

    # widget stylesheets
    border_style = "border: 1px solid;"
    no_border_style = "border: 0px; padding-top: 3px;"
    frame_border_style = """
        QFrame#sortFrame {
            border: 1px solid;
        }
    """

    def __init__(self, sp_main=None, ss_config=None):
        super(SpikeSortingDialog, self).__init__(sp_main)

        # sets the input arguments
        self.sp_main = sp_main
        self.ss_config = ss_config

        if self.sp_main is not None:
            # creates the preprocessing run class object
            self.session_obj = self.sp_main.session_obj
            self.session = self.session_obj.session
            self.prep_opt = [self.session.prep_obj.per_shank, self.session.prep_obj.concat_runs]

            # preprocessing options
            self.per_shank_pp = self.session.prep_obj.per_shank
            self.concat_runs_pp = self.session.prep_obj.concat_runs

        else:
            self.session = None

        # sets the central widget
        self.main_widget = QWidget(self)
        self.ss_obj = SpikeSortInfo(None if (self.sp_main is None) else self.session_obj)

        # widget layouts
        self.main_layout = QGridLayout()
        self.sort_layout = QVBoxLayout()
        self.progress_layout = QVBoxLayout()
        self.cont_layout = QHBoxLayout()
        self.checkbox_layout = QHBoxLayout()

        # container class fields
        self.sort_frame = QFrame(self)
        self.progress_frame = QFrame(self)
        self.checkbox_frame = QFrame(self)
        self.cont_frame = QFrame(self)

        # other widget class fields
        self.tab_group_sort = QTabWidget(self)
        self.prog_bar = cw.QDialogProgress(font=cw.font_lbl, is_task=True, timer_lbl=True)
        self.button_cont = []
        self.checkbox_opt = []
        self.solver_tab = {}

        # boolean class fields
        self.ss_change = False
        self.is_running = True
        self.is_updating = False
        self.per_shank = False
        self.concat_runs = False
        self.is_prop_change = False
        self.is_worker_running = False

        # initialisations
        self.s_props = {}
        self.s_prop_flds = {}
        self.g_type = None
        self.s_type = None
        self.t_worker = None

        # initialises the major widget groups
        self.init_class_fields()
        self.init_sorting_frame()
        self.init_checkbox_opt()
        self.init_progress_frame()
        self.init_button_frame()
        self.set_widget_config()

        # runs the other special initialisations
        self.init_other_special()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # creates the dialog window
        self.setWindowTitle("Spike Sorting Parameters")
        self.setFixedSize(self.dlg_width, self.dlg_height)
        self.setWindowModality(Qt.WindowModality(1))
        # self.setLayout(self.main_layout)
        # self.setModal(True)

        # sets the main widget properties
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        # resets the frame object names
        for qf in self.findChildren(QFrame):
            qf.setObjectName('sortFrame')

        # sets up the property fields
        for s_type in ['local', 'image', 'other']:
            self.init_sorter_props(s_type)

    def init_button_frame(self):

        # initialisations
        b_str = [self.sort_str[0], 'Close Window']
        cb_fcn = [self.start_spike_sort, self.close_window]

        # sets the control button panel properties
        self.cont_frame.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.cont_frame.setLayout(self.cont_layout)
        self.cont_frame.setStyleSheet(self.frame_border_style)

        # button group layout properties
        self.cont_layout.setContentsMargins(0, 0, 0, 0)
        self.cont_layout.setSpacing(x_gap)

        # creates the control buttons
        for bs, cb in zip(b_str, cb_fcn):
            # creates the button object
            button_new = cw.create_push_button(self, bs, font=cw.font_lbl)
            self.cont_layout.addWidget(button_new)
            self.button_cont.append(button_new)

            # sets the button properties
            button_new.pressed.connect(cb)
            button_new.setFixedHeight(cf.but_height)
            button_new.setStyleSheet(self.border_style)

        # sets the control button properties
        self.button_cont[0].setCheckable(True)

    def init_sorting_frame(self):

        # sets the sorting parameter panel properties
        self.sort_frame.setLayout(self.sort_layout)
        self.sort_frame.setStyleSheet(self.frame_border_style)
        self.sort_layout.setSpacing(0)
        self.sort_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.sort_layout.addWidget(self.tab_group_sort)

        # sets up the sorter tab groups (for each type)
        for i, (gn, gf) in enumerate(self.sorter_groups.items()):
            # creates the sorter group tab
            grp_tab = self.create_sort_group_tab(gf)
            self.tab_group_sort.addTab(grp_tab, gn)
            self.tab_group_sort.setTabEnabled(i, grp_tab.isEnabled())
            self.tab_group_sort.setTabToolTip(i, self.sorter_group_desc[gf])

        # sets the main tab group callback function
        self.tab_group_sort.currentChanged.connect(self.sort_tab_change)

        # resets the tab types
        self.reset_tab_types()

    def init_checkbox_opt(self):

        # initialisations
        c_str = [' Split Recording By Shank', ' Concatenate Experimental Runs']
        cb_fcn = [self.checkbox_split_shank, self.checkbox_concat_expt]

        # sets the frame/layout properties
        self.checkbox_frame.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.checkbox_frame.setLayout(self.checkbox_layout)
        self.checkbox_frame.setStyleSheet(self.frame_border_style)
        self.checkbox_layout.setContentsMargins(2 * x_gap, 0, 2 * x_gap, 0)
        self.checkbox_layout.setSpacing(self.but_height + 2 * self.gap_sz)

        # creates the control buttons
        for cs, cb in zip(c_str, cb_fcn):
            # creates the button object
            checkbox_new = cw.create_check_box(self, cs, False, font=cw.font_lbl)
            self.checkbox_layout.addWidget(checkbox_new)
            self.checkbox_opt.append(checkbox_new)

            # sets the button properties
            checkbox_new.pressed.connect(cb)
            checkbox_new.setFixedHeight(cf.but_height)
            checkbox_new.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        if self.sp_main is not None:
            # updates the checkbox properties
            self.checkbox_opt[0].setCheckState(cf.chk_state[self.per_shank_pp])
            self.checkbox_opt[1].setCheckState(cf.chk_state[self.concat_runs_pp])

    def init_progress_frame(self):

        # sets the frame/layout properties
        self.progress_frame.setContentsMargins(0, 0, 0, 0)
        self.progress_frame.setLayout(self.progress_layout)
        self.progress_frame.setStyleSheet(self.frame_border_style)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(0)

        # creates the progressbar widgets
        self.prog_bar.set_enabled(False)
        self.prog_bar.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.prog_bar.lbl_obj.setContentsMargins(0, 2 * (x_gap - 1), 0, 0)
        self.progress_layout.addWidget(self.prog_bar)

    def init_sorter_props(self, s_type):

        # retrieves the sorter list
        s_list = getattr(self.ss_obj, '{0}_s'.format(s_type))

        for sl in s_list:
            # sets an empty sorter name (some sorters don't have descriptions)
            s_name = None
            s_desc = None

            # sets the sorter specific parameter fields
            match sl:
                case 'ironclust':
                    # case is Ironcluster
                    s_name = 'IronClust'
                    s_desc = ("Ironclust is a density-based spike sorter designed for high-density probes \n"
                              "(e.g. Neuropixels). It uses features and spike location estimates for clustering, and \n"
                              "it performs a drift correction. For more information see https://doi.org/10.1101/101030")

                case 'simple':
                    # case is simple
                    s_name = 'Simple'
                    s_desc = ("Implementation of a very simple sorter usefull for teaching.\n\n"
                              " * detect peaks\n"
                              " * project waveforms with SVD or PCA\n"
                              " * apply a well known clustering algos from scikit-learn\n\n"
                              "No template matching. No auto cleaning.\n\n"
                              "Mainly usefull for few channels (1 to 8), teaching and testing.")

                case 'tridesclous2':
                    # case is Tridesclous2
                    s_name = 'Tridesclous2'
                    s_desc = ("Tridesclous2 is a template-matching spike sorter with a real-time engine.\n"
                              "For more information see https://tridesclous.readthedocs.io")

                case 'lupin':
                    # case is Lupin
                    s_name = 'Lupin'
                    s_desc = ("Lupin solver")

                case 'waveclus_snippets':
                    # case is Wave Clus
                    s_name = 'Wave Clus Snippets'

            if s_desc is None:
                s_desc = get_sorter_description(sl)
                if (s_desc is None) or (len(s_desc) == 0):
                    s_desc = 'No Description'

            # retrieves the sorter description and name fields
            if s_name is None:
                s_name = self.get_sorter_name(s_desc)

            # sets the property fields for the sorter
            self.s_prop_flds[sl] = {
                'name': s_name,
                'desc': s_desc,
                'tab': None,
                'grp': None,
            }

    def init_other_special(self):

        # special case - loading the kilosort4 parameter info takes quite a long
        #                time to run (~30s). therefore, load using a background thread
        if 'kilosort4' in self.ss_obj.all_s:
            # if the sorting information is set, then exit
            if 'kilosort4' in self.session.sort_obj.s_props:
                self.s_prop_flds['kilosort4']['tab'].setup_tab_objects()
                self.set_sorter_tab_enabled('kilosort4', True)
                return

            # resets the tab object (if current sorter is kilosort4)
            if self.s_type == 'kilosort4':
                # determines the sorter list (that kilosort4 belongs to)
                s_list = getattr(self.ss_obj, '{0}_s'.format(self.g_type))
                if len(s_list) == 1:
                    # if there are no other sorters, then wait for the sorter to load instead
                    self.set_sorter_tab_enabled('kilosort4', True)
                    return

                else:
                    # otherwise, determines the first non-kilosort4 solver and resets the tab
                    i_sort0 = s_list.index('kilosort4')
                    i_sort_new = np.where(np.array(s_list) != 'kilosort4')[0][0]
                    self.tab_group_sort.currentWidget().findChild(QTabWidget).setCurrentIndex(i_sort_new)

            # connects the preprocessing signal function
            self.is_worker_running = True
            self.session.sort_obj.update_prog.connect(self.info_worker_progress)

            # creates the threadworker object
            sort_props = (self.ss_obj, 'kilosort4')
            self.t_worker = ThreadWorker(self.sp_main, self.run_get_info_worker, sort_props)
            self.t_worker.start()

    def set_widget_config(self):

        # main layout properties
        self.main_layout.setHorizontalSpacing(x_gap)
        self.main_layout.setVerticalSpacing(x_gap)
        self.main_layout.setContentsMargins(2 * x_gap, x_gap, 2 * x_gap, 2 * x_gap)
        # self.setLayout(self.main_layout)

        # adds the main widgets to the main layout
        self.main_layout.addWidget(self.sort_frame, 0, 0, 1, 1)
        self.main_layout.addWidget(self.checkbox_frame, 1, 0, 1, 1)
        self.main_layout.addWidget(self.progress_frame, 2, 0, 1, 1)
        self.main_layout.addWidget(self.cont_frame, 3, 0, 1, 1)

        # set the grid layout column sizes
        self.main_layout.setRowStretch(0, self.p_row[0])
        self.main_layout.setRowStretch(1, self.p_row[1])
        self.main_layout.setRowStretch(2, self.p_row[2])
        self.main_layout.setRowStretch(3, self.p_row[3])

    # ---------------------------------------------------------------------------
    # Property Field Functions
    # ---------------------------------------------------------------------------

    def create_sort_group_tab(self, p_str):

        # creates the tab widget
        obj_tab = QWidget()
        obj_tab.setObjectName(p_str)

        # creates the children objects for the current parent object
        tab_layout = QFormLayout(obj_tab)
        tab_layout.setSpacing(0)
        tab_layout.setContentsMargins(1, 1, 0, 0)
        tab_layout.setLabelAlignment(cf.align_type['right'])

        # creates the panel object
        panel_frame = QFrame()
        panel_frame.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
        panel_frame.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        tab_layout.addWidget(panel_frame)

        # sets up the parameter layout
        layout_para = QVBoxLayout()
        layout_para.setSpacing(x_gap)

        # sets up the sort group tab
        s_list = getattr(self.ss_obj, '{0}_s'.format(p_str))
        if len(s_list):
            # creates the tab group widget
            obj_tab_group = QTabWidget(self)
            obj_tab_group.setObjectName(p_str)
            layout_para.addWidget(obj_tab_group)
            layout_para.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

            # creates the solver parameter tabs
            for i, k in enumerate(s_list):
                # creates the spike sorter tab object
                v = self.s_prop_flds[k]
                obj_tab_para = SpikeSorterTab(self, k)
                obj_tab_group.addTab(obj_tab_para, v['name'])
                obj_tab_group.setTabToolTip(i, v['desc'])

                # sets the solver properties (if already available)
                if k in self.session.sort_obj.s_props:
                    obj_tab_para.s_props = self.session.sort_obj.s_props[k]

                # connects the callback functions
                obj_tab_para.prop_change.connect(self.sort_prop_change)

                # stores the tab widget
                self.s_prop_flds[k]['tab'] = obj_tab_para
                self.s_prop_flds[k]['grp'] = p_str
                if k in ['kilosort4']:
                    obj_tab_group.setTabEnabled(i, False)

            # sets the tabgroup callback function
            obj_tab_group.currentChanged.connect(self.sort_tab_change)

        else:
            obj_tab.setEnabled(False)

        # sets the tab layout
        panel_frame.setLayout(layout_para)
        obj_tab.setLayout(tab_layout)

        # returns the tab object
        return obj_tab

    # ---------------------------------------------------------------------------
    # Thread Worker Functions
    # ---------------------------------------------------------------------------

    def run_get_info_worker(self, sort_obj):

        ss_obj, p_name = sort_obj
        self.session.sort_obj.get_info(ss_obj, p_name)

    def info_worker_progress(self, pr_type, data):

        # updates the tab properties
        s_tab = self.s_prop_flds['kilosort4']['tab']
        self.prog_bar.set_progbar_state(pr_type == 0)
        self.button_cont[0].setEnabled(pr_type == 1)

        match pr_type:
            case 0:
                # case is starting
                self.prog_bar.update_prog_fields('Loading Information...')

            case 1:
                # case is finishing
                s_tab.s_props = data
                s_tab.setEnabled(True)
                self.is_worker_running = False

                # updates the progressbar
                self.prog_bar.update_prog_fields(self.prog_bar.wait_lbl)

                # re-enables the tab header
                self.set_sorter_tab_enabled('kilosort4', True)

                # deletes the worker object
                try:
                    self.t_worker.deleteLater()
                    self.t_worker = None
                except:
                    pass

                # connects the spike sorting signal function
                self.session.sort_obj.update_prog.connect(self.worker_progress)

    def worker_progress(self):

        pass

    # ---------------------------------------------------------------------------
    # Widget Event Functions
    # ---------------------------------------------------------------------------

    def sort_tab_change(self):

        # resets the tab types
        self.reset_tab_types()

        # retrieves the currently selected tab properties
        s_prop_t = self.s_prop_flds[self.s_type]['tab']
        if not s_prop_t.is_init:
            # initialise the sorter tab (if not initalised)
            s_prop_t.setup_tab_objects()

    def checkbox_split_shank(self):

        self.per_shank = self.checkbox_opt[0].checkState() == cf.chk_state[False]

    def checkbox_concat_expt(self):

        self.concat_runs = self.checkbox_opt[1].checkState() == cf.chk_state[False]

    def start_spike_sort(self):

        # if manually updating, then exit
        if self.is_updating:
            return

        # resets the button state
        self.is_running = not self.button_cont[0].isChecked()
        time.sleep(0.05)

        if self.is_running:
            if not self.check_sort_overwrite():
                # if the user cancelled, then exit the function
                self.is_updating = True
                self.button_cont[0].setChecked(False)
                self.is_updating = False

                # exits the function
                return

            # disables the panel properties
            self.set_sorting_props(False)
            self.button_cont[0].setChecked(True)

            # updates the progressbar
            self.prog_bar.set_label("Running Spike Sorting")
            self.prog_bar.set_progbar_state(True)
            time.sleep(0.1)

            # sets up the configuration dictionary
            sort_config = self.setup_config_dict()

            # retrieves the preprocessing information
            prep_obj = self.sp_main.session_obj.session.prep_obj
            sort_opt = (self.per_shank and (not prep_obj.per_shank),
                        self.concat_runs and (not prep_obj.concat_runs))

            # starts running the pre-processing
            self.setup_spike_sorting_worker((sort_config, sort_opt))

        else:
            # stops the worker
            self.t_worker.force_quit()
            time.sleep(0.01)

            # disables the progressbar fields
            self.prog_bar.set_progbar_state(False)

            # resets the other properties
            self.set_sorting_props(True)

    def close_window(self):

        # force closes any running workers
        if (self.t_worker is not None) and self.t_worker.is_running:
            # stops the progressbar
            self.prog_bar.set_progbar_state(False)
            time.sleep(0.1)

            # force closes the thread worker
            self.t_worker.force_quit()

        # if there is a change, prompt the user if they would like to update the props
        if self.is_prop_change:
            # case is the user chose to update the parameters
            self.update_sort_para_changes()

            q_str = 'Do you want to update the parameter changes?'
            u_choice = QMessageBox.question(self.sp_main, 'Update Changes?', q_str, cf.q_yes_no_cancel, cf.q_yes)
            if u_choice == cf.q_yes:
                # case is the user chose to update the parameters
                self.update_sort_para_changes()

            elif u_choice == cf.q_cancel:
                return

        # runs the post window close functions
        self.close_spike_sorting.emit(self.ss_change)

        # closes the window
        self.close()

    # ---------------------------------------------------------------------------
    # Spike Sorting Worker Functions
    # ---------------------------------------------------------------------------

    def set_checkbox_enabled_props(self):

        # sets the by shank checkbox enabled properties
        n_shank = self.session_obj.get_shank_count()
        self.checkbox_opt[0].setEnabled((n_shank > 1) and (not self.per_shank_pp))

        # sets the concatenation checkbox enabled properties
        n_run = self.session.get_run_count()
        self.checkbox_opt[1].setEnabled((n_run > 1) and (not self.concat_runs_pp))

    def setup_spike_sorting_worker(self, sort_obj):

        # creates the threadworker object
        self.t_worker = ThreadWorker(self.sp_main, self.run_spike_sorting_worker, sort_obj)
        self.t_worker.work_finished.connect(self.spike_sorting_complete)

        # starts the worker object
        self.t_worker.start()

    def run_spike_sorting_worker(self, sort_obj):

        # sorting parameters
        sort_config, sort_opt = sort_obj
        per_shank, concat_runs = sort_opt
        run_sorter_method = self.get_sorter_method()

        # runs the preprocessing
        try:
            self.session.sort_obj.sort(sort_config, per_shank, concat_runs, run_sorter_method)
            return []
        except Exception as e:
            return str(e)

    def spike_sorting_complete(self, sorting_msg):

        # stops and updates the progressbar
        self.prog_bar.stop_timer()

        if len(sorting_msg):
            # case is there was a spike-sorting calculation error
            error_msg = self.get_spike_sorting_error(sorting_msg)
            cf.show_error(error_msg, 'Spike Sorting Calculation Error', True)
            self.prog_bar.set_progbar_state(False)

            # updates the boolean flags
            self.ss_change = False

        else:
            # updates the boolean flags
            self.ss_change = True

            # resets the progressbar
            self.prog_bar.set_label('Spike Sorting Complete')
            self.prog_bar.set_full_prog()

        # resets the other properties
        self.set_sorting_props(True)

    def reset_tab_types(self):

        # tab-group change callback function
        h_tab_sel = self.tab_group_sort.currentWidget()
        self.g_type = h_tab_sel.objectName()

        # retrieves the sub-group type
        h_tab_grp_sub = h_tab_sel.findChild(QTabWidget)
        self.s_type = h_tab_grp_sub.currentWidget().objectName()

    # ---------------------------------------------------------------------------
    # Worker Progress Functions
    # ---------------------------------------------------------------------------

    def worker_progress(self, pr_type, pr_dict):

        # initialisations
        pr_val = None
        m_str = [None, None]

    def setup_overall_progress_msg(self):

        # initialisations
        m_str0 = 'Progress'

    # ---------------------------------------------------------------------------
    # Miscellaneous Methods
    # ---------------------------------------------------------------------------

    def set_sorting_props(self, state):

        # sets the close button properties
        self.sort_frame.setEnabled(state)
        self.checkbox_frame.setEnabled(state)
        self.button_cont[1].setEnabled(state)
        self.button_cont[0].setText(self.sort_str[not state])

        # updates the checkbox properties
        if state:
            self.set_checkbox_enabled_props()

        # pause for update...
        time.sleep(0.01)

    def set_sorter_tab_enabled(self, sl_name, state):

        g_tab, i_tab = self.get_sorter_tab_props(sl_name)
        h_tab_grp = self.tab_group_sort.findChild(QTabWidget, name=g_tab)
        h_tab_grp.setTabEnabled(i_tab, state)

    def setup_config_dict(self):

        # retrieves the sorter parameters
        h_tab_s = self.tab_group_sort.currentWidget()
        s_props_s = h_tab_s.findChild(SpikeSorterTab, name=self.s_type).s_props

        # determines the parameters with non-default value
        s_dict = {}
        ndef_para = [k for (k, v) in s_props_s.items() if (v.value != v.dvalue)]
        for nd_p in ndef_para:
            # determines which level
            p_sp = nd_p.split('-')
            n_lvl = len(p_sp) - 1

            # sets the parameter field within the config dictionary
            s_dict_p = s_dict
            for i_lvl in range(n_lvl):
                p_fld = p_sp[i_lvl + 1]
                if (i_lvl + 1) == n_lvl:
                    # case is the leaf level
                    s_dict_p[p_fld] = s_props_s[nd_p].get('value')

                else:
                    # case is a branch level
                    if p_fld not in s_dict_p:
                        s_dict_p[p_fld] = {}
                    s_dict_p = s_dict_p[p_fld]

        return {'sorting': {self.s_type: s_dict}}

    def get_sorter_tab_props(self, s_name):

        s_props = self.s_prop_flds[s_name]
        s_list = getattr(self.ss_obj, '{0}_s'.format(s_props['grp']))
        return s_props['grp'], s_list.index(s_name)

    def update_sort_para_changes(self):

        for sl_k, sl_v in self.s_prop_flds.items():
            s_props = sl_v['tab'].s_props
            if s_props is not None:
                self.session.sort_obj.s_props[sl_k] = s_props

    def sort_prop_change(self):

        self.is_prop_change = True

    def get_sorter_method(self):

        match self.g_type:
            case 'local':
                # case is a local solver
                return 'local'

            case 'custom':
                # FINISH ME!
                pass

            case _:
                # case is using occker
                return 'docker'

    def check_sort_overwrite(self):

        # determines if the output path exists
        out_path = self.session._s.get_output_path()
        if not out_path.exists():
            return True

        # retrieves the sorter output paths
        out_path = self.get_output_file_path(deepcopy(out_path))
        if len(out_path):
            # case is there is at least one output path that exists
            q_str = ('Spike sorting data already exists for this experiment. Do you want to overwrite?\n'
                     'Note that this operation cannot be reversed.')
            u_choice = QMessageBox.question(self.sp_main, 'Overwrite Folder?', q_str, cf.q_yes_no, cf.q_yes)
            if u_choice == cf.q_yes:
                # case is the user chose to overwrite the folder
                self.delete_sorter_folders(out_path)
                return True

            else:
                # otherwise, flag that the user ooes not want to overwrite the existing
                return False

        else:
            # case is none of the final output paths exist
            return True

    def get_output_file_path(self, out_path_base):

        # field retrieval
        out_path = []
        n_run = self.session.get_run_count()
        n_shank = self.session_obj.get_shank_count()

        # retrieves the session per shank/concat run flags
        per_shank = self.session.prep_obj.per_shank or self.per_shank
        concat_runs = self.session.prep_obj.concat_runs or self.concat_runs

        # retrieves the full output paths (based on type)
        if concat_runs:
            # case is the runs are concatenated
            out_path_concat = out_path_base / "concat_run" / "sorting"
            if not out_path_concat.exists():
                # case is the base output path doesn't exist so exit
                return []

            elif per_shank:
                # case is analysing by shank
                for i_shank in range(n_shank):
                    out_path_new = out_path_concat / 'shank_{0}'.format(i_shank)
                    if out_path_new.exists():
                        out_path.append(out_path_new)

            else:
                # case is grouping analysis
                out_path.append(out_path_concat)

        else:
            # case is the runs are analysed separately
            r_names = self.session.get_run_names()
            for i_run, rn in enumerate(r_names):
                out_path_run = out_path_base / rn / "sorting"
                if per_shank:
                    # case is analysing by shank
                    for i_shank in range(n_shank):
                        out_path_new = out_path_run / 'shank_{0}'.format(i_shank)
                        if out_path_new.exists():
                            out_path.append(out_path_new)

                elif out_path_run.exists():
                    # case is grouping analysis
                    out_path.append(out_path_run)

        # returns the array
        return out_path

    def get_spike_sorting_error(self, sorting_msg):

        if re.search(r'n_samples=\d+ should be >= n_clusters=\d+', sorting_msg) is not None:
            # case is the sample count is too low
            err_msg = ('The number of samples found is lower than the cluster count.\n'
                       'Try reducing the parameter "Single-Channel Template Count".')

        else:
            # other message type
            err_msg = sorting_msg

        return err_msg

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def get_sorter_name(s_desc):

        # memory allocation
        s_name_list = []

        # search for the words that comprise the sorter name (capitalised words)
        for s_desc_sp in s_desc.split():
            if s_desc_sp == 'pykilosort':
                s_name_list.append(s_desc_sp.capitalize())
                break

            elif s_desc_sp[0].isupper() or s_desc_sp.isnumeric():
                # if capitalised, then add
                s_name_list.append(s_desc_sp)

            else:
                # otherwise, exit the function
                break

        # returns the final sorter name
        return ' '.join(s_name_list)

    @staticmethod
    def delete_sorter_folders(out_path):
        for op in out_path:
            # force deletes the log file
            for log_file in op.rglob('kilosort4.log'):
                try:
                    os.remove(log_file)
                except PermissionError as pe:
                    logging.shutdown()
                    os.system(f'del /f /q "{log_file}"')

            shutil.rmtree(op, ignore_errors=True)


# ----------------------------------------------------------------------------------------------------------------------

"""
    RunSpikeSorting:  
"""


class RunSpikeSorting(QObject):
    # pyqtSignal functions
    update_prog = pyqtSignal(int, object)

    def __init__(self, s):
        super(RunSpikeSorting, self).__init__()

        # session object
        self.s = s
        self.s_props = {}

        # boolean class fields
        self.per_shank = False
        self.concat_runs = False
        self.run_sorter_method = False

    def sort(self, ss_config, per_shank, concat_runs, run_sorter_method):

        # sets the input arguments
        self.per_shank = per_shank
        self.concat_runs = concat_runs
        self.ss_config = ss_config
        self.run_sorter_method = run_sorter_method

        # runs the spike sorting solver
        self.s.sort(
            ss_config,
            run_sorter_method=run_sorter_method,
            per_shank=self.per_shank,
            concat_runs=self.concat_runs,
        )

    def get_info(self, ss_obj, p_name):

        # initialises the progressbar
        self.update_prog.emit(0, None)

        # initialises the progressbar
        self.update_prog.emit(1, ss_obj.setup_sorter_para('kilosort4'))


# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeSorterTab:  
"""


class SpikeSorterTab(QTabWidget):
    # pyqtsignal functions
    prop_change = pyqtSignal()

    # widget dimensions
    x_gap = 5
    hght_row = 25
    item_row_size = 23

    # array class fields
    tree_hdr = ['Property', 'Value']

    # value to label sign key
    sign_v2l = {
        -1: 'neg',
        0: 'both',
        1: 'pos',
    }

    # value to label sign key
    sign_l2v = {
        'neg': -1,
        'both': 0,
        'pos': 1,
    }

    # solver ignored parameter groups
    ig_para_grp = {
        'kilosort4': ['Fixed']
    }

    # font properties
    gray_col = QColor(160, 160, 160, 255)
    item_child_font = cw.create_font_obj(8)
    item_font = cw.create_font_obj(9, True, QFont.Weight.Bold)

    # label alignment
    lbl_align_r = cw.align_flag['right'] | cw.align_flag['vcenter']
    lbl_align_l = cw.align_flag['left'] | cw.align_flag['vcenter']

    # widget stylesheets
    tree_style = """    
        QTreeWidget::item {
            height: 23px;
        }        
        QTreeWidget::item:has-children {
            background: #A0A0A0;
            padding-left: 5px;
            color: white;
        }
    """
    tree_style_win = """
        QTreeWidget {{
            font: {font} 8px;
            hover-background-color: transparent; 
            selection-background-color: transparent; 
        }}           
    """.format(font=cw.font_base)

    def __init__(self, main_dlg, s_name):
        super(SpikeSorterTab, self).__init__(main_dlg)

        # sets the input arguments
        self.s_name = s_name
        self.main_dlg = main_dlg

        if cf.is_win:
            self.tree_style += self.tree_style_win

        # field retrieval
        self.tree_prop = QTreeWidget(self)
        self.tab_layout = QVBoxLayout()

        # other class fields
        self.s_props = None
        self.n_grp, self.n_para = 0, 0
        self.h_grp, self.h_para = {}, []

        # boolean class fields
        self.is_init = False
        self.is_updating = False

        # initialises the class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the layout propeties
        self.tab_layout.setContentsMargins(0, 0, 0, 0)

        # sets the main widget names
        self.setLayout(self.tab_layout)
        self.setObjectName(self.s_name)

    def setup_tab_objects(self):

        # retrieves the sorter properties
        if self.s_props is None:
            self.s_props = self.main_dlg.ss_obj.setup_sorter_para(self.s_name)

        # sets the tree-view properties
        self.tree_prop.setLineWidth(1)
        self.tree_prop.setColumnCount(2)
        self.tree_prop.setIndentation(12)
        self.tree_prop.setItemsExpandable(True)
        self.tree_prop.setStyleSheet(self.tree_style)
        self.tree_prop.setHeaderLabels(self.tree_hdr)
        self.tree_prop.setFrameStyle(QFrame.Shape.WinPanel | QFrame.Shadow.Plain)
        self.tree_prop.setAlternatingRowColors(True)
        # self.tree_prop.setItemDelegateForColumn(0, cw.HTMLDelegate())

        # determines the unique parameter class indices
        p_fld = np.array(list(self.s_props.keys()))
        p_class = [self.s_props[pf].get_para_class() for pf in p_fld]
        p_grp, i_grp = np.unique(p_class, return_inverse=True)
        is_ok = np.ones(len(p_fld), dtype=bool)

        # creates the table fields for each
        for i, pg in enumerate(p_grp):
            # determines the parameters within the current grouping
            j_grp = np.where(i_grp == i)[0]

            # determine if there are any feasible parameters
            is_ok_grp = is_ok[j_grp]
            if not np.any(is_ok_grp):
                # if not, then continue
                continue

            elif (self.s_name in self.ig_para_grp) and (pg in self.ig_para_grp[self.s_name]):
                # if the parameter group is to be ignored, then continue
                continue

            else:
                # otherwise, get the reduced parameter group
                p_fld_grp = p_fld[j_grp]

            # creates the parent item
            item = QTreeWidgetItem()
            # item = QTreeWidgetItem(self.tree_prop)

            # adds the tree widget item
            for j, ps in enumerate(p_fld_grp):
                if not is_ok_grp[j]:
                    continue

                elif len(self.s_props[ps].get('child')):
                    is_ok[np.array([x.startswith(ps) for x in p_fld])] = False
                    is_ok_grp[np.array([x.startswith(ps) for x in p_fld_grp])] = False

                # creates the property name field
                item_ch, obj_prop = self.create_child_tree_item(item, ps)

                # sets the item properties
                if item_ch is not None:
                    self.set_item_align(item_ch, ps)
                    item.addChild(item_ch)

                # adds the child tree widget item
                if obj_prop is not None:
                    obj_prop.setFixedHeight(self.item_row_size)
                    self.tree_prop.setItemWidget(item_ch, 1, obj_prop)

            # adds the item (if there are children items)
            if item.childCount():
                self.tree_prop.addTopLevelItem(item)
                item.setText(0, pg)
                item.setFont(0, self.item_font)
                item.setFirstColumnSpanned(True)
                self.expand_all_nodes(item)

            else:
                del item

        # adds the tree widget to the parent widget
        self.tab_layout.addWidget(self.tree_prop)

        # resizes the columns to fit, then resets to fixed size
        tree_header = self.tree_prop.header()
        tree_header.setDefaultAlignment(cf.align_type['center'])
        tree_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tree_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)

        # updates the initialisation flag
        self.is_init = True

    def create_child_tree_item(self, item_p, p_fld, i_edit=None):

        # initialisations
        item_ch, h_obj = None, None

        if p_fld not in self.s_props:
            # case is fields not in properties
            return item_ch, h_obj

        else:
            # otherwise, retrieve the main property values
            props = self.s_props[p_fld]
            p_type, p_value = props.get('type').strip(), props.get('value')
            if isinstance(p_value, dict) and (len(p_value) == 0):
                # special case: dictionary with no values
                return item_ch, h_obj

            else:
                # if the dictionary
                p_desc = self.reshape_para_desc(props.get('desc'))

        # if creating a group editbox item
        if i_edit is None:
            # case is the other parameter types
            lbl_str = '{0}'.format(props.get('label'))

        else:
            # case is an editbox grouping
            p_value = p_value[i_edit]
            p_type = p_type.replace('group_', '')
            lbl_str = 'Element #{0}'.format(i_edit + 1)

        # initialisations
        cb_fcn_base = pfcn(self.prop_update, props, p_fld)

        # creates the tree widget item
        item_ch = QTreeWidgetItem(item_p)
        item_ch.setText(0, lbl_str)
        item_ch.setToolTip(0, p_desc)

        match p_type:
            case p_type if p_type in ['edit_float', 'edit_int', 'edit_string']:
                # case is a lineedit
                if p_value is None:
                    p_value = ""

                elif (p_type != 'edit_string'):
                    p_value = str(self.convert_edit_value(p_value, p_fld, False))

                # creates the lineedit widget
                h_obj = cw.create_line_edit(None, p_value, font=self.item_child_font)
                h_obj.setObjectName(p_fld)

                # sets the object callback functions
                cb_fcn = pfcn(cb_fcn_base, h_obj)
                h_obj.editingFinished.connect(cb_fcn)

            case 'combobox':
                # case is a combobox
                h_obj = QComboBox()

                # adds the combobox items
                p_list = props.get('list')
                for p in p_list:
                    h_obj.addItem(p)

                # converts the combo value
                p_value = self.convert_combo_value(p_value, p_fld.split('-')[-1])
                i_sel0 = p_list.index(p_value)

                # sets the widget properties
                h_obj.setCurrentIndex(i_sel0)
                h_obj.setObjectName(p_fld)
                h_obj.setFont(self.item_child_font)
                h_obj.setEnabled(len(p_fld) > 1)

                # sets the object callback functions
                cb_fcn = pfcn(cb_fcn_base, h_obj)
                h_obj.currentIndexChanged.connect(cb_fcn)

            case 'checkbox':
                # case is a checkbox
                h_obj = QCheckBox()

                # sets the widget properties
                h_obj.setCheckState(cf.chk_state[p_value])
                h_obj.setStyleSheet("padding-left: 5px;")
                h_obj.setObjectName(p_fld)

                # sets the object callback functions
                cb_fcn = pfcn(cb_fcn_base, h_obj)
                h_obj.clicked.connect(cb_fcn)

            case p_type if p_type in ['group_edit_float', 'group_edit_int']:
                # case is a lineedit group

                # creates the editbox groups
                n_edit = len(p_value)
                for i_edit in range(n_edit):
                    # creates the child node
                    item_ch_d, h_obj_d = self.create_child_tree_item(item_ch, p_fld, i_edit)
                    if item_ch_d is None:
                        continue

                    # sets the item properties
                    item_ch_d.setTextAlignment(0, self.lbl_align_r)
                    item_ch.addChild(item_ch_d)

                    # adds the child tree widget item
                    h_obj_d.setFixedHeight(self.item_row_size)
                    h_obj_d.setObjectName('{0}_{1}'.format(p_fld, i_edit))
                    self.tree_prop.setItemWidget(item_ch_d, 1, h_obj_d)

                    # sets the object callback functions
                    cb_fcn = pfcn(cb_fcn_base, h_obj_d, i_edit)
                    h_obj_d.editingFinished.connect(cb_fcn)

                # # expands the children tree nodes
                # item_ch.setExpanded(True)

            case 'filespec':
                # case is a checkbox
                h_obj = cw.QEditButton(None, p_value, p_fld, b_sz=self.item_row_size - 2)
                h_obj.obj_edit.setReadOnly(True)

                # sets the object callback functions
                h_obj.connect(cb_fcn_base)

            case 'dict':
                # case is a dictionary

                # if there are no dictionary fields then exit
                if len(props.get('child')) == 0:
                    item_p.removeChild(item_ch)
                    return None, None

                # case is a dictionary
                for k in props.get('child'):
                    # creates the child node
                    item_ch_d, obj_prop_d = self.create_child_tree_item(item_ch, k)

                    # sets the item properties
                    if item_ch_d is not None:
                        self.set_item_align(item_ch_d, k)
                        item_ch.addChild(item_ch_d)

                    if obj_prop_d is not None:
                        # adds the child tree widget item
                        obj_prop_d.setFixedHeight(self.item_row_size)
                        self.tree_prop.setItemWidget(item_ch_d, 1, obj_prop_d)

            case 'fixed':
                item_p.removeChild(item_ch)
                return None, None

        # returns the objects
        return item_ch, h_obj

    # ---------------------------------------------------------------------------
    # Widget Update Event Functions
    # ---------------------------------------------------------------------------

    def prop_update(self, p_props, p_str, h_obj, i_edit=None):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        if isinstance(h_obj, QCheckBox):
            self.check_prop_update(h_obj, p_props, p_str)

        elif isinstance(h_obj, QLineEdit):
            self.edit_prop_update(h_obj, p_props, p_str)

        elif isinstance(h_obj, QComboBox):
            self.combo_prop_update(h_obj, p_props, p_str)

        elif isinstance(h_obj, cw.QEditButton):
            self.file_spec_update(h_obj, p_props, p_str)

    def check_prop_update(self, h_obj, s_prop_p, p_str):

        # updates the value field
        s_prop_p.set('value', h_obj.isChecked())
        self.prop_change.emit()

    def edit_prop_update(self, h_obj, s_prop_p, p_str, i_edit=None):

        # field retrieval
        new_str = h_obj.text()
        p_min = s_prop_p.get('min')
        p_max = s_prop_p.get('max')
        p_isint = s_prop_p.get('isint')

        if s_prop_p.get('type').strip() == 'edit_string':
            # case is a string field
            self.prop_change.emit()
            if i_edit is None:
                s_prop_p.set('value', new_str)
            else:
                s_prop_p.value[i_edit] = new_str

        else:
            # determines if the new value is valid
            chk_val = cf.check_edit_num(new_str, min_val=p_min, max_val=p_max, is_int=p_isint)
            if chk_val[1] is None:
                # converts the editbox value (parameter dependent)
                new_val = self.convert_edit_value(chk_val[0], p_str, True)
                if p_isint:
                    new_val = int(new_val)

                # case is the value is valid
                if i_edit is None:
                    s_prop_p.set('value', new_val)
                else:
                    s_prop_p.value[i_edit] = new_val

                # flag that the property has been updated
                self.prop_change.emit()

            else:
                # retrieves the previous value
                if i_edit is None:
                    p_val_pr = s_prop_p.get('value')
                else:
                    p_val_pr = s_prop_p.value[i_edit]

                # otherwise, reset the previous value
                p_val_pr = self.convert_edit_value(p_val_pr, p_str, False)
                if (p_val_pr is None) or isinstance(p_val_pr, str):
                    # case is the parameter is empty
                    h_obj.setText('')

                else:
                    # otherwise, update the numeric string
                    h_obj.setText('%g' % p_val_pr)

    def combo_prop_update(self, h_obj, s_prop_p, p_str):

        # parameter specific updates
        p_value = h_obj.currentText()
        match p_str[-1]:
            case p_name if p_name in ['detect_sign', 'peak_sign']:
                p_value = self.sign_l2v[p_value]

        # updates the property field
        self.prop_change.emit()
        s_prop_p.set('value', p_value)

    def file_spec_update(self, h_obj, s_prop_p, p_str):

        # sets the default file path
        def_path = s_prop_p.get('value')
        if (def_path is None) or (len(def_path) == 0):
            # if no path is set, use the current directory
            def_path = os.getcwd()

        # retrieves the parameter path info fields
        f_filter, f_caption, is_dir, is_open = self.get_para_path_info(p_str)

        # runs the file dialog
        file_dlg = cw.FileDialogModal(
            caption=f_caption, f_filter=f_filter, f_directory=def_path, dir_only=is_dir)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # sets the file path
            self.prop_change.emit()
            nw_path = file_dlg.selectedFiles()[0]
            s_prop_p.set('value', nw_path)

            # sets the other path fields
            f_name = os.path.split(nw_path)[1]
            h_obj.obj_edit.setText('../{0}'.format(f_name))
            h_obj.obj_edit.setToolTip(nw_path)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_item_align(self, item, p_fld):

        # sets the text alignment
        p_type_ch = self.s_props[p_fld].get('type').strip()
        if p_type_ch == 'dict':
            item.setTextAlignment(0, self.lbl_align_l)
        else:
            item.setTextAlignment(0, self.lbl_align_r)

    def convert_combo_value(self, p_value, p_fld):

        # special parameter field updates
        match p_fld:
            case p_fld if p_fld in ['detect_sign', 'peak_sign']:
                if isinstance(p_value, int):
                    p_value = self.sign_v2l[p_value]

            case 'version':
                p_value = str(p_value)

        # returns the parameter value
        return p_value

    def get_prop_field(self, p_str):

        s_prop_p = self.s_props[p_str]
        for p in p_str[1:]:
            s_prop_p = s_prop_p[p]

        return s_prop_p

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def get_para_path_info(p_str):

        # initialisations
        is_dir = False
        is_open = True

        match p_str:
            case 'neural_nets_path':
                # case is the neural network path file (yass)
                f_caption = 'Select Neural Network Path File'
                f_filter = 'Neural Network File (*.pt, *.ckpt)'

            case 'prm_template_name':
                # case is the prm template file (ironclust)
                f_caption = 'Select PRM Template File'
                f_filter = '.prm Template File (*.prm)'

            case 'tempdir':
                # case is the temporary directory (mountainsort4)
                is_dir, is_open, f_filter = True, False, None
                f_caption = 'Select Temporary File Directory'

            # case 'out_file':
            #     # case is the output file (herdingspikes)
            #     is_open = False
            #     f_caption = 'Set Output Filename'
            #
            # case 'output_filename':
            #     # case is the output filename (pykilosort)
            #     is_open = False
            #     f_caption = 'Set Output Filename'

        return f_filter, f_caption, is_dir, is_open

    @staticmethod
    def convert_edit_value(p_val, p_fld, is_set_para):

        # return a none value if already none
        if p_val is None:
            return None

        match p_fld:
            case 'chunk_memory':
                if is_set_para:
                    # case is setting the parameter value
                    return '{0}M'.format(p_val)
                else:
                    # case is getting the parameter value
                    return int(p_val.replace('M', ''))

            case 'chunk_duration':
                if is_set_para:
                    # case is setting the parameter value
                    return '{0}s'.format(p_val)
                else:
                    # case is getting the parameter value
                    return float(p_val.replace('s', ''))

            case _:
                # case is the other parameters
                return p_val

    def expand_all_nodes(self, item):

        # expands the current node
        item.setExpanded(True)
        for i in range(item.childCount()):
            self.expand_all_nodes(item.child(i))

    @staticmethod
    def reshape_para_desc(p_desc0):

        # parameters
        i_ofs = 0
        n_col_sp = 50
        np_desc0 = len(p_desc0)

        # if the string is short, then exit
        if (p_desc0 is None) or (np_desc0 == 0):
            return "No description provided..."

        elif np_desc0 <= n_col_sp:
            return p_desc0

        # otherwise, determine the points to place a carriage return
        p_desc_sp = np.array(p_desc0.split())
        n_desc_s = np.cumsum([len(x) + 1 for x in p_desc_sp])

        # inserts carriage returns at the necessary locations
        while np.any(n_desc_s > n_col_sp):
            ii = np.where(n_desc_s > n_col_sp)[0]
            if len(ii):
                jj = ii[0] + (i_ofs + 1)
                p_desc_sp = np.insert(p_desc_sp, jj, '\n')
                n_desc_s -= n_desc_s[ii[0]]
                i_ofs += 1

        # recombines the string
        return ' '.join(p_desc_sp)


# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeSortPara:  
"""


class SpikeSortPara(object):
    def __init__(self, ss_df, ss_info0, p_fld, s_name, value, desc):
        super(SpikeSortPara, self).__init__()

        # retrieves the parameter integer index
        i_row = self.get_para_index(ss_info0, p_fld, s_name)
        ss_info = ss_info0.iloc[i_row]

        # common parameter fields
        self.label = ss_info['Label']
        self.type = ss_info['Type']
        self.pptype = ss_info['PP']
        self.ctype = ss_info['C1']

        # other class fields
        self.desc = desc
        self.value = value
        self.dvalue = value
        self.ss_df = ss_df

        # numerical fields
        self.isint = self.type in ['group_edit_int', 'edit_int']
        self.min = convert_string(ss_info['Min'], self.isint)
        self.max = convert_string(ss_info['Max'], self.isint)

        # combobox fields
        self.list = []

        # children parameter fields (dictionaries)
        self.child = []
        self.parent = []

    def set(self, p_fld, p_value):
        setattr(self, p_fld, p_value)

    def get(self, p_fld):
        return getattr(self, p_fld)

    def get_para_class(self):

        if self.type == 'dict':
            return self.label.strip()
        else:
            return self.ctype.strip()

    def get_para_index(self, ss_info0, p_fld, s_name):

        if ss_info0.shape[0] > 1:
            p_fld_sp = p_fld.split('-')
            is_dict_fld = np.array([(x[0].islower() or (x[0] == '*')) for x in ss_info0['C1']])

            # special cases: dictionary fields (not captured by below cases)
            match p_fld:
                case 'spykingcircus2-whitening':
                    # whitening (for spykingcircus2)
                    return np.where(is_dict_fld)[0][0]

            if len(p_fld_sp) == 2:
                # parameter is not a sub-dictionary field
                i_fld = np.where(~is_dict_fld)[0]
                if len(i_fld) == 1:
                    # case is there is a unique parameter match
                    return i_fld[0]

                else:
                    # otherwise, parameter is solver specific
                    p_fld_f = p_fld_sp[-1]
                    match p_fld_f:
                        case 'lam':
                            match s_name:
                                case 'kilosort':
                                    # case is the kilosort solver
                                    return np.where(ss_info0['Type'] == 'group_edit_float')[0][0]

                                case s_name if s_name in ['kilosort2', 'kilosort2_5', 'kilosort3', 'pykilosort']:
                                    # case is the kilosort2/kilosort2.5 solver
                                    return np.where(ss_info0['Type'] == 'edit_float')[0][0]

                        case 'gather_mode':
                            match s_name:
                                case 'lupin':
                                    # case is the lupin solver
                                    return np.where(ss_info0['C1'] == 'Spike Detection')[0][0]

                                case 'tridesclous2':
                                    # case is the tridesclous2 solver
                                    return np.where(ss_info0['C1'] == 'Job Parameters')[0][0]

                        case 'min_firing_rate':
                            match s_name:
                                case 'lupin':
                                    # case is the lupin solver
                                    return np.where(ss_info0['C1'] == 'Template Matching')[0][0]

                                case 'tridesclous2':
                                    # case is the tridesclous2 solver
                                    return np.where(ss_info0['C1'] == 'Template Filtering')[0][0]

                                case 'spykingcircus2':
                                    # case is the tridesclous2 solver
                                    return np.where(ss_info0['C1'] == 'Other Parameters')[0][0]

                        case 'n_pca_features':
                            match s_name:
                                case 'lupin':
                                    # case is the lupin solver
                                    return np.where(ss_info0['C1'] == 'Feature Extraction')[0][0]

                                case 'tridesclous2':
                                    # case is the tridesclous2 solver
                                    return np.where(ss_info0['C1'] == 'Clustering')[0][0]

                        case 'n_peaks_per_channel':
                            match s_name:
                                case 'lupin':
                                    # case is the lupin solver
                                    return np.where(ss_info0['C1'] == 'Spike Selection')[0][0]

                                case 'tridesclous2':
                                    # case is the tridesclous2 solver
                                    return np.where(ss_info0['C1'] == 'Peak Selection')[0][0]

                        case 'n_svd_components_per_channel':
                            match s_name:
                                case s_name if s_name in ['lupin', 'simple']:
                                    # case is the lupin solver
                                    return np.where(ss_info0['C1'] == 'Feature Extraction')[0][0]

                                case 'tridesclous2':
                                    # case is the tridesclous2 solver
                                    return np.where(ss_info0['C1'] == 'Template Matching')[0][0]

                        case p_fld_f if p_fld_f in ['ms_before', 'ms_after']:
                            match s_name:
                                case s_name if s_name in ['lupin', 'tridesclous2']:
                                    # case is the lupin solver
                                    return np.where(ss_info0['C1'] == 'Template Matching')[0][0]

                                case 'simple':
                                    # case is the tridesclous2 solver
                                    return np.where(ss_info0['C1'] == 'Spike Detection')[0][0]

                        case 'seed':
                            match s_name:
                                case s_name if s_name in ['lupin', 'pykilosort', 'simple', 'tridesclous2']:
                                    # case is the lupin solver
                                    return np.where(ss_info0['C1'] == 'Merging')[0][0]

                                case 'spykingcircus2':
                                    # case is the tridesclous2 solver
                                    return np.where(ss_info0['C1'] == 'Other Parameters')[0][0]

                        case 'split_radius_um':
                            match s_name:
                                case 'lupin':
                                    # case is the lupin solver
                                    return np.where(ss_info0['C1'] == 'Clustering')[0][0]

                                case 'tridesclous2':
                                    # case is the tridesclous2 solver
                                    return np.where(ss_info0['C1'] == 'Merging')[0][0]

                        case 'whitening':
                            return np.where(ss_info0['C1'] == 'Preprocessing')[0][0]

            else:
                # parameter is a sub-dictionary field
                i_fld = np.where(is_dict_fld)[0]
                if len(i_fld) == 1:
                    # case is there is a unique parameter match
                    return i_fld[0]

                else:
                    # otherwise, parameter is solver specific
                    c_type = f"C{len(p_fld_sp) - 2}"
                    return np.where(ss_info0[c_type] == p_fld_sp[-2])[0][0]


        else:
            return 0

# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeSortInfo:  
"""


class SpikeSortInfo(QObject):
    # other static class fields
    ig_para = ['shift', 'scale', 'datashift',
               'fs', 'x_centers', 'delete_tmp_files']
    l_pattern = rf"(?<={re.escape('spikeinterface/')}).*?(?={re.escape('-')})"

    # group parameter to class key
    grp_key = {
        'sparsity': 'Sparsity',
        'clustering': 'Clustering',
        'whitening': 'Whitening',
        'selection': 'Selection',
        'cache_preprocessing': 'Cache Preprocessing',
    }

    def __init__(self, ses_obj=None):
        super(SpikeSortInfo, self).__init__()

        # sets the session object
        self.ses_obj = ses_obj

        # memory allocation
        self.all_s = available_sorters()
        self.local_s = installed_sorters()
        self.image_s = []
        self.other_s = []
        self.custom_s = []

        # spike sorting parameters
        self.ss_df = None
        self.ss_para = {}
        self.ss_info = {}
        self.p_dict_all = {}

        # loads the sorting parameters
        self.load_sort_para()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def load_sort_para(self):

        # sets up the property fields
        self.get_sorter_info()

        # reads the spike sorting parameter csv file
        self.ss_df = pd.read_csv(cw.ssort_para, header=0)

        # sets up the spike sorting parameter dictionary
        idx_ss = deepcopy(self.ss_df.columns).delete(0)
        for i_row, d_row in self.ss_df[idx_ss].iterrows():
            # field retrieval
            df_row = d_row.to_frame().T
            p = self.ss_df.iat[i_row, 0]

            if p in self.ss_info:
                # if parameter exists in dictionary, then appen to the dataframe
                self.ss_info[p] = pd.concat([self.ss_info[p], df_row], ignore_index=True).reset_index(drop=True)

            else:
                # otherwise, initailise the dataframe row
                self.ss_info[p] = df_row.reset_index(drop=True)

    def setup_all_sort_para(self):

        # initialisations
        s_props = {}
        s_list = ['kilosort4']
        ig_list = ['rtsort']

        # removes sorters from the ignore list
        for sl in ig_list:
            if sl in self.all_s:
                self.all_s.remove(sl)

        # sets the sorter setup index array
        ind_s = np.array(range(len(self.all_s)), dtype=int)
        for sl in s_list:
            # if available, reset the sorter index
            if sl in self.all_s:
                ind_m = ind_s != self.all_s.index(sl)
                ind_s = np.hstack((ind_s[ind_m], ind_s[~ind_m]))

        # retrieves the parameters (over all sorters)
        for sl in np.array(self.all_s)[ind_s]:
            s_props[sl] = self.setup_sorter_para(sl)

        # returns the sorting props
        return s_props

    def setup_sorter_para(self, s_name):

        # initialisations
        p_info = get_default_sorter_params(s_name)
        p_desc = get_sorter_params_description(s_name)

        # sorter specific updates
        p_fld_common = list(set(p_info.keys()).intersection(set(p_desc.keys())))
        match s_name:
            case 'spykingcircus2':
                # case is the tridesclous2 sorter
                if 'legacy' not in p_info['clustering']:
                    p_fld_new = ['legacy'] + list(p_info['clustering'].keys())
                    p_info['clustering']['legacy'] = p_info['clustering']['method'] != 'iterative-hdbscan'
                    p_info['clustering'] = cf.reorder_dict_fields(p_info['clustering'], p_fld_new)

        if s_name == 'kilosort4':
            pass

        # stores the parameter field for the sorter
        p_dict = {}
        p_fld_common = sorted(p_fld_common, key=str.casefold)
        self.setup_sorter_para_fields(s_name, p_fld_common, p_info, p_desc, p_str=[s_name], p_dict=p_dict)
        return p_dict

    def setup_sorter_para_fields(self, s_name, p_fld, p_value, p_desc=None, p_str=[], p_dict={}):

        # sets up the fields for all common parameters in the sorter
        for pf0 in p_fld:
            # skip any parameters that are being ignored
            if (pf0 in self.ig_para) or (pf0 not in self.ss_info):
                continue

            # sets up the base parameter field
            pf = '-'.join(p_str + [pf0])
            p_desc_f = self.get_description_field(p_desc, pf0)
            p_dict[pf] = SpikeSortPara(self.ss_df, self.ss_info[pf0], pf, s_name, p_value[pf0], p_desc_f)

            # resets the temporary dictionary field
            self.p_dict_all[pf] = p_dict[pf]

            # sets parameter specific fields
            pf_sp = pf.split('-')
            p_type = p_dict[pf].type
            match p_type:
                case p_type if p_type in ['edit_float', 'edit_int', 'group_edit_float', 'group_edit_int']:
                    # case is a numerical float
                    p_dict[pf] = self.setup_para_limits(pf, p_dict[pf])

                case 'combobox':
                    # case is a combobox (enumeration)
                    # d_name = pf.split('-')[-2]
                    p_dict[pf].set('list', self.setup_para_list(pf0, s_name, pf_sp[-2]))

                case 'dict':
                    # case is a dictionary field

                    # sets up the dictionary the dictionary parameters
                    self.setup_para_dict_fields(pf, p_dict)

                    # sets the dictionary children field names/properties
                    p_str_c = p_str + [pf0]
                    for k in p_dict[pf].value.keys():
                        p_str_ch = '-'.join(p_str_c + [k])
                        p_dict[pf].child.append(p_str_ch)
                        p_dict[p_str_ch].ctype = p_dict[pf].label

                case 'fixed':
                    # case is a fixed parameter field
                    match pf.split('-')[-1]:
                        case 'bad_channels':
                            pass

                            # # case is bad channels (kilosort4)
                            # if self.ses_obj is not None:
                            #     bad_ch = self.ses_obj.get_bad_channels()[1]
                            #     p_dict[pf].set('value', bad_ch)

        # returns the dictionary
        return p_dict

    def setup_para_limits(self, p_fld, p_dict):

        # sets the lower parameter limit
        p_lim_lo = 0 if p_dict.get('isint') else 0.

        # specific parameter updates
        match p_fld.split('-')[-1]:
            case 'batch_size':
                # case is the batch size (kilosort4)

                # determines the maximum batch size
                batch_size_max = int(self.ses_obj.get_frame_count() / 2)
                p_dict.set('max', batch_size_max)

                # if infeasible, then reset the batch size values
                if p_dict.get('value') > batch_size_max:
                    p_dict.set('value', batch_size_max)

            case _:
                # case is the other parameters

                # sets the parameter upper limit
                p_dict.set('max', self.get_limit_value(p_dict.get('max'), np.inf))

        # sets the lower/upper limits
        p_dict.set('min', self.get_limit_value(p_dict.get('min'), p_lim_lo))

        return p_dict

    def setup_para_dict_fields(self, p_fld, p_dict):

        # field retrieval
        p_str = p_fld.split('-')
        pf_ch = p_dict[p_fld].get('value')

        # sets up the parameter
        if (pf_ch is None) or (len(pf_ch) == 0):
            # determines the dictionary parameter field indices
            i_pf = self.ss_df["C1"] == p_str[1]
            for i in range(2, len(p_str)):
                i_pf = np.logical_and(i_pf, self.ss_df[f"C{i}"] == p_str[i])

            if len(p_str) == 6:
                # case is searching last parameter class column
                idx_pf = np.where(i_pf)[0]

            else:
                # otherwise, search the subsequent column
                i_pf2 = self.ss_df[f"C{len(p_str)}"] == '***'
                idx_pf = np.where(np.logical_and(i_pf, i_pf2))[0]

            # sets up the parameter dictionary
            pf_d = self.ss_df['Parameter'].iloc[idx_pf]
            pf_ch = self.setup_para_dict(p_str, pf_d)
            p_dict[p_fld].value = pf_ch

        # sets up the dictionary children parameter fields
        self.setup_sorter_para_fields(p_str[0], list(pf_ch.keys()), pf_ch, p_str=p_str, p_dict=p_dict)

    def setup_para_dict(self, p_str, pf_d):

        # memory allocation
        pf_ch = {}

        # sets up the dictionary fields
        for pf in pf_d:
            match pf:
                case pf if pf in ['clusterer', 'whitening']:
                    pf_ch[pf] = dict()

                case _:
                    if self.ss_info[pf].iloc[0]['Type'] == 'dict':
                        pf_ch[pf] = dict()
                    else:
                        pf_ch[pf] = self.get_default_para_value(p_str, pf)

        return pf_ch

    def get_default_para_value(self, p_str, pf):

        # field retrieval
        np_str = len(p_str)
        c1_type = p_str[1]

        match pf:
            # --- GENERAL JOB PARAMETERS --- #

            case 'chunk_duration':
                # case is the chunk duration
                return 1

            case 'mp_context':
                # case is the multiprocessor context
                return 'none'

            case 'n_jobs':
                # case is the file save job count
                return 1

            case 'pool_engine':
                # case is the parallel computing type
                return 'process'

            case 'progress_bar':
                # case is progressbar display
                return True

            # --- LUPIN SOLVER DICTIONARY PARAMETERS --- #

            case 'dtype':
                # case is the data type
                return 'float32'

            case 'filter_mode':
                # case is the filtering mode
                return 'sos'

            case 'filter_order':
                # case is the filtering order
                return 5

            case 'freq_max':
                # case is the min frequency
                return 6000

            case 'freq_min':
                # case is the max frequency
                return 300

            case 'ftype':
                # case is the filter type
                return 'bessel'

            case 'local_radius':
                # case is the neigbourhood radius
                return [30.0, 55.0]

            case 'margin_ms':
                # case is the buffer time
                return 5

            case 'min_local_neighbors':
                # case is the min local neighbour count
                return 5

            case 'operator':
                # case is the operator type
                return 'median'

            case 'reference':
                # case is the reference flag
                return 'global'

            # --- SIMPLE SOLVER DICTIONARY PARAMETERS --- #

            case 'affinity':
                # case is the affinity method
                return 'euclidean'

            case 'algorithm':
                # case is the clustering algorithm
                return 'best'

            case 'alpha':
                # case is the distance scale factor
                return 10

            case 'batch_size':
                # case is the batch size
                return 1024

            case 'cluster_selection_epsilon':
                # case is the cluster selection threshold
                return 0

            case 'cluster_selection_method':
                # case is the cluster selection method
                return 'eom'

            case 'cluster_selection_persistence':
                # case is the cluster persistance threshold
                return 0

            case 'convergence_iter':
                # case is the convergence iteration count
                return 15

            case 'core_dist_n_jobs':
                # case is the distributed core count
                match p_str[0]:
                    case 'simple':
                        # case is the simple solver
                        return 4

                    case 'spykingcircus2':
                        # case is the spykingcircus2 solver
                        return -1

            case 'covariance_type':
                # case is the covariance type
                return 'full'

            case 'damping':
                # case is the damping factor
                return 0.5

            case 'init':
                # case is the initialisation method
                return 'kmeans++'

            case 'isocut_threshold':
                # case is the clustering threshold
                return 2

            case 'leaf_size':
                # case is the branch leaf size
                return 40

            case 'max_cluster_size':
                # case is the max cluster size
                return 0

            case 'max_iter':
                # case is the max iteration count
                match p_str[0]:
                    case 'simple':
                        # case is the simple solver
                        return 300

                    case 'spykingcircus2':
                        # case is the spykingcircus2 solver
                        return 1000

            case 'max_iterations_per_pass':
                # case is the max iteration pass count
                return 500

            case 'max_no_improvement':
                # case is the max improvement count
                return 10

            case 'min_bin_freq':
                # case is the minimum binning frequency
                return 1

            case 'min_cluster_size':
                # case is the minimum cluster size
                match p_str[0]:
                    case 'simple':
                        # case is the simple solver
                        return 5

                    case 'spykingcircus2':
                        # case is the spykingcircus2 solver
                        match p_str[3]:
                            case 'clusterer':
                                return 10

                            case _:
                                return 20

            case 'n_clusters':
                # case is the cluster count
                return 8

            case 'n_components':
                # case is the PCA component count
                match p_str[0]:
                    case 'simple':
                        # case is the simple solver
                        return 1

                    case 'spykingcircus2':
                        # case is the spykingcircus2 solver
                        match np_str:
                            case 2:
                                return 5

                            case 4:
                                return 10

            case 'n_init':
                # case is the initial cluster size
                return 200

            case 'p':
                # case is the power exponent
                return 2

            case 'reassignment_ratio':
                # case is the reassignment ratio
                return 0.01

            case 'tol':
                # case is the tolerance
                return 1.0e-3

            # --- SPYKINGCIRCUS2 SOLVER PARAMETERS --- #

            case 'motion_aware':
                # case is allow drift flag
                return False

            case 'scale_amplitudes':
                # case is the amplitude scale flag
                return False

            case 'select_per_channel':
                # case is the select per channel flag
                return False

            case 'use_fine_detector':
                # case is the fine detector flag
                return True

            case 'engine':
                # case is the convolution calculation engine
                return 'numpy'

            case 'feature':
                # case is the spike feature
                return 'ptp'

            case 'peak_sign':
                # case is the peak sign
                return 'neg'

            case 'stop_criteria':
                # case is the stopping criteria
                return 'max_failures'

            case 'torch_device':
                # case is the torch device
                return 'cpu'

            case 'amplitude_fitting_radius_um':
                # case is the amplitude fitting neighbourhood size
                return 150.0

            case 'allow_single_cluster':
                # case the allow single cluster flag
                return True

            case 'apply_local_svd':
                # case is the apply local svd flag
                return True

            case 'bin_mode':
                # case is the binning mode
                return 'channels'

            case 'enforce_diagonal_to_zero':
                # case is enforce zero diagonal flag
                return True

            case 'normed_distances':
                # case is the normalise distance flag
                return True

            case 'min_firing_rate':
                # case is the minimum firing rate
                return 0.1

            case 'min_snr':
                # case is the minimum snr
                match c1_type:
                    case 'cleaning':
                        return 5.0

                    case 'clustering':
                        return 2.5

            case 'max_jitter_ms':
                # case is the maximum temporal shift
                return 0.2

            case 'remove_empty':
                # case is the remove empty flag
                return True

            case 'radius_um':
                # case is the neighbourhood radius
                match c1_type:
                    case 'general':
                        return 100

                    case 'motion_correction':
                        return 80

                    case c1_type if c1_type in ['clustering', 'detection']:
                        return 50

            case 'sparsify_threshold':
                # case is the sparsify threshold
                return 1

            case 'nb_projections':
                # case is the pca projection count
                return 10

            case 'sparse_mode':
                # case is the sparsity mode
                return 'knn'

            case pf if pf in ['neighborhood_radius_um', 'neighbors_radius_um']:
                # case is the neighbourhood radius
                return 50

            case 'n_neighbors':
                # case is the neighbourhood size
                return 5

            case 'use_lags':
                # case is use time lags flag
                return True

            case 'similarity_metric':
                # case is the similarity metric
                return 'I1'

            case 'similarity_thresh':
                # case is the similarity threshold
                return 0.8

            case 'num_shifts':
                # case is the temporal shift count
                return 3

            case 'window_length_ms':
                # case is the window length
                return 0.25

            case 'amplitude_mode':
                # case is the amplitude mode
                return 'peak_to_peak'

            case 'method':
                # case is the method selection
                match c1_type:
                    case 'clustering':
                        # case is the clustering methods
                        match p_str[3]:
                            case 'peak_localization_kwargs':
                                return 'center_of_mass'

                            case 'sparsity':
                                return 'snr'

                            case 'split':
                                return 'hdbscan'

                    case 'motion_correction':
                        # case is the motion correction methods
                        match p_str[2]:
                            case 'detect_kwargs':
                                return 'locally_exclusive'

                            case 'estimate_motion_kwargs':
                                return 'dredge_ap'

                            case 'localize_peak_kwargs':
                                return 'grid_convolution'

            case 'threshold':
                # case is the threshold value
                match c1_type:
                    case 'clustering':
                        return 0.25

                    case 'matching':
                        return 50.0

            case 'recursive':
                # case is the apply recursion flag
                return True

            case 'split_radius_um':
                # case is the split neighbourhood radius
                return 100.0

            case 'recursive_depth':
                # case is the recursion depth
                return 3

            case 'projection_mode':
                # case is the projection mode
                return 'tsvd'

            case 'min_size_split':
                # case is the minimum split size
                return 1

            case 'n_pca_features':
                # case is the PCA feature count
                return 1

            case 'ms_after':
                # case is the pre-peak duration
                match c1_type:
                    case 'clustering':
                        return 1.5

                    case 'matching':
                        return 0.8

            case 'ms_before':
                # case is the post-peak duration
                match c1_type:
                    case 'clustering':
                        return 0.5

                    case 'matching':
                        return 0.5

            case 'gather_mode':
                # case is the gathering mode
                match c1_type:
                    case 'detection':
                        return 'memory'

                    case 'matching':
                        return 'numpy'

            case 'skip_after_n_peaks':
                # case is the PCA feature count
                return None

            case 'amplitude_variance':
                # case is the amplitude variance
                return 1.0

            case 'cluster_radius_um':
                # case is the cluster neighbourhood radius
                return 150.0

            case 'detect_threshold':
                # case is the detection threshold
                match c1_type:
                    case 'motion_correction':
                        return 8

                    case c1_type if c1_type in ['detection', 'matching']:
                        return 5

            case 'detection_radius_um':
                # case is the detection radius
                return 100.0

            case 'exclude_sweep_ms':
                # case is the detection radius
                match c1_type:
                    case 'detection':
                        return 1.0

                    case c1_type if c1_type in ['motion_correction', 'matching']:
                        return 0.8

            case 'interpolation_time_bin_size_s':
                # case is the interpolation time bin size
                return 1.0

            case 'jitter_factor':
                # case is the jitter factor
                return 8.0

            case 'motion_step_um':
                # case is the drift step size
                return 2.0

            case 'omp_min_sps':
                # case is the OMP minimum firing rate
                return 0.1

            case 'peak_shift_ms':
                # case is the peak shift time
                return 0.2

            case 'relative_error':
                # case is the relative error
                return 5E-05

            case 'scale_max':
                # case is the maximum scale factor
                return np.inf

            case 'scale_min':
                # case is the minimum scale factor
                return 0.0

            case 'sparsity_radius_um':
                # case is the sparsity neighbourhood radius
                return 100.0

            case 'vicinity':
                # case is the vicinity area
                return 2.0

            case 'visibility_threshold':
                # case is the visibility threshold
                return 1.0

            case 'approx_rank':
                # case is the initial rank approximate
                return 5

            case 'max_failures':
                # case is the maximum failure count
                return 5

            case 'max_peeler_loop':
                # case is the maximum peeler loop count
                return 2

            case 'rank':
                # case is the SVD component count
                return 5

            case 'refractory_period_frames':
                # case is the refractory period size
                return 10

            case 'sample_shift':
                # case is the template sample shift
                return 2

            case 'amplitude_limits':
                # case is the amplitude limits
                return [0.7, 1.4]

            case 'amplitudes':
                # case is the allowable template amplitude limits
                return [0.6, np.inf]

    def setup_para_list(self, p_fld, s_name, d_name):

        match p_fld:
            case 'affinity':
                # case is the affinity method (simple)
                return ['euclidean', 'precomputed']

            case 'algorithm':
                # case is the optimisation algorithm (spykingcircus2)
                return ['best', 'generic', 'prims_kdtree', 'prims_balltree', 'boruvka_kdtree', 'boruvka_balltre']

            case 'amplitude_mode':
                # case is amplitude mode (spykingcircus2)
                return ['extremum', 'at_index', 'peak_to_peak']

            case 'bin_mode':
                # case is binning mode (spykingcircus2)
                return ['channels']

            case 'border_mode':
                # case is the border mode (spykingcircus2)
                return ['remove_channels', 'force_extrapolate', 'force_zeros']

            case 'cache_preprocessing_mode':
                # case is the preprocessing cache mode (lupin)
                return ['auto', 'memory', 'folder', 'file']

            case 'cluster_selection_method':
                # case is the cluster selection methods (simple/tridesclous2)
                return ['leaf', 'eom']

            case 'clusterer':
                # case is the clusterer type
                return ['hdbscan', 'isosplit', 'hdbscan-gpu', 'kmeans',
                        'mean_shift', 'affinity_propagation', 'gaussian_mixture']

            case 'common_ref_type':
                # case is the common reference type (ironclust)
                return ['none', 'mean', 'median', 'trimmean']

            case 'common_reference':
                # case is the common reference calculation type (herdingspikes)
                return ['average', 'median']

            case 'covariance_type':
                # case is the covariance type (simple)
                return ['full', 'tied', 'diag', 'spherical']

            case 'detect_sign':
                # case is the peak detection sign
                match s_name:
                    case s_name if s_name in ['combinato', 'hdsort', 'mountainsort4', 'tridesclous']:
                        # case is the older sorter types
                        return ['neg', 'pos']

                    case _:
                        # case is the newer sorter types
                        return ['neg', 'pos', 'both']

            case 'direction':
                # case is the peak direction (spykingcircus2)
                return ['x', 'y', 'z']

            case 'dtype':
                # case is the data type
                match s_name:
                    case 'yass':
                        # case is the yass solver
                        return ['int16']

                    case s_name if s_name in ['lupin', 'tridesclous2']:
                        # case is the lupin solver
                        return ['float32']

            case 'engine':
                # case is the convolution calculation engine (spykingcircus2)
                return ['numpy', 'torch', 'auto']

            case 'feature':
                # case is the signal feature flag (spykingcircus2)
                return ['ptp', 'mean', 'energy', 'peak_voltage']

            case 'feature_type':
                # case is the feature type
                match s_name:
                    case 'ironclust':
                        # case is the ironclust sorter
                        return ['gpca', 'pca', 'vpp', 'vmin', 'vminmax', 'cov', 'energy', 'xcov']

                    case s_name if s_name in ['waveclus', 'waveclus_snippets']:
                        # case is the waveclus/waveclus_snippets sorters:
                        return ['wav', 'pca']

            case p_fld if p_fld in ['filter_type', 'filter_detect_type']:
                # case is the filter/filter detect types (ironclust)
                return ["none", "bandpass", "wiener", "fftdiff", "ndiff"]

            case 'filter_mode':
                # case is the filtering mode (lupin)
                return ['sos', 'ba']

            case 'ftype':
                # case is the filtering function type (lupin/spykingcircus2)
                return ['butter', 'bessel', 'cheby1']

            case 'gather_mode':
                # case is the detected peak gathering mode (lupin/spykingcircus2/tridesclous2)
                return ['memory', 'numpy', 'zarr', 'none']

            case 'init':
                # case is the initialisation method (simple)
                return ['kmeans++', 'random']

            case 'initialize':
                # case is the template initialisation method (kilosort)
                return ['fromData', 'no']

            case 'loop_mode':
                # case is the loop mode (hdsort)
                return ['loop', 'local_parfor', 'grid']

            case 'method':
                # case is the method selection
                match d_name:
                    case 'clustering':
                        # case is the main clustering method
                        return ["iterative-hdbscan", "iterative-isosplit", "hdbscan-positions",
                                "random-projections", "graph-clustering"]

                    case 'peak_localization_kwargs':
                        return ["center_of_mass", "monopolar_triangulation", "grid_convolution"]

                    case 'sparsity':
                        return ["radius", "snr", "best_channels", "closest_channels",
                                "amplitude", "energy", "by_property"]

                    case 'clusterer':
                        return ["hdbscan", "isosplit"]

                    case 'detect_kwargs':
                        return ["locally_exclusive"]

                    case 'estimate_motion_kwargs':
                        return ["iterative_template", "dredge_ap", "decentralized", "medicine"]

                    case 'localize_peak_kwargs':
                        return ["monopolar_triangulation", "grid_convolution", "center_of_mass"]

                    case 'detection':
                        # case is detection comboboxes
                        return ["locally_exclusive", "matched_filtering"]

                    case 'matching':
                        # case is matching comboboxes
                        return ['nearest', 'nearest-svd', 'tdc-peeler', 'circus-omp', 'wobble']

                    case 'selection':
                        # case is selection comboboxes
                        return ['uniform']

            case 'mode':
                # case is the mode selection
                match d_name:
                    case 'cache_preprocessing':
                        # case is cache preprocessing (spykingcircus2/tridesclous2)
                        return ['memory', 'folder', 'zarr']

                    case 'whitening':
                        # case is whitening (spykingcircus2)
                        return ['local', 'global']

                    case 'weight_method':
                        # case is the weighting method (spykingcircus2)
                        return ["gaussian_2d"]

            case p_fld if p_fld in ['motion_correction_preset', 'preset']:
                # case is the motion correction presets (spykingcircus2/tridesclous2)
                p_list = ['dredge', 'dredge_fast', 'nonrigid_accurate',
                          'nonrigid_fast_and_accurate', 'rigid_fast', 'kilosort_like']
                if p_fld == 'motion_correction_preset':
                    p_list += ['medicine']

                return p_list

            case 'mp_context':
                # case is the (multiple solvers)
                return ["spawn", "none"]

            case 'operator':
                # case is the (lupin/tridesclous2)
                return ["median", "average"]

            case 'peak_sign':
                # case is the peak sign (simple/spykingcircus2/tridesclous2)
                return ['neg', 'pos', 'both']

            case 'pool_engine':
                # case is the parallel computing type (ironclust)
                return ['thread', 'process']

            case 'preprocessing_function':
                # case is the preprocessing function (pykilosort)
                return ['kilosort2', 'destriping']

            case 'projection_mode':
                # case is the projection mode (spykingcircus2)
                return ['tsvd']

            case 'reference':
                # case is the reference flag (lupin)
                return ['global', 'single', 'local']

            case 'scheme':
                # case is the sorting scheme
                return ['1', '2', '3']

            case 'scheme2_training_recording_sampling_mode':
                # case is the scheme 2 training sampling mode (mountainsort5)
                return ['initial', 'uniform']

            case 'similarity_metric':
                # case is the similarity metric (spykingcircus2)
                return ['cosine', 'I1', 'I2']

            case 'sparse_mode':
                # case is the sparsity mode (spykingcircus2)
                return ['knn']

            case 'spatial_interpolation_method':
                # case is the spatial interpolation method (spykingcircus2)
                return ['kriging', 'remove_channels']

            case 'stop_criteria':
                # case is the stopping criteria (spykingcircus2)
                return ['max_failures', 'omp_min_sps', 'relative_error']

            case 'template_matching_engine':
                # case is the template matching engine (lupin)
                return ['wobble', 'circus-omp', 'tdc-peeler', 'nearest-svd', 'nearest']

            case 'torch_device':
                # case is the torch device (kilosort4)
                match s_name:
                    case 'kilosort4':
                        # case is the kilosort4 solver
                        return ['auto', 'cuda', 'cpu']

                    case 'spykingcircus2':
                        # case is the spykingcircus2 solver
                        return ['none', 'cpu', 'cuda']

            case 'version':
                # case is the ironclust version (ironclust)
                return ['1', '2']

            case 'whitening':
                # case is kilosort1/kilosort2 whitening type
                return ['full', 'noSpikes']

            case 'win_shape':
                # case is the windowing shape (spykingcircus2)
                return ['gaussian', 'rect']

    # ---------------------------------------------------------------------------
    # Getter Functions
    # ---------------------------------------------------------------------------

    def get_sorter_info(self):

        try:
            # retrieves the docker client
            client = docker.from_env(timeout=5)
            image_list = client.images.list()

        except:
            # if there was a timeout error, then exit
            return

        # sets the other sorters
        self.other_s = list(set(self.all_s) - set(self.local_s))
        self.other_s.sort()

        # removes any local sorters from the other sorters list
        for l_sort in self.local_s:
            if l_sort in self.other_s:
                i_match = self.other_s.index(l_sort)
                self.other_s.pop(i_match)

        # removes any docker images from the other sorters list
        for img_l in image_list:
            # retrieves the sorter name from the repo tag
            r_tag = img_l.attrs['RepoTags'][0]
            s_name = re.search(self.l_pattern, r_tag)[0]

            # if the sorter is in the other sorters list, then remove it and add to the image sorter list
            if s_name in self.other_s:
                self.image_s.append(s_name)
                i_match = self.other_s.index(s_name)
                self.other_s.pop(i_match)

    def get_para_label(self, p_fld, s_type):

        pass

    def get_para_type(self, p_fld, s_type):

        pass

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def get_limit_value(p_val, p_val_def):

        if np.isnan(p_val) or np.isinf(p_val):
            # case is the parameter value is not set, so use the default value
            return p_val_def

        else:
            # otherwise, return the limit value
            return p_val

    @staticmethod
    def get_description_field(p_desc, pf):

        return '' if (p_desc is None) else p_desc[pf]
