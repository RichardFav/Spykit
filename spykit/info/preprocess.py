# custom module imports
import time
import numpy as np
from copy import deepcopy

# spikeinterface/spikewrap module import
from spikeinterface.preprocessing import depth_order
from spikeinterface.full import phase_shift, bandpass_filter, common_reference
from spikeinterface.preprocessing.motion import correct_motion
from spikewrap.structure._preprocess_run import PreprocessedRun
from spikewrap.structure._raw_run import (ConcatRawRun, SeparateRawRun)
from spikewrap.process._preprocessing import remove_channels, interpolate_channels

# spykit module imports
import spykit.common.common_widget as cw
import spykit.common.common_func as cf
from spykit.info.utils import InfoWidgetPara
from spykit.threads.utils import ThreadWorker

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QFrame, QTabWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QListWidget, QGridLayout, QSpacerItem, QDialog, QMainWindow, QProgressBar)
from PyQt6.QtCore import QSize, pyqtSignal, QObject, QTimeLine
from PyQt6.QtGui import QIcon, QFont, QColor

# ----------------------------------------------------------------------------------------------------------------------

# preprocessing task map dictionary
prep_task_map = {
    'Raw': 'raw',
    'Phase Shift': 'phase_shift',
    'Bandpass Filter': 'bandpass_filter',
    'Channel Interpolation': 'interpolate_channels',
    'Remove Bad Channels': 'remove_channels',
    'Common Reference': 'common_reference',
    'Whitening': 'whitening',
    'Drift Correction': 'drift_correct',
    'Sorting': 'sorting',
}

# array class fields
pp_flds = {
    'raw': 'Raw',
    'bandpass_filter': 'Bandpass Filter',
    'phase_shift': 'Phase Shift',
    'common_reference': 'Common Reference',
    'whitening': 'Whitening',
    'drift_correct': 'Drift Correction',
    'waveforms': 'Wave Forms',
    'sparce_opt': 'Sparsity Options',
    'interpolate_channels': 'Channel Interpolation',
    'remove_channels': 'Remove Bad Channels',
}

# other dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    PreprocessConfig:
"""


class PreprocessConfig(object):
    def __init__(self):

        self.prep_task = []
        self.task_name = []
        self.task_para = {}

        self.prep_opt = {
            "per_shank": False,
            "concat_runs": False,
        }

    def add_prep_task(self, p_task, t_para=None, t_name=None):

        self.prep_task.append(p_task)

        if t_para is not None:
            self.task_para[p_task] = t_para

        if t_name is not None:
            self.task_name.append(t_name)

    def set_prep_opt(self, per_shank, concat_runs):

        self.prep_opt = {
            "per_shank": per_shank,
            "concat_runs": concat_runs,
        }

    def setup_config_dicts(self):

        # sets up the configuration dictionary list
        pp_cfig = {}
        for i_ref, pt in enumerate(self.prep_task):
            # sets up the configuration for the preprocessing group
            pp_cfig[str(i_ref+1)] = [pt, self.task_para[pt]]

        # returns the configuration dictionary list
        return pp_cfig

    def clear(self):

        self.prep_task = []
        self.task_name = []
        self.task_para = {}

        self.prep_opt = {
            "per_shank": False,
            "concat_runs": False,
        }


# ----------------------------------------------------------------------------------------------------------------------

"""
    PreprocessInfoTab:
