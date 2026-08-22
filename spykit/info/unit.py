# module import
import time
import numpy as np
import pandas as pd
from copy import deepcopy

# spykit module imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.info.utils import InfoWidget
from spykit.common.common_widget import QLabelCombo, QLabelCheckCombo, QLabelText, font_lbl

# pyqt imports
from PyQt6.QtWidgets import QWidget, QGridLayout, QAbstractItemView
from PyQt6.QtCore import (Qt, QSize, pyqtSignal)

# ----------------------------------------------------------------------------------------------------------------------

bc_var_map = cw.hist_map | {
    'clusterID': 'Cluster ID#',
    'ksTest_pValue': 'KS-Test P-Value',
    'mainPeak_after_width': 'Post-Main Peak Width',
    'mainPeak_before_width': 'Pre-Main Peak Width',
    'mainTrough_width': 'Main Trough Width',
    'maxChannels': 'Max Channel',
    # 'phy_clusterID': 'Phy Cluster ID#',
    'troughToPeak2Ratio': 'Trough/2nd Peak Ratio',
}

int_col = [
    'maxChannels',
    'phy_clusterID',
    'clusterID',
    'nPeaks',
    'nTroughs',
    'nSpikes',
]

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitInfoTab:
"""


class UnitInfoTab(InfoWidget):
    # pyqtSignal signal functions
    run_change = pyqtSignal(QWidget)
    data_change = pyqtSignal(QWidget)
    shank_change = pyqtSignal(QWidget)
    status_change = pyqtSignal(QWidget, object)
    set_update_flag = pyqtSignal(bool)
    mouse_move = pyqtSignal(object)
    mouse_leave = pyqtSignal(object)

    # table cell item flags
    item_flag = {
        True: Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable,
        False: Qt.ItemFlag.ItemIsEnabled,
    }

    # object dimensions
    i_col_unit = 0
    i_col_type = 1
    but_height = 16

    def __init__(self, sp_main, t_str):
        super(UnitInfoTab, self).__init__(sp_main, t_str)

        # main sub-class fields
        self.sp_main = sp_main
        self.session_obj = self.sp_main.session_obj

        # field initialisations
        self.i_pk_ch = None
        self.df_unit = None
        self.data_flds = None
        self.unit_lbl = None
        self.i_unit_sel = None
        self.unit_spike_tab = None

        # table properties/event functions
        self.table_delegate = None
        self.table_move_fcn = None
        self.table_leave_fcn = None
        self.table_click_fcn = None

        # boolean class fields
        self.is_filt = None
        self.is_updating = False

        # plot option widgets
        self.opt_widget = QWidget()
        self.opt_layout = QGridLayout()
        self.run_type = QLabelCombo(None, 'Session Run:', None, font_lbl=font_lbl)
        self.shank_type = QLabelCombo(None, "Recording Shank:", None, font_lbl=font_lbl)
        self.status_filter = QLabelCheckCombo(None, lbl="Unit Type Filter:", font=font_lbl)
        self.unit_label = QLabelText(None, lbl_str="Selected Unit:", text_str='N/A',
                                     font_lbl=font_lbl, font_txt=font_lbl)

        # initialises the other class fields
        self.init_option_fields()
        self.init_other_class_fields()

    # ---------------------------------------------------------------------------
    # Class Initialisation Functions
    # ---------------------------------------------------------------------------

    def init_option_fields(self):

        # adds the option widget to the tab layout
        self.tab_layout.addWidget(self.opt_widget)
        self.opt_widget.setLayout(self.opt_layout)
        self.opt_widget.setContentsMargins(0, 0, 0, 0)

        # adds the widgets to the layout widget
        self.opt_layout.addWidget(self.run_type.obj_lbl, 0, 0, 1, 1)
        self.opt_layout.addWidget(self.run_type.obj_cbox, 0, 1, 1, 1)
        self.opt_layout.addWidget(self.shank_type.obj_lbl, 1, 0, 1, 1)
        self.opt_layout.addWidget(self.shank_type.obj_cbox, 1, 1, 1, 1)
        self.opt_layout.addWidget(self.status_filter.h_lbl, 2, 0, 1, 1)
        self.opt_layout.addWidget(self.status_filter.h_combo, 2, 1, 1, 1)
        self.opt_layout.addWidget(self.unit_label.obj_lbl, 3, 0, 1, 1)
        self.opt_layout.addWidget(self.unit_label.obj_txt, 3, 1, 1, 1)

        # sets the option combobox layout properties
        self.opt_layout.setColumnStretch(0, 10)
        self.opt_layout.setColumnStretch(1, 20)
        self.opt_layout.setColumnStretch(2, 1)

        # connects the signal/slot functions
        self.run_type.connect(self.combo_run_change)
        self.shank_type.connect(self.combo_shank_change)

        # adds status filter check combobox
        self.status_filter.item_clicked.connect(self.check_filter_item)
        self.status_filter.setEnabled(False)

    def init_other_class_fields(self):

        # creates the table widget
        self.create_table_widget(False)
        self.opt_layout.addWidget(self.undock_obj, 0, 2, 1, 1, alignment=cw.align_flag['right'])

        # sets the table selection behaviour
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # resets the table mouse move event
        self.table.setMouseTracking(True)
        self.table_leave_fcn = self.table.leaveEvent
        self.table_move_fcn = self.table.mouseMoveEvent
        self.table.cellClicked.connect(self.table_cell_click)

        # resets the event functions
        self.table.leaveEvent = self.table_mouse_leave
        self.table.mouseMoveEvent = self.table_mouse_move

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_field(self, p_fld, i_fld=None):

        return self.session_obj.get_mem_map_field(p_fld, i_fld)

    def get_filtered_items(self):

        # initialisations
        ch_info = None
        unit_id = self.get_unit_indices()
        n_row = self.df_unit.shape[0]

        # determines the selected filtered items
        sel_filt0 = self.status_filter.get_selected_items()
        sel_filt = [' '.join(x.split()[:-1]) for x in sel_filt0]

        # determines which items meet the filter selection
        self.is_filt = np.zeros(n_row, dtype=bool)
        for i_row in range(n_row):
            item = self.table.item(i_row, self.i_col_type)
            self.is_filt[unit_id[i_row] - 1] = item.text() in sel_filt

        # resets the row highlight (based on filter selection - if selected)
        if self.i_unit_sel is not None:
            self.set_row_highlight(self.is_filt[self.i_unit_sel - 1], True)

    def get_unit_indices(self):

        # retrieves the unit ID's for each row
        unit_id = []
        for i in range(self.df_unit.shape[0]):
            item = self.table.item(i, self.i_col_unit)
            unit_id.append(int(item.text()))

        return np.array(unit_id)

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_field(self, p_fld, p_val, i_fld=None):

        return self.session_obj.set_mem_map_field(p_fld, p_val, i_fld)

    def set_table_row_colour(self, i_row, c_stat):

        row_colour = cw.get_unit_col(c_stat)
        for i_col in range(self.table.columnCount()):
            self.table.item(i_row, i_col).setBackground(row_colour)

    def set_combobox_props(self):

        # field retrieval
        is_per_shank = self.session_obj.is_per_shank(False)
        is_concat_run = self.session_obj.is_concat_run()
        run_list = ['Concatenated Run'] if is_concat_run else self.session_obj.session.get_run_names()

        # flag that the widgets are being manually updated
        self.is_updating = True
        self.run_type.blockSignals(True)
        self.shank_type.blockSignals(True)

        # sets the run type comobobox properties
        self.run_type.addItems(run_list, True)
        self.run_type.set_current_index(0)
        self.run_type.set_enabled((not is_concat_run) and (len(run_list) > 1))

        # sets the shank type comobobox properties
        self.shank_type.addItems(self.session_obj.get_shank_names(is_per_shank), True)
        self.shank_type.set_current_index(0)
        self.shank_type.set_enabled(is_per_shank)

        # resets the update flag
        self.is_updating = False
        self.run_type.blockSignals(False)
        self.shank_type.blockSignals(False)

    def set_table_rows(self):

        self.get_filtered_items()

        unit_id = self.get_unit_indices()
        for i_row in range(self.df_unit.shape[0]):
            self.table.setRowHidden(i_row, not self.is_filt[unit_id[i_row] - 1])

    def set_row_highlight(self, is_highlight_on, reset_lbl=False):

        # retrieves the row index corresponding the unit selection
        i_row_sel = np.where(self.get_unit_indices() == self.i_unit_sel)[0][0]

        if is_highlight_on:
            # row highlight is turned on
            self.set_table_row_colour(i_row_sel, 'selected')
            self.unit_label.set_label('Unit #{0}'.format(self.i_unit_sel))

        else:
            # row highlight is turned off
            c_stat = self.df_unit['Unit Type'].iloc[self.i_unit_sel - 1]
            self.set_table_row_colour(i_row_sel, c_stat.lower())

            if reset_lbl:
                self.unit_label.set_label('N/A')

    # ---------------------------------------------------------------------------
    # Mouse Event Functions
    # ---------------------------------------------------------------------------

    def table_mouse_move(self, evnt):

        self.table_move_fcn(evnt)
        self.mouse_move.emit(evnt)

    def table_mouse_leave(self, evnt):

        self.table_leave_fcn(evnt)
        self.mouse_leave.emit(evnt)
        self.table_delegate.force_close()

    def table_cell_click(self, i_row, i_col, update_spike_table=True):

        # removes any previous row highlights
        if self.i_unit_sel is not None:
            self.set_row_highlight(False)

        # force closes the combobox (if open)
        self.table_delegate.force_close()

        # resets the selected unit index
        unit_lbl = self.table.item(i_row, self.i_col_unit).text()
        self.i_unit_sel = int(unit_lbl)

        # sets the row highlight
        self.set_row_highlight(True)

        # resets the probe unit highlight marker
        self.reset_probe_roi_location(i_row)

        # updates the post-processing tabs
        post_tab = self.sp_main.prop_manager.get_prop_tab('postprocess')
        if post_tab is not None:
            # flag that manual updating is occuring
            self.is_updating = True

            # resets the editbox value
            for t_type in ['unithist', 'unitmet', 'waveform']:
                pp_sub_tab = post_tab.get_tab_view(t_type)
                h_edit_unit = pp_sub_tab.findChild(cw.QLineEdit, name='i_unit')
                h_edit_unit.setText('%g' % self.i_unit_sel)
                pp_sub_tab.set_para_value('i_unit', self.i_unit_sel)

            # resets the update flag
            self.is_updating = False

        # resets the spike trace property tab properties
        if update_spike_table:
            spike_tab = self.sp_main.prop_manager.get_prop_tab('tracespike')
            spike_tab.table_cell_clicked(i_row, update_unit_table=False)

    def reset_probe_roi_location(self, i_row=None):

        if self.i_unit_sel is None:
            return

        # channel position/index
        i_ch_unit = self.i_pk_ch[self.i_unit_sel - 1]
        ch_pos_unit = self.ch_pos[self.i_pk_ch[self.i_unit_sel - 1] - 1, :]

        # resets the probe roi position
        probe_view = self.sp_main.plot_manager.get_plot_view('probe')
        if probe_view is not None:
            type_lbl = self.table.item(i_row, self.i_col_type).text().lower()
            probe_view.reset_unit_roi_position(i_ch_unit, ch_pos_unit, type_lbl)

    # ---------------------------------------------------------------------------
    # Widget Event Functions
    # ---------------------------------------------------------------------------

    def check_filter_item(self, update_data=True):

        # retrieves the filtered items
        self.get_filtered_items()

        # resets the table view
        self.status_change.emit(self, self.is_filt)
        if update_data:
            self.data_change.emit(self)

    def combo_run_change(self, _):

        # if manually updating, then exit
        if not self.is_updating:
            self.run_change.emit(self)

    def combo_shank_change(self, _):

        # if manually updating, then exit
        if not self.is_updating:
            self.shank_change.emit(self)

    def combo_type_change(self, index, c_box):

        # field retrieval
        unit_type = c_box.currentText()
        i_row, i_col = index.row(), index.column()
        i_type_new = self.table_delegate.items.index(unit_type)

        # exit if there is no change in unit type
        i_type_prev = self.get_field('unit_type', i_row)[0]
        if i_type_prev == i_type_new:
            return

        # updates the unit type field
        self.set_field('unit_type', i_type_new, i_row)

        # updates the trace spikes/unit type tabs
        self.update_unit_type(unit_type, i_row, False)
        self.unit_spike_tab.update_unit_type(unit_type, i_row)

        # updates the plot view unit types
        self.sp_main.plot_manager.update_unit_type(unit_type, i_row)

        # remove me later
        pass

    # ---------------------------------------------------------------------------
    # Miscellaneous Methods
    # ---------------------------------------------------------------------------

    def remap_channel_indices(self, q_hdr, q_met):

        # field retrieval
        ch_pos0 = self.get_field('ch_pos')
        i_col_ch = np.where(q_hdr == 'maxChannels')[0][0]
        probe_view = self.sp_main.plot_manager.get_plot_view('probe')

        # re-maps the bombcell channel indices by height
        i_pk_ch0 = q_met[:, i_col_ch].astype(int)
        self.i_pk_ch, self.ch_pos = cf.map_bombcell_channels(i_pk_ch0, ch_pos0)

        # remaps the channel indices
        i_shank = self.session_obj.get_shank_index()
        if probe_view.sub_view.ch_map[i_shank] is None:
            probe_view.sub_view.remap_channel_indices(ch_pos0, i_shank)

        # re-maps the channel indices to the probe map over all shanks
        q_met[:, i_col_ch] = probe_view.sub_view.ch_map[i_shank][self.i_pk_ch - 1]
        # for ch_map in probe_view.sub_view.ch_map:
        #     ii = np.isin(self.i_pk_ch, ch_map)
        #     q_met[ii, i_col_ch] = self.i_pk_ch[ii]

        return q_met

    def setup_unit_table_data(self, return_fields=False):

        # sets up the unit type fields
        unit_lbl_nw = cw.get_unit_labels(self.get_field('splitGoodAndMua_NonSomatic'))

        # sets the column headers
        q_hdr = self.get_field('q_hdr')[0]
        is_ok = np.array([x in bc_var_map for x in q_hdr])
        c_hdr0 = np.array(['Unit Type'] + [bc_var_map[x] for x in q_hdr[is_ok]])

        # sets the unit metrics dataframe
        unit_type = self.get_unit_type_labels(unit_lbl_nw)
        q_met = self.remap_channel_indices(q_hdr, self.get_field('q_met')[:, is_ok])
        df_unit_0 = pd.DataFrame(np.hstack((unit_type.reshape(-1, 1), q_met)), columns=c_hdr0)
        df_unit_nw, c_hdr_nw = self.reorder_unit_dataframe(df_unit_0, c_hdr0)

        # sets the dtype of specific columns
        for i_ch in int_col:
            if i_ch in bc_var_map:
                p_fld = bc_var_map[i_ch]
                df_unit_nw[p_fld] = df_unit_nw[p_fld].astype(float).astype(int)

        if return_fields:
            # case is returning the new fields (will be updated elsewhere)
            return df_unit_nw, c_hdr_nw, unit_lbl_nw

        else:
            # otherwise, update the class fields
            self.df_unit, self.c_hdr, self.unit_lbl = df_unit_nw, c_hdr_nw, unit_lbl_nw

    def update_unit_type(self, unit_type, i_row, update_table=True):

        # updates the unit type within the table (if required)
        if update_table:
            self.is_updating = True
            self.table.item(i_row, self.i_col_type).setText(unit_type)
            self.is_updating = False

        # resets the class fields
        self.df_unit['Unit Type'][i_row] = unit_type

        # resets the class widget properties
        self.set_table_row_colour(i_row, unit_type)
        self.reset_unit_status()

        # resets the table properties and filtered items
        self.set_table_rows()
        self.check_filter_item()

    def reset_unit_status(self):

        # field retrieval
        unit_type = self.get_field('unit_type')

        # initialisations
        self.is_updating = True
        self.status_filter.blockSignals(True)

        # resets the status filter
        for i_filt, s_filt in enumerate(self.unit_lbl):
            n_unit = sum(unit_type == i_filt)[0]
            unit_lbl_filt = f"{s_filt} ({n_unit})"
            self.status_filter.reset_item(i_filt, unit_lbl_filt)

        # resets the update flag
        self.is_updating = False
        self.status_filter.blockSignals(False)

    def update_unit_status(self):

        # field retrieval
        unit_type = self.get_field('unit_type')

        # initialisations
        self.is_updating = True
        self.set_update_flag.emit(True)
        self.status_filter.blockSignals(True)

        # resets the status filter
        self.status_filter.clear()
        self.status_filter.setEnabled(True)
        for i_filt, s_filt in enumerate(self.unit_lbl):
            n_unit = sum(unit_type == i_filt)[0]
            unit_lbl_filt = f"{s_filt} ({n_unit})"
            self.status_filter.add_item(unit_lbl_filt, True)

        # resets the update flag
        self.is_updating = False
        self.set_update_flag.emit(False)
        self.status_filter.blockSignals(False)

    def get_unit_type_labels(self, unit_lbl_nw=None):

        if unit_lbl_nw is None:
            unit_lbl_nw = self.unit_lbl

        return np.array([unit_lbl_nw[x[0]] for x in self.get_field('unit_type')])

    def reset_selected_cell(self, i_row):

        # return if manually updating
        if self.is_updating:
            return

        elif self.is_filt is None:
            self.get_filtered_items()

        # field retrieval
        item_sel = self.table.selectedItems()
        i_col = item_sel[0].column() if len(item_sel) else 0

        # force runs the cell click callback
        self.table_cell_click(i_row, i_col)
        self.table.verticalScrollBar().setValue(i_row - np.sum(~self.is_filt[:i_row]))

    def reorder_unit_dataframe(self, df_unit_0, c_hdr0):

        # sets the fixed column header array
        c_hdr_nw = ['Cluster ID#', 'Unit Type', 'Max Channel',
                    'Spike Count', 'Peak Count', 'Trough Count']
        c_hdr = c_hdr_nw + list(set(c_hdr0) - set(c_hdr_nw))

        # re-orders the dataframe
        return df_unit_0.reindex(columns=c_hdr), c_hdr