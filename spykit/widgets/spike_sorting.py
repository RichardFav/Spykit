# module import
import re
import os
import time
import docker
import shutil
import platform
import numpy as np
import pandas as pd
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
    dlg_width = 450
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

    def __init__(self, main_obj=None, ss_config=None):
        super(SpikeSortingDialog, self).__init__(main_obj)

        # sets the input arguments
        self.main_obj = main_obj
        self.ss_config = ss_config

        if main_obj is not None:
            # creates the preprocessing run class object
            self.session = self.main_obj.session_obj.session
            self.prep_opt = [self.session.prep_obj.per_shank, self.session.prep_obj.concat_runs]

            # preprocessing options
            self.per_shank_pp = self.session.prep_obj.per_shank
            self.concat_runs_pp = self.session.prep_obj.concat_runs

        else:
            self.session = None

        # sets the central widget
        self.main_widget = QWidget(self)
        self.ss_obj = SpikeSortInfo(None if (main_obj is None) else main_obj.session_obj)

        # widget layouts
        self.main_layout = QGridLayout()
        self.sort_layout = QVBoxLayout()
        self.progress_layout = QVBoxLayout()
        self.cont_layout = QHBoxLayout()
        self.checkbox_layout = QHBoxLayout()

        # class widgets
        self.sort_frame = QFrame(self)
        self.progress_frame = QFrame(self)
        self.checkbox_frame = QFrame(self)
        self.cont_frame = QFrame(self)
        self.tab_group_sort = QTabWidget(self)
        self.prog_bar = cw.QDialogProgress(font=cw.font_lbl, is_task=True, timer_lbl=True)

        # other class widget
        self.button_cont = []
        self.checkbox_opt = []
        self.solver_tab = {}

        # boolean class fields
        self.has_ss = False
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
        c_str = ['Split Recording By Shank', 'Concatenate Experimental Runs']
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

        if self.main_obj is not None:
            # updates the checkbox properties
            self.set_checkbox_enabled_props()
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
            self.t_worker = ThreadWorker(self, self.run_get_info_worker, (self.ss_obj, 'kilosort4'))
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
            prep_obj = self.main_obj.session_obj.session.prep_obj
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
            q_str = 'Do you want to update the parameter changes?'
            u_choice = QMessageBox.question(self.main_obj, 'Update Changes?', q_str, cf.q_yes_no_cancel, cf.q_yes)
            if u_choice == cf.q_yes:
                # case is the user chose to update the parameters
                self.update_sort_para_changes()

            elif u_choice == cf.q_cancel:
                return

        # runs the post window close functions
        self.close_spike_sorting.emit(self.has_ss)

        # closes the window
        self.close()

    # ---------------------------------------------------------------------------
    # Spike Sorting Worker Functions
    # ---------------------------------------------------------------------------

    def set_checkbox_enabled_props(self):

        # sets the by shank checkbox enabled properties
        n_shank = self.main_obj.session_obj.get_shank_count()
        self.checkbox_opt[0].setEnabled((n_shank > 1) and (not self.per_shank_pp))

        # sets the concatenation checkbox enabled properties
        n_run = self.session.get_run_count()
        self.checkbox_opt[1].setEnabled((n_run > 1) and (not self.concat_runs_pp))

    def setup_spike_sorting_worker(self, sort_obj):

        # creates the threadworker object
        self.t_worker = ThreadWorker(self, self.run_spike_sorting_worker, sort_obj)
        self.t_worker.work_finished.connect(self.spike_sorting_complete)

        # starts the worker object
        self.t_worker.start()

    def run_spike_sorting_worker(self, sort_obj):

        # sorting parameters
        sort_config, sort_opt = sort_obj
        per_shank, concat_runs = sort_opt
        run_sorter_method = self.get_sorter_method()

        # runs the preprocessing
        self.session.sort_obj.sort(sort_config, per_shank, concat_runs, run_sorter_method)

    def spike_sorting_complete(self):

        # stops and updates the progressbar
        self.prog_bar.stop_timer()
        self.prog_bar.set_label('Spike Sorting Complete')
        self.prog_bar.set_full_prog()

        # resets the other properties
        self.set_sorting_props(True)

        # updates the boolean flags
        self.has_ss = True

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
            q_str = 'Spike sorting data already exists for this experiment. Do you want to overwrite?'
            u_choice = QMessageBox.question(self.main_obj, 'Overwrite Folder?', q_str, cf.q_yes_no, cf.q_yes)
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
        n_shank = self.main_obj.session_obj.get_shank_count()

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

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None,
                          p_min=None, p_max=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'ch_fld': ch_fld, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'p_min': p_min, 'p_max': p_max}

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

        # retrieves the
        s_props = ss_obj.setup_sorter_para('kilosort4')

        # initialises the progressbar
        self.update_prog.emit(1, s_props)


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

    # font objects
    gray_col = QColor(160, 160, 160, 255)
    item_child_font = cw.create_font_obj(8)
    item_font = cw.create_font_obj(9, True, QFont.Weight.Bold)
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
        QTreeWidget {
            font: Arial 8px;
            hover-background-color: transparent; 
            selection-background-color: transparent; 
        }                        
    """

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
            item = QTreeWidgetItem(self.tree_prop)

            # sets the item properties
            item.setText(0, pg)
            item.setFont(0, self.item_font)
            item.setFirstColumnSpanned(True)
            item.setExpanded(True)

            # adds the tree widget item
            self.tree_prop.addTopLevelItem(item)
            for j, ps in enumerate(p_fld_grp):
                if not is_ok_grp[j]:
                    continue

                elif len(self.s_props[ps].get('child')):
                    is_ok[np.array([x.startswith(ps) for x in p_fld])] = False
                    is_ok_grp[np.array([x.startswith(ps) for x in p_fld_grp])] = False

                if ps.endswith('seed'):
                    a = 1

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

        # REMOVE ME LATER
        item_ch, h_obj = None, None

        # retrieves the main property values
        props = self.s_props[p_fld]
        p_type, p_value = props.get('type').strip(), props.get('value')
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

                # expands the children tree nodes
                item_ch.setExpanded(True)

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

                # expands the children tree nodes
                item_ch.setExpanded(True)

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

    @staticmethod
    def reshape_para_desc(p_desc0):

        # parameters
        i_ofs = 0
        n_col_sp = 50

        # if the string is short, then exit
        if p_desc0 is None:
            return "No description provided..."

        elif len(p_desc0) <= n_col_sp:
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
    def __init__(self, ss_info, value, desc):
        super(SpikeSortPara, self).__init__()

        # sets the integer flag
        isint = ss_info['type'] in ['group_edit_int', 'edit_int']

        # common parameter fields
        self.label = ss_info['label']
        self.type = ss_info['type']
        self.ctype = ss_info['class']
        self.value = value
        self.dvalue = value
        self.desc = desc

        # numerical fields
        self.isint = isint
        self.min = convert_string(ss_info['min'], isint)
        self.max = convert_string(ss_info['max'], isint)

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

        if isinstance(self.ctype, float):
            return "Unclassified"

        else:
            return self.ctype.strip()


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
        self.ss_para = {}
        self.ss_info = {}

        # loads the sorting parameters
        self.load_sort_para()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def load_sort_para(self):

        # sets up the property fields
        self.get_sorter_info()

        # reads the spike sorting parameter csv file
        df = pd.read_csv(cw.ssort_para, header=0)
        for row in df.itertuples():
            self.ss_info[row.Parameter] = {
                'label': row.Label,
                'type': row.Type,
                'class': row.Class,
                'min': row.Min,
                'max': row.Max,
            }

    def setup_all_sort_para(self):

        # initialisations
        s_props = {}

        # retrieves the parameters (over all sorters)
        for sl in self.all_s:
            s_props[sl] = self.setup_sorter_para(sl)

        # returns the sorting props
        return s_props

    def setup_sorter_para(self, s_name):

        # initialisations
        p_info = get_default_sorter_params(s_name)
        p_desc = get_sorter_params_description(s_name)

        # determines the common info/description fields
        p_fld_common = list(set(p_info.keys()).intersection(set(p_desc.keys())))
        match s_name:
            # appends parameter fields (based on sorter type)
            case 'tridesclous2':
                # case is the tridesclous2 sorter
                p_fld_common += ['apply_motion_correction', 'motion_correction']

        # stores the parameter field for the sorter
        p_dict = {}
        self.setup_sorter_para_fields(s_name, p_fld_common, p_info, p_desc, p_str=[s_name], p_dict=p_dict)
        return p_dict

    def setup_sorter_para_fields(self, s_name, p_fld, p_value, p_desc=None, p_str=[], p_dict={}):

        # sets up the fields for all common parameters in the sorter
        for pf0 in p_fld:
            # skip any parameters that are being ignored
            if (pf0 in self.ig_para) or (pf0 not in self.ss_info):
                continue

            # special parameter
            match pf0:
                case pf0 if pf0 in ['threshold', 'mode', 'method', 'method_kwargs']:
                    # case is the threshold level
                    if len(p_str) > 1:
                        # if part of a sub-classification, then reset to the parent
                        self.ss_info[pf0]['class'] = self.ss_info[p_str[-1]]['class']

            # sets up the base parameter field
            pf = '-'.join(p_str + [pf0])
            p_desc_f = self.get_description_field(p_desc, pf0)
            p_dict[pf] = SpikeSortPara(self.ss_info[pf0], p_value[pf0], p_desc_f)

            # sets parameter specific fields
            p_type = p_dict[pf].type
            match p_type:
                case p_type if p_type in ['edit_float', 'edit_int', 'group_edit_float', 'group_edit_int']:
                    # case is a numerical float
                    p_dict[pf] = self.setup_para_limits(pf, p_dict[pf])

                case 'combobox':
                    # case is a combobox (enumeration)
                    d_name = pf.split('-')[-2]
                    p_dict[pf].set('list', self.setup_para_list(pf0, s_name, d_name))

                case 'dict':
                    # case is a dictionary field
                    p_str_c = p_str + [pf0]
                    self.setup_para_dictionary(pf, p_dict, s_name, p_str_c)

                    # sets the children field names
                    for k in p_dict[pf].value.keys():
                        p_dict[pf].child.append('-'.join(p_str_c + [k]))

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

    def setup_para_dictionary(self, p_fld, p_dict, s_name, p_str):

        # memory allocation
        p_fld_ch = p_dict[p_fld].get('value')
        self.setup_sorter_para_fields(s_name, list(p_fld_ch.keys()), p_fld_ch, p_str=p_str, p_dict=p_dict)

    def setup_para_list(self, p_fld, s_name, d_name=None):

        match p_fld:
            case 'amplitude_mode':
                # case is amplitude mode (spykingcircus2)
                return ['extremum', 'at_index', 'peak_to_peak']

            case 'clusterer':
                # case is the clusterer
                return ['hdbscan']

            case 'cluster_selection_method':
                # case is the cluster selection methods (simple/tridesclous2)
                return ['leaf', 'eom']

            case 'common_ref_type':
                # case is the common reference type (ironclust)
                return ['none', 'mean', 'median', 'trimmean']

            case 'common_reference':
                # case is the common reference calculation type (herdingspikes)
                return ['average', 'median']

            case 'detect_sign':
                # case is the peak detection sign
                match s_name:
                    case s_name if s_name in ['combinato', 'hdsort', 'mountainsort4', 'tridesclous']:
                        # case is the older sorter types
                        return ['neg', 'pos']

                    case _:
                        # case is the newer sorter types
                        return ['neg', 'pos', 'both']

            case 'dtype':
                # case is the data type (fixed)
                return ['int16']

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

            case 'ftype':
                # case is the filtering function type (spykingcircus2)
                return ['bessel']  # QUESTION: Any more filtering functions?!

            case 'loop_mode':
                # case is the loop mode (hdsort)
                return ['loop', 'local_parfor', 'grid']

            case 'method':
                # case is the method selection
                match d_name:
                    case d_name if d_name in ['clustering', 'matching']:
                        # case is clustering/matching dictionary
                        match s_name:
                            case s_name if s_name in ['spykingcircus2', 'tridesclous2']:
                                # case is the spykingcircus2 sorter
                                return ['naive', 'tridesclous', 'circus', 'circus-omp-svd', 'wobble']

                            case 'simple':
                                # case is the simple sorter
                                return ['hdbscan']  # QUESTION: Any more filtering functions?!

                    case 'detection':
                        # case is the detection dictionary
                        return ['by_channel', 'locally_exclusive', 'locally_exclusive_cl',
                                'by_channel_torch', 'locally_exclusive_torch', 'matched_filtering']

                    case 'selection':
                        # case is the selection dictionary (spykingcircus2/tridesclous2)
                        return ['uniform', 'uniform_locations', 'smart_sampling_amplitudes',
                                'smart_sampling_locations', 'smart_sampling_locations_and_time']

                    case 'sparsity':
                        # case is the sparsity dictionary (spykingcircus2)
                        return ['radius', 'best_channels', 'closest_channels', 'snr', 'amplitude', 'energy']

            case 'mode':
                # case is the mode selection
                match d_name:
                    case 'cache_preprocessing':
                        # case is cache preprocessing (spykingcircus2/tridesclous2)
                        return ['memory', 'folder', 'zarr']

                    case 'whitening':
                        # case is whitening (spykingcircus2)
                        return ['local', 'global']

            case 'peak_sign':
                # case is the peak sign (simple/spykingcircus2/tridesclous2)
                return ['neg', 'pos', 'both']

            case 'preprocessing_function':
                # case is the preprocessing function (pykilosort)
                return ['kilosort2', 'destriping']

            case 'preset':
                # case is the motion correction presets (spykingcircus2/tridesclous2)
                return ['dredge', 'dredge_fast', 'nonrigid_accurate',
                        'nonrigid_fast_and_accurate', 'rigid_fast', 'kilosort_like']

            case 'scheme':
                # case is the sorting scheme
                return ['1', '2', '3']

            case 'scheme2_training_recording_sampling_mode':
                # case is the scheme 2 training sampling mode (mountainsort5)
                return ['initial', 'uniform']

            case 'torch_device':
                # case is the torch device (kilosort4)
                return ['auto', 'cuda', 'cpu']

            case 'version':
                # case is the ironclust version (ironclust)
                return ['1', '2']

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

        match pf:
            case 'apply_motion_correction':
                return 'Apply Motion Correction?'

            case 'motion_correction':
                return 'Motion Correction Parameters'

            case _:
                return '' if (p_desc is None) else p_desc[pf]
