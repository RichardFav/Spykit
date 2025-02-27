# module import
import functools

# spike pipeline imports
import spike_pipeline.common.common_func as cf
from spike_pipeline.plotting.utils import PlotWidget, PlotPara

# pyqt6 module import
from PyQt6.QtWidgets import (QWidget)
from PyQt6.QtCore import pyqtSignal

class TraceParaClass(PlotPara):
    def __init__(self):
        super(TraceParaClass, self).__init__('Trace')
        a = 1


class TracePlotWidget(PlotWidget):
    def __init__(self):
        super(TracePlotWidget, self).__init__('trace')
        a = 1


class TracePlot(TraceParaClass, TracePlotWidget):
    # pyqtsignal functions
    hide_plot = pyqtSignal()

    def __init__(self, session_info):
        TracePlotWidget.__init__(self)
        TraceParaClass.__init__(self)

        # main class fields
        self.session_info = session_info

        # sets up the plot regions
        self.setup_subplots()

        # initialises the other class fields
        self.init_class_fields()

    def init_class_fields(self):

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = functools.partial(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

    # ---------------------------------------------------------------------------
    # Plot Button Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'new':
                # case is the new button
                cf.show_error('Finish Me!')

            case 'open':
                # case is the open button
                cf.show_error('Finish Me!')

            case 'save':
                # case is the save button
                cf.show_error('Finish Me!')

            case 'close':
                # case is the close button
                self.hide_plot.emit()
