# custom module imports
from spike_pipeline.info.common import InfoTab
from spike_pipeline.common.common_widget import QWidget, QLabelCombo, font_lbl

# pyqt imports
from PyQt6.QtCore import pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------


class ChannelInfoTab(InfoTab):
    # pyqtSignal signal functions
    run_change = pyqtSignal(QWidget)
    data_change = pyqtSignal(QWidget)

    def __init__(self, t_str):
        super(ChannelInfoTab, self).__init__(t_str)

        # boolean class fields
        self.is_updating = False

        # adds the widget combo
        self.data_type = QLabelCombo(None, 'Plot Data Type:', None, font_lbl=font_lbl)
        self.tab_layout.addWidget(self.data_type)

        # adds the widget combo
        self.run_type = QLabelCombo(None, 'Session Run:', None, font_lbl=font_lbl)
        self.tab_layout.addWidget(self.run_type)

        # creates the table widget
        self.create_table_widget()

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
