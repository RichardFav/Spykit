# custom module imports
import spike_pipeline.common.common_widget as cw
from spike_pipeline.info.utils import InfoWidget

# ----------------------------------------------------------------------------------------------------------------------


class UnitInfoTab(InfoWidget):
    def __init__(self, t_str, main_obj):
        super(UnitInfoTab, self).__init__(t_str, main_obj)

        # creates the table widget
        self.create_table_widget()
        