# module import
import os
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMetricPara:
"""


class UnitMetricPara(PropPara):
    # pyqtSignal functions
    combo_update = pyqtSignal(str)
    edit_update = pyqtSignal(str)
    check_update = pyqtSignal(str)

    def __init__(self, p_info):

        # initialises the class parameters
        self.is_updating = True
        super(UnitMetricPara, self).__init__(p_info)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def _check_update(p_str, _self):

        if not _self.is_updating:
            _self.check_update.emit(p_str)

    # trace property observer properties
    show_grid = cf.ObservableProperty(pfcn(_check_update, 'show_grid'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMetricProps:
"""


class UnitMetricProps(PropWidget):
    # field properties
    type = 'unitmet'

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # initialises the property widget
        self.setup_prop_fields()
        super(UnitMetricProps, self).__init__(self.main_obj, 'unitmet', self.p_info)

        # sets up the parameter fields
        self.p_props = UnitMetricPara(self.p_info['ch_fld'])

        # other class fields
        self.plot_view = None
        self.is_updating = False

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        for ch_k, ch_v in self.p_info['ch_fld'].items():
            if ch_v['type'] in 'edit':
                setattr(self, ch_k, self.get_para_value(ch_k))

        # retrieves and updates the region config properties
        self.obj_rconfig = self.findChild(cw.QRegionConfig)
        self.obj_rconfig.set_enabled(True)
        self.obj_rconfig.config_reset.connect(self.reset_plot_config)

        # sets the initial configuration
        self.g_id0 = np.zeros((6,4), dtype=int)
        self.g_id0[:3, :2], self.g_id0[:3, 2:] = 1, 2
        self.g_id0[3, :2], self.g_id0[3, 2:], self.g_id0[4:, :] = 3, 4, 5
        self.obj_rconfig.reset_config_id(self.g_id0)
        self.obj_rconfig.reset_selector_widgets(self.g_id0)

        # sets the parameter layout properties
        self.f_layout.setSpacing(5)

        # sets up the unit type fields
        if bool(self.get_mem_map_field('splitGoodAndMua_NonSomatic')):
            self.unit_lbl = ['Noise', 'Somatic Good', 'Somatic MUA', 'Non-somatic Good', 'Non-somatic MUA']
        else:
            self.unit_lbl = ['Noise', 'Good', 'MUA', 'Non-Somatic']

    def setup_prop_fields(self):

        # initialisations
        self.p_list_plot = ['Mean Template Waveform', 'Raw Template Waveform',
                            'Spatial Decay', 'Auto-Correlogram', 'Spiking Activity']

        # sets up the subgroup fields
        p_tmp = {
            'i_unit': self.create_para_field('Cluster ID#', 'edit', 1),
            'show_metric': self.create_para_field('Show Metrics', 'checkbox', True),
            'show_grid': self.create_para_field('Show Plot Gridlines', 'checkbox', True),
            'r_cfig': self.create_para_field('', 'rconfig', None, p_list=self.p_list_plot),
        }

        # updates the class field
        self.p_info = {'name': 'Metrics', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def check_update(self, p_str):

        pass

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_plot_view(self, plot_view_new):

        self.plot_view = plot_view_new

    def set_para_value(self, p_fld, p_val):

        setattr(self.p_props, p_fld, p_val)

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_para_value(self, p_fld):

        return getattr(self.p_props, p_fld)

    def get_mem_map_field(self, p_fld):

        return self.main_obj.main_obj.session_obj.get_mem_map_field(p_fld)

    def get_unit_type(self, i_unit):

        i_type = int(self.get_mem_map_field('unit_type')[i_unit])
        return self.unit_lbl[i_type]

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def reset_para_value(self, p_fld, p_val):

        # resets the parameter value (without activating callback)
        self.p_props.is_updating = True
        setattr(self.p_props, p_fld, p_val)
        self.p_props.is_updating = False

    def reset_plot_config(self):

        # updates the plot title
        self.plot_view.update_plot_config()