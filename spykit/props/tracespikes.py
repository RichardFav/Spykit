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

# pyqtgraph modules
import pyqtgraph as pg

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

class TraceSpikeMixin:
    # plot properties
    sym = 'o'
    sym_size = 10

    # ---------------------------------------------------------------------------
    # Spike Marker Functions
    # ---------------------------------------------------------------------------

    def create_spike_markers(self):

        for i_lbl, u_lbl in enumerate(self.unit_lbl):
            # initialises plot marker indices
            u_lbl_lo = u_lbl.lower()
            self.i_unit_sp[u_lbl_lo] = []

            # creates plot marker
            l_pen_spike = pg.mkPen(color=cw.unit_col[u_lbl_lo])
            l_brush_spike = pg.mkBrush(color=cw.unit_col[u_lbl_lo])
            self.h_spike[u_lbl_lo] = self.trace_view.plot_item.plot(
                [np.nan],
                [np.nan],
                pen=None,
                symbol=self.sym,
                symbolSize=self.sym_size,
                symbolPen=l_pen_spike,
                symbolBrush=l_brush_spike
            )

            self.trace_view.h_plot[0, 0].addItem(self.h_spike[u_lbl_lo])

    def clear_spike_markers(self):

        for i_lbl, u_lbl in enumerate(self.unit_lbl):
            # clear plot marker indices
            u_lbl_lo = u_lbl.lower()
            self.i_unit_sp[u_lbl_lo] = []

            # clears the plot item
            self.trace_view.h_plot[0, 0].removeItem(self.h_spike[u_lbl_lo])

    # ---------------------------------------------------------------------------
    # Spike Channel Functions
    # ---------------------------------------------------------------------------

    def toggle_unit_index(self, u_type, i_unit):

        if i_unit in self.i_unit_sp[u_type]:
            # adds the new item
            self.i_unit_sp[u_type].append().sort()

        else:
            # removes existing item
            i_unit_ind = self.i_unit_sp[u_type].index(i_unit)
            self.i_unit_sp[u_type].pop(i_unit_ind).sort()

        # updates the spike markers
        self.update_unit_spike_markers(u_type)

    def update_unit_spike_markers(self, u_type):

        #
        pass

    def hide_spike_markers(self):

        pass

    def reset_spike_markers(self):

        # initialisations
        spk_channel_win = None

        # initialises the previous frame
        i_frm_nw = np.array([self.trace_view.i_frm0, self.trace_view.i_frm1])
        if self.i_frm_pr is not None:
            # case is previous frame index data
            if np.array_equal(self.i_frm_pr, i_frm_nw):
                # if no change in frame indices then exit
                return

            # previous index comparison
            a = 1

        else:
            # otherwise, determine the first spike greater than the lower limit
            i_spk0 = np.searchsorted(self.i_spike, i_frm_nw[0], 'left')
            if self.i_spike[i_spk0] < i_frm_nw[1]:
                # if this value is less than the upper limit, then determine the spikes within the window
                i_spk1 = np.searchsorted(self.i_spike[i_spk0:], i_frm_nw[1], 'left') + i_spk0
                spk_cluster_win = self.spk_cluster[i_spk0:i_spk1]
                spk_channel_win = np.array(self.data['Channel'][spk_cluster_win - 1])

        if spk_channel_win is not None:
            # determines the selected channels which have spikes within the trace window
            in_win = np.isin(spk_channel_win, self.trace_view.session_obj.get_selected_channels())
            if np.any(in_win):
                # if spikes within the window, then update the
                spk_cluster_win = spk_cluster_win[in_win]
                spk_channel_win = spk_channel_win[in_win]
                i_spike_win = self.i_spike[i_spk0:i_spk1][in_win]

                #
                pass
            else:
                # otherwise, clear the spike markers
                self.hide_spike_markers()

        else:
            # otherwise, clear the spike markers
            self.hide_spike_markers()

        # resets the previous frame indices
        self.i_frm_pr = i_frm_nw


# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceSpikeProps:
"""


class TraceSpikeProps(TraceSpikeMixin, PropWidget):
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
        TraceSpikeMixin.__init__(self)

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
        self.is_marker_init = False

        # other class fields
        self.h_spike = {}
        self.i_unit_sp = {}
        self.i_frm_pr = None

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # column indices
        self.i_col_tupe = self.c_hdr.index('Unit Type')
        self.i_col_unit = self.c_hdr.index('Unit')
        self.i_col_ch = self.c_hdr.index('Channel')
        self.i_col_count = self.c_hdr.index('Count')

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

        # unit selection memory allocation
        self.n_unit_pp = self.main_obj.main_obj.main_obj.session_obj.post_data.n_unit_pp
        self.is_filt = np.empty(self.n_unit_pp.shape, dtype=object)
        for i_pp, n_pp in enumerate(self.n_unit_pp.flat):
            self.is_filt[np.unravel_index(i_pp, self.is_filt.shape)] = np.zeros(n_pp, dtype=bool)

        # memory mapped field retrieval
        self.spk_cluster = self.get_field('spk_cluster')[:, 0]
        self.i_spike = self.get_field('i_spike')[:, 0].astype(np.uint32)
        self.unit_lbl = cw.get_unit_labels(self.get_field('splitGoodAndMua_NonSomatic'))

        # table dimensioning
        n_row_max = np.max(self.n_unit_pp)
        table_dim = (n_row_max, len(self.c_hdr))
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

                else:
                    # case is a string field
                    item.setFlags(self.norm_item_flag)

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

        # initialises the spike markers
        if not self.is_marker_init:
            self.create_spike_markers()
            self.is_marker_init = True

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

    def get_table_data_frame(self):

        # retrieves the raw metric data frame
        q_met_df = self.main_obj.main_obj.main_obj.session_obj.get_metric_table_values()[self.c_hdr_0].astype(int)

        # field retrieval
        i_shank = self.main_obj.main_obj.session_obj.get_shank_index()
        probe_view = self.main_obj.main_obj.main_obj.plot_manager.get_plot_view('probe')

        # re-maps the channel indices to the probe map
        self.i_pk_ch = q_met_df['maxChannels'].astype(int)
        q_met_df['maxChannels'] = probe_view.sub_view.ch_map[i_shank][self.i_pk_ch - 1]

        return q_met_df

    def get_metric_table_values(self):

        # field retrieval
        unit_type = self.get_unit_type_labels().reshape(-1, 1)
        show_spike = np.zeros((self.get_field('n_unit'), 1), dtype=bool)
        q_met_df = self.get_table_data_frame()

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




