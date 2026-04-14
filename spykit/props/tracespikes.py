# module import
import time
import numpy as np
import pandas as pd
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceSpikePara:
"""

class TraceSpikePara(PropPara):
    # pyqtSignal functions
    edit_update = pyqtSignal(str)

    def __init__(self, p_info):

        # initialises the class parameters
        self.is_updating = True
        super(TraceSpikePara, self).__init__(p_info)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def _edit_update(p_str, _self):

        if not _self.is_updating:
            _self.edit_update.emit(p_str)

    @staticmethod
    def _check_update(p_str, _self):

        if not _self.is_updating:
            _self.check_update.emit(p_str)

    # trace property observer properties
    i_spike = cf.ObservableProperty(pfcn(_edit_update, 'i_spike'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceSpikeProps:
"""


class TraceSpikeProps(PropWidget):
    # field properties
    type = 'tracespike'
    c_hdr_0 = ['clusterID', 'maxChannels', 'nSpikes']
    c_hdr = ['', 'Unit Type', 'Unit', 'Channel', 'Count']

    # font types
    table_font = cw.create_font_obj(size=8)
    table_hdr_font = cw.create_font_obj(size=8, is_bold=True, font_weight=QFont.Weight.Bold)

    # table cell item flags
    norm_item_flag = Qt.ItemFlag.ItemIsEnabled
    check_item_flag = norm_item_flag | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # initialises the property widget
        self.setup_prop_fields()
        super(TraceSpikeProps, self).__init__(self.main_obj, 'unitmet', self.p_info)

        # sets up the parameter fields
        self.p_props = TraceSpikePara(self.p_info['ch_fld'])

        # other class widgets
        # self.unit_label = cw.QLabelText(None, lbl_str="Selected Unit:", text_str='N/A',
        #                                 font_lbl=cw.font_lbl, font_txt=cw.font_lbl)
        self.table = cw.QInfoTable(None, self.type, False)
        self.edit_spike = self.findChild(cw.QLabelEdit, name='i_spike')

        # other class fields
        self.plot_view = None
        self.is_updating = False

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # sets the parameter layout properties
        self.f_layout.setSpacing(5)
        # self.f_layout.addWidget(self.unit_label)
        self.f_layout.addWidget(self.table)

        # connects the editbox slot functions
        self.p_props.edit_update.connect(self.edit_update)
        for ch_k, ch_v in self.p_info['ch_fld'].items():
            if ch_v['type'] in 'edit':
                setattr(self, ch_k, self.get_para_value(ch_k))

        # sets the table widget properties
        self.table.setColumnCount(len(self.c_hdr))
        self.table.setHorizontalHeaderLabels(self.c_hdr)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.resizeColumnsToContents()

        # table function callback function
        self.table.cellChanged.connect(self.table_cell_changed)

        # sets the table header properties
        table_hdr = self.table.horizontalHeader()
        table_hdr.setFont(self.table_hdr_font)
        table_hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table_hdr.setStretchLastSection(True)

        # sets the other widget properties
        self.edit_spike.set_enabled(False)

    def setup_prop_fields(self):

        # sets up the subgroup fields
        p_tmp = {
            'i_spike': self.create_para_field('Spike Index', 'edit', 1),
        }

        # updates the class field
        self.p_info = {'name': 'Metrics', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_spike_table(self):

        # sets up the unit type fields
        self.unit_lbl = cw.get_unit_labels(self.get_field('splitGoodAndMua_NonSomatic'))

        # table creation
        n_row_max = np.max(self.main_obj.main_obj.main_obj.session_obj.post_data.n_unit_pp)
        table_dim = (n_row_max, len(self.c_hdr))

        # if the table/data shape is equal then exit
        if (self.table.rowCount(), self.table.columnCount()) == table_dim:
            return

        # flag that manual update is taking place
        self.is_updating = True
        time.sleep(0.05)

        # clears the table model
        self.table.clear()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(table_dim[0])
        self.table.setColumnCount(table_dim[1])

        # sets the table header view
        self.get_metric_table_values()
        self.table.setHorizontalHeaderLabels(self.c_hdr)

        for i_col in range(table_dim[1]):
            # updates the table header font
            self.table.horizontalHeaderItem(i_col).setFont(self.table_hdr_font)

            # creates all table items for current column
            value0 = self.data.iloc[0][self.data.columns[i_col]]
            for i_row in range(table_dim[0]):
                # creates the widget item
                item = QTableWidgetItem()
                item.setFont(self.table_font)

                # sets the item properties (based on the field values)
                if isinstance(value0, bool):
                    # case is a boolean field
                    item.setFlags(self.check_item_flag)
                    # item.setCheckState(cf.chk_state[values[i_row]])

                else:
                    # case is a string field
                    item.setFlags(self.norm_item_flag)
                    # item.setText(str(values[i_row]))

                # adds the item to the table
                item.setTextAlignment(cf.align_type['center'])
                self.table.setItem(i_row, i_col, item)

        # resets the update flag
        self.is_updating = False

    def set_spike_table_data(self):

        # field retrieval
        self.get_metric_table_values()

        # flag that manual update is taking place
        self.is_updating = True

        for i_row, c_stat in enumerate(self.data['Unit Type']):
            # sets the table row colour
            self.table.setRowHidden(i_row, False)
            self.set_table_row_colour(i_row, c_stat.lower())

            for i_col in range(self.table.columnCount()):
                # sets the item value (based on the field values)
                value = self.data.iloc[i_row][self.data.columns[i_col]]
                if isinstance(value, bool):
                    # case is a boolean field
                    self.table.item(i_row, i_col).setCheckState(cf.chk_state[value])

                else:
                    # case is a string field
                    self.table.item(i_row, i_col).setText(str(value))

        # hides the extra table rows
        for i_row in reversed(range(self.data.shape[0], self.table.rowCount())):
            self.table.setRowHidden(i_row, True)

        # resets the update flag
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def edit_update(self, p_str):

        # if force updating, then exit the function
        if self.is_updating:
            return

        # field retrieval
        h_edit = self.findChild(cw.QLineEdit,name=p_str)
        nw_val = h_edit.text()

    def table_cell_changed(self):

        if self.is_updating:
            return

        pass

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_trace_view(self, trace_view_new):

        self.trace_view = trace_view_new

    def set_para_value(self, p_fld, p_val):

        setattr(self.p_props, p_fld, p_val)

    def set_table_row_colour(self, i_row, c_stat):

        for i_col in range(self.table.columnCount()):
            self.table.item(i_row, i_col).setBackground(cw.unit_col[c_stat])

    def set_table_rows(self, is_filt):

        for i_row in range(self.data.shape[0]):
            self.table.setRowHidden(i_row, not is_filt[i_row])

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_metric_table_values(self):

        # field retrieval
        unit_type = self.get_unit_type_labels().reshape(-1, 1)
        show_spike = np.zeros((self.get_field('n_unit'), 1), dtype=bool)
        q_met_df = self.main_obj.main_obj.main_obj.session_obj.get_metric_table_values()[self.c_hdr_0].astype(int)

        # sets the final metric dataframe
        self.data = pd.DataFrame(np.hstack((show_spike, unit_type, q_met_df), dtype=object), columns=self.c_hdr)

    def get_unit_type_labels(self):

        return np.array([self.unit_lbl[x[0]] for x in self.get_field('unit_type')])

    def get_para_value(self, p_fld):

        return getattr(self.p_props, p_fld)

    def get_field(self, p_fld):

        return self.main_obj.main_obj.session_obj.get_mem_map_field(p_fld)

    def get_unit_indices(self):

        # retrieves the unit ID's for each row
        unit_id = []
        for i in range(self.data.shape[0]):
            item = self.table.item(i, self.i_col_unit)
            unit_id.append(int(item.text()))

        return np.array(unit_id)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