"""


class PreprocessInfoTab(InfoWidgetPara):
    def __init__(self, t_str, main_obj):
        super(PreprocessInfoTab, self).__init__(t_str, main_obj, layout=QFormLayout)

        # class field initialisation
        self.bad_channel_fcn = None
        self.keep_channel_fcn = None
        self.removed_channel_fcn = None
        self.is_channel_removed = None
        self.configs = PreprocessConfig()

        # initialises the major widget groups
        self.setup_prop_fields()
        self.init_filter_edit()
        self.init_property_frame()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_prop_fields(self):

        # -----------------------------------------------------------------------
        # Preprocessing Properties
        # -----------------------------------------------------------------------

        # list arrays
        mode_list = ['global', 'local']
        operator_list = ['median', 'average']
        reference_list = ['global', 'single', 'local']
        preset_list = ['dredge', 'dredge_fast', 'nonrigid_accurate',
                       'nonrigid_fast_and_accurate', 'rigid_fast', 'kilosort_like']

        # sets up the parameter fields
        pp_str = {
            # bandpass filter parameters
            'bandpass_filter': {
                'freq_min': self.create_para_field('Min Frequency', 'edit', 300),
                'freq_max': self.create_para_field('Max Frequency', 'edit', 6000),
                'margin_ms': self.create_para_field('Margin (ms)', 'edit', 5),
            },

            # common reference parameters
            'common_reference': {
                'operator': self.create_para_field('Operator', 'combobox', operator_list[0], p_list=operator_list),
                'reference': self.create_para_field('Reference', 'combobox', reference_list[0], p_list=reference_list),
            },

            # phase shift parameters
            'phase_shift': {
                'margin_ms': self.create_para_field('Margin (ms)', 'edit', 40),
            },

            # # whitening parameters
            # 'whitening': {
            #     'apply_mean': self.create_para_field('Subtract Mean', 'checkbox', False),
            #     'mode': self.create_para_field('Mode', 'combobox', mode_list[0], p_list=mode_list),
            #     'radius_um': self.create_para_field('Radius (um)', 'edit', 100),
            # },

            # drift correction parameters
            'drift_correct': {
                'preset': self.create_para_field('Preset', 'combobox', preset_list[0], p_list=preset_list),
            },

            # # sparsity option parameters
            # 'sparce_opt': {
            #     'sparse': self.create_para_field('Use Sparsity?', 'checkpanel', True, ch_fld=pp_sp),
            # },
        }

        # sets up the property fields for each section
        for pp_k in pp_flds.keys():
            # sets up the parent fields
            self.p_props[pp_k] = {}
            if pp_k not in pp_str:
                continue

            self.p_prop_flds[pp_k] = {
                'name': pp_flds[pp_k],
                'props': pp_str[pp_k],
            }

            # sets the children properties
            for k, p in pp_str[pp_k].items():
                self.p_props[pp_k][k] = p['value']

    # ---------------------------------------------------------------------------
    # Preprocessing Config Functions
    # ---------------------------------------------------------------------------

    def setup_config_dict(self, prep_task, is_sorting=False):

        # clears the configuration array
        self.configs.clear()

        # determines if there are any channels to remove
        rmv_channels = self.get_remove_channels()
        if len(rmv_channels):
            # if so, then append the remove channels step
            prep_task = ['Remove Bad Channels'] + prep_task

        # adds the preparation tasks to the configuration field
        for pp_t in prep_task:
            pp = prep_task_map[pp_t]

            match pp:
                case 'interpolate_channels':
                    # case is interpolate channel step
                    c_dict = {
                        'channel_ids': self.get_interp_channels(),
                    }

                    # adds the preprocessing task to the list
                    self.configs.add_prep_task(pp, c_dict, pp_t)

                case 'remove_channels':
                    # case is remove channel step

                    # sets up the config dictionary
                    c_dict = {
                        'channel_ids': rmv_channels,
                    }

                    # adds the preprocessing task to the list
                    self.configs.add_prep_task(pp, c_dict, pp_t)

                case _:
                    # case is another step type
                    self.configs.add_prep_task(pp, self.p_props[pp], pp_t)

        # sorting?
        if is_sorting:
            pass

        # returns the configuration dictionaries
        return self.configs.setup_config_dicts()

    def get_remove_channels(self):

        not_rmv = np.logical_not(self.is_channel_removed())
        not_keep = np.logical_not(self.keep_channel_fcn())
        return self.bad_channel_fcn(['out'], not_keep, not_rmv)

    def get_interp_channels(self):

        is_keep = self.keep_channel_fcn()
        not_rmv = np.logical_not(self.is_channel_removed())
        is_feas = np.logical_or(is_keep, not_rmv)

        return self.bad_channel_fcn(['dead', 'noise'], is_feas=is_feas)

# ----------------------------------------------------------------------------------------------------------------------

"""
    PreprocessSetup:
