# module import
import os
import time
import numpy as np
from pathlib import Path
from copy import deepcopy
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QGroupBox,
                             QLabel, QFrame, QSpacerItem, QSizePolicy, QToolBar, QLineEdit)
from PyQt6.QtCore import Qt, QSize, QEvent, pyqtSignal
from PyQt6.QtGui import QFont, QAction, QIcon

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    FilterWidget:
"""


class FilterWidget(QWidget):
    # pyqtsignal funcions
    widget_clicked = pyqtSignal()

    # widget dimensions
    combo_pad = 10
    widget_hght = 20

    # widget style-sheet
    combo_style = """
        QComboBox { 
            padding: 2px 5px;        
            border: 1px solid; 
        }
        QComboBox QAbstractItemView {
            background-color: rgba(255, 255, 255, 255);
            selection-background-color: rgba(0, 120, 215, 200);
        }
        QComboBox QLineEdit {
            padding: 2px 5px;        
        }
    """

    def __init__(self, main_obj, f_lbl):
        super(FilterWidget, self).__init__()

        # input arguments
        self.f_lbl = f_lbl
        self.main_obj = main_obj
        f_lbl_txt = f"  {self.f_lbl}  "

        # other class widgets
        self.hist_map = None
        self.param_map = None
        self.filt_combo = None
        self.filt_layout = QVBoxLayout()
        self.filt_lbl = cw.create_text_label(
            None, f_lbl_txt, font=cw.font_lbl, align='center')

        # boolean class fields
        self.is_combo = f_lbl != 'Comparison Value'

        # creates the filter widget
        self.init_class_fields()
        self.init_filter_widgets()

    # ---------------------------------------------------------------------------
    # Class Widget Initialisation Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # layout properties
        self.setLayout(self.filt_layout)
        self.filt_layout.setContentsMargins(0, 0, 0, 0)
        self.filt_layout.setSpacing(0)

        # label properties
        self.filt_lbl.setFixedHeight(self.widget_hght)
        self.filt_layout.addWidget(self.filt_lbl)

    def init_filter_widgets(self):

        if self.is_combo:
            # case is a combobox widget
            match self.f_lbl:
                case 'Operator':
                    # case is the inter-filter operator
                    p_list = ['AND', 'OR']

                case 'Filter Metric':
                    # case is the filter metric
                    self.hist_map = cf.rev_dict(cw.hist_map)
                    p_list = list(self.hist_map.keys())

                case 'Condition':
                    # case is the filter condition
                    p_list = ['Less Than', 'Less Than/Equal To', 'Greater Than',
                              'Greater Than/Equal To', 'Is Not NaN']

            self.filt_combo = cw.create_combo_box(None, text=[''] + p_list)

        else:
            # case is a edit-dropdown widget
            match self.f_lbl:
                case 'Comparison Value':
                    # case is the inter-filter operator
                    self.param_map = cf.rev_dict(cw.param_map)
                    p_list = list(self.param_map.keys())

            self.filt_combo = cw.QEditCombo(None, None, [''] + p_list)

        # adds the widget to the layout
        self.filt_combo.setObjectName(self.f_lbl)
        self.filt_combo.setFixedHeight(self.widget_hght)
        self.filt_layout.addWidget(self.filt_combo)
        self.filt_combo.setStyleSheet(self.combo_style)

        # installs an event filter
        self.filt_combo.installEventFilter(self)

        # center aligns the combobox item
        for i in range(len(p_list) + 1):
            if self.f_lbl == 'Operator':
                self.filt_combo.setItemData(
                    i, Qt.AlignmentFlag.AlignCenter, Qt.ItemDataRole.TextAlignmentRole)
            else:
                self.filt_combo.setItemData(
                    i, Qt.AlignmentFlag.AlignLeft, Qt.ItemDataRole.TextAlignmentRole)

        # resizes the combobox (ensures item text fits)
        sz_combo = self.filt_combo.sizeHint()
        self.filt_combo.setFixedWidth(sz_combo.width() + self.combo_pad)

    # ---------------------------------------------------------------------------
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

    def mousePressEvent(self, evnt):

        self.widget_clicked.emit()
        super().mousePressEvent(evnt)

    def eventFilter(self, obj, event):

        # if the widget is clicked, then emit a signal
        if event.type() == QEvent.Type.MouseButtonPress:
            self.widget_clicked.emit()

        return super().eventFilter(obj, event)

# ----------------------------------------------------------------------------------------------------------------------

"""
    FilterBlock:
"""

class FilterBlock(QFrame):
    # pyqtsignal funcions
    groupbox_click = pyqtSignal()
    frame_clicked = pyqtSignal(int)
    toolbar_update = pyqtSignal()

    # scalar class fields
    n_fld = 4

    # fixes array fields
    t_lbl = ['Operator', 'Filter Metric', 'Condition', 'Comparison Value']

    def __init__(self, main_obj, i_filt_nw):
        super(FilterBlock, self).__init__()

        # input arguments
        self.main_obj = main_obj
        self.i_filt = i_filt_nw

        # other class widget fields
        self.spacer = None
        self.map_func = None
        self.filt_widget = []
        self.main_layout = QHBoxLayout()
        self.filt_opt = np.empty(self.n_fld, dtype=object)

        # creates the filter block widget
        self.create_filter_block()

    # ---------------------------------------------------------------------------
    # Class Widget Initialisation Functions
    # ---------------------------------------------------------------------------

    def create_filter_block(self):

        # sets the frame properties
        self.setObjectName('filtFrame')
        self.setFrameShape(QFrame.Shape.Box)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        self.set_frame_highlight(False)

        # layout properties
        self.setLayout(self.main_layout)
        self.main_layout.setSpacing(x_gap)
        self.main_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

        for i_tl, tl in enumerate(self.t_lbl):
            # creates the new filter widget
            f_widget_nw = FilterWidget(self.main_obj, tl)
            f_widget_nw.widget_clicked.connect(self.widget_clicked_event)

            # sets the parameter group
            cb_cbox = pfcn(self.filter_update, i_tl)
            if tl == 'Comparison Value':
                # case is the comparison value filter option
                f_widget_nw.filt_combo.connect(cb_cbox)

            else:
                # case is the other filter options
                f_widget_nw.filt_combo.currentIndexChanged.connect(cb_cbox)

            # adds the widget to the main class widget
            self.filt_widget.append(f_widget_nw)
            self.main_layout.addWidget(f_widget_nw)

        # creates the spacer item
        sz_hint = self.filt_widget[0].sizeHint()
        self.filt_widget[0].setFixedSize(sz_hint.width(), sz_hint.height())
        self.spacer = QSpacerItem(sz_hint.width() + x_gap, sz_hint.height(),
                                  QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # removes the "operator" groupbox (if first level)
        if self.i_filt == 0:
            self.set_filter_level()

    # ---------------------------------------------------------------------------
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

    def filter_update(self, i_filt, *args):

        # retrieves the current text
        nw_text = self.filt_widget[i_filt].filt_combo.currentText()

        if len(nw_text):
            # case is the field is not empty
            if i_filt == 3:
                # case is the numeric field

                # determines if the new value is valid
                nw_text = self.get_param_value(nw_text)
                chk_val = cf.check_edit_num(nw_text)
                if chk_val[1] is None:
                    self.filt_opt[i_filt] = nw_text

                elif self.filt_opt[i_filt] is None:
                    # case is there is no previous value
                    self.filt_widget[i_filt].filt_combo.setCurrentText("")
                    return

                else:
                    # otherwise, set the previous valid value
                    self.filt_widget[i_filt].filt_combo.setCurrentText(self.filt_opt[i_filt])
                    return

            else:
                # case is the other filter type
                self.filt_opt[i_filt] = nw_text
        else:
            # case is the field is empty
            self.filt_opt[i_filt] = None

        # updates the menu item properties
        self.toolbar_update.emit()

    def widget_clicked_event(self):

        self.frame_clicked.emit(self.i_filt)

    def mousePressEvent(self, event):

        # Triggered when the frame is clicked
        self.frame_clicked.emit(self.i_filt)

        # runs the widget event function
        super().mousePressEvent(event)

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def get_param_value(self, nw_text):

        if nw_text in self.filt_widget[-1].param_map:
            p_value = '%g' % self.map_func(self.filt_widget[-1].param_map[nw_text])

            self.filt_widget[-1].filt_combo.blockSignals(True)
            self.filt_widget[-1].filt_combo.setCurrentText(p_value)
            self.filt_widget[-1].filt_combo.blockSignals(False)

            return p_value

        else:
            return nw_text

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_frame_highlight(self, is_on):

        if is_on:
            self.setStyleSheet("""
                #filtFrame {
                    border: 2px solid red;
                }
            """)

        else:
            self.setStyleSheet("""
                #filtFrame {
                    border: 2px solid black;
                }
            """)

    def set_filter_level(self, i_filt_nw=None):

        if i_filt_nw is not None:
            self.i_filt = i_filt_nw

        if self.i_filt == 0:
            # "hides" the operator field
            self.main_layout.removeWidget(self.filt_widget[0])
            self.filt_widget[0].setParent(None)
            self.main_layout.insertItem(0, self.spacer)

        else:
            # "shows" the operator field
            self.main_layout.removeItem(self.spacer)
            self.main_layout.insertWidget(0, self.filt_widget[0])
            self.filt_widget[0].setVisible(True)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def clear_block(self):

        for i in range(self.n_fld):
            # resets the field options
            self.filt_opt[i] = None

            # clears the filter widget fields
            self.filt_widget[i].blockSignals(True)
            self.filt_widget[i].setCurrentIndex(0)
            self.filt_widget[i].blockSignals(False)

        # updates the menu item properties
        self.toolbar_update.emit()

    def is_filter_complete(self):

        if self.i_filt == 0:
            return ~np.any(self.filt_opt[1:] == None)

        else:
            return ~np.any(self.filt_opt == None)

# ----------------------------------------------------------------------------------------------------------------------

"""
    FilterManagerMixin:
