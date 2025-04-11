# module import
import numpy as np

#
import spike_pipeline.common.common_func as cf

# custom module imports
from spike_pipeline.info.utils import InfoWidget
from spike_pipeline.common.common_widget import QWidget, QLabelCombo, QLabelCheckCombo, font_lbl

# pyqt imports
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------


class ChannelInfoTab(InfoWidget):
    # pyqtSignal signal functions
    run_change = pyqtSignal(QWidget)
    data_change = pyqtSignal(QWidget)
    status_change = pyqtSignal(QWidget, object)
    set_update_flag = pyqtSignal(bool)
    mouse_move = pyqtSignal(object)
    mouse_enter = pyqtSignal(object)
    mouse_leave = pyqtSignal(object)
    force_reset_flags = pyqtSignal(object)

    row_col = {
        'good': cf.get_colour_value('g', 128),
        'dead': cf.get_colour_value('r', 128),
        'noise': cf.get_colour_value('y', 128),
        'out': cf.get_colour_value('b', 128),
        'rejected': cf.get_colour_value('dg', 128),
        'removed': cf.get_colour_value('k', 128),
    }

    # table cell item flags
    item_flag = {
        True: Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable,
        False: Qt.ItemFlag.ItemIsEnabled,
    }

    # other parameters
    i_sel_col = 0
    i_keep_col = 1
    i_status_col = 2
    i_channel_col = 3

    def __init__(self, t_str):
        super(ChannelInfoTab, self).__init__(t_str)

        # field initialisations
        self.data_flds = None
        self.table_move_fcn = None
        self.table_leave_fcn = None
        self.get_avail_channel_fcn = None

        # boolean class fields
        self.is_filt = None
        self.is_updating = False

        # adds the plot data type combobox
        self.data_type = QLabelCombo(None, 'Plot Data Type:', None, font_lbl=font_lbl)
        self.run_type = QLabelCombo(None, 'Session Run:', None, font_lbl=font_lbl)
        self.status_filter = QLabelCheckCombo(None, lbl="Status Filter", font=font_lbl)

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # adds the widgets to the main widget
        self.tab_layout.addWidget(self.data_type)
        self.tab_layout.addWidget(self.run_type)
        self.tab_layout.addWidget(self.status_filter)

        # sets the data type combobox properties
        self.data_type.setContentsMargins(0, self.x_gap, 0, 0)

        # adds status filter check combobox
        self.status_filter.item_clicked.connect(self.check_filter_item)
        self.status_filter.setEnabled(False)

        # creates the table widget
        self.create_table_widget()
        self.get_filtered_items()

        # resets the table mouse move event
        self.table.setMouseTracking(True)
        self.table_leave_fcn = self.table.leaveEvent
        self.table_move_fcn = self.table.mouseMoveEvent

        # resets the event functions
        self.table.leaveEvent = self.table_mouse_leave
        self.table.mouseMoveEvent = self.table_mouse_move

    def table_mouse_move(self, evnt):

        self.table_move_fcn(evnt)
        self.mouse_move.emit(evnt)

    def table_mouse_leave(self, evnt):

        self.table_leave_fcn(evnt)
        self.mouse_leave.emit(evnt)

    def reset_combobox_fields(self, cb_type, cb_list):

        # flag that the combobox is being updated manually
        self.is_updating = True

        # retrieves the combo box
        combo = getattr(self, '{0}_type'.format(cb_type))

        # clears and resets the combobox fields
        combo.clear()
        for cb in cb_list:
            combo.addItem(cb)

        # resets the combobox fields
        combo.set_enabled(len(cb_list) > 1)

        match cb_type:
            case 'run':
                combo.connect(self.combo_run_change)

            case 'data':
                combo.connect(self.combo_data_change)

        # resets the update flag
        self.is_updating = False

    def combo_data_change(self, h_combo):

        # if manually updating, then exit
        if not self.is_updating:
            self.data_change.emit(self)

    def combo_run_change(self, h_combo):

        # if manually updating, then exit
        if not self.is_updating:
            self.run_change.emit(self)

    def combo_status_change(self, h_combo):

        # if manually updating, then exit
        if not self.is_updating:
            self.status_change.emit(self)

    def reset_data_types(self, d_names, d_flds):

        # indicate that
        self.is_updating = True

        # resets the
        self.data_type.obj_cbox.clear()
        self.data_type.obj_cbox.addItems(d_names)
        self.data_type.set_enabled(len(d_names) > 1)

        # updates the data field
        self.data_flds = d_flds

        # resets the update flag
        self.is_updating = False

    def update_channel_status(self, ch_status, is_keep):

        # initialisations
        self.is_updating = True
        self.set_update_flag.emit(True)
        ch_avail = self.get_avail_channel_fcn()

        # updates the table with the new information
        ch_list, i_rmv = [], []
        for i_row, (ch_id, c_stat) in enumerate(ch_status.items()):
            item = self.table.item(i_row, self.i_status_col)

            if ch_id in ch_avail:
                # case is the channel is available
                self.set_table_row_colour(i_row, c_stat if is_keep[i_row] else 'rejected')
                self.set_table_row_enabled(i_row, True)
                item.setText(c_stat)

                if c_stat not in ch_list:
                    ch_list.append(c_stat)

            else:
                # case is the item has been removed
                i_rmv.append(i_row)
                self.set_table_row_colour(i_row, 'removed')
                self.set_table_row_enabled(i_row, False)
                item.setText('removed')

        if len(i_rmv):
            self.force_reset_flags.emit(i_rmv)

        # resets the status filter
        self.status_filter.clear()
        self.status_filter.setEnabled(True)
        for s_filt in ch_list:
            self.status_filter.add_item(s_filt, True)

        # resets the update flag
        self.is_updating = False
        self.set_update_flag.emit(False)

    def get_filtered_items(self):

        # determines the selected filter items
        sel_filt = self.status_filter.get_selected_items()

        # determines which items meet the filter selection
        self.is_filt = np.zeros(self.table.rowCount(), dtype=bool)
        for i_row in range(self.table.rowCount()):
            item = self.table.item(i_row, self.i_status_col)
            self.is_filt[i_row] = item.text() in sel_filt

    def check_filter_item(self):

        self.get_filtered_items()

        for i_row in range(self.table.rowCount()):
            self.table.setRowHidden(i_row, not self.is_filt[i_row])

        self.status_change.emit(self, self.is_filt)
        self.data_change.emit(self)

    def set_table_row_colour(self, i_row, c_stat):

        for i_col in range(self.table.columnCount()):
            self.table.item(i_row, i_col).setBackground(self.row_col[c_stat])

    def set_table_row_enabled(self, i_row, state):

        # item retrieval
        item_sel = self.table.item(i_row, self.i_sel_col)
        item_keep = self.table.item(i_row, self.i_keep_col)

        # updates the item flags
        item_sel.setFlags(self.item_flag[state])
        item_keep.setFlags(self.item_flag[state])

        if not state:
            item_sel.setCheckState(cf.chk_state[False])
            item_keep.setCheckState(cf.chk_state[False])

    def get_table_device_id(self, i_row_sel):

        i_row_sel = np.min([self.table.rowCount() - 1, i_row_sel])
        return int(self.table.item(i_row_sel, self.i_channel_col).text())

    def keep_channel_reset(self, is_keep):

        # initialisations
        self.is_updating = True
        self.set_update_flag.emit(True)

        for i_row, state in enumerate(is_keep):
            h_cell = self.table.item(i_row, self.i_keep_col)
            h_cell.setCheckState(cf.chk_state[state])

        # initialisations
        self.is_updating = False
        self.set_update_flag.emit(False)