"""


class PreprocessSetup(QDialog):
    # parameters
    n_but = 4
    gap_sz = 5
    but_height = 20
    dlg_height = 300
    dlg_width = 450

    # array class fields
    b_icon = ['arrow_right', 'arrow_left', 'arrow_up', 'arrow_down']
    tt_str = ['Add Task', 'Remove Task', 'Move Task Up', 'Move Task Down']

    # widget stylesheets
    border_style = "border: 1px solid;"
    frame_style = QFrame.Shape.WinPanel | QFrame.Shadow.Plain
    frame_border_style = """
        QFrame#prepFrame {
            border: 1px solid;
        }
    """

    def __init__(self, main_obj=None):
        super(PreprocessSetup, self).__init__(main_obj)

        # sets the input arguments
        self.main_obj = main_obj

        # creates the preprocessing run class object
        session = self.main_obj.session_obj.session
        self.prep_obj = RunPreProcessing(session._s)

        # class layouts
        self.list_layout = QGridLayout(self)
        self.checkbox_layout = QHBoxLayout()
        self.button_layout = QVBoxLayout()
        self.task_layout = QGridLayout()
        self.progress_layout = QVBoxLayout()
        self.control_layout = QHBoxLayout()

        # class widgets
        self.button_frame = QFrame(self)
        self.task_frame = QFrame(self)
        self.progress_frame = QFrame(self)
        self.checkbox_frame = QWidget(self)
        self.add_list = QListWidget(None)
        self.task_list = QListWidget(None)
        self.spacer_top = QSpacerItem(20, 60, cf.q_min, cf.q_max)
        self.spacer_bottom = QSpacerItem(20, 60, cf.q_min, cf.q_max)

        # other class field initialisations
        self.task_order = []
        self.checkbox_opt = []
        self.button_control = []
        self.prog_bar = []

        # array class fields
        self.l_task = ['Phase Shift', 'Bandpass Filter', 'Channel Interpolation', 'Common Reference', 'Drift Correction']

        # boolean class fields
        self.has_pp = False
        self.per_shank = False
        self.concat_runs = False

        # initialises the class fields
        self.init_class_fields()
        self.init_task_para_frame()
        self.init_progress_frame()
        self.init_control_buttons()
        self.set_widget_config()

        # self.setModal(True)

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the dialog window properties
        self.setWindowTitle("Preprocessing Setup")
        self.setFixedSize(self.dlg_width, self.dlg_height)

        for qf in self.findChildren(QFrame):
            qf.setObjectName('prepFrame')

    def init_task_para_frame(self):

        # sets the frame/layout properties
        self.task_frame.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.task_frame.setLayout(self.task_layout)
        self.task_frame.setStyleSheet(self.frame_border_style)
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_layout.setHorizontalSpacing(x_gap)

        # initialises the checkbox options
        self.init_checkbox_opt()
        self.init_task_listboxes()
        self.init_order_buttons()

        # adds the items to the task layout
        self.task_layout.addWidget(self.task_list, 0, 0, 1, 1)
        self.task_layout.addLayout(self.button_layout, 0, 1, 1, 1)
        self.task_layout.addWidget(self.add_list, 0, 2, 1, 1)
        self.task_layout.addWidget(self.checkbox_frame, 1, 0, 1, 3)

        # sets the task layout row/column stretches
        self.task_layout.setColumnStretch(0, self.gap_sz)
        self.task_layout.setColumnStretch(1, 1)
        self.task_layout.setColumnStretch(2, self.gap_sz)
        self.task_layout.setRowStretch(0, 5)
        self.task_layout.setRowStretch(1, 1)

    def init_checkbox_opt(self):

        # initialisations
        c_str = ['Split Recording By Shank', 'Concatenate Experimental Runs']
        cb_fcn = [self.checkbox_split_shank, self.checkbox_concat_expt]

        # sets the frame/layout properties
        self.checkbox_frame.setContentsMargins(0, 0, 0, 0)
        self.checkbox_frame.setLayout(self.checkbox_layout)
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)
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
            # checkbox_new.setStyleSheet(self.border_style)

        # sets the by shank checkbox enabled properties
        n_shank = self.main_obj.session_obj.get_shank_count()
        self.checkbox_opt[0].setEnabled(n_shank > 1)

        # sets the concatenation checkbox enabled properties
        n_run = self.main_obj.session_obj.session.get_run_count()
        self.checkbox_opt[1].setEnabled(n_run > 1)

        # determines if partial preprocessing has taken place
        pp_runs = self.main_obj.session_obj.get_pp_runs()
        if len(pp_runs):
            # flag that partial preprocessing has taken place
            self.has_pp = True
            self.per_shank = self.main_obj.session_obj.session.prep_obj.per_shank
            self.concat_runs = self.main_obj.session_obj.session.prep_obj.concat_runs

            # sets the checkbox values
            self.checkbox_opt[0].setCheckState(cf.chk_state[self.per_shank])
            self.checkbox_opt[1].setCheckState(cf.chk_state[self.concat_runs])

            # disables the checkboxes
            for cb_opt in self.checkbox_opt:
                cb_opt.setEnabled(False)

            # removes the tasks from the list that have been completed
            for pp_names in [pp_flds[v[0]] for v in pp_runs[0]._pp_steps.values()]:
                if pp_names in self.l_task:
                    self.l_task.pop(self.l_task.index(pp_names))

        # channel interpolation field (if it exists) if either a) there are no bad channels or
        # b) the common reference calculations have already taken place
        if 'Channel Interpolation' in self.l_task:
            bad_ch_id = self.main_obj.session_obj.get_bad_channels()
            if (len(bad_ch_id) == 0) or ('Common Reference' not in self.l_task):
                self.l_task.pop(self.l_task.index('Channel Interpolation'))

    def init_task_listboxes(self):

        # added list widget properties
        self.add_list.setStyleSheet(self.border_style)
        self.add_list.itemClicked.connect(self.set_button_props)

        # task list widget properties
        self.task_list.addItems(self.l_task)
        self.task_list.setStyleSheet(self.border_style)
        self.task_list.itemClicked.connect(self.set_button_props)

    def init_order_buttons(self):

        # initialisations
        cb_fcn = [self.button_add, self.button_remove, self.button_up, self.button_down]

        # button layout properties
        self.button_layout.setSpacing(x_gap)
        self.button_layout.addItem(self.spacer_top)

        # adds the spacers/buttons to the button layout
        for bi, cb, tt in zip(self.b_icon, cb_fcn, self.tt_str):
            # creates the button object
            button_new = cw.create_push_button(self, "")

            # sets the button properties
            button_new.setObjectName(bi)
            button_new.setToolTip(tt)
            button_new.setIcon(QIcon(cw.icon_path[bi]))
            button_new.setIconSize(QSize(self.but_height - 2, self.but_height - 2))
            button_new.setFixedSize(self.but_height, self.but_height)
            button_new.setStyleSheet(self.border_style)

            # sets the button callback
            button_new.pressed.connect(cb)
            self.button_layout.addWidget(button_new)
            self.button_control.append(button_new)

        # adds the button spacer object
        self.button_layout.addItem(self.spacer_bottom)

    def init_progress_frame(self):

        # sets the frame/layout properties
        self.progress_frame.setContentsMargins(0, 0, 0, 0)
        self.progress_frame.setLayout(self.progress_layout)
        self.progress_frame.setStyleSheet(self.frame_border_style)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(0)

        # creates the progressbar widgets
        for i in range(2):
            prog_bar_new = QPreprocessProgWidget(font=cw.font_lbl, is_task=bool(i))
            prog_bar_new.set_enabled(False)
            prog_bar_new.setContentsMargins(x_gap, x_gap, x_gap, i * x_gap)

            self.prog_bar.append(prog_bar_new)
            self.progress_layout.addWidget(prog_bar_new)

    def init_control_buttons(self):

        # initialisations
        b_str = ['Start Preprocessing', 'Close Window']
        cb_fcn = [self.start_preprocess, self.close_window]

        # sets the frame/layout properties
        self.button_frame.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.button_frame.setLayout(self.control_layout)
        self.button_frame.setStyleSheet(self.frame_border_style)
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.control_layout.setSpacing(2 * self.gap_sz)

        # creates the control buttons
        for bs, cb in zip(b_str, cb_fcn):
            # creates the button object
            button_new = cw.create_push_button(self, bs, font=cw.font_lbl)
            self.control_layout.addWidget(button_new)
            self.button_control.append(button_new)

            # sets the button properties
            button_new.pressed.connect(cb)
            button_new.setFixedHeight(cf.but_height)
            button_new.setStyleSheet(self.border_style)

        # sets the control button properties
        self.set_button_props()

    def set_widget_config(self):

        # main layout properties
        self.list_layout.setHorizontalSpacing(x_gap)
        self.list_layout.setVerticalSpacing(x_gap)
        self.list_layout.setContentsMargins(2 * x_gap, x_gap, 2 * x_gap, 2 * x_gap)
        self.setLayout(self.list_layout)

        # adds the main widgets to the main layout
        self.list_layout.addWidget(self.task_frame, 0, 0, 1, 1)
        self.list_layout.addWidget(self.progress_frame, 1, 0, 1, 1)
        self.list_layout.addWidget(self.button_frame, 2, 0, 1, 1)

        # set the grid layout column sizes
        self.list_layout.setRowStretch(0, 6)
        self.list_layout.setRowStretch(1, 2)
        self.list_layout.setRowStretch(2, 1)

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def checkbox_split_shank(self):

        self.per_shank = self.checkbox_opt[0].checkState() == cf.chk_state[False]

    def checkbox_concat_expt(self):

        self.concat_runs = self.checkbox_opt[1].checkState() == cf.chk_state[False]

    def button_add(self):

        # swaps the selected item between lists
        i_index = self.task_list.currentIndex()
        task_add = self.task_list.takeItem(i_index.row()).text()

        if self.check_task_order(self.task_order + [task_add]):
            # adds the task/list items
            self.add_list.addItem(task_add)
            self.task_order.append(task_add)

            # updates the button properties
            self.set_button_props()

        else:
            # otherwise, re-add the item to the list item
            self.task_list.addItem(task_add)

    def button_remove(self):

        # swaps the selected item between lists
        i_index = self.add_list.currentIndex()
        task_remove = self.add_list.takeItem(i_index.row()).text()

        # removes the task/list items
        self.task_list.addItem(task_remove)
        self.task_order.pop(i_index.row())

        # updates the button properties
        self.set_button_props()

    def button_up(self):

        # field retrieval
        i_row_sel = self.add_list.currentRow()
        item_sel = self.add_list.item(i_row_sel)
        item_prev = self.add_list.item(i_row_sel - 1)

        # determines if the new order is feasible
        task_order_new = self.get_reordered_list(i_row_sel + np.asarray([-1, 0]))
        if self.check_task_order(task_order_new):
            # reorders the items
            name_sel, name_prev = item_sel.text(), item_prev.text()
            item_sel.setText(name_prev)
            item_prev.setText(name_sel)

            # resets the row selection and button properties
            self.task_order = task_order_new
            self.add_list.setCurrentRow(i_row_sel - 1)
            self.set_button_props()

    def button_down(self):

        # field retrieval
        i_row_sel = self.add_list.currentRow()
        item_sel = self.add_list.item(i_row_sel)
        item_next = self.add_list.item(i_row_sel + 1)

        # determines if the new order is feasible
        task_order_new = self.get_reordered_list(i_row_sel + np.asarray([0, 1]))
        if self.check_task_order(task_order_new):
            # reorders the items
            name_sel, name_next = item_sel.text(), item_next.text()
            item_sel.setText(name_next)
            item_next.setText(name_sel)

            # resets the row selection and button properties
            self.task_order = task_order_new
            self.add_list.setCurrentRow(i_row_sel + 1)
            self.set_button_props()

    def start_preprocess(self):

        if self.main_obj is not None:
            # sets the preprocessing options
            prep_tab = self.main_obj.info_manager.get_info_tab('preprocess')
            prep_tab.configs.set_prep_opt(self.per_shank, self.concat_runs)

            # retrieves the selected tasks
            prep_task = []
            for i in range(self.add_list.count()):
                prep_task.append(self.add_list.item(i).text())

            # starts running the pre-processing
            prep_opt = (self.per_shank, self.concat_runs)
            self.main_obj.setup_preprocessing_worker(prep_task, prep_opt)

            # # closes the dialog window
            # self.close_window()

    def close_window(self):

        self.close()

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_button_props(self):

        # field retrieval
        n_added = self.add_list.count() - 1
        i_row_add = self.add_list.currentRow()
        i_row_task = self.task_list.currentRow()
        is_added_sel = i_row_add >= 0

        # updates the button properties
        self.button_control[0].setEnabled(i_row_task >= 0)
        self.button_control[1].setEnabled(i_row_add >= 0)
        self.button_control[2].setEnabled(is_added_sel and (i_row_add > 0))
        self.button_control[3].setEnabled(is_added_sel and (i_row_add < n_added))
        self.button_control[4].setEnabled(n_added >= 0)

    def check_task_order(self, task_new):

        # first check: ensure that bad channel interpolation occurs
        #              before common reference averaging

        # determines if
        i_fld = np.zeros(2, dtype=int)
        task_fld = ['Channel Interpolation', 'Common Reference']

        # determines if the required tasks have been added
        for i, tf in enumerate(task_fld):
            if tf in task_new:
                # if so, then determine the task index
                i_fld[i] = task_new.index(tf)

            else:
                # otherwise, return a false value
                return True

        # if the order is infeasible, then output an error to screen
        if np.diff(i_fld)[0] < 0:
            t_str = 'Preprocessing Order Error'
            cf.show_error("Bad Channel Interpolation must occur before Common Reference Averaging.", t_str)
            return False

        # otherwise, return a feasible flag
        return True

    def get_reordered_list(self, i_swap):

        tasks = deepcopy(self.task_order)
        print(tasks)

        tasks[i_swap[0]], tasks[i_swap[1]] = tasks[i_swap[1]], tasks[i_swap[0]]
        return tasks

# ----------------------------------------------------------------------------------------------------------------------

"""
    RunPreProcessing: 
