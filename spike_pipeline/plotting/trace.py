# spike pipeline imports
from spike_pipeline.plotting.utils import PlotWidget, PlotPara

# pyqt6 module import
from PyQt6.QtWidgets import (QWidget)


class TraceParaClass(PlotPara):
    def __init__(self):
        super(TraceParaClass, self).__init__('Trace')
        a = 1


class TracePlotWidget(PlotWidget):
    def __init__(self):
        super(TracePlotWidget, self).__init__('trace')
        a = 1


class TracePlot(TraceParaClass, TracePlotWidget):
    def __init__(self, session_info):
        TracePlotWidget.__init__(self)
        TraceParaClass.__init__(self)

        # main class fields
        self.session_info = session_info

        # sets up the plot regions
        self.setup_subplots()

