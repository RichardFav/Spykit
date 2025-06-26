# module import
import re
import time
import docker
import numpy as np
import pandas as pd
from copy import deepcopy
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
                             QLineEdit, QCheckBox, QTabWidget, QSizePolicy, QProgressBar)
from PyQt6.QtCore import pyqtSignal, QTimeLine, Qt, QObject

# widget dimensions
x_gap = 5

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

    # widget stylesheets
    border_style = "border: 1px solid;"
    no_border_style = "border: 0px; padding-top: 3px;"
    frame_border_style = """
        QFrame#sortFrame {
            border: 1px solid;
        }
    """

    def __init__(self, main_obj, ss_config):
        super(SpikeSortingDialog, self).__init__(main_obj)

        # sets the input arguments
        self.main_obj = main_obj
        self.ss_config = ss_config

        # creates the preprocessing run class object
        self.session = self.main_obj.session_obj.session
        self.prep_opt = [self.session.prep_obj.per_shank, self.session.prep_obj.concat_runs]

        # sets the central widget
        self.main_widget = QWidget(self)

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

        # sorter class fields
        self.all_sorters = available_sorters()
        self.local_sorters = installed_sorters()
        self.image_sorters = []
        self.other_sorters = []
        self.custom_sorters = []

        # other class widget
        self.prog_bar = []
        self.button_cont = []
        self.checkbox_opt = []
        self.solver_tab = {}

        # boolean class fields
        self.has_ss = False
        self.is_running = True
        self.is_updating = False
        self.per_shank = False
        self.concat_runs = False

        # preprocessing options
        self.per_shank_pp = self.session.prep_obj.per_shank
        self.concat_runs_pp = self.session.prep_obj.concat_runs

        # initialisations
        self.s_props = {}
        self.s_prop_flds = {}
        self.s_type = 'kilosort2'
        self.t_worker = None

        # initialises the major widget groups
        self.init_class_fields()
        self.init_sorting_frame()
        self.init_checkbox_opt()
        self.init_progress_frame()
        self.init_button_frame()
        self.set_widget_config()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_prop_fields(self, s_type):

        # retrieves the sorter list
        self.s_prop_flds[s_type] = {}
        s_list = getattr(self, '{0}_sorters'.format(s_type))

        # -----------------------------------------------------------------------
        # Sorting Properties
        # -----------------------------------------------------------------------

        for sl in s_list:
            # sets an empty sorter name (some sorters don't have descriptions)
            s_name = None

            #
            match sl:
                case 'combinato':
                    # case is Combinato

                    #
                    ds_list = ['Negative', 'Positive']

                    #
                    pp = {
                        # 'detect_sign': self.create_para_field('Use Common Avg Ref', 'combobox'),

                        # 'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort2'),
                        # 'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2')
                    }

                case 'hdsort':
                    # case is HDSort
                    pp = {}

                case 'herdingspikes':
                    # case is Herding Spikes
                    pp = {}

                case 'ironclust':
                    # case is Ironcluster
                    pp = {}
                    s_name = 'IronClust'

                case 'kilosort':
                    # case is Kilosort
                    pp = {}

                case 'kilosort2':
                    # case is Kilosort2
                    pp = {}

                case 'kilosort2_5':
                    # case is Kilosort2.5
                    pp = {}

                case 'kilosort3':
                    # case is Kilosort3
                    pp = {}

                case 'kilosort4':
                    # case is Kilosort4

                    # parameter values
                    p_max = np.inf
                    p_val0 = 60000

                    # sets up the parameter dictionary
                    pp = {
                        # 'batch_size': self.create_para_field(
                        #     'Data Batch Size', 'edit', p_val0, p_fld=sl, p_min=1, p_max=p_max),
                    }

                case 'klusta':
                    # case is Klusta
                    pp = {}

                case 'mountainsort4':
                    # case is Mountainsort4
                    pp = {}

                case 'mountainsort5':
                    # case is MountainSort5
                    pp = {}

                case 'pykilosort':
                    # case is pykilosort
                    pp = {}

                case 'simple':
                    # case is simple
                    pp = {}
                    s_name = 'Simple'

                case 'spykingcircus':
                    # case is Spyking Circus
                    pp = {}

                case 'spykingcircus2':
                    # case is Spyking Circus 2
                    pp = {}

                case 'tridesclous':
                    # case is Tridesclous
                    pp = {}

                case 'tridesclous2':
                    # case is Tridesclous2
                    pp = {}
                    s_name = 'Tridesclous2'

                case 'waveclus':
                    # case is Wave Clus
                    pp = {}

                case 'waveclus_snippets':
                    # case is Wave Clus
                    pp = {}
                    s_name = 'Wave Clus Snippets'

                case 'yass':
                    # case is Yass
                    pp = {}

            # retrieves the sorter description and name fields
            s_desc = get_sorter_description(sl)
            if s_name is None:
                s_name = self.get_sorter_name(s_desc)

            if (s_desc is None) or (len(s_desc) == 0):
                s_desc = 'No Description'

            # sets the property fields for the sorter
            self.s_prop_flds[s_type][sl] = {'name': s_name, 'props': pp, 'desc': s_desc}

        # # sets up the sorting tab parameter fields
        # pp_k2 = {'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort2'),
        #          'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2')}
        # pp_k2_5 = {'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort2_5'),
        #            'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2_5'), }
        # pp_k3 = {'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort3'),
        #          'freq_min': self.create_para_field('Min Frequency', 'edit', 300, p_fld='kilosort3'), }
        # pp_m5 = {'scheme': self.create_para_field('Scheme', 'edit', 2, p_fld='mountainsort5'),
        #          'filter': self.create_para_field('Filter', 'checkbox', False, p_fld='mountainsort5'), }

        # # stores the sorting properties
        # self.s_prop_flds = {
        #     'kilosort2': {'name': 'KiloSort 2', 'props': pp_k2},
        #     'kilosort2_5': {'name': 'KiloSort 2.5', 'props': pp_k2_5},
        #     'kilosort3': {'name': 'KiloSort 3', 'props': pp_k3},
        #     'mountainsort5': {'name': 'MountainSort 5', 'props': pp_m5},
        # }

        # initialises the fields for all properties
        for kp, vp in self.s_prop_flds[s_type].items():
            # sets up the parent field
            self.s_props[kp] = {}

            # sets the children properties
            for k, p in vp['props'].items():
                self.s_props[kp][k] = p['value']

    def init_class_fields(self):

        # creates the dialog window
        self.setWindowTitle("Spike Sorting Parameters")
        self.setFixedSize(self.dlg_width, self.dlg_height)
        # self.setFixedWidth(self.dlg_width)
        self.setWindowModality(Qt.WindowModality(1))
        self.setLayout(self.main_layout)

        # sets the main widget properties
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        # resets the frame object names
        for qf in self.findChildren(QFrame):
            qf.setObjectName('sortFrame')

        # sets up the property fields
        for s_type in ['local', 'image', 'other']:
            self.setup_prop_fields(s_type)

    def init_button_frame(self):

        # initialisations
        b_str = [self.sort_str[0], 'Close Window']
        cb_fcn = [self.start_spike_sort, self.close_window]

        # sets the control button panel properties
        self.cont_frame.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.cont_frame.setLayout(self.cont_layout)
        self.cont_frame.setStyleSheet(self.frame_border_style)
        self.cont_layout.setContentsMargins(0, 0, 0, 0)
        self.cont_layout.setSpacing(2 * x_gap)

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
            grp_tab = self.create_para_object(QVBoxLayout(), gf, None, 'sorttab', None)
            self.tab_group_sort.addTab(grp_tab, gn)
            self.tab_group_sort.setTabEnabled(i, grp_tab.isEnabled())

        # # # creates the tab group object
        # for k, v in self.s_prop_flds.items():
        #     tab_layout = QVBoxLayout()
        #     obj_tab = self.create_para_object(tab_layout, k, v['props'], 'tab', [k])
        #     self.tab_group_sort.addTab(obj_tab, v['name'])
        #
        # # tab-group change callback function
        # i_tab0 = list(self.s_props.keys()).index(self.s_type)
        # self.tab_group_sort.setCurrentIndex(i_tab0)
        # self.tab_group_sort.currentChanged.connect(self.sort_tab_change)

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

        # sets the by shank checkbox enabled properties
        n_shank = self.main_obj.session_obj.get_shank_count()
        self.checkbox_opt[0].setEnabled((n_shank > 1) and (not self.per_shank_pp))
        self.checkbox_opt[0].setCheckState(cf.chk_state[self.per_shank_pp])

        # sets the concatenation checkbox enabled properties
        n_run = self.session.get_run_count()
        self.checkbox_opt[1].setEnabled((n_run > 1) and (not self.concat_runs_pp))
        self.checkbox_opt[1].setCheckState(cf.chk_state[self.concat_runs_pp])

    def init_progress_frame(self):

        # sets the frame/layout properties
        self.progress_frame.setContentsMargins(0, 0, 0, 0)
        self.progress_frame.setLayout(self.progress_layout)
        self.progress_frame.setStyleSheet(self.frame_border_style)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(0)

        # creates the progressbar widgets
        for i in range(self.n_prog):
            prog_bar_new = cw.QDialogProgress(font=cw.font_lbl, is_task=bool(i))
            prog_bar_new.set_enabled(False)
            prog_bar_new.setContentsMargins(x_gap, x_gap, x_gap, i * x_gap)

            self.prog_bar.append(prog_bar_new)
            self.progress_layout.addWidget(prog_bar_new)

    def set_widget_config(self):

        # main layout properties
        self.main_layout.setHorizontalSpacing(x_gap)
        self.main_layout.setVerticalSpacing(x_gap)
        self.main_layout.setContentsMargins(2 * x_gap, x_gap, 2 * x_gap, 2 * x_gap)
        self.setLayout(self.main_layout)

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

    def create_sorter_tab_group(self, grp_type):

        # retrieves the list of sorters
        s_list = getattr(self, '{0}_sorters'.format(grp_type))

        #
        return len(s_list)

    def create_para_object(self, layout, p_str, p_val, p_type, p_str_p):

        match p_type:
            case p_type if p_type in ['tab', 'sorttab']:
                # case is a tab widget

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
                layout_para = QFormLayout(panel_frame) if p_type == 'tab' else QVBoxLayout()
                layout_para.setSpacing(x_gap)

                if p_type == 'tab':
                    # case is a solver parameter tab
                    if len(p_val):
                        # sets the layout parameters
                        layout_para.setLabelAlignment(cf.align_type['right'])
                        layout_para.setContentsMargins(2 * x_gap, 2 * x_gap, 2 * x_gap, x_gap)

                        # creates the tab parameter objects
                        for k, v in p_val.items():
                            self.create_para_object(layout_para, k, v, v['type'], p_str_p + [k])

                else:
                    # case is a solver tab group

                    # sets up the sort group tab
                    s_list = getattr(self, '{0}_sorters'.format(p_str))
                    if len(s_list):
                        # creates the tab group widget
                        obj_tab_group = QTabWidget()
                        layout_para.addWidget(obj_tab_group)
                        layout_para.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

                        # creates the solver parameter tabs
                        s_prop_tab = self.s_prop_flds[p_str]
                        for k, v in s_prop_tab.items():
                            obj_tab_para = self.create_para_object(QVBoxLayout(), k, v['props'], 'tab', [k])
                            obj_tab_group.addTab(obj_tab_para, v['name'])
                            obj_tab_para.setToolTip(v['desc'])

                    else:
                        obj_tab.setEnabled(False)

                # sets the tab layout
                panel_frame.setLayout(layout_para)
                obj_tab.setLayout(tab_layout)

                # returns the tab object
                return obj_tab

            # case is a checkbox
            case 'checkbox':
                # creates the checkbox widget
                obj_checkbox = cw.create_check_box(
                    None, p_val['name'], p_val['value'], font=cw.font_lbl, name=p_str)
                obj_checkbox.setContentsMargins(0, 0, 0, 0)

                # adds the widget to the layout
                layout.addRow(obj_checkbox)

                # sets up the slot function
                cb_fcn = pfcn(self.prop_update, p_str_p, obj_checkbox)
                obj_checkbox.stateChanged.connect(cb_fcn)

            case 'edit':
                # sets up the editbox string
                lbl_str = '{0}:'.format(p_val['name'])
                if p_val['value'] is None:
                    # parameter string is empty
                    edit_str = ''

                elif isinstance(p_val['value'], str):
                    # parameter is a string
                    edit_str = p_val['value']

                else:
                    # parameter is numeric
                    edit_str = '%g' % (p_val['value'])

                # creates the label/editbox widget combo
                obj_edit = cw.QLabelEdit(None, lbl_str, edit_str, name=p_str, font_lbl=cw.font_lbl)
                # obj_edit.obj_lbl.setFixedWidth(self.lbl_width)
                obj_edit.obj_lbl.setStyleSheet(self.no_border_style)
                layout.addRow(obj_edit)

                # sets up the label/editbox slot function
                cb_fcn = pfcn(self.prop_update, p_str_p)
                obj_edit.connect(cb_fcn)

    # ---------------------------------------------------------------------------
    # Widget Event Functions
    # ---------------------------------------------------------------------------

    def checkbox_split_shank(self):

        self.per_shank = self.checkbox_opt[0].checkState() == cf.chk_state[False]

    def checkbox_concat_expt(self):

        self.concat_runs = self.checkbox_opt[1].checkState() == cf.chk_state[False]

    def sort_tab_change(self):

        i_tab_nw = self.tab_group_sort.currentIndex()
        self.s_type = list(self.s_prop_flds)[i_tab_nw]

    def prop_update(self, p_str, h_obj):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        if isinstance(h_obj, QCheckBox):
            self.check_prop_update(h_obj, p_str)

        elif isinstance(h_obj, QLineEdit):
            self.edit_prop_update(h_obj, p_str)

        # flag that the property has been updated
        self.prop_updated.emit()

    def check_prop_update(self, h_obj, p_str):

        cf.set_multi_dict_value(self.s_props, p_str, h_obj.isChecked())

    def edit_prop_update(self, h_obj, p_str):

        # field retrieval
        str_para = []
        nw_val = h_obj.text()

        if p_str in str_para:
            # case is a string field
            cf.set_multi_dict_value(self.s_props, p_str, nw_val)

        else:
            # determines if the new value is valid
            chk_val = cf.check_edit_num(nw_val, min_val=0)
            if chk_val[1] is None:
                # case is the value is valid
                cf.set_multi_dict_value(self.s_props, p_str, chk_val[0])

            else:
                # otherwise, reset the previous value
                p_val_pr = self.s_props[p_str[0]][p_str[1]]
                if (p_val_pr is None) or isinstance(p_val_pr, str):
                    # case is the parameter is empty
                    h_obj.setText('')

                else:
                    # otherwise, update the numeric string
                    h_obj.setText('%g' % p_val_pr)

    def start_spike_sort(self):

        # if manually updating, then exit
        if self.is_updating:
            return

        # resets the button state
        self.is_running = not self.button_cont[0].isChecked()

        if self.is_running:
            # sets up the configuration dictionary
            sort_config = self.setup_config_dict()

            # retrieves the preprocessing information
            prep_obj = self.main_obj.session_obj.session.prep_obj
            sort_opt = (prep_obj.per_shank, prep_obj.concat_runs)

            # starts running the pre-processing
            self.setup_spike_sorting_worker((sort_config, sort_opt))

        else:
            # case is cancelling the calculations
            self.is_running = False

            # stops the worker
            self.t_worker.force_quit()
            self.t_worker.deleteLater()
            time.sleep(0.01)

            # disables the progressbar fields
            for pb in self.prog_bar:
                pb.set_progbar_state(False)

            # resets the other properties
            self.set_preprocess_props(True)
            self.button_control[0].setText(self.sort_str[0])

    def close_window(self):

        # runs the post window close functions
        self.close_spike_sorting.emit(self.has_ss)

        # closes the window
        self.close()

    # ---------------------------------------------------------------------------
    # Spike Sorting Worker Functions
    # ---------------------------------------------------------------------------

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

        # runs the preprocessing
        self.session.sort_obj.sort(sort_config, per_shank, concat_runs)

    def spike_sorting_complete(self):

        # pauses for a little bit...
        time.sleep(0.25)

        # updates the boolean flags
        self.has_ss = True

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

    def setup_config_dict(self):

        return {'sorting': {self.s_type: self.s_props[self.s_type]}}

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
            if s_desc_sp[0].isupper() or s_desc_sp.isnumeric():
                # if capitalised, then add
                s_name_list.append(s_desc_sp)

            else:
                # otherwise, exit the function
                break

        # returns the final sorter name
        return ' '.join(s_name_list)

