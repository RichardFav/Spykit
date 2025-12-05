# module import
import os

# spikewrap/spikeinterface module imports
import spykit.common.common_widget as cw
from spykit.plotting.trace import TracePlot
from spykit.plotting.probe import ProbePlot
from spykit.plotting.trigger import TriggerPlot
from spykit.plotting.unitmetrics import UnitMetricPlot
from spykit.plotting.unithist import UnitHistPlot
from spykit.plotting.waveform import WaveFormPlot
from spykit.plotting.upset import UpSetPlot

# list of all plot types
plot_types = {
    'trace': TracePlot,                 # trace plot type
    'probe': ProbePlot,                 # probe plot type
    'trigger': TriggerPlot,             # sync plot type
    'unitmet': UnitMetricPlot,          # unit metrics plot type
    'unithist': UnitHistPlot,           # unit metrics plot type
    'waveform': WaveFormPlot,           # waveform plot type
    'upset': UpSetPlot,                 # unit upset plot type

}

# list of plot title names
plot_names = {
    'trace': 'Trace View',
    'probe': 'Probe View',
    'trigger': 'Trigger View',
    'unitmet': 'Metrics View',
    'unithist': 'Histograms View',
    'waveform': 'Waveforms View',
    'upset': 'UpSet View',
}