"""

class FilterManagerMixin:

    # ---------------------------------------------------------------------------
    # Filter Block Functions
    # ---------------------------------------------------------------------------

    def add_filter_block(self, reset_spacer=True):

        # removes the spacer item
        if reset_spacer:
            self.filt_layout.removeItem(self.spacer)

        # creates and adds the new filter object
        obj_filt_nw = FilterBlock(self.main_obj, self.n_filt)
        self.filt_layout.addWidget(obj_filt_nw)

        # sets the slot/function handles
        obj_filt_nw.frame_clicked.connect(self.frame_click_event)
        obj_filt_nw.toolbar_update.connect(self.update_toolbar_props)
        obj_filt_nw.map_func = self.get_field

        # updates the other fields
        self.n_filt += 1
        self.obj_filt.append(obj_filt_nw)

        # re-adds the spacer item
        if reset_spacer:
            self.filt_layout.insertItem(self.n_filt, self.spacer)

    def remove_filter_block(self, i_blk):

        # resets the filter index
        for i in range((i_blk + 1), self.n_filt):
            self.obj_filt[i].set_filter_level(i - 1)

        # deletes the filter block
        self.obj_filt[i_blk].delete()
        self.obj_filt[i_blk].pop()

    def clear_filter_blocks(self):

        # deletes all filter blocks
        for i in reversed(range(self.n_filt)):
            if i == 0:
                self.obj_filt[i].clear_block()

            else:
                self.obj_filt[i].delete()
                self.obj_filt[i].pop()
                self.n_filt -= 1

    def move_filter_block(self, i_blk, m_dir):

        pass

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitFilterDialog:
"""

