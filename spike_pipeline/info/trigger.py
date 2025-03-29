# custom module imports
import spike_pipeline.common.common_widget as cw
from spike_pipeline.info.utils import InfoWidget
from spike_pipeline.common.common_widget import QWidget, QLabelCombo, font_lbl

# pyqt imports
from PyQt6.QtCore import pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------


class TriggerInfoTab(InfoWidget):
    # pyqtSignal signal functions
    run_change = pyqtSignal(QWidget)
    init_para = pyqtSignal(str, object)

    def __init__(self, t_str):
        super(TriggerInfoTab, self).__init__(t_str)

        # boolean class fields
        self.is_updating = False

        # adds the widget combo
        self.run_type = QLabelCombo(None, 'Session Run:', None, font_lbl=font_lbl)
        self.tab_layout.addWidget(self.run_type)

        # creates the table widget
        self.create_table_widget()

    def init_para_tab(self):

        # sets up the subgroup fields
        ch_fld = {

        }

        # updates the class field
        return {'name': 'Trigger', 'type': 'v_panel', 'ch_fld': ch_fld}

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

        # resets the update flag
        self.is_updating = False

    def combo_run_change(self, h_combo):

        # if manually updating, then exit
        if not self.is_updating:
            self.run_change.emit(self)

