# module import
import numpy as np
from copy import deepcopy
from functools import partial as pfcn

# custom module imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QWidget, QFrame, QFormLayout, QVBoxLayout, QLineEdit, QCheckBox,
                             QTabWidget, QSizePolicy)
from PyQt6.QtCore import pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeSorting:  
"""


class SpikeSorting(QDialog):
    # pyqtsignal functions
    prop_updated = pyqtSignal()

    # widget dimensions
    x_gap = 5
    min_width = 300
    min_height = 300

    def __init__(self, parent=None):
        super(SpikeSorting, self).__init__(parent)

        # initialisations
        self.s_props = {}
        self.s_type = 'mountainsort5'

        # sorting group widgets
        self.main_layout = QVBoxLayout()
        self.frame_sort = QFrame(self)
        self.tab_group_sort = QTabWidget(self)
        self.layout_sort = QVBoxLayout()

        # initialises the major widget groups
        self.setup_dialog()
        self.setup_prop_fields()
        self.init_sorting_frame()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_dialog(self):

        # creates the dialog window
        self.setWindowTitle("Spike Sorting Parameters")
        self.setFixedWidth(self.min_width)

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

    def init_sorting_frame(self):

        # field retrieval
        # self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

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

        # # creates the tab group object
        for k, v in self.s_prop_flds.items():
            tab_layout = QVBoxLayout()
            obj_tab = self.create_para_object(tab_layout, k, v['props'], 'tab', [k])
            self.tab_group_sort.addTab(obj_tab, v['name'])

        # tab-group change callback function
        i_tab0 = list(self.s_props.keys()).index(self.s_type)
        self.tab_group_sort.setCurrentIndex(i_tab0)
        self.tab_group_sort.currentChanged.connect(self.sort_tab_change)

        # adds the frame to the parent widget
        self.main_layout.addWidget(self.frame_sort)

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
                layout_para.setSpacing(self.x_gap)
                layout_para.setContentsMargins(2 * self.x_gap, 2 * self.x_gap, 2 * self.x_gap, self.x_gap)

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
                lbl_str = '{0}'.format(p_val['name'])
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

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}