class UnitFilterDialog(FilterManagerMixin, QDialog):
    # widget dimensions
    x_gap = 5
    n_filt_max = 6

    # font objects
    tool_name = ['add', 'remove', 'close', None, 'tick',
                 'restart', None, 'arrow_up', 'arrow_down']
    tool_lbl = ['Add Filter', 'Remove Filter', 'Clear All Filters', None,
                'Apply Filter', 'Reset Original', None, 'Move Up', 'Move Down']
    font_hdr = cw.create_font_obj(size=10, is_bold=True, font_weight=QFont.Weight.Bold)

    def __init__(self, main_obj):
        FilterManagerMixin.__init__(self)
        super(UnitFilterDialog, self).__init__()

        # input arguments
        self.main_obj = main_obj

        # class widget setup
        self.tool_bar = QToolBar(self)
        self.filt_group = QGroupBox("FILTER CONDITIONS")

        # class layout setup
        self.main_layout = QVBoxLayout()
        self.filt_layout = QVBoxLayout()

        # memory allocation
        self.n_filt = 0
        self.i_filt_sel = None
        self.obj_filt = []

        # initialises the class fields/objects
        self.init_class_fields()
        self.init_tool_bar()
        self.init_class_objects()

    # ---------------------------------------------------------------------------
    # Class Initialisation Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # main widget properties
        self.setLayout(self.main_layout)
        self.setWindowTitle('Unit Metric Filter')

        # sets up the groupbox widget
        self.main_layout.addWidget(self.tool_bar)
        self.main_layout.addWidget(self.filt_group)
        self.filt_group.setLayout(self.filt_layout)
        self.filt_group.setFont(self.font_hdr)

        # layout spacing
        self.filt_layout.setSpacing(x_gap)
        self.filt_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

    def init_tool_bar(self):

        # sets the toolbar properties
        self.tool_bar.setMovable(False)
        self.tool_bar.setStyleSheet(cw.toolbar_style)
        self.tool_bar.setIconSize(QSize(cf.but_height + 1, cf.but_height + 1))

        # adds the toolbar action widget
        for t_n, t_l in zip(self.tool_name, self.tool_lbl):
            if t_n is None:
                # case is a separator line
                self.tool_bar.addSeparator()

            else:
                # creates the action item
                h_icon = QIcon(cw.icon_path[t_n])
                h_action = QAction(h_icon, t_l, self)
                self.tool_bar.addAction(h_action)

                # sets the action object properties
                cb_fcn = pfcn(self.tool_bar_event, t_n)
                h_action.setParent(self.tool_bar)
                h_action.triggered.connect(cb_fcn)
                h_action.setObjectName(t_n)
                h_action.setEnabled(False)

    def init_class_objects(self):

        # adds the first filter block
        self.add_filter_block(False)

        # creates the group height
        sz_hint_grp = self.filt_group.sizeHint()
        sz_hint_blk = self.obj_filt[0].sizeHint()
        hght_spacer = sz_hint_blk.height() * (self.n_filt_max - 1)
        hght_grp = hght_spacer + sz_hint_grp.height()
        self.filt_group.setFixedHeight(hght_grp)

        # creates the spacer item
        self.spacer = QSpacerItem(sz_hint_blk.width(), hght_spacer,
                                  QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.filt_layout.addItem(self.spacer)

    # ---------------------------------------------------------------------------
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

    def tool_bar_event(self, t_type):

        match t_type:
            case 'add':
                # case is adding a filter
                self.add_filter_block()

            case 'remove':
                # case is removing a filter
                pass

            case 'close':
                # case is clearing all filters
                pass

            case 'tick':
                # case is applying the filters
                pass

            case 'restart':
                # case is resetting the original filter
                pass

            case 'arrow_up':
                # case is moving the filter up
                pass

            case 'arrow_down':
                # case is moving the filter up
                pass

        # updates the toolbar properties
        self.update_toolbar_props()

    def frame_click_event(self, i_filt_nw):

        # removes any existing highlight
        if self.i_filt_sel is not None:
            self.obj_filt[self.i_filt_sel].set_frame_highlight(False)

        # adds the newly clicked filter highlight
        self.i_filt_sel = i_filt_nw
        self.obj_filt[i_filt_nw].set_frame_highlight(True)

        # updates the toolbar properties
        self.update_toolbar_props()

    # ---------------------------------------------------------------------------
    # Dialog Toolbar Functions
    # ---------------------------------------------------------------------------

    def update_toolbar_props(self):

        # add/apply filter toolbar items
        all_filt_set = self.is_all_filter_complete()
        for tn in ['add', 'tick']:
           self.set_toolbar_enabled(tn, all_filt_set)

        # remove filter toolbar item
        can_remove_filt = ((self.i_filt_sel is not None) and
                           (self.n_filt > 1))
        self.set_toolbar_enabled('remove', can_remove_filt)

        # clear all filters toolbar item
        can_clear_filt = self.has_any_filter_set()
        self.set_toolbar_enabled('close', can_clear_filt)

        # reset original toolbar item
        can_reset_filt = False
        self.set_toolbar_enabled('restart', can_reset_filt)

        # move filter up toolbar item
        can_move_up_filt = ((self.i_filt_sel is not None) and
                            (self.i_filt_sel > 0))
        self.set_toolbar_enabled('arrow_up', can_move_up_filt)

        # move filter down toolbar item
        can_move_down_filt = ((self.i_filt_sel is not None) and
                              ((self.i_filt_sel + 1) < self.n_filt))
        self.set_toolbar_enabled('arrow_down', can_move_down_filt)

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_field(self, p_fld):

        return self.main_obj.session_obj.get_mem_map_field(p_fld)

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_toolbar_enabled(self, t_type, state):

        h_action = self.findChild(QAction, name=t_type)
        h_action.setEnabled(state)

    def is_all_filter_complete(self):

        return np.all([x.is_filter_complete() for x in self.obj_filt])

    def has_any_filter_set(self):

        return (self.n_filt > 1) or np.any(self.obj_filt[0].filt_opt != None)