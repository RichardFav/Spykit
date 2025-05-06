# module import
import os

# spikewrap/spikeinterface module imports
from spykit.props.trace import TraceProps
from spykit.props.trigger import TriggerProps
from spykit.props.config import ConfigProps
from spykit.props.general import GeneralProps

# list of all plot types
prop_types = {
    'trace': TraceProps,                    # trace property type
    'trigger': TriggerProps,                # sync property type
    'config': ConfigProps,                  # region configuration property type
    'general': GeneralProps,                # general property type
}

# list of plot title names
prop_names = {
    'trace': 'Trace',
    'trigger': 'Trigger',
    'config': 'Configuration',
    'general': 'General',
}
