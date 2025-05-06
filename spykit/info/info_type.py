# spikewrap/spikeinterface module imports
import spykit.common.common_widget as cw
from spykit.info.unit import UnitInfoTab
from spykit.info.channel import ChannelInfoTab
from spykit.info.preprocess import PreprocessInfoTab
from spykit.info.status import StatusInfoTab

# list of all plot types
info_types = {
    'unit': UnitInfoTab,                    # unit information tab
    'channel': ChannelInfoTab,              # channel information tab
    'preprocess': PreprocessInfoTab,        # preprocess information tab
    'status': StatusInfoTab,                # status calculation information tab
}

# list of plot title names
info_names = {
    'unit': 'Unit',
    'channel': 'Channel',
    'preprocess': 'Preprocessing',
    'status': 'Status',
}
