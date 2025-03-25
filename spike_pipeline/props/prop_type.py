# module import
import os

# spikewrap/spikeinterface module imports
from spike_pipeline.props.trace import TraceProps
from spike_pipeline.props.trigger import TriggerProps
from spike_pipeline.props.config import ConfigProps
from spike_pipeline.props.general import GeneralProps

# list of all plot types
prop_types = {
    'trace': TraceProps,                # trace property type
    'trigger': TriggerProps,            # sync property type
    'config': ConfigProps,              # region configuration property type
    'general': GeneralProps,            # general property type
}

# list of plot title names
prop_names = {
    'trace': 'Trace',
    'trigger': 'Trigger',
    'config': 'Configuration',
    'general': 'General',
}