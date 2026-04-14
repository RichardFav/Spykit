# module import
import numpy as np
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
    c_hdr = ['', 'Unit ID#', 'Unit Type', 'Channel ID#', 'Count']

    # font types
    table_font = cw.create_font_obj(size=8)
    table_hdr_font = cw.create_font_obj(size=8, is_bold=True, font_weight=QFont.Weight.Bold)

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
        self.table = cw.QInfoTable(None, self.type, True)

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

        # sets the table header properties
        table_hdr = self.table.horizontalHeader()
        table_hdr.setFont(self.table_hdr_font)
        table_hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

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

    def setup_info_table(self):

        # retrieves the table data values
        self.get_metric_table_values()

        # if the table/data shape is equal then exit
        if (self.table.rowCount(), self.table.columnCount()) == table_dim:
            return

        # flag that manual update is taking place
        self.is_updating = True

        # clears the table model
        self.table.clear()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(table_dim[0])
        self.table.setColumnCount(table_dim[1])

        for i_col in range(len(c_hdr)):
            # updates the table header font
            self.table.horizontalHeaderItem(i_col).setFont(self.table_hdr_font)

            # creates all table items for current column
            values = self.data[self.data.columns[i_col]]
            for i_row in range(table_dim[0]):
                # creates the widget item
                item = QTableWidgetItem()
                item.setFont(self.table_font)

                # sets the item properties (based on the field values)
                if isinstance(values[i_row], np.bool_):
                    # case is a boolean field
                    item.setFlags(self.check_item_flag)
                    item.setCheckState(cf.chk_state[values[i_row]])

                else:
                    # case is a string field
                    item.setFlags(self.norm_item_flag)
                    item.setText(str(values[i_row]))

                # adds the item to the table
                item.setTextAlignment(cf.align_type['center'])
                self.table.setItem(i_row, i_col, item)

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

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_trace_view(self, trace_view_new):

        self.trace_view = trace_view_new

    def set_para_value(self, p_fld, p_val):

        setattr(self.p_props, p_fld, p_val)

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_metric_table_values(self):

        self.q_met = self.main_obj.main_obj.main_obj.session_obj.get_metric_table()
        pass

    def get_para_value(self, p_fld):

        return getattr(self.p_props, p_fld)

    def get_mem_map_field(self, p_fld):

        return self.main_obj.main_obj.session_obj.get_mem_map_field(p_fld)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

