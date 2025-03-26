# module import
import os
import time
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtWidgets import QTableWidget, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    TriggerPara:
"""


class TriggerPara(PropPara):
    # pyqtSignal functions
    pair_update = pyqtSignal()

    def __init__(self, p_info):
        self.is_updating = True
        super(TriggerPara, self).__init__(p_info)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def _pair_update(_self):

        if not _self.is_updating:
            _self.pair_update.emit()

    # trace property observer properties
    button_flag = cf.ObservableProperty(_pair_update)

# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceProp:
"""


class TriggerProps(PropWidget):
    # array class fields
    c_hdr = ['Region', 'Start (s)', 'Finish (s)']
    item_index = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    item_flag = item_index | Qt.ItemFlag.ItemIsEditable

    # font types
    table_font = cw.create_font_obj(size=8)
    table_hdr_font = cw.create_font_obj(size=8, is_bold=True, font_weight=QFont.Weight.Bold)

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # field initialisation
        self.n_row = 0
        self.b_state = 0
        self.i_row_sel = None

        # initialises the property widget
        self.setup_prop_fields()
        super(TriggerProps, self).__init__(self.main_obj, 'trigger', self.p_info)

        # sets up the parameter fields
        self.p_props = TriggerPara(self.p_info['ch_fld'])

        # widget field retrieval
        self.button_pair = self.findChild(cw.QButtonPair)
        self.table_region = self.findChild(QTableWidget)

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # connects the slot functions
        self.p_props.pair_update.connect(self.pair_update)

        # resets the table properties
        n_col = len(self.c_hdr)
        self.table_region.setColumnCount(n_col)
        self.table_region.setHorizontalHeaderLabels(self.c_hdr)
        self.table_region.verticalHeader().setVisible(False)

        self.table_region.cellChanged.connect(self.table_changed)
        self.table_region.cellClicked.connect(self.table_selected)

        # sets the button properties
        self.button_pair.set_enabled(1, False)

        # resets the section resize mode
        horz_hdr = self.table_region.horizontalHeader()
        horz_hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for i_col in range(n_col):
            # updates the table header font
            self.table_region.horizontalHeaderItem(i_col).setFont(self.table_hdr_font)

        # flag initialisation is complete
        self.is_init = True

    def setup_prop_fields(self):

        # array fields
        b_str = ['Add Row', 'Remove Row']

        # sets up the subgroup fields
        p_tmp = {
            'button_flag': self.create_para_field(b_str, 'buttonpair', 0),
            'region_index': self.create_para_field('Region Indices', 'table', None),
        }

        # updates the class field
        self.p_info = {'name': 'Trigger', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def table_selected(self):

        self.i_row_sel = self.table_region.currentRow()
        self.button_pair.set_enabled(1, True)

    def table_changed(self):

        if self.is_updating:
            return

    def pair_update(self):

        # determines the selected button
        i_button = int(np.log2(abs(self.b_state - self.p_props.button_flag)))

        # resets the table row count
        self.is_updating = True
        self.n_row += 1 - 2 * (i_button == 1)

        if i_button == 0:
            # case is adding a new row
            nw_row = [self.n_row, 0, 0]
            self.table_region.setRowCount(self.n_row)

            for i_col, c_val in enumerate(nw_row):
                # creates the widget item
                item = cw.QTableWidgetItemSortable(None)
                item.setFont(self.table_font)

                # case is a string field
                item.setFlags(self.item_index if i_col == 0 else self.item_flag)
                item.setText(str(c_val))

                # adds the item to the table
                item.setTextAlignment(cf.align_type['center'])
                self.table_region.setItem(self.n_row - 1, i_col, item)

        else:
            # case is removing a row
            for i_row in range((self.i_row_sel + 1), (self.n_row + 1)):
                item = self.table_region.item(i_row, 0)
                item.setText(str(i_row))

            # resets the other properties
            self.button_pair.set_enabled(1, False)
            self.table_region.removeRow(self.i_row_sel)
            self.i_row_sel = None

        # resets the button state
        self.is_updating = False
        self.b_state = self.p_props.button_flag
