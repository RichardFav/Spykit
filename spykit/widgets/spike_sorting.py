# module import
import numpy as np
from copy import deepcopy
from functools import partial as pfcn

# custom module imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QWidget, QFrame, QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLineEdit, QCheckBox, QTabWidget, QSizePolicy, QProgressBar)
from PyQt6.QtCore import pyqtSignal, QTimeLine

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeSortingDialog:  
"""


class SpikeSortingDialog(QMainWindow):
    # pyqtsignal functions
    prop_updated = pyqtSignal()

    # widget dimensions
    n_prog = 2
    dlg_width = 350
    dlg_height = 300
    p_row = np.array([7, 2, 1])

    # array class fields
    sort_str = ['Start Spike Sorting', 'Cancel Spike Sorting']

    # widget stylesheets
    border_style = "border: 1px solid;"
    no_border_style = "border: 0px; padding-top: 3px;"
    frame_border_style = """
        QFrame#sortFrame {
            border: 1px solid;
        }
    """

    def __init__(self, parent=None):
        super(SpikeSortingDialog, self).__init__(parent)

        # initialisations
        self.s_props = {}
        self.s_type = 'kilosort2'

        # sets the central widget
        self.main_widget = QWidget(self)

        # widget layouts
        self.main_layout = QGridLayout()
        self.sort_layout = QVBoxLayout()
        self.progress_layout = QVBoxLayout()
        self.cont_layout = QHBoxLayout()

        # class widgets
        self.sort_frame = QFrame(self)
        self.progress_frame = QFrame(self)
        self.cont_frame = QFrame(self)
        self.tab_group_sort = QTabWidget(self)

        # other class widget
        self.prog_bar = []
        self.button_cont = []

        # boolean class fields
        self.is_updating = False
        self.is_running = True

        # sets up the property fields
        self.setup_prop_fields()

        # initialises the major widget groups
        self.init_class_fields()
        self.init_sorting_frame()
        self.init_progress_frame()
        self.init_button_frame()
        self.set_widget_config()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_prop_fields(self):

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
        for kp, vp in self.s_prop_flds.items():
            # sets up the parent field
            self.s_props[kp] = {}

            # sets the children properties
            for k, p in vp['props'].items():
                self.s_props[kp][k] = p['value']

    def init_class_fields(self):

        # creates the dialog window
        self.setWindowTitle("Spike Sorting Parameters")
        self.setFixedSize(self.dlg_width, self.dlg_height)
        self.setLayout(self.main_layout)

        # sets the main widget properties
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        # adds the frame to the parent widget
        self.main_layout.addWidget(self.sort_frame)
        self.main_layout.addWidget(self.cont_frame)

        # resets the frame object names
        for qf in self.findChildren(QFrame):
            qf.setObjectName('sortFrame')

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

        # # creates the tab group object
        for k, v in self.s_prop_flds.items():
            tab_layout = QVBoxLayout()
            obj_tab = self.create_para_object(tab_layout, k, v['props'], 'tab', [k])
            self.tab_group_sort.addTab(obj_tab, v['name'])

        # tab-group change callback function
        i_tab0 = list(self.s_props.keys()).index(self.s_type)
        self.tab_group_sort.setCurrentIndex(i_tab0)
        self.tab_group_sort.currentChanged.connect(self.sort_tab_change)

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
        self.main_layout.addWidget(self.progress_frame, 1, 0, 1, 1)
        self.main_layout.addWidget(self.cont_frame, 2, 0, 1, 1)

        # set the grid layout column sizes
        self.main_layout.setRowStretch(0, self.p_row[0])
        self.main_layout.setRowStretch(1, self.p_row[1])
        self.main_layout.setRowStretch(2, self.p_row[2])

    # ---------------------------------------------------------------------------
    # Property Field Functions
    # ---------------------------------------------------------------------------

    def create_para_object(self, layout, p_str, p_val, p_type, p_str_p):

        match p_type:
            case 'tab':
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
                layout_para = QFormLayout(panel_frame)
                layout_para.setLabelAlignment(cf.align_type['right'])
                layout_para.setSpacing(x_gap)
                layout_para.setContentsMargins(2 * x_gap, 2 * x_gap, 2 * x_gap, x_gap)

                # creates the tab parameter objects
                for k, v in p_val.items():
                    self.create_para_object(layout_para, k, v, v['type'], p_str_p + [k])

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

        if state:
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
            self.button_control[4].setText('Start Preprocessing')

        else:
            # case is cancelling the calculations
            self.is_running = True

    def close_window(self):

        self.close()

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}
