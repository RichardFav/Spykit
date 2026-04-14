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
from PyQt6.QtGui import QFont

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMetricPara:
"""


class UnitMetricPara(PropPara):
    # pyqtSignal functions
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
    def _edit_update(p_str, _self):

        if not _self.is_updating:
            _self.edit_update.emit(p_str)

    @staticmethod
    def _check_update(p_str, _self):

        if not _self.is_updating:
            _self.check_update.emit(p_str)

    # trace property observer properties
    i_unit = cf.ObservableProperty(pfcn(_edit_update, 'i_unit'))
    show_metric = cf.ObservableProperty(pfcn(_check_update, 'show_metric'))
    show_grid = cf.ObservableProperty(pfcn(_check_update, 'show_grid'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMetricProps:
"""


class UnitMetricProps(PropWidget):
    # field properties
    type = 'unitmet'

    # font sizes
    lbl_size = 10
    tick_size = 9
    title_sub_size0 = 12
    title_main_size0 = 25

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

        # retrieves the metric table
        self.get_metric_table_values()

        for ch_k, ch_v in self.p_info['ch_fld'].items():
            if ch_v['type'] in 'edit':
                setattr(self, ch_k, self.get_para_value(ch_k))

        # connects the slot functions
        self.p_props.edit_update.connect(self.edit_update)
        self.p_props.check_update.connect(self.check_update)

        # retrieves and updates the region config properties
        self.obj_rconfig = self.findChild(cw.QRegionConfig)
        self.obj_rconfig.set_enabled(True)
        self.obj_rconfig.config_reset.connect(self.reset_plot_config)

        # sets the initial configuration
        self.g_id0 = np.zeros((9,4), dtype=int)
        self.g_id0[:4, :2], self.g_id0[:4, 2:] = 1, 2
        self.g_id0[4:6, :2], self.g_id0[4:6, 2:] = 3, 4
        self.g_id0[6:, :3], self.g_id0[6:, 3] = 5, 6
        self.obj_rconfig.reset_config_id(self.g_id0)
        self.obj_rconfig.reset_selector_widgets(self.g_id0)

        # sets the parameter layout properties
        self.f_layout.setSpacing(5)

        # sets up the unit type fields
        if bool(self.get_mem_map_field('splitGoodAndMua_NonSomatic')):
            self.unit_lbl = ['Noise', 'Somatic Good', 'Somatic MUA', 'Non-somatic Good', 'Non-somatic MUA']
        else:
            self.unit_lbl = ['Noise', 'Good', 'MUA', 'Non-Somatic']

        # sets up the title/label font sizes
        self.title_sub_size = '{0}pt'.format(self.title_sub_size0)
        self.title_main_font = cw.create_font_obj(
            self.title_main_size0, is_bold=True, font_weight=QFont.Weight.Bold)
        self.lbl_font = cw.create_font_obj(
            self.lbl_size, is_bold=True, font_weight=QFont.Weight.Bold)
        self.tick_font = cw.create_font_obj(
            self.tick_size, is_bold=True, font_weight=QFont.Weight.Bold)

    def setup_prop_fields(self):

        # initialisations
        self.p_list_plot = ['Mean Template Waveform', 'Raw Template Waveform',
                            'Spatial Decay', 'Auto-Correlogram', 'Spiking Activity',
                            'Spike Amplitudes']

        # sets up the subgroup fields
        p_tmp = {
            'i_unit': self.create_para_field('Cluster Unit ID#', 'edit', 1),
            'show_metric': self.create_para_field('Show Metrics', 'checkbox', True),
            'show_grid': self.create_para_field('Show Plot Gridlines', 'checkbox', False),
            'r_cfig': self.create_para_field('', 'rconfig', None, p_list=self.p_list_plot),
        }

        # updates the class field
        self.p_info = {'name': 'Metrics', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def edit_update(self, p_str):

        # if force updating, then exit the function
        if self.is_updating:
            return

        # field retrieval
        h_edit = self.findChild(cw.QLineEdit,name=p_str)
        nw_val = h_edit.text()

        match p_str:
            case 'i_unit':
                min_val, max_val = 1, self.get_mem_map_field('q_met').shape[0]

        # determines if the new value is valid
        chk_val = cf.check_edit_num(nw_val, min_val=min_val, max_val=max_val, is_int=True)
        if chk_val[1] is None:
            # updates the parameter value
            setattr(self, p_str, int(chk_val[0]))

            # parameter specific updates
            match p_str:
                case 'i_unit':
                    # case is the cluster index
                    unit_tab = self.main_obj.main_obj.main_obj.info_manager.get_info_tab('unit')
                    unit_tab.reset_selected_cell(chk_val[0] - 1)

            # updates the histogram view
            if self.plot_view is not None:
                setattr(self.plot_view, p_str, int(chk_val[0]))

        else:
            # otherwise, reset the previous value
            p_val_pr = getattr(self, p_str)
            h_edit.setText('%g' % p_val_pr)
            self.reset_para_value(p_str, p_val_pr)

    def check_update(self, p_str):

        # updates the histogram view
        if self.plot_view is not None:
            setattr(self.plot_view, p_str, self.get_para_value(p_str))

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

    def get_metric_table_values(self):

        self.q_met = self.main_obj.main_obj.main_obj.session_obj.get_metric_table()

    def get_raw_traces(self, i_unit_f, i_ch):

        # determines the channel index offset
        i_shank = self.main_obj.main_obj.session_obj.get_shank_index()
        i_ch_ofs = self.main_obj.main_obj.session_obj.post_data.i_ch_ofs[i_shank]

        return self.get_mem_map_field('avg_sig')[i_unit_f, i_ch + i_ch_ofs, :]

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def scale_font_sizes(self, p_wid, p_hght):

        # calculates the new scale factor
        p_scl = np.min([p_wid, p_hght])
        f_sz_sub = int(np.ceil(self.title_sub_size0 * p_scl))
        f_sz_main = int(np.ceil(self.title_main_size0 * p_scl))
        f_sz_lbl = int(np.ceil(self.lbl_size * p_scl))
        f_sz_tick = int(np.ceil(self.tick_size * p_scl))

        # resets the title string
        self.title_sub_size = '{0}pt'.format(f_sz_sub)

        # resets the font objects
        self.title_main_font.setPointSize(f_sz_main)
        self.lbl_font.setPointSize(f_sz_lbl)
        self.tick_font.setPointSize(f_sz_tick)

    def reset_para_value(self, p_fld, p_val):

        # resets the parameter value (without activating callback)
        self.p_props.is_updating = True
        setattr(self.p_props, p_fld, p_val)
        self.p_props.is_updating = False

    def reset_plot_config(self):

        # updates the plot title
        self.plot_view.update_plot_config()

    def get_metric_col_index(self, h_str):

        return np.where(self.get_mem_map_field('q_hdr') == h_str)[1][0]