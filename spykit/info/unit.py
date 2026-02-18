# module import
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
    'mainPeak_before_width': 'Pre-Meain Peak Width',
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


class UnitInfoTab(InfoWidget):
    # pyqtSignal signal functions
    data_change = pyqtSignal(QWidget)
    status_change = pyqtSignal(QWidget, object)
    set_update_flag = pyqtSignal(bool)
    mouse_move = pyqtSignal(object)
    mouse_leave = pyqtSignal(object)

    row_col = {
        'noise': cf.get_colour_value('r', 128),
        'good': cf.get_colour_value('g', 128),
        'somatic good': cf.get_colour_value('g', 128),
        'mua': cf.get_colour_value('c', 128),
        'somatic mua': cf.get_colour_value('c', 128),
        'non-somatic': cf.get_colour_value('y', 128),
        'non-somatic good': cf.get_colour_value('y', 128),
        'non-somatic mua': cf.get_colour_value('m', 128),
        'selected': cf.get_colour_value([217, 255, 251], 128),
    }

    # table cell item flags
    item_flag = {
        True: Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable,
        False: Qt.ItemFlag.ItemIsEnabled,
    }

    # object dimensions
    but_height = 16
    i_col_unit = 2

    def __init__(self, t_str, main_obj):
        super(UnitInfoTab, self).__init__(t_str, main_obj)

        # sets the input arguments
        self.main_obj = main_obj

        # field initialisations
        self.df_unit = None
        self.data_flds = None
        self.i_unit_sel = None
        self.table_move_fcn = None
        self.table_leave_fcn = None
        self.table_click_fcn = None

        # boolean class fields
        self.is_filt = None
        self.is_updating = False

        # plot option widgets
        self.opt_widget = QWidget()
        self.opt_layout = QGridLayout()
        self.status_filter = QLabelCheckCombo(None, lbl="Filter Status:", font=font_lbl)
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
        self.opt_layout.addWidget(self.status_filter.h_lbl, 0, 0, 1, 1)
        self.opt_layout.addWidget(self.status_filter.h_combo, 0, 1, 1, 1)
        self.opt_layout.addWidget(self.unit_label.obj_lbl, 1, 0, 1, 1)
        self.opt_layout.addWidget(self.unit_label.obj_txt, 1, 1, 1, 1)

        # sets the option combobox layout properties
        self.opt_layout.setColumnStretch(0, 10)
        self.opt_layout.setColumnStretch(1, 20)
        self.opt_layout.setColumnStretch(2, 1)

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
    # Getter Functions
    # ---------------------------------------------------------------------------

    def get_filtered_items(self):

        # initialisations
        ch_info = None
        i_shank_sel = None
        unit_id = self.get_unit_indices()
        n_row = deepcopy(self.table.rowCount())

        # determines which items meet the filter selection
        sel_filt = self.status_filter.get_selected_items()
        self.is_filt = np.zeros(n_row, dtype=bool)
        for i_row in range(n_row):
            item = self.table.item(i_row, 0)
            self.is_filt[unit_id[i_row] - 1] = item.text() in sel_filt

        # resets the row highlight (based on filter selection - if selected)
        if self.i_unit_sel is not None:
            self.reset_row_highlight(self.is_filt[self.i_unit_sel - 1], True)

    def get_field(self, p_fld):

        return self.main_obj.session_obj.get_mem_map_field(p_fld)

    # ---------------------------------------------------------------------------
    # Setter Functions
    # ---------------------------------------------------------------------------

    def set_table_row_colour(self, i_row, c_stat):

        for i_col in range(self.table.columnCount()):
            self.table.item(i_row, i_col).setBackground(self.row_col[c_stat])

    def reset_table_rows(self):

        self.get_filtered_items()

        unit_id = self.get_unit_indices()
        for i_row in range(self.table.rowCount()):
            self.table.setRowHidden(i_row, not self.is_filt[unit_id[i_row] - 1])

    def reset_row_highlight(self, is_highlight_on, reset_lbl=False):

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

    def get_unit_indices(self):

        # retrieves the unit ID's for each row
        unit_id = []
        for i in range(self.table.rowCount()):
            item = self.table.item(i, self.i_col_unit)
            unit_id.append(int(item.text()))

        return np.array(unit_id)

    # ---------------------------------------------------------------------------
    # Mouse Event Functions
    # ---------------------------------------------------------------------------

    def table_mouse_move(self, evnt):

        self.table_move_fcn(evnt)
        self.mouse_move.emit(evnt)

    def table_mouse_leave(self, evnt):

        self.table_leave_fcn(evnt)
        self.mouse_leave.emit(evnt)

    def table_cell_click(self, i_row, i_col):

        # removes any previous row highlights
        if self.i_unit_sel is not None:
            self.reset_row_highlight(False)

        # sets the row highlight
        unit_lbl = self.table.item(i_row, self.i_col_unit).text()
        self.i_unit_sel = int(unit_lbl)

        # resets the probe unit highlight marker
        self.reset_row_highlight(True)

        # updates the other fields
        a = 1

    # ---------------------------------------------------------------------------
    # Widget Event Functions
    # ---------------------------------------------------------------------------

    def check_filter_item(self):

        # retrieves the filtered items
        self.get_filtered_items()

        # resets the table view
        self.status_change.emit(self, self.is_filt)
        self.data_change.emit(self)

    # ---------------------------------------------------------------------------
    # Miscellaneous Methods
    # ---------------------------------------------------------------------------

    def setup_unit_table(self):

        # sets up the unit type fields
        if self.get_field('splitGoodAndMua_NonSomatic'):
            self.unit_lbl = ['Noise', 'Somatic Good', 'Somatic MUA', 'Non-somatic Good', 'Non-somatic MUA']
        else:
            self.unit_lbl = ['Noise', 'Good', 'MUA', 'Non-Somatic']

        # sets the column headers
        q_hdr = self.main_obj.session_obj.get_mem_map_field('q_hdr')[0]
        is_ok = np.array([x in bc_var_map for x in q_hdr])
        c_hdr = np.array(['Unit Type'] + [bc_var_map[x] for x in q_hdr[is_ok]])

        # sets the unit metrics dataframe
        unit_type = np.array([self.unit_lbl[x[0]] for x in self.get_field('unit_type')])
        q_met = self.main_obj.session_obj.get_mem_map_field('q_met')[:, is_ok]
        self.df_unit = pd.DataFrame(np.hstack((unit_type.reshape(-1, 1), q_met)), columns=c_hdr)

        # sets the dtype of specific columns
        for i_ch in int_col:
            if i_ch in bc_var_map:
                p_fld = bc_var_map[i_ch]
                self.df_unit[p_fld] = self.df_unit[p_fld].astype(float).astype(int)

        # sets the table data/row colours
        self.main_obj.info_manager.setup_info_table(self.df_unit, 'unit', c_hdr)
        for i_row, c_stat in enumerate(self.df_unit['Unit Type']):
            self.set_table_row_colour(i_row, c_stat.lower())

    def update_unit_status(self):

        # initialisations
        self.is_updating = True
        self.set_update_flag.emit(True)

        # resets the status filter
        self.status_filter.clear()
        self.status_filter.setEnabled(True)
        for s_filt in self.unit_lbl:
            self.status_filter.add_item(s_filt, True)

        # resets the update flag
        self.is_updating = False
        self.set_update_flag.emit(False)
