# custom module imports
import numpy as np
from copy import deepcopy

import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.common_func as cf
from spike_pipeline.info.utils import InfoWidgetPara
from spike_pipeline.threads.utils import ThreadWorker

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QFrame, QTabWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QListWidget, QGridLayout, QSpacerItem, QDialog)
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtCore import QSize

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

    def add_prep_task(self, p_task, t_para=None, t_name=None):

        self.prep_task.append(p_task)

        if t_para is not None:
            self.task_para[p_task] = t_para

        if t_name is not None:
            self.task_name.append(t_name)

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
        self.task_para = {}


# ----------------------------------------------------------------------------------------------------------------------

"""
    PreprocessInfoTab:
"""


class PreprocessInfoTab(InfoWidgetPara):
    def __init__(self, t_str):
        super(PreprocessInfoTab, self).__init__(t_str, layout=QFormLayout)

        # class field initialisation
        self.bad_channel_fcn = None
        self.keep_channel_fcn = None
        self.removed_channel_fcn = None
        self.is_channel_removed = None
        self.configs = PreprocessConfig()

        # sorting group widgets
        self.frame_sort = QFrame(self)
        self.tab_group_sort = QTabWidget(self)
        self.layout_sort = QVBoxLayout()

        # initialises the major widget groups
        self.setup_prop_fields()
        self.init_filter_edit()
        self.init_property_frame()
        self.init_sorting_frame()

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

            # whitening parameters
            'whitening': {
                'apply_mean': self.create_para_field('Subtract Mean', 'checkbox', False),
                'mode': self.create_para_field('Mode', 'combobox', mode_list[0], p_list=mode_list),
                'radius_um': self.create_para_field('Radius (um)', 'edit', 100),
            },

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

        # -----------------------------------------------------------------------
        # Sorting Properties
        # -----------------------------------------------------------------------

        # sets up the sorting tab parameter fields
        pp_k2 = {'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort2'),
                 'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2')}
        pp_k2_5 = {'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort2_5'),
                   'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2_5'), }
        pp_k3 = {'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort3'),
                 'freq_min': self.create_para_field('Min Frequency', 'edit', 300, p_fld='kilosort3'), }
        pp_m5 = {'scheme': self.create_para_field('Scheme', 'edit', 2, p_fld='mountainsort5'),
                 'filter': self.create_para_field('Filter', 'checkbox', False, p_fld='mountainsort5'), }

        # stores the sorting properties
        self.s_prop_flds = {
            'kilosort2': {'name': 'KiloSort 2', 'props': pp_k2},
            'kilosort2_5': {'name': 'KiloSort 2.5', 'props': pp_k2_5},
            'kilosort3': {'name': 'KiloSort 3', 'props': pp_k3},
            'mountainsort5': {'name': 'MountainSort 5', 'props': pp_m5},
        }

        # initialises the fields for all properties
        self.is_sort_para = True
        for kp, vp in self.s_prop_flds.items():
            # sets up the parent field
            self.s_props[kp] = {}

            # sets the children properties
            for k, p in vp['props'].items():
                self.s_props[kp][k] = p['value']

    def init_sorting_frame(self):

        # initialisations
        self.s_type = 'mountainsort5'

        # sets the frame properties
        self.frame_sort.setLineWidth(1)
        self.frame_sort.setFixedHeight(120)
        self.frame_sort.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.WinPanel)
        # self.frame_sort.setStyleSheet("border: 1px solid;")

        # adds the tab group to the layout
        self.frame_sort.setLayout(self.layout_sort)
        self.layout_sort.setSpacing(0)
        self.layout_sort.setContentsMargins(0, 0, 0, 0)
        self.layout_sort.addWidget(self.tab_group_sort)

        # creates the tab group object
        for k, v in self.s_prop_flds.items():
            tab_layout = QVBoxLayout()
            obj_tab = self.create_para_object(tab_layout, k, v['props'], 'tab', [k])
            self.tab_group_sort.addTab(obj_tab, v['name'])

        # tab-group change callback function
        i_tab0 = list(self.s_props.keys()).index(self.s_type)
        self.tab_group_sort.setCurrentIndex(i_tab0)
        self.tab_group_sort.currentChanged.connect(self.sort_tab_change)

        # adds the frame to the parent widget
        self.tab_layout.addRow(self.frame_sort)

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


class PreprocessSetup(QDialog):
    # parameters
    n_but = 4
    x_gap = 5
    gap_sz = 5
    but_height = 20
    dlg_height = 200
    dlg_width = 400

    # array class fields
    b_icon = ['arrow_right', 'arrow_left', 'arrow_up', 'arrow_down']
    tt_str = ['Add Task', 'Remove Task', 'Move Task Up', 'Move Task Down']
    l_task = ['Phase Shift', 'Bandpass Filter', 'Channel Interpolation', 'Common Reference', 'Drift Correction']

    # widget stylesheets
    border_style = "border: 1px solid;"
    frame_style = QFrame.Shape.WinPanel | QFrame.Shadow.Plain

    def __init__(self, main_obj=None):
        super(PreprocessSetup, self).__init__()

        # sets the input arguments
        self.main_obj = main_obj
        self.setWindowTitle("Preprocessing Setup")
        self.setFixedSize(self.dlg_width, self.dlg_height)

        # sets the main widget/layout
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()

        # class layouts
        self.list_layout = QGridLayout(self)
        self.button_layout = QVBoxLayout()
        self.control_layout = QHBoxLayout()

        # class widgets
        self.task_order = []
        self.button_control = []
        self.button_frame = QWidget(self)
        self.add_list = QListWidget(None)
        self.task_list = QListWidget(None)
        self.spacer_top = QSpacerItem(20, 60, cf.q_min, cf.q_max)
        self.spacer_bottom = QSpacerItem(20, 60, cf.q_min, cf.q_max)

        # initialises the class fields
        self.init_class_fields()
        self.init_control_buttons()
        self.set_button_props()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # initialisations
        cb_fcn = [self.button_add, self.button_remove, self.button_up, self.button_down]

        # removes any existing
        pp_runs = self.main_obj.session_obj.session._s._pp_runs
        if len(pp_runs):
            for pp_names in [pp_flds[v[0]] for v in pp_runs[0]._pp_steps.values()]:
                if pp_names in self.l_task:
                    self.l_task.pop(self.l_task.index(pp_names))

        # channel interpolation field (if it exists) if either a) there are no bad channels or
        # b) the common reference calculations have already taken place
        if 'Channel Interpolation' in self.l_task:
            bad_ch_id = self.main_obj.session_obj.get_bad_channels()
            if (len(bad_ch_id) == 0) or ('Common Reference' not in self.l_task):
                self.l_task.pop(self.l_task.index('Channel Interpolation'))

        # sets up the main layout
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.main_widget)
        self.main_widget.setLayout(self.list_layout)

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
        self.list_layout.addWidget(self.button_frame, 1, 0, 1, 3)

        # set the grid layout column sizes
        self.list_layout.setColumnStretch(0, self.gap_sz)
        self.list_layout.setColumnStretch(1, 1)
        self.list_layout.setColumnStretch(2, self.gap_sz)
        self.list_layout.setRowStretch(0, 5)
        self.list_layout.setRowStretch(1, 1)

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

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

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
            # retrieves the selected tasks
            prep_task = []
            for i in range(self.add_list.count()):
                prep_task.append(self.add_list.item(i).text())

            # sets up the bad channel detection worker
            self.main_obj.setup_preprocessing_worker(prep_task)

            # runs the pre-processing
            self.close_window()

    def close_window(self):

        self.close()

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
