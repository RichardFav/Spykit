# module import
import functools
import numpy as np
import pyqtgraph as pg

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

        # parameters
        self.t_start = 0
        self.t_trace = np.min([session_info.session_props.t_dur, 2])

        # sets up the plot regions
        self.setup_subplots()
        self.plot_item = self.h_plot.getPlotItem()

        # initialises the other class fields
        self.init_class_fields()

    def init_class_fields(self):

        # sets the plot item properties
        self.plot_item.setMouseEnabled(y=False)
        self.plot_item.hideAxis('left')

        # sets the axis limits
        self.v_box.setXRange(self.t_start, self.t_start + self.t_trace)
        self.v_box.setLimits(xMin=0, xMax=self.session_info.session_props.t_dur)

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = functools.partial(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

    def reset_trace_view(self):

        y_ofs = 0.2

        #
        i_channel = self.session_info.get_selected_channels()

        if len(i_channel):
            s_freq = self.session_info.session_props.s_freq
            ch_ids = self.session_info.get_channel_ids(i_channel)

            i_frm0 = int(self.t_start * s_freq)
            i_frm1 = int((self.t_start + self.t_trace) * s_freq)

            x_data = np.linspace(self.t_start, self.t_start + self.t_trace, i_frm1 - i_frm0)
            y_data = self.session_info.get_traces(start_frame=i_frm0, end_frame=i_frm1, channel_ids=ch_ids)

            for i in range(y_data.shape[1]):
                y_min, y_max = np.min(y_data[:, i]), np.max(y_data[:, i])
                y_scl = y_ofs + (1 - y_ofs) * (y_data[:, i] - y_min) / (y_max - y_min)
                self.plot_item.plot(x_data, y_scl + i, clear=(i == 0))

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
