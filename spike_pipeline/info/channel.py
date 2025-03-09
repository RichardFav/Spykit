# custom module imports
import spike_pipeline.common.common_widget as cw
from spike_pipeline.info.common import InfoTab

# ----------------------------------------------------------------------------------------------------------------------


class ChannelInfoTab(InfoTab):
    def __init__(self, t_str):
        super(ChannelInfoTab, self).__init__(t_str)

        # adds the widget combo
        self.data_type = cw.QLabelCombo(None, 'Plot Data Type:', None, font_lbl=cw.font_lbl)
        self.tab_layout.addWidget(self.data_type)

        # adds the widget combo
        self.run_type = cw.QLabelCombo(None, 'Session Run:', None, font_lbl=cw.font_lbl)
        self.tab_layout.addWidget(self.run_type)

        # creates the table widget
        self.create_table_widget()

    def reset_combobox_fields(self, cb_type, cb_list):

        # retrieves the combo box
        combo = getattr(self, '{0}_type'.format(cb_type))

        # clears and resets the combobox fields
        combo.clear()
        for cb in cb_list:
            combo.addItem(cb)

        # resets the combobox fields
        combo.set_enabled(len(cb_list) > 1)
