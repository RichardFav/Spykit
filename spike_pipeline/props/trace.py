# module import
from functools import partial as pfcn

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    TracePara:
"""


class TracePara(PropPara):
    # pyqtSignal functions
    combo_update = pyqtSignal(str)
    edit_update = pyqtSignal(str)
    check_update = pyqtSignal(str)

    def __init__(self, p_info):
        self.is_updating = True
        super(TracePara, self).__init__(p_info)
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
    t_start = cf.ObservableProperty(pfcn(_edit_update, 't_start'))
    t_finish = cf.ObservableProperty(pfcn(_edit_update, 't_finish'))
    t_span = cf.ObservableProperty(pfcn(_edit_update, 't_span'))
    c_lim_lo = cf.ObservableProperty(pfcn(_edit_update, 'c_lim_lo'))
    c_lim_hi = cf.ObservableProperty(pfcn(_edit_update, 'c_lim_hi'))
    scale_signal = cf.ObservableProperty(pfcn(_check_update, 'scale_signal'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceProps:
"""


class TraceProps(PropWidget):
    # parameters
    t_span0 = 0.1
    plot_list = ['Trace', 'Heatmap', 'Auto']

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # field initialisation
        self.trace_view = None
        self.t_dur = self.main_obj.session_obj.session_props.t_dur

        # initialises the property widget
        self.setup_prop_fields()
        super(TraceProps, self).__init__(self.main_obj, 'trace', self.p_info)

        # sets up the parameter fields
        self.p_props = TracePara(self.p_info['ch_fld'])

        # widget object field retrieval
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

        # flag initialisation is complete
        self.is_init = True

    def setup_prop_fields(self):

        # sets up the subgroup fields
        p_tmp = {
            'plot_type': self.create_para_field('Plot Type', 'combobox', self.plot_list[0], p_list=self.plot_list),
            't_start': self.create_para_field('Start Time (s)', 'edit', 0),
            't_finish': self.create_para_field('Finish Time (s)', 'edit', self.t_span0),
            't_span': self.create_para_field('Duration (s)', 'edit', self.t_span0),
            'c_lim_lo': self.create_para_field('Lower Colour Limit', 'edit', -200),
            'c_lim_hi': self.create_para_field('Upper Colour Limit', 'edit', 200),
            'scale_signal': self.create_para_field('Scale Signals', 'checkbox', True),
            'c_map': self.create_para_field('Colormap', 'colormapchooser', 'viridis'),
        }

        # updates the class field
        self.p_info = {'name': 'Trace', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def edit_update(self, p_str):

        # flag that property values are being updated manually
        self.p_props.is_updating = True

        # updates the dependent field(s)
        fld_update = []
        match p_str:
            case 't_start':
                fld_update = ['t_finish']
                self.set('t_finish', self.get('t_start') + self.get('t_span'))

            case 't_finish':
                fld_update = ['t_start']
                self.set('t_start', self.get('t_finish') - self.get('t_span'))

            case 't_span':
                if (self.t_dur - self.get('t_start')) < self.get('t_span'):
                    # case is the span can't fit within the signal
                    self.set('t_finish', self.t_dur)
                    self.set('t_start', self.t_dur - self.get('t_span'))
                    fld_update = ['t_start', 't_finish']

                else:
                    fld_update = ['t_finish']
                    self.set('t_finish', self.get('t_start') + self.get('t_span'))

        # resets the parameter fields
        for pf in fld_update:
            edit_obj = self.findChild(cw.QLineEdit, name=pf)
            edit_obj.setText(str(self.get(pf)))

        # resets the property check flag
        self.p_props.is_updating = False

        # resets the plot views
        if self.is_init:
            self.reset_trace_props()

    def combo_update(self, p_str):

        # resets the plot views
        if self.is_init:
            self.reset_trace_props()

    def check_update(self, p_str):

        # resets the plot views
        if self.is_init:
            self.reset_trace_props()

    def colormap_update(self, p_str):

        # resets the plot views
        if self.is_init:
            self.reset_trace_props()

    def colour_selected(self, c_map_new):

        self.p_props.c_map = c_map_new
        self.reset_trace_props()

    # ---------------------------------------------------------------------------
    # Plot View Setter Functions
    # ---------------------------------------------------------------------------

    def set_trace_view(self, trace_view_new):

        self.trace_view = trace_view_new

    # ---------------------------------------------------------------------------
    # Plot View Update Functions
    # ---------------------------------------------------------------------------

    def reset_trace_props(self):

        if self.trace_view is not None:
            self.trace_view.reset_trace_props()
