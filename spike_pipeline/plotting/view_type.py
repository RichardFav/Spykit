# module import
import os

# PyQt6 module imports
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# spikewrap/spikeinterface module imports
import spike_pipeline.common.common_widget as cw
from spike_pipeline.plotting.trace import TracePlot
from spike_pipeline.plotting.probe import ProbePlot
from spike_pipeline.plotting.trigger import TriggerPlot

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
