    # custom module imports
import time

import numpy as np
from copy import deepcopy

import spykit.common.common_widget as cw
import spykit.common.common_func as cf
from spykit.info.utils import InfoWidgetPara
from spykit.threads.utils import ThreadWorker

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QFrame, QTabWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QListWidget, QGridLayout, QSpacerItem, QDialog, QMainWindow)
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtCore import QSize, pyqtSignal

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
    x_gap = 5
    gap_sz = 5
    but_height = 20
    dlg_height = 200
    dlg_width = 450

    # array class fields
    b_icon = ['arrow_right', 'arrow_left', 'arrow_up', 'arrow_down']
    tt_str = ['Add Task', 'Remove Task', 'Move Task Up', 'Move Task Down']

    # widget stylesheets
    border_style = "border: 1px solid;"
    frame_style = QFrame.Shape.WinPanel | QFrame.Shadow.Plain

    def __init__(self, main_obj=None):
        super(PreprocessSetup, self).__init__(main_obj)

        # sets the input arguments
        self.main_obj = main_obj

        # class layouts
        self.list_layout = QGridLayout(self)
        self.checkbox_layout = QHBoxLayout()
        self.button_layout = QVBoxLayout()
        self.control_layout = QHBoxLayout()

        # class widgets
        self.task_order = []
        self.checkbox_opt = []
        self.button_control = []
        self.button_frame = QWidget(self)
        self.checkbox_frame = QWidget(self)
        self.add_list = QListWidget(None)
        self.task_list = QListWidget(None)
        self.spacer_top = QSpacerItem(20, 60, cf.q_min, cf.q_max)
        self.spacer_bottom = QSpacerItem(20, 60, cf.q_min, cf.q_max)

        # array class fields
        self.l_task = ['Phase Shift', 'Bandpass Filter', 'Channel Interpolation', 'Common Reference', 'Drift Correction']

        # boolean class fields
        self.has_pp = False
        self.per_shank = False
        self.concat_runs = False

        # initialises the class fields
        self.init_checkbox_opt()
        self.init_class_fields()
        self.init_control_buttons()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

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

    def init_class_fields(self):

        # initialisations
        cb_fcn = [self.button_add, self.button_remove, self.button_up, self.button_down]

        # sets the dialog window properties
        self.setWindowTitle("Preprocessing Setup")
        self.setFixedSize(self.dlg_width, self.dlg_height)

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

        # main layout properties
        self.list_layout.setHorizontalSpacing(self.x_gap)
        self.list_layout.setVerticalSpacing(0)
        self.list_layout.setContentsMargins(self.x_gap, 0, self.x_gap, 0)
        self.setLayout(self.list_layout)

        # added list widget properties
        self.add_list.setStyleSheet(self.border_style)
        self.add_list.itemClicked.connect(self.set_button_props)

        # task list widget properties
        self.task_list.addItems(self.l_task)
        self.task_list.setStyleSheet(self.border_style)
        self.task_list.itemClicked.connect(self.set_button_props)

        # button layout properties
        self.button_layout.setSpacing(self.x_gap)

        # adds the spacers/buttons to the button layout
        self.button_layout.addItem(self.spacer_top)
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

        self.button_layout.addItem(self.spacer_bottom)

        # adds the main widgets to the main layout
        self.list_layout.addWidget(self.task_list, 0, 0, 1, 1)
        self.list_layout.addLayout(self.button_layout, 0, 1, 1, 1)
        self.list_layout.addWidget(self.add_list, 0, 2, 1, 1)
        self.list_layout.addWidget(self.checkbox_frame, 1, 0, 1, 3)
        self.list_layout.addWidget(self.button_frame, 2, 0, 1, 3)

        # set the grid layout column sizes
        self.list_layout.setColumnStretch(0, self.gap_sz)
        self.list_layout.setColumnStretch(1, 1)
        self.list_layout.setColumnStretch(2, self.gap_sz)
        self.list_layout.setRowStretch(0, 5)
        self.list_layout.setRowStretch(1, 1)
        self.list_layout.setRowStretch(2, 1)

    def init_control_buttons(self):

        # initialisations
        b_str = ['Start Preprocessing', 'Close Window']
        cb_fcn = [self.start_preprocess, self.close_window]

        # sets the frame/layout properties
        self.button_frame.setContentsMargins(0, 0, 0, 0)
        self.button_frame.setLayout(self.control_layout)
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.control_layout.setSpacing(self.but_height + 2 * self.gap_sz)

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

            # closes the dialog window
            self.close_window()

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