# ----------------------------------------------------------------------------------------------------------------------

"""
    RunSpikeSorting:  
"""


class RunSpikeSorting(QObject):

    def __init__(self, s):
        super(RunSpikeSorting, self).__init__()

        # session object
        self.s = s

        # boolean class fields
        self.per_shank = False
        self.concat_runs = False

    def sort(self, ss_config, per_shank, concat_runs):

        # sets the input arguments
        self.per_shank = per_shank
        self.concat_runs = concat_runs
        self.ss_config = ss_config

        # REMOVE ME LATER
        ss_config = {'sorting': {'kilosort4': {'batch_size': 5000}}}

        # runs the spike sorting solver
        self.s.sort(
            ss_config,
            run_sorter_method="local",
            per_shank=self.per_shanke,
            concat_runs=self.concat_runs,
        )

        # initialises the progressbar
        self.update_prep_prog(0)


# ----------------------------------------------------------------------------------------------------------------------

"""
    RunSpikeSorting:  
"""


class SpikeSortPara(QObject):
    # common sorter fields

    # other static class fields
    l_pattern = rf"(?<={re.escape('spikeinterface/')}).*?(?={re.escape('-')})"

    def __init__(self, s):
        super(SpikeSortPara, self).__init__()

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

        # REMOVE ME LATER
        self.setup_sorter_para(self.all_s[0])

    def load_sort_para(self):

        # sets up the property fields
        self.get_sorter_info()

        # reads the spike sorting parameter csv file
        df = pd.read_csv(cw.ssort_para, header=0)
        for row in df.itertuples():
            self.ss_info[row.Parameter] = {'label': row.Label, 'type': row.Type}

    def get_sorter_info(self):

        # retrieves the docker client
        client = docker.from_env()
        if client is None:
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
        for img_l in client.images.list():
            # retrieves the sorter name from the repo tag
            r_tag = img_l.attrs['RepoTags'][0]
            s_name = re.search(self.l_pattern, r_tag)[0]

            # if the sorter is in the other sorters list, then remove it and add to the image sorter list
            if s_name in self.other_s:
                self.image_s.append(s_name)
                i_match = self.other_s.index(s_name)
                self.other_s.pop(i_match)

    def setup_sorter_para(self, s_name):

        # initialisations
        p_dict = {}
        p_info = get_default_sorter_params(s_name)
        p_desc = get_sorter_params_description(s_name)

        # determines the common info/description fields
        k_common = list(set(p_info.keys()).intersection(set(p_desc.keys())))
        match s_name:
            # appends parameter fields (based on sorter type)
            case 'tridesclous2'
                # case is the tridesclous2 sorter
                k_common += ['apply_motion_correction', 'motion_correction']

        # sets up the fields for all common parameters in the sorter
        for k in k_common:
            # sets up the base parameter field
            p_dict[k] = self.setup_para_field(self.ss_info[k], p_info[k], p_desc[k])

            # sets parameter specific fields
            p_type = p_dict[k]['type']
            match p_type:
                case p_type if p_type in ['edit_float', 'edit_int']:
                    # case is a numerical float
                    p_dict[k] = self.setup_para_limits(p_dict[k], s_name)

                case 'edit_string'
                    # case is a string
                    pass

                case 'group_edit_float':
                    # case is a multi-numerical float
                    pass

                case 'group_edit_int':
                    # case is a multi-numerical integer
                    pass

                case 'checkbox'
                    # case is a checkbox (boolean)
                    pass

                case 'combobox':
                    # case is a combobox (enumeration)
                    p_dict[k]['list'] = self.setup_para_list(k, s_name)

                case 'filespec':
                    # case is a file chooser
                    pass

                case 'dict':
                    # case is a dictionary field
                    p_dict[k] = self.setup_para_dictionary(p_dict[k], s_name)

    def setup_para_limits(self, p_dict, s_name=None, d_name=None):

        pass

    def setup_para_dictionary(self, p_dict, s_name=None, d_name=None):

        pass

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
                return ['bessel']                       # QUESTION: Any more filtering functions?!

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
                                return ['hdbscan']              # QUESTION: Any more filtering functions?!

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

    def get_para_label(self, p_fld, s_type):

        pass

    def get_para_type(self, p_fld, s_type):

        pass

    def setup_para_field(self, ss_info, value, desc):

        return {
            # common parameter fields
            'value': v,
            'label': ss_info['label'],
            'type': ss_info['type'],
            'desc': desc,

            # numerical fields
            'min': 0,
            'max': inf,
            'isint': ss_info['type'] in ['group_edit_int', 'edit_int'],

            # combobox fields
            'list': [],

            # children parameter fields (dictionaries)
            'children': [],
        }