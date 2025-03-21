# custom module imports
import spike_pipeline.common.common_widget as cw
from spike_pipeline.info.common import InfoTab

# ----------------------------------------------------------------------------------------------------------------------


class TriggerInfoTab(InfoTab):
    def __init__(self, t_str):
        super(TriggerInfoTab, self).__init__(t_str)

        # creates the table widget
        self.create_table_widget()