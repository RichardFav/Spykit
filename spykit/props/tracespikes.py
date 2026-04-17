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
    m_size = cf.ObservableProperty(pfcn(_edit_update, 'm_size'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceSpikeMixin:
"""

class TraceSpikeMixin:
    # plot properties
    sym = 'o'
    sym_size = 20

    # pen objects
    l_pen_spike = pg.mkPen(color='white', width=2)

    # ---------------------------------------------------------------------------
    # Spike Marker Functions
    # ---------------------------------------------------------------------------

    def create_spike_markers(self):

        for i_lbl, u_lbl in enumerate(self.unit_lbl):
            # initialises plot marker indices
            u_lbl_lo = u_lbl.lower()
            self.i_unit_sp[u_lbl_lo] = []

            # creates plot marker
            # l_brush_spike = pg.mkBrush(color=cw.unit_col[u_lbl_lo])
            self.h_spike[u_lbl_lo] = self.trace_view.plot_item.plot(
                [np.nan],
                [np.nan],
                pen=None,
                symbol=self.sym,
                symbolSize=self.get_para_value('m_size'),
                symbolPen=self.l_pen_spike,
                symbolBrush=cw.unit_col[u_lbl_lo]
            )

            self.trace_view.h_plot[0, 0].addItem(self.h_spike[u_lbl_lo])

    def delete_spike_markers(self):

        # clear class fields
        self.i_spike_win = None
        self.spk_cluster_win = None
        self.spk_channel_win = None

        for i_lbl, u_lbl in enumerate(self.unit_lbl):
            # clear plot marker indices
            u_lbl_lo = u_lbl.lower()
            self.i_unit_sp[u_lbl_lo] = []

            # deletes the plot item
            self.trace_view.h_plot[0, 0].removeItem(self.h_spike[u_lbl_lo])

    def clear_spike_markers(self):

        if self.markers_cleared:
            return

        # clear class fields
        self.markers_cleared = True

        # clear spike window fields
        for i_lbl, u_lbl in enumerate(self.unit_lbl):
            # clear plot marker indices
            u_lbl_lo = u_lbl.lower()

            # clears the plot item
            self.h_spike[u_lbl_lo].setData(x=[np.nan], y=[np.nan])

    def reset_marker_size(self):

        # resets the marker size
        m_size = int(self.get_para_value('m_size'))
        for i_lbl, u_lbl in enumerate(self.unit_lbl):
            self.h_spike[u_lbl.lower()].setData(symbolSize=m_size)

        # resets the spike markers
        self.reset_spike_markers()

    def update_spike_markers(self):

        #
        unit_type_win = np.array(self.data['Unit Type'][self.spk_cluster_win[self.in_win] - 1])

        # clear spike window fields
        for i_lbl, u_lbl in enumerate(self.unit_lbl):
            # clear plot marker indices
            if u_lbl in unit_type_win:
                # updates the markers
                is_unit = unit_type_win == u_lbl
                self.update_unit_spike_markers(u_lbl, is_unit)

            else:
                # otherwise, clear the plot
                self.h_spike[u_lbl.lower()].setData(x=[np.nan], y=[np.nan])

        # flag the markers are not cleared
        self.markers_cleared = False

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

    def update_unit_spike_markers(self, u_lbl, is_unit):

        # memory allocation
        x_spk, y_spk = np.array([]), np.array([])

        # field retrieval
        use_diff = int(self.trace_view.use_diff_signal())
        i_spike_unit = self.i_spike_win[self.in_win][is_unit] - self.trace_view.i_frm0
        spike_channel_unit = self.spk_channel_win[self.in_win][is_unit] - 1
        spike_cluster_unit = self.spk_cluster_win[self.in_win][is_unit] - 1

        # sets the spike coordinates for each unique unit cluster
        spk_ch, i_spk_ch = np.unique(spike_channel_unit, return_inverse=True)
        for i_spk, spk in enumerate(spk_ch):
            # if not selected within the table, then continue
            ii = i_spk_ch == i_spk
            i_spk_unit = spike_cluster_unit[ii]
            if not self.is_filt[self.i_run, self.i_shank][i_spk_unit[0]]:
                continue

            # retrieves the spike x-coordinates
            x_spk = np.append(x_spk, self.trace_view.x_tr[0, i_spike_unit[ii] - use_diff])

            # retrieves the spike y-oordinates
            i_ch = np.where(self.i_ch_sel == spk)[0][0]
            y_spk = np.append(y_spk, self.trace_view.y_tr[i_ch, i_spike_unit[ii] - use_diff])

        # updates the unit's spike marker coordinates
        if len(x_spk):
            self.h_spike[u_lbl.lower()].setData(x=x_spk, y=y_spk)
        else:
            self.h_spike[u_lbl.lower()].setData(x=[np.nan], y=[np.nan])

    def reset_spike_markers(self):

        # initialisations
        reset_win = False
        spk_channel_win = None

        # initialises the previous frame
        i_frm_nw = np.array([self.trace_view.i_frm0, self.trace_view.i_frm1])
        if self.i_frm_pr is not None:
            # previous index comparison
            if not np.array_equal(i_frm_nw, self.i_frm_pr):
                reset_win = True
                if i_frm_nw[0] > self.i_frm_pr[1]:
                    # new lower limit exceeds previous upper limit
                    self.reset_spike_index_limits(i_frm_nw, i_start=self.i_spk0)

                elif i_frm_nw[1] < self.i_frm_pr[0]:
                    # new upper limit exceeds previous lower limit
                    self.reset_spike_index_limits(i_frm_nw, i_finish=self.i_spk0)

                else:
                    # resets the spike lower/upper limits
                    self.reset_index_lower_limit(i_frm_nw)
                    self.reset_index_upper_limit(i_frm_nw)

        else:
            # case is resetting the index limits
            reset_win = True
            self.reset_spike_index_limits(i_frm_nw)

        if (self.i_spk1 is not None):
            # reset if chande in lower/upper limits
            if reset_win:
                self.spk_cluster_win = self.spk_cluster[self.i_spk0:self.i_spk1]
                self.spk_channel_win = np.array(self.data['Channel'][self.spk_cluster_win - 1])
                self.i_spike_win = self.i_spike[self.i_spk0:self.i_spk1]

            # determines the selected channels which have spikes within the trace window
            self.i_ch_sel = self.trace_view.session_obj.get_selected_channels()
            self.in_win = np.isin(self.spk_channel_win - 1, self.i_ch_sel)
            if np.any(self.in_win):
                # if spikes within the window, then update the
                self.update_spike_markers()

            else:
                # otherwise, clear the spike markers
                self.clear_spike_markers()

        else:
            # otherwise, clear the spike markers
            self.clear_spike_markers()

        # resets the previous frame indices
        self.i_frm_pr = i_frm_nw

    def reset_spike_index_limits(self, i_frm_nw, i_start=0, i_finish=None):

        # sets the spikes (based on start/finish indices)
        if i_finish is None:
            i_spike_lim = self.i_spike[i_start:]
        else:
            i_spike_lim = self.i_spike[i_start:i_finish]

        # determine first spike greater than the lower limit
        i_spk_lo = np.searchsorted(i_spike_lim, i_frm_nw[0], 'right')
        if self.i_spike[i_spk_lo] < i_frm_nw[1]:
            # if this value is less than the upper limit, then determine the spikes within the window
            reset_win = True
            self.i_spk1 = np.searchsorted(i_spike_lim[i_spk_lo:], i_frm_nw[1], 'left') + (i_spk_lo + i_start)
        else:
            # otherwise, flag that there are no spikes in the window
            self.i_spk1 = None

        # sets the lower spike limit
        self.i_spk0 = i_spk_lo + i_start

    def reset_index_lower_limit(self, i_frm_win):

        # resets the lower spike limit
        if i_frm_win[0] > self.i_frm_pr[0]:
            # window has moved to the right
            i_spike_ofs = self.i_spk0
            i_spk_chk = self.i_spike[self.i_spk0:]
            self.i_spk0 = np.searchsorted(i_spk_chk, i_frm_win[0], 'right') + i_spike_ofs

        elif i_frm_win[0] < self.i_frm_pr[0]:
            # window has moved to the left
            i_spk_chk = self.i_spike[:self.i_spk0]
            self.i_spk0 = np.searchsorted(i_spk_chk, i_frm_win[0], 'right')

    def reset_index_upper_limit(self, i_frm_win):

        if (self.i_spike[self.i_spk0] > i_frm_win[1]):
            # no spikes in window (first spike index > upper limit)
            self.i_spk1 = None

        else:
            # otherwise, reset the upper limit
            i_spk_chk = self.i_spike[self.i_spk0:]
            if i_frm_win[1] > i_spk_chk[-1]:
                self.i_spk1 = len(i_spk_chk) + self.i_spk0 - 1
            else:
                self.i_spk1 = np.searchsorted(i_spk_chk, i_frm_win[1], 'left') + self.i_spk0

            # check if the last spike is within the limits
            if self.i_spike[self.i_spk1] < i_frm_win[0]:
                self.i_spk1 = None

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
        self.i_run = self.main_obj.main_obj.session_obj.get_current_run_index()
        self.i_shank = self.main_obj.main_obj.session_obj.get_shank_index()

        # other class widgets
        # self.unit_label = cw.QLabelText(None, lbl_str="Selected Unit:", text_str='N/A',
        #                                 font_lbl=cw.font_lbl, font_txt=cw.font_lbl)
        self.table = cw.QInfoTable(None, self.type, False)
        self.edit_spike = self.findChild(cw.QLabelEdit, name='i_spike')

        # other class fields
        self.plot_view = None
        self.is_updating = False
        self.is_marker_init = False
        self.markers_cleared = False

        # other class fields
        self.h_spike = {}
        self.i_unit_sp = {}
        self.i_frm_pr = None

        self.in_win = None
        self.i_ch_sel = None
        self.i_spike_win = None
        self.spk_cluster_win = None
        self.spk_channel_win = None
        self.s_freq = self.main_obj.main_obj.session_obj.session_props.s_freq

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

        # sets the table header properties
        table_hdr = self.table.horizontalHeader()
        table_hdr.setFont(self.table_hdr_font)
        table_hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table_hdr.setStretchLastSection(True)

        # sets the other widget properties
        self.edit_spike.set_enabled(False)

        # table function callback function
        self.table.cellChanged.connect(self.table_cell_changed)
        self.table.blockSignals(True)

    def setup_prop_fields(self):

        # sets up the subgroup fields
        p_tmp = {
            'i_spike': self.create_para_field('Unit Spike Index', 'edit', 1),
            'm_size': self.create_para_field('Spike Marker Size', 'edit', 15),
        }

        # updates the class field
        self.p_info = {'name': 'Metrics', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_unit_spike_info(self):

        # exit if already setup
        if self.i_spike_info[self.i_run, self.i_shank] is not None:
            return

        # field retrieval
        n_spike = np.array(self.data['Count'])
        i_spike = self.get_field('i_spike')[:, 0]
        spk_clust = self.get_field('spk_cluster')[:, 0]

        # sets up the spike info field
        self.i_spike_info[self.i_run, self.i_shank] = {
            'i_ofs': np.append([0], np.cumsum(n_spike[:-1])),
            'i_spike': i_spike[np.lexsort((i_spike, spk_clust))],
        }

    def setup_spike_table(self):

        # memory allocation
        self.n_unit = self.get_field('n_unit')
        self.n_unit_pp = self.main_obj.main_obj.main_obj.session_obj.post_data.n_unit_pp
        self.i_spike_info = np.empty(self.n_unit_pp.shape, dtype=object)

        # unit selection memory allocation
        self.is_filt = np.empty(self.n_unit_pp.shape, dtype=object)
        for i_pp, n_pp in enumerate(self.n_unit_pp.flat):
            self.is_filt[np.unravel_index(i_pp, self.is_filt.shape)] = np.zeros((n_pp, 1), dtype=bool)

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
        self.setup_unit_spike_info()

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
        self.table.blockSignals(False)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def edit_update(self, p_str):

        # if force updating, then exit the function
        if self.is_updating:
            return

        # field retrieval
        h_edit = self.findChild(cw.QLabelEdit,name=p_str)
        nw_val = h_edit.get_text()

        match p_str:
            case 'i_spike':
                # case is the spike index
                min_val, max_val = 1, 30

            case 'm_size':
                # case is the marker size
                min_val, max_val = 5, 30

        # determines if the new value is valid
        chk_val = cf.check_edit_num(nw_val, min_val=min_val, max_val=max_val, is_int=True)
        if chk_val[1] is None:
            # updates the parameter value
            setattr(self, p_str, int(chk_val[0]))

            # performs the parameter specific update
            match p_str:
                case 'i_spike':
                    # case is the spike index
                    pass

                case 'm_size':
                    # case is the marker size
                    self.reset_marker_size()

        else:
            # otherwise, reset the previous value
            h_edit.set_text('%g' % getattr(self, p_str))

    def table_cell_changed(self, i_row, i_col):

        if self.is_updating:
            return

        # field reset
        item_chk = self.table.item(i_row, i_col)
        i_unit = int(self.table.item(i_row, self.i_col_unit).text()) - 1
        self.is_filt[self.i_run, self.i_shank][i_unit] = (
            item_chk.checkState() == cf.chk_state[True])

        # updates the spike markers
        self.reset_spike_markers()

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
        self.i_run = self.main_obj.main_obj.session_obj.get_current_run_index()
        self.i_shank = self.main_obj.main_obj.session_obj.get_shank_index()
        probe_view = self.main_obj.main_obj.main_obj.plot_manager.get_plot_view('probe')

        # re-maps the channel indices to the probe map
        self.i_pk_ch = q_met_df['maxChannels'].astype(int)
        q_met_df['maxChannels'] = probe_view.sub_view.ch_map[self.i_shank][self.i_pk_ch - 1]

        return q_met_df

    def get_metric_table_values(self):

        # field retrieval
        unit_type = self.get_unit_type_labels().reshape(-1, 1)
        show_spike = self.is_filt[self.i_run, self.i_shank]
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




