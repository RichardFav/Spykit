# spikewrap/spikeinterface module imports
import spike_pipeline.common.common_widget as cw
from spike_pipeline.info.unit import UnitInfoTab
from spike_pipeline.info.channel import ChannelInfoTab
from spike_pipeline.info.preprocess import PreprocessInfoTab

# list of all plot types
info_types = {
    'unit': UnitInfoTab,                    # unit information tab
    'channel': ChannelInfoTab,              # channel information tab
    'preprocess': PreprocessInfoTab,        # preprocess information tab
}

# list of plot title names
info_names = {
    'unit': 'Unit',
    'channel': 'Channel',
    'preprocess': 'Preprocessing',
}
