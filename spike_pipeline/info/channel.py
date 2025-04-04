# module import
import numpy as np

#
import spike_pipeline.common.common_func as cf

# custom module imports
from spike_pipeline.info.utils import InfoWidget
from spike_pipeline.common.common_widget import QWidget, QLabelCombo, QLabelCheckCombo, font_lbl

# pyqt imports
from PyQt6.QtCore import pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------


class ChannelInfoTab(InfoWidget):
    # pyqtSignal signal functions
    run_change = pyqtSignal(QWidget)
    data_change = pyqtSignal(QWidget)
    status_change = pyqtSignal(QWidget, object)
    set_update_flag = pyqtSignal(bool)

    row_col = {
        'good': cf.get_colour_value('g', 128),
        'dead': cf.get_colour_value('r', 128),
        'noise': cf.get_colour_value('dg', 128),
        'out': cf.get_colour_value('y', 128),
    }

    # other parameters
    i_status_col = 2

    def __init__(self, t_str):
        super(ChannelInfoTab, self).__init__(t_str)

        # field initialisations
        self.data_flds = None

        # boolean class fields
        self.is_filt = None
        self.is_updating = False

        # adds the plot data type combobox
        self.data_type = QLabelCombo(None, 'Plot Data Type:', None, font_lbl=font_lbl)
        self.data_type.setContentsMargins(0, self.x_gap, 0, 0)
        self.tab_layout.addWidget(self.data_type)

        # adds the session run type combobox
        self.run_type = QLabelCombo(None, 'Session Run:', None, font_lbl=font_lbl)
        self.tab_layout.addWidget(self.run_type)

        # adds status filter check combobox
        self.status_filter = QLabelCheckCombo(None, lbl="Status Filter", font=font_lbl)
        self.status_filter.item_clicked.connect(self.check_filter_item)
        self.status_filter.setEnabled(False)
        self.tab_layout.addWidget(self.status_filter)

        # creates the table widget
        self.create_table_widget()
        self.get_filtered_items()

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

    def update_channel_status(self, ch_status):

        # initialisations
        self.is_updating = True
        self.set_update_flag.emit(True)

        # updates the table with the new information
        for i_row, c_stat in enumerate(ch_status):
            item = self.table.item(i_row, self.i_status_col)
            self.set_table_row_colour(i_row, c_stat)
            item.setText(c_stat)

        # resets the status filter
        self.status_filter.clear()
        self.status_filter.setEnabled(True)
        for s_filt in np.unique(ch_status):
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
            item = self.table.item(i_row, 1)
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
