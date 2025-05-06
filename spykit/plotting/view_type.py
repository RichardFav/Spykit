# module import
import os

# spikewrap/spikeinterface module imports
import spykit.common.common_widget as cw
from spykit.plotting.trace import TracePlot
from spykit.plotting.probe import ProbePlot
from spykit.plotting.trigger import TriggerPlot

# list of all plot types
plot_types = {
    'trace': TracePlot,                 # trace plot type
    'probe': ProbePlot,                 # probe plot type
    'trigger': TriggerPlot,             # sync plot type
}

# list of plot title names
plot_names = {
    'trace': 'Trace View',
    'probe': 'Probe View',
    'trigger': 'Trigger View',
}