"""


class RunPreProcessing(QObject):
    # pyqtSignal functions
    update_prog = pyqtSignal(str, float)

    # preprocessing function dictionary
    pp_funcs = {
        "phase_shift": phase_shift,
        "bandpass_filter": bandpass_filter,
        "common_reference": common_reference,
        "remove_channels": remove_channels,
        "interpolate_channels": interpolate_channels,
        "drift_correct": correct_motion,
    }

    def __init__(self, s):
        super(RunPreProcessing, self).__init__()

        # session object
        self.s = s

        # index/scalar class fields
        self.i_run = None
        self.n_run = None
        self.p_run = None
        self.i_shank = None
        self.n_shank = None
        self.p_shank = None
        self.i_step = None
        self.n_step = None

        # other class field initialisations
        self.per_shank = None
        self.concat_runs = None
        self.prepro_dict = None
        self.pp_steps_new = None
        self.pp_steps_tot = None
        self.run_name = None
        self.file_format = None
        self.raw_data_path = None

    def preprocess(self, pp_steps, per_shank, concat_runs):

        # sets the input arguments
        self.per_shank = per_shank
        self.concat_runs = concat_runs
        self.pp_steps_new = pp_steps

        # initialises the progressbar
        self.update_prep_prog(0)

        # runs the preprocessing task grouping
        runs_to_pp: list[SeparateRawRun | ConcatRawRun]

        # sets the preprocessing runs (based on previous calculation type)
        if len(self.s._pp_runs):
            # case is there has already been partial preprocessing
            is_raw = False
            runs_to_pp = [x._preprocessed for x in self.s._pp_runs]

            # appends the new preprocessing steps to the total list
            i_ofs = len(self.pp_steps_tot)
            for i, pp_s in pp_steps.items():
                i_tot = int(i) + i_ofs
                self.pp_steps_tot[(str(i_tot))] = pp_s

        else:
            # case is there is no preprocessing
            is_raw = True
            self.pp_steps_tot = pp_steps

            # sets the raw runs to preprocess
            if concat_runs:
                runs_to_pp = [self.s._get_concat_raw_run()]
            else:
                runs_to_pp = self.s._raw_runs

            # retrieves the run-specific information
            self.run_name = [run._run_name for run in runs_to_pp]
            self.file_format = [run._file_format for run in runs_to_pp]
            self.raw_data_path = [run._parent_input_path for run in runs_to_pp]

        # runs the preprocessing for each run (for all tasks)
        self.n_run = len(runs_to_pp)
        for i_run_pp, run in enumerate(runs_to_pp):
            # update the progressbar for the current run
            self.update_prep_prog(1, i_run_pp)

            # runs the preprocessing for the current run
            preprocessed_run = self.preprocess_run(run, is_raw)

            # retrieves the run names
            orig_run_names = (
                run._orig_run_names if isinstance(run, ConcatRawRun) else None
            )

            # stores the preprocessing data
            self.s._pp_runs.append(
                PreprocessedRun(
                    run_name=self.run_name[self.i_run],
                    file_format=self.file_format[self.i_run],
                    raw_data_path=self.raw_data_path[self.i_run],
                    ses_name=self.s._ses_name,
                    session_output_path=self.s._output_path,
                    pp_steps=self.pp_steps_tot,
                    orig_run_names=orig_run_names,
                    preprocessed_data=preprocessed_run,
                )
            )

        # flag that preprocessing is complete
        self.update_prep_prog(4)

    def preprocess_run(self, run, is_raw):

        preprocessed = {}

        if is_raw:
            # case is starting preprocessing from raw

            # determines the runs to process
            if self.per_shank:
                runs_to_preprocess = run._get_split_by_shank()
            else:
                runs_to_preprocess = run._raw

            # runs the preprocessing over each grouping
            self.n_shank = len(runs_to_preprocess.items())
            for i_shank_pp, (shank_id, raw_rec) in enumerate(runs_to_preprocess.items()):
                self.update_prep_prog(2, i_shank_pp)
                preprocessed[shank_id] = self.preprocess_recording({"0-raw": raw_rec})

        else:
            # case is running from previous preprocessing

            # runs the preprocessing over each grouping
            self.n_shank = len(run.items())
            for i_shank, (shank_id, pp_rec) in enumerate(run.items()):
                self.update_prep_prog(2, i_shank_pp)
                preprocessed[shank_id] = pp_rec
                self.preprocess_recording(pp_rec)

        return preprocessed

    def preprocess_recording(self, pp_data):

        # field retrieval
        step_ofs = len(pp_data) - 1
        self.n_task = len(self.pp_steps_new)
        prev_name = list(pp_data.keys())[-1]
        pp_step_names = [item[0] for item in self.pp_steps_tot.values()]

        for i_step, (step_num, pp_info) in enumerate(self.pp_steps_new.items()):
            # updates the progressbar
            pp_name, pp_opt = pp_info
            self.update_prep_prog(3, i_step, pp_name)

            # retrieves the preprocessing step parameters
            if self.per_shank and (pp_name == 'interpolate_channels'):
                # if analysing by shank, and interpolating bad channels, then ensure the channels for removal exist
                # on the current shank
                shank_id = np.intersect1d(pp_opt['channel_ids'], pp_data[prev_name].channel_ids)
                if len(shank_id):
                    # if there are bad channels, then reset the field
                    pp_opt['channel_ids'] = shank_id

                else:
                    # if there are no bad channels, then continue
                    pp_step_names.pop(pp_step_names.index(pp_name))
                    continue

            if (pp_name == 'drift_correct') and (pp_data[prev_name]._dtype.kind == 'i'):
                # special case - the motion correction code only works on float32 data types
                #                if the data is uint16, then covert before running
                preprocessed_rec = self.pp_funcs[pp_name](pp_data[prev_name].astype('float32'), **pp_opt)

            else:
                # otherwise, run the spikewrap function as per normal
                preprocessed_rec = self.pp_funcs[pp_name](pp_data[prev_name], **pp_opt)

            # stores the preprocessing run object
            step_num_tot = int(step_num) + step_ofs
            new_name = f"{str(step_num_tot)}-" + "-".join(["raw"] + pp_step_names[: step_num_tot])
            pp_data[new_name] = preprocessed_rec

            # resets the previous run name
            prev_name = new_name

        return pp_data

    def update_prep_prog(self, pr_type, i_val=None, pp_str=None):

        # initialisations
        m_str = None
        pr_val = None

        match pr_type:
            case 0:
                # case is preprocessing initialising
                m_str = 'Initialising Preprocessing'

                self.i_run = 0
                self.i_shank = 0
                self.i_task = 0

                pr_val = 0.
                self.n_task = 1
                self.n_shank = 1

            case 1:
                # case is new preprocessing run
                m_str = 'Initialising Run...'

                self.i_run = i_val
                self.i_shank = 0
                self.i_task = 0

                self.p_run = 1. / self.n_run
                self.p_shank = 0.

            case 2:
                # case is new preprocessing shank
                m_str = 'Initialising Shank...'

                self.i_shank = i_val
                self.i_task = 0

                self.p_shank = self.p_run / self.n_shank

            case 3:
                # case is new preprocessing task
                self.i_task = i_val

                # sets up the message string
                m_type = 2 * int(self.n_run > 1) + int(self.n_shank > 1)
                match m_type:
                    case 0:
                        # case is single run/shank expt
                        m_suff = ''

                    case 1:
                        # case is a multi-shank session
                        m_suff = ' (S{0}/{1})'.format(self.i_shank + 1, self.n_shank)

                    case 2:
                        # case is a multi-run session
                        m_suff = ' (R{0}/{1})'.format(self.i_run + 1, self.n_run)

                    case 3:
                        # case is multi run/shank expt
                        m_suff = '(R{1}/{2}, S{3}/{4})'.format(self.i_run + 1, self.n_run,
                                                               self.i_shank + 1, self.n_shank)

                # sets the task string
                m_str = 'Task: {0}{1}'.format(pp_str, m_suff)

            case 4:
                # case is preprocessing completion
                pr_val = 1.
                m_str = 'Preprocessing Complete!'

        if pr_val is None:
            pr_val_run = self.i_run * self.p_run
            pr_val_shank = self.i_shank * self.p_shank
            pr_task = self.p_shank * (self.i_task + 1) / (self.n_task + 1)
            pr_val = pr_val_run + pr_val_shank + pr_task

        # updates the progressbar
        self.update_prog.emit(m_str, pr_val)


# ----------------------------------------------------------------------------------------------------------------------

"""
    QPreprocessProgWidget:
"""


class QPreprocessProgWidget(QWidget):
    # static string fields
    dp_max = 10
    p_max = 1000
    t_period = 1000
    lbl_width = 200
    wait_lbl = 'Waiting For User Input...'

    prog_style = """
        QProgressBar {
            border: 2px solid black;
            border-radius: 5px;
            background-color: #E0E0E0;
        }
        QProgressBar::chunk {
            background-color: #19e326;
            width: 10px; 
            margin: 0.25px;
        }
    """

    def __init__(self, parent=None, font=None, is_task=True):
        super(QPreprocessProgWidget, self).__init__(parent)

        # input arguments
        self.is_task = is_task

        # widget setup
        self.layout = QHBoxLayout(self)
        self.lbl_obj = cw.create_text_label(self, self.wait_lbl, font, align='right')
        self.prog_bar = QProgressBar(self, minimum=0, maximum=self.p_max, textVisible=False)
        self.time_line = QTimeLine(self.t_period) if is_task else None

        # other class fields
        self.n_jobs = 0
        self.pr_max = 1.0
        self.is_running = False
        self.p_max_r = self.p_max + 2 * self.dp_max

        # initialises the class fields
        self.init_class_fields()

    def init_class_fields(self):

        # sets up the layout properties
        self.layout.setSpacing(x_gap)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # adds the widgets to the layout
        self.layout.addWidget(self.lbl_obj)
        self.layout.addWidget(self.prog_bar)

        # sets the label properties
        self.lbl_obj.setContentsMargins(0, x_gap, 0, 0)
        self.lbl_obj.setFixedWidth(self.lbl_width)

        # sets the progressbar properties
        self.prog_bar.setStyleSheet(self.prog_style)

        # sets the timeline properties
        if self.is_task:
            self.time_line.setLoopCount(int(1e6))
            self.time_line.setFrameRange(0, self.p_max)
            self.time_line.setUpdateInterval(50)
            self.time_line.frameChanged.connect(self.prog_timer)

    def prog_timer(self):

        pr_scl = self.p_max_r * self.pr_max
        p_val = int(pr_scl * self.time_line.currentValue()) - self.dp_max
        p_val = np.min([self.p_max, np.max([0, p_val])])
        self.prog_bar.setValue(p_val)

    def set_progbar_state(self, state=None):

        if state is None:
            state = self.is_running

        if state:
            # starts the timeline widget
            self.start_timer()

        else:
            # stops the timeline widget
            self.stop_timer()

            # resets the progressbar
            self.prog_bar.setValue(self.p_max)
            time.sleep(0.25)
            self.prog_bar.setValue(0)

            # resets the text label
            self.lbl_obj.setText(self.wait_lbl)

    def start_timer(self):

        if self.time_line is not None:
            self.is_running = True
            self.time_line.start()

    def stop_timer(self):

        if self.time_line is not None:
            self.time_line.stop()
            self.is_running = False

    def set_enabled(self, state):

        self.lbl_obj.setEnabled(state)
        self.prog_bar.setEnabled(state)