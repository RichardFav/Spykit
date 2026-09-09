# spikewrap/spikeinterface module imports
import spykit.common.common_widget as cw
from spykit.info.unit import UnitInfoTab
from spykit.info.channel import ChannelInfoTab
from spykit.info.status import StatusInfoTab

# list of all plot types
info_types = {
    'channel': ChannelInfoTab,              # channel information tab
    'status': StatusInfoTab,                # status calculation information tab
    'unit': UnitInfoTab,                    # unit information tab
}

# list of plot title names
info_names = {
    'channel': 'Channel',
    'status': 'Status',
    'unit': 'Unit',
}
