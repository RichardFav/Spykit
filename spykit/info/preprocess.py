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
                             QListWidget, QGridLayout, QSpacerItem, QDialog, QMainWindow, QProgressBar, QMessageBox)
from PyQt6.QtCore import QSize, pyqtSignal, QObject, QTimeLine, Qt
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
        return self.bad_channel_fcn(['out'], not_keep, not_rmv)[0]

    def get_interp_channels(self):

        is_keep = self.keep_channel_fcn()
        not_rmv = np.logical_not(self.is_channel_removed())
        is_feas = np.logical_or(is_keep, not_rmv)

        return self.bad_channel_fcn(['dead', 'noise'], is_feas=is_feas)[0]

# ----------------------------------------------------------------------------------------------------------------------

"""
    PreprocessSetup:
"""


class PreprocessSetup(QMainWindow):
    # pyqtSignal functions
    close_preprocessing = pyqtSignal(bool)

    # parameters
    n_but = 4
    gap_sz = 5
    n_prog = 2
    but_height = 20
    dlg_height_orig = 300
    dlg_height_auto = 130
    dlg_width = 450
    p_row = np.array([7, 2, 1])

    # array class fields
    prep_str = ['Start Preprocessing', 'Cancel Preprocessing']
    b_icon = ['arrow_right', 'arrow_left', 'arrow_up', 'arrow_down']
    tt_str = ['Add Task', 'Remove Task', 'Move Task Up', 'Move Task Down']

    # widget stylesheets
    border_style = "border: 1px solid;"
    frame_border_style = """
        QFrame#prepFrame {
            border: 1px solid;
        }
    """

    def __init__(self, main_obj, prep_obj_auto):
        super(PreprocessSetup, self).__init__(main_obj)

        # sets the input arguments
        self.main_obj = main_obj
        self.prep_obj_auto = prep_obj_auto
        self.is_auto = prep_obj_auto is not None

        # creates the preprocessing run class object
        self.session = self.main_obj.session_obj.session

        # sets the central widget
        self.main_widget = QWidget(self)

        # class layouts
        self.list_layout = QGridLayout(self)
        self.checkbox_layout = QHBoxLayout()
        self.button_layout = QVBoxLayout()
        self.task_layout = QGridLayout()
        self.progress_layout = QVBoxLayout()
        self.control_layout = QHBoxLayout()

        # class widgets
        self.button_frame = QFrame(self)
        self.task_frame = QFrame(None if self.is_auto else self)
        self.progress_frame = QFrame(self)
        self.checkbox_frame = QWidget()

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
        self.is_running = False
        self.is_updating = False

        # index/scalar class fields
        self.i_run = None
        self.i_shank = None
        self.i_step = None
        self.n_run = None
        self.n_shank = None
        self.n_step = None
        self.n_task = None
        self.p_run = None
        self.p_shank = None
        self.pr_task = None
        self.t_worker = None
        self.dlg_height = self.dlg_height_auto if self.is_auto else self.dlg_height_orig

        # initialises the class fields
        self.init_class_fields()
        self.init_task_para_frame()
        self.init_progress_frame()
        self.init_control_buttons()
        self.set_widget_config()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the dialog window properties
        self.setWindowTitle("Preprocessing Setup")
        self.setFixedSize(self.dlg_width, self.dlg_height)
        self.setWindowModality(Qt.WindowModality(1))
        # self.setModal(True)

        # sets the main widget properties
        self.main_widget.setLayout(self.list_layout)
        self.setCentralWidget(self.main_widget)

        # resets the frame object names
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

        # connects the preprocessing signal function
        self.session.prep_obj.update_prog.connect(self.worker_progress)

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
        n_run = self.session.get_run_count()
        self.checkbox_opt[1].setEnabled(n_run > 1)

        # determines if partial preprocessing has taken place
        pp_runs = self.main_obj.session_obj.get_pp_runs()
        if len(pp_runs):
            # flag that partial preprocessing has taken place
            self.has_pp = True
            self.per_shank = self.session.prep_obj.per_shank
            self.concat_runs = self.session.prep_obj.concat_runs

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
            bad_ch_id = self.main_obj.session_obj.get_bad_channels()[0]
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
        for i in range(self.n_prog):
            prog_bar_new = cw.QDialogProgress(font=cw.font_lbl, is_task=bool(i))
            prog_bar_new.set_enabled(False)
            prog_bar_new.setContentsMargins(x_gap, x_gap, x_gap, i * x_gap)

            self.prog_bar.append(prog_bar_new)
            self.progress_layout.addWidget(prog_bar_new)

    def init_control_buttons(self):

        # initialisations
        b_str = [self.prep_str[0], 'Close Window']
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
        self.button_control[4].setCheckable(True)
        self.set_button_props()

    def set_widget_config(self):

        # main layout properties
        self.list_layout.setHorizontalSpacing(x_gap)
        self.list_layout.setVerticalSpacing(x_gap)
        self.list_layout.setContentsMargins(2 * x_gap, x_gap, 2 * x_gap, 2 * x_gap)
        self.setLayout(self.list_layout)

        if self.is_auto:
            # adds the main widgets to the main layout
            self.list_layout.addWidget(self.progress_frame, 0, 0, 1, 1)
            self.list_layout.addWidget(self.button_frame, 1, 0, 1, 1)

            # set the grid layout column sizes
            self.list_layout.setRowStretch(0, self.p_row[1])
            self.list_layout.setRowStretch(1, self.p_row[2])

        else:
            # adds the main widgets to the main layout
            self.list_layout.addWidget(self.task_frame, 0, 0, 1, 1)
            self.list_layout.addWidget(self.progress_frame, 1, 0, 1, 1)
            self.list_layout.addWidget(self.button_frame, 2, 0, 1, 1)

            # set the grid layout column sizes
            self.list_layout.setRowStretch(0, self.p_row[0])
            self.list_layout.setRowStretch(1, self.p_row[1])
            self.list_layout.setRowStretch(2, self.p_row[2])

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

        # if manually updating, then exit
        if self.is_updating:
            return

        # resets the button state
        self.is_running = not self.button_control[4].isChecked()
        self.button_control[4].setText(self.prep_str[self.is_running])

        if self.is_running:
            # case is starting the calculations

            # other field initialisations
            if self.is_auto:
                # case is loading from file
                self.n_task = len(self.prep_obj_auto[0])
                self.setup_preprocessing_worker(self.prep_obj_auto)

            else:
                # retrieves the task count
                self.n_task = deepcopy(self.add_list.count())

                # sets the preprocessing options
                prep_tab = self.main_obj.info_manager.get_info_tab('preprocess')
                prep_tab.configs.set_prep_opt(self.per_shank, self.concat_runs)

                # retrieves the selected tasks
                prep_task = []
                for i in range(self.n_task):
                    prep_task.append(self.add_list.item(i).text())

                # starts running the pre-processing
                prep_opt = (self.per_shank, self.concat_runs)
                self.setup_preprocessing_worker((prep_task, prep_opt))

        else:
            # stops the worker
            self.t_worker.force_quit()
            self.t_worker.deleteLater()
            time.sleep(0.01)

            # disables the progressbar fields
            for pb in self.prog_bar:
                pb.set_progbar_state(False)

            # resets the other properties
            self.set_preprocess_props(True)
            self.button_control[4].setText(self.prep_str[0])

    def close_window(self):

        # if there are outstanding tasks, then promopt the user
        if (self.add_list.count() > 0) or ((not self.has_pp) and self.is_auto):
            q_str = 'There are still outstanding tasks to process. Do you still want to continue?'
            u_choice = QMessageBox.question(self.main_obj, 'Close Window?', q_str, cf.q_yes_no, cf.q_yes)
            if u_choice == cf.q_no:
                # case is the user chose not to close
                return

        if self.has_pp:
            # updates the pre-processing information
            pr_val = self.session.prep_obj.pp_steps_tot.values()
            prep_tab = self.main_obj.info_manager.get_info_tab('preprocess')

            # resets the preprocessing configuration fields
            prep_tab.configs.prep_task = [x[0] for x in pr_val]
            prep_tab.configs.task_name = [pp_flds[x] for x in prep_tab.configs.prep_task]
            prep_tab.configs.task_para = dict(pr_val)
            prep_tab.configs.set_prep_opt(self.per_shank, self.concat_runs)

        # runs the post window close functions
        self.close_preprocessing.emit(self.has_pp)

        # closes the window
        self.close()

    # ---------------------------------------------------------------------------
    # Preprocessing Worker Functions
    # ---------------------------------------------------------------------------

    def setup_preprocessing_worker(self, prep_obj):

        # creates the threadworker object
        self.t_worker = ThreadWorker(self, self.run_preprocessing_worker, prep_obj)
        self.t_worker.work_finished.connect(self.preprocessing_complete)

        # starts the worker object
        self.t_worker.start()

    def run_preprocessing_worker(self, prep_obj):

        # runs the session pre-processing
        prep_tab = self.main_obj.info_manager.get_info_tab('preprocess')

        # case is running from the Preprocessing dialog
        if isinstance(prep_obj, tuple):
            prep_task, prep_opt = prep_obj
            per_shank, concat_runs = prep_opt
            pp_config = prep_tab.setup_config_dict(prep_task)

        else:
            # case is running from loading session
            pp_config = prep_obj.setup_config_dicts()

        # runs the preprocessing
        self.session.prep_obj.preprocess(pp_config, per_shank, concat_runs)

    def preprocessing_complete(self):

        # pauses for a little bit...
        time.sleep(0.25)

        # updates the boolean flags
        self.has_pp = True

        if self.is_auto:
            # case is automatically opening
            self.close_window()

        else:
            # stops the timer
            for pb in self.prog_bar:
                pb.set_progbar_state(False)

            # resets the current session (if run to completion)
            if self.is_running:
                # clears the added list
                self.is_updating = True
                self.add_list.clear()
                self.is_updating = False

                # resets the completion flag
                self.is_running = False

            # resets the other fields
            self.set_preprocess_props(True)
            for cb in self.checkbox_opt:
                cb.setEnabled(False)

            # resets the toggle button
            self.is_updating = True
            self.button_control[4].setChecked(False)
            self.button_control[4].setText(self.prep_str[0])
            self.is_updating = False

        # deletes the worker object
        self.t_worker.deleteLater()

    # ---------------------------------------------------------------------------
    # Worker Progress Functions
    # ---------------------------------------------------------------------------

    def worker_progress(self, pr_type, pr_dict):

        # initialisations
        pr_val = None
        m_str = [None, None]

        # updates the values from the dictionary
        for pd, pv in pr_dict.items():
            setattr(self, pd, pv)

        match pr_type:
            case 0:
                # case is intialising preprocessing

                # resets the index values
                self.i_run = 0
                self.i_shank = 0
                self.i_task = 0

                # resets the index sizes
                self.n_run = 1
                self.n_shank = 1

                # sets the run/shank proportional multipliers
                self.p_run = 1.
                self.p_shank = 1.

                # sets the progress values
                pr_val = np.zeros(2, dtype=float)
                m_str = ['Initialising Preprocessing', 'Initialising Task Data']

                # enables the progressbar
                for pb in self.prog_bar:
                    pb.set_progbar_state(True)

                # disables the required dialog widgets
                self.set_preprocess_props(False)

            case 1:
                # case is new preprocessing run

                # sets up the message labels
                m_str[0] = self.setup_overall_progress_msg()
                m_str[1] = 'Initialising Run Data...'

                # resets the index values
                self.i_shank = 0
                self.i_task = 0

            case 2:
                # case is new preprocessing shank

                # resets the index values
                self.i_task = 0

                # sets up the message labels
                m_str[0] = self.setup_overall_progress_msg()
                m_str[1] = 'Initialising Shank Data...'

            case 3:
                # case is performing a preprocessing task

                # updates the list selection
                self.reset_list_selection(self.i_task)

                # sets up the message labels
                m_str[1] = 'Task: {0}'.format(pp_flds[self.pr_task])

            case 4:
                # case is the run count
                self.p_run = 1 / self.n_run

            case 5:
                # case is the shank count
                self.p_shank = 1 / self.n_shank

            case 6:
                # case is preprocessing completion

                # sets the progress values
                pr_val = np.ones(2, dtype=float)
                m_str = ['Preprocessing Complete', 'All Tasks Complete']

        # calculates the
        if pr_val is None:
            # calculates the run/shank proportional components
            pr_val_run = self.i_run * self.p_run
            pr_val_shank = self.i_shank * self.p_shank

            # calculates and sets the task/overall proportions
            pr_task = 0. if (self.n_task is None) else self.i_task / self.n_task
            pr_overall = pr_val_run + pr_val_shank + self.p_run * self.p_shank * pr_task
            pr_val = np.array([pr_overall, pr_task])

        # updates the progressbar fields
        for pb, ms, pv in zip(self.prog_bar, m_str, pr_val):
            pb.update_prog_fields(ms, pv)

    def setup_overall_progress_msg(self):

        # initialisations
        m_str0 = 'Progress'
        p_type = 2 * int(self.n_shank > 1) + int(self.n_run > 1)

        match p_type:
            case 0:
                # case is a single run/shank session
                m_str1 = '(All Runs/Shanks)'

            case 1:
                # case is a multi run/single shank session
                m_str1 = '(Run {0}/{1}, All Shanks)'.format(self.i_run + 1, self.n_run)

            case 2:
                # case is a single run/multi shank session
                m_str1 = '(All Runs, Shank {0}/{1})'.format(self.i_shank + 1, self.n_shank)

            case 3:
                # case is a multi run/shank session
                m_str1 = '(Run {0}/{1}, Shank {2}/{3})'.format(self.i_run + 1, self.n_run,
                                                             self.i_shank + 1, self.n_shank)

        # returns the final string
        return '{0}: {1}'.format(m_str0, m_str1)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def reset_list_selection(self, i_sel):

        self.is_updating = True
        self.add_list.setCurrentRow(i_sel)
        self.is_updating = False

    def set_preprocess_props(self, state):

        # sets the task frame widget properties
        for hc in self.task_frame.findChildren(QWidget):
            hc.setEnabled(state)

        # resets the button properties (if reenabling)
        if state:
            self.set_button_props()

        # sets the close button properties
        self.button_control[5].setEnabled(state)

        # pause for update...
        time.sleep(0.01)

    def set_button_props(self):

        # if manually updating, then exit
        if self.is_updating:
            return

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
        self.button_control[4].setEnabled((n_added >= 0) or self.is_auto)

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
    update_prog = pyqtSignal(int, dict)

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

        # boolean class fields
        self.per_shank = False
        self.concat_runs = False

        # other class field initialisations
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
        n_run_pp = len(self.s._pp_runs)
        if n_run_pp:
            # case is there has already been partial preprocessing
            is_raw = False
            runs_to_pp = [x._preprocessed for x in self.s._pp_runs]

            # appends the new preprocessing steps to the total list
            i_ofs = len(self.pp_steps_tot)
            for i, pp_s in pp_steps.items():
                i_tot = int(i) + i_ofs
                self.pp_steps_tot[(str(i_tot))] = pp_s

            # sets the run count
            self.update_prep_prog(4, n_run_pp)

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

            # sets the run count
            self.update_prep_prog(4, len(runs_to_pp))

        # runs the preprocessing for each run (for all tasks)
        for i_run, run in enumerate(runs_to_pp):
            # sets the shank count (first run only)
            if i_run == 0:
                self.update_prep_prog(5, self.get_shank_count(run, is_raw))

            # update the progressbar for the current run
            self.update_prep_prog(1, i_run)

            # runs the preprocessing for the current run
            preprocessed_run = self.preprocess_run(run, is_raw)

            # retrieves the run names
            orig_run_names = (
                run._orig_run_names if isinstance(run, ConcatRawRun) else None
            )

            # stores the preprocessing data
            if n_run_pp == 0:
                self.s._pp_runs.append(
                    PreprocessedRun(
                        run_name=self.run_name[i_run],
                        file_format=self.file_format[i_run],
                        raw_data_path=self.raw_data_path[i_run],
                        ses_name=self.s._ses_name,
                        session_output_path=self.s._output_path,
                        pp_steps=self.pp_steps_tot,
                        orig_run_names=orig_run_names,
                        preprocessed_data=preprocessed_run,
                    )
                )

        # flag that preprocessing is complete
        self.update_prep_prog(6)

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
            for i_shank, (shank_id, raw_rec) in enumerate(runs_to_preprocess.items()):
                self.update_prep_prog(2, i_shank)
                preprocessed[shank_id] = self.preprocess_recording({"0-raw": raw_rec})

        else:
            # case is running from previous preprocessing

            # runs the preprocessing over each grouping
            self.update_prep_prog(5, len(run.items()))
            for i_shank, (shank_id, pp_rec) in enumerate(run.items()):
                self.update_prep_prog(2, i_shank)
                preprocessed[shank_id] = pp_rec
                self.preprocess_recording(pp_rec)

        return preprocessed

    def preprocess_recording(self, pp_data):

        # field retrieval
        step_ofs = len(pp_data) - 1
        prev_name = list(pp_data.keys())[-1]
        pp_step_names = [item[0] for item in self.pp_steps_tot.values()]

        for i_step, (step_num, pp_info) in enumerate(self.pp_steps_new.items()):
            # updates the progressbar
            run_pp_step = True
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
                    run_pp_step = False

            if run_pp_step:
                if (pp_name == 'drift_correct') and (pp_data[prev_name]._dtype.kind == 'i'):
                    # special case - the motion correction code only works on float32 data types
                    #                if the data is uint16, then covert before running
                    preprocessed_rec = self.pp_funcs[pp_name](pp_data[prev_name].astype('float32'), **pp_opt)

                elif (pp_name == 'remove_channels') and ('channel_ids' in pp_opt):
                    ch_ids = pp_data[prev_name].channel_ids
                    if np.all([x in ch_ids for x in pp_opt['channel_ids']]):
                        # runs the spikewrap function as per normal
                        preprocessed_rec = self.pp_funcs[pp_name](pp_data[prev_name], **pp_opt)

                    else:
                        # otherwise, skip the step
                        preprocessed_rec = pp_data[prev_name]

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
        pr_dict = {}

        match pr_type:
            case 1:
                # case is new preprocessing run
                pr_dict = {'i_run': i_val}

            case 2:
                # case is new preprocessing shank
                pr_dict = {'i_shank': i_val}

            case 3:
                # case is new preprocessing task
                pr_dict = {'i_task': i_val, 'pr_task': pp_str}

            case 4:
                # case is the run count
                pr_dict = {'n_run': i_val}

            case 5:
                # case is the shank count
                pr_dict = {'n_shank': i_val}

        # updates the progressbar
        self.update_prog.emit(pr_type, pr_dict)
        time.sleep(0.05)

    def get_shank_count(self, run, is_raw):

        if is_raw:
            if self.per_shank:
                return len(run._get_split_by_shank())
            else:
                return len(run._raw)

        else:
            return len(run.items())