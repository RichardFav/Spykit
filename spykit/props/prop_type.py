# module import
import os

# spikewrap/spikeinterface module imports
from spykit.props.trace import TraceProps
from spykit.props.traceprops import TraceViewProps
from spykit.props.tracespikes import TraceSpikeProps
from spykit.props.trigger import TriggerProps
from spykit.props.config import ConfigProps
from spykit.props.general import GeneralProps
from spykit.props.postprocess import PostProcProps
from spykit.props.unitmetrics import UnitMetricProps
from spykit.props.unithist import UnitHistProps
from spykit.props.waveform import WaveFormProps
from spykit.props.upset import UpSetProps

# list of all plot types
prop_types = {
    'trace': TraceProps,                    # trace property type
    'traceview': TraceViewProps,            # trace view property type
    'tracespike': TraceSpikeProps,            # trace spike property type
    'trigger': TriggerProps,                # sync property type
    'config': ConfigProps,                  # region configuration property type
    'general': GeneralProps,                # general property type
    'postprocess': PostProcProps,           # post-processing property type
    'unitmet': UnitMetricProps,             # unit metric property type
    'unithist': UnitHistProps,              # unit histogram property type
    'waveform': WaveFormProps,              # waveform property type
    'upset': UpSetProps,                    # unit upset property type
}

# list of property tab names
prop_names = {
    'trace': 'Trace',
    'traceview': 'Properties',
    'tracespike': 'Unit Spikes',
    'trigger': 'Trigger',
    'config': 'Configuration',
    'general': 'General',
    'postprocess': 'Postprocessing',
    'unitmet': 'Metrics',
    'unithist': 'Histograms',
    'waveform': 'Waveforms',
    'upset': 'UpSet',
}
