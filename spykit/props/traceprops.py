# module import
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceViewPara:
"""

class TraceViewPara(PropPara):
    # pyqtSignal functions
    combo_update = pyqtSignal(str)
    edit_update = pyqtSignal(str)
    check_update = pyqtSignal(str)

    def __init__(self, p_info):

        # initialises the class parameters
        self.is_updating = True
        super(TraceViewPara, self).__init__(p_info)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def _combo_update(p_str, _self):

        if not _self.is_updating:
            _self.combo_update.emit(p_str)

    @staticmethod
    def _edit_update(p_str, _self):

        if not _self.is_updating:
            _self.edit_update.emit(p_str)

    @staticmethod
    def _check_update(p_str, _self):

        if not _self.is_updating:
            _self.check_update.emit(p_str)

    # trace property observer properties
    plot_type = cf.ObservableProperty(pfcn(_combo_update, 'plot_type'))
    data_type = cf.ObservableProperty(pfcn(_combo_update, 'data_type'))
    sig_type = cf.ObservableProperty(pfcn(_combo_update, 'sig_type'))
    t_start = cf.ObservableProperty(pfcn(_edit_update, 't_start'))
    t_finish = cf.ObservableProperty(pfcn(_edit_update, 't_finish'))
    t_span = cf.ObservableProperty(pfcn(_edit_update, 't_span'))
    c_lim_lo = cf.ObservableProperty(pfcn(_edit_update, 'c_lim_lo'))
    c_lim_hi = cf.ObservableProperty(pfcn(_edit_update, 'c_lim_hi'))
    sort_by = cf.ObservableProperty(pfcn(_combo_update, 'sort_by'))
    scale_signal = cf.ObservableProperty(pfcn(_check_update, 'scale_signal'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceViewProps:
"""

class TraceViewProps(PropWidget):
    # pyqtSignal functions
    data_change = pyqtSignal(QWidget)

    # field properties
    type = 'traceview'

    # parameters
    t_span0 = 0.02
    sort_list = ['Depth', 'Channel ID']
    sig_list = ['Difference', 'Absolute']
    plot_list = ['Trace', 'Heatmap', 'Auto']

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # field initialisation
        self.data_flds = None
        self.trace_view = None
        self.is_updating = False
        self.t_dur = np.round(self.main_obj.main_obj.session_obj.session_props.t_dur, cf.n_dp)

        # initialises the property widget
        self.setup_prop_fields()
        super(TraceViewProps, self).__init__(self.main_obj, 'trace', self.p_info)

        # sets up the parameter fields
        self.p_props = TraceViewPara(self.p_info['ch_fld'])

        # widget object field retrieval
        self.data_type = self.findChild(cw.QLabelCombo, name='data_type')
        self.edit_start = self.findChild(cw.QLineEdit, name='t_start')
        self.edit_finish = self.findChild(cw.QLineEdit, name='t_finish')
        self.cmap_chooser = self.findChild(cw.QColorMapChooser, name='c_map')

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # connects the slot functions
        self.p_props.edit_update.connect(self.edit_update)
        self.p_props.combo_update.connect(self.combo_update)
        self.p_props.check_update.connect(self.check_update)

        # sets the colourmap chooser slot function
        self.cmap_chooser.colour_selected.connect(self.colour_selected)

        # sets the data type combobox properties
        self.data_type.set_enabled(False)

        # updates the other properties
        self.check_update('scale_signal')

        # flag initialisation is complete
        self.is_init = True

    def setup_prop_fields(self):

        # initialisations
        data_type = ['Raw']

        # sets up the subgroup fields
        p_tmp = {
            'plot_type': self.create_para_field('Plot Type', 'combobox', self.plot_list[0], p_list=self.plot_list),
            'data_type': self.create_para_field('Data Type', 'combobox', data_type[0], p_list=data_type),
            'sig_type': self.create_para_field('Signal Type', 'combobox', self.sig_list[0], p_list=self.sig_list),
            't_start': self.create_para_field('Start Time (s)', 'edit', 0),
            't_finish': self.create_para_field('Finish Time (s)', 'edit', self.t_span0),
            't_span': self.create_para_field('Trace Time-Span (s)', 'edit', self.t_span0),
            'c_lim_lo': self.create_para_field('Lower Voltage Limit', 'edit', -200),
            'c_lim_hi': self.create_para_field('Upper Voltage Limit', 'edit', 200),
            'sort_by': self.create_para_field('Sort Signals By', 'combobox', self.sort_list[0], p_list=self.sort_list),
            'scale_signal': self.create_para_field('Auto-Scale Trace Signals', 'checkbox', True),
            'c_map': self.create_para_field('Colormap', 'colormapchooser', 'RdBu'),
        }

        # updates the class field
        self.p_info = {'name': 'Trace', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def edit_update(self, p_str):

        # # flag that property values are being updated manually
        # self.p_props.is_updating = True

        # # updates the dependent field(s)
        # fld_update = []
        # match p_str:
        #     case 't_start':
        #         fld_update = ['t_finish']
        #         t_finish = np.round(self.get('t_start') + self.get('t_span'), cf.n_dp)
        #         self.set_n('t_finish', t_finish)
        #
        #     case 't_finish':
        #         fld_update = ['t_span']
        #         t_span = np.round(self.get('t_finish') - self.get('t_start'), cf.n_dp)
        #         self.set_n('t_span', t_span)
        #
        #     case 't_span':
        #         if (self.t_dur - self.get('t_start')) < self.get('t_span'):
        #             # case is the span can't fit within the signal
        #             t_start = np.round(self.t_dur - self.get('t_span'), cf.n_dp)
        #             self.set_n('t_finish', self.t_dur)
        #             self.set_n('t_start', t_start)
        #             fld_update = ['t_start', 't_finish']
        #
        #         else:
        #             fld_update = ['t_finish']
        #             t_finish = np.round(self.get('t_start') + self.get('t_span'), cf.n_dp)
        #             self.set_n('t_finish', t_finish)

        # # resets the parameter fields
        # for pf in fld_update:
        #     edit_obj = self.findChild(cw.QLineEdit, name=pf)
        #     edit_obj.setText(str(self.get(pf)))

        # # resets the property check flag
        # self.p_props.is_updating = False

        # resets the plot views
        if self.is_init:
            self.reset_trace_props(p_str)

    def combo_update(self, p_str):

        # exit if manually updating
        if self.is_updating:
            return

        match p_str:
            case 'data_type':
                # case is altering the data type field
                self.data_change.emit(self)

        # resets the plot views
        if self.is_init:
            self.reset_trace_props(p_str)

    def check_update(self, p_str):

        match p_str:
            case 'scale_signal':
                # resets the enabled property
                scale_signal = self.p_props.scale_signal
                self.set_widget_enable('c_lim_lo', not scale_signal)
                self.set_widget_enable('c_lim_hi', not scale_signal)

        # resets the plot views
        if self.is_init:
            self.reset_trace_props(p_str)

    def colormap_update(self, p_str):

        # resets the plot views
        if self.is_init:
            self.reset_trace_props(p_str)

    def colour_selected(self, c_map_new):

        self.p_props.c_map = c_map_new
        self.reset_trace_props(None)

    # ---------------------------------------------------------------------------
    # Plot View Setter Functions
    # ---------------------------------------------------------------------------

    def set_trace_view(self, trace_view_new):

        self.trace_view = trace_view_new

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def reset_trace_props(self, p_str):

        if self.trace_view is not None:
            self.trace_view.reset_trace_props(p_str)

    def reset_data_types(self, d_names, d_flds=None):

        # indicate that
        self.is_updating = True

        # resets the
        self.data_type.obj_cbox.clear()
        self.data_type.obj_cbox.addItems(d_names)
        self.data_type.set_enabled(len(d_names) > 1)

        # updates the data field
        if d_flds is not None:
            self.data_flds = d_flds

        # resets the update flag
        self.is_updating = False

    def set_widget_enable(self, p_str, state):

        h_widget = self.findChild(cw.QLabelEdit, name=p_str)
        h_widget.set_enabled(state)