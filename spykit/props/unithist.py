# module import
import os
import math
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitHistPara:
"""


class UnitHistPara(PropPara):
    # pyqtSignal functions
    edit_update = pyqtSignal(str)
    check_update = pyqtSignal(str)
    checklist_update = pyqtSignal(str)

    def __init__(self, p_info):

        # initialises the class parameters
        self.is_updating = True
        super(UnitHistPara, self).__init__(p_info)
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

    @staticmethod
    def _checklist_update(p_str, _self):

        if not _self.is_updating:
            _self.checklist_update.emit(p_str)

    # trace property observer properties
    i_unit = cf.ObservableProperty(pfcn(_edit_update, 'i_unit'))
    hist_type = cf.ObservableProperty(pfcn(_checklist_update, 'hist_type'))
    opt_config = cf.ObservableProperty(pfcn(_check_update, 'opt_config'))
    n_r = cf.ObservableProperty(pfcn(_edit_update, 'n_r'))
    n_c = cf.ObservableProperty(pfcn(_edit_update, 'n_c'))
    n_bin = cf.ObservableProperty(pfcn(_edit_update, 'n_bin'))
    show_thresh = cf.ObservableProperty(pfcn(_check_update, 'show_thresh'))
    show_grid = cf.ObservableProperty(pfcn(_check_update, 'show_grid'))

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitHistProps:
"""


class UnitHistProps(PropWidget):
    # field properties
    type = 'unithist'

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # initialises the property widget
        self.setup_prop_fields()
        super(UnitHistProps, self).__init__(self.main_obj, 'unithist', self.p_info)

        # sets up the parameter fields
        self.p_props = UnitHistPara(self.p_info['ch_fld'])

        # other class fields
        self.plot_view = None
        self.is_updating = False

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        for ch_k, ch_v in self.p_info['ch_fld'].items():
            if ch_v['type'] in 'edit':
                setattr(self, ch_k, self.get_para_value(ch_k))

        # resets the object sizes
        h_chklist = self.findChild(cw.QLabelCheckCombo)
        h_chklist.h_lbl.setFixedWidth(70)
        h_chklist.h_combo.setFixedWidth(200)

        # connects the slot functions
        self.p_props.edit_update.connect(self.edit_update)
        self.p_props.check_update.connect(self.check_update)
        self.p_props.checklist_update.connect(self.checklist_update)

        # other checkbox updates
        self.check_update('opt_config')

        # sets up the unit type fields
        if bool(self.get_mem_map_field('splitGoodAndMua_NonSomatic')):
            self.unit_lbl = ['Noise', 'Somatic Good', 'Somatic MUA', 'Non-somatic Good', 'Non-somatic MUA']
        else:
            self.unit_lbl = ['Noise', 'Good', 'MUA', 'Non-Somatic']

    def setup_prop_fields(self):

        # retrieves the feasible metrics
        self.get_feasible_metrics()

        # field retrieval
        self.p_met_fin = self.p_met[self.can_plot]
        self.n_unit, _ = self.get_mem_map_field('q_met').shape

        # memory allocation
        n_bin0 = 40
        n_met = len(self.p_met_fin)
        show_hist = np.ones(n_met, dtype=bool)
        n_row, n_col = self.calc_opt_config()

        # sets up the subgroup fields
        p_tmp = {
            'i_unit': self.create_para_field('Cluster ID#', 'edit', 1),
            'hist_type': self.create_para_field('Metric', 'checklist', show_hist, p_list=self.p_met_fin),
            'opt_config': self.create_para_field('Use Optimal Configuration?', 'checkbox', True),
            'n_r': self.create_para_field('Row Count', 'edit', n_row),
            'n_c': self.create_para_field('Column Count', 'edit', n_col),
            'n_bin': self.create_para_field('Max Bin Count', 'edit', n_bin0),
            'show_thresh': self.create_para_field('Show Threshold Markers', 'checkbox', True),
            'show_grid': self.create_para_field('Show Plot Gridlines', 'checkbox', True),
        }

        # updates the class field
        self.p_info = {'name': 'Histograms', 'type': 'v_panel', 'ch_fld': p_tmp}

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
            case p_str if p_str in ['n_r', 'n_c']:
                n_met = np.sum(self.get_para_value('hist_type'))
                min_val = int(np.ceil(n_met / (self.n_c if (p_str == 'n_r') else self.n_r)))
                max_val = n_met

            case 'n_bin':
                min_val, max_val = 10, 100

            case 'i_unit':
                min_val, max_val = 1, self.n_unit

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
                    unit_tab.table_cell_click(chk_val[0] - 1, 0)

            # updates the histogram view
            if self.plot_view is not None:
                setattr(self.plot_view, p_str, int(chk_val[0]))

        else:
            # otherwise, reset the previous value
            p_val_pr = getattr(self, p_str)
            h_edit.setText('%g' % p_val_pr)
            self.reset_para_value(p_str, p_val_pr)

    def check_update(self, p_str):

        # field retrieval
        reset_config = False
        h_chk = self.findChild(cw.QCheckBox, name=p_str)

        match p_str:
            case 'opt_config':
                # updates the line-edit properties
                is_chk = h_chk.checkState() == cf.chk_state[False]

                # determines if the dimensions need updating
                n_row, n_col = self.calc_opt_config()
                reset_dim = not np.array_equal([self.n_r, self.n_c], [n_row, n_col])

                # resets the row/column properties
                for pn in ['n_r', 'n_c']:
                    # widget handle retrieval
                    h_ledit = self.findChild(cw.QLabelEdit, name=pn)
                    h_ledit.set_enabled(is_chk)

                    if reset_dim:
                        # retrieves the dimension value
                        dim_val = n_row if (pn == 'n_r') else n_col

                        # updates the parameter class field
                        self.reset_para_value(pn, dim_val)
                        self.reset_view_para_value(pn, dim_val)

                        # updates the editbox
                        self.is_updating = True
                        h_ledit.set_text('%g' % dim_val)
                        self.is_updating = False

        # updates the histogram view
        if self.plot_view is not None:
            setattr(self.plot_view, p_str, self.get_para_value(p_str))

    def checklist_update(self, p_str):

        # if force updating, then exit the function
        if self.is_updating:
            return

        # field retrieval
        hist_type = self.get_para_value('hist_type')
        n_plot = int(self.get_para_value('n_r') * self.get_para_value('n_c'))

        # determines if the selection is feasible
        if np.sum(hist_type) > n_plot:
            # if the selected metric exceeds the number of plots then output an error
            e_str = "The current metric selection exceeds the subplot count ({0})." \
                    "\nYou will need to expand the subplot count before continuing.".format(n_plot)
            cf.show_error(e_str, "Insuffiction Subplot Count")

            # determines the index of the
            i_hist_type = np.where(hist_type)[0]
            i_met_chg = np.setdiff1d(i_hist_type, self.plot_view.i_met)[0]

            # resets the parameter field
            hist_type[i_met_chg] = False
            self.reset_para_value('hist_type', hist_type)

            # resets the checklist marker
            self.is_updating = True
            h_chklist = self.findChild(cw.QLabelCheckCombo, name=p_str)
            h_chklist.set_checked(i_met_chg, False)
            self.is_updating = False

        # case is updating the unit type
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

    def get_feasible_metrics(self):

        # field retrieval
        self.p_met = np.array(list(cw.hist_map.values()))
        self.can_plot = np.ones(len(self.p_met), dtype=bool)

        # sets the plot feasibility flags
        for i, pm in enumerate(self.p_met):
            match pm:
                case 'RPV tauR Estimate':
                    # case is the RPV tau estimate
                    self.can_plot[i] = (
                            self.get_mem_map_field('tauR_valuesMin') != self.get_mem_map_field('tauR_valuesMax'))

                case 'Spatial Decay':
                    # case is spatial decay
                    self.can_plot[i] = self.get_mem_map_field('computeSpatialDecay') == 1

                case pm if pm in ['Raw Amplitude', 'SNR']:
                    # case is the raw signal metrics
                    self.can_plot[i] = bool(self.get_mem_map_field('extractRaw'))

                case pm if pm in ['Max Drift', 'Cumulative Drift']:
                    # case is the drift metrics
                    self.can_plot[i] = bool(self.get_mem_map_field('computeDrift'))

                case pm if pm in ['Isolation Distance', 'L-Ratio']:
                    # case is the distance metrics
                    self.can_plot[i] = (bool(self.get_mem_map_field('computeDistanceMetrics'))
                                   and not np.isnan(self.get_mem_map_field('isoDmin')))

                case '% Spike Missing (Sym)':
                    # redundant fields?
                    self.can_plot[i] = False

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

    def reset_view_para_value(self, p_str, p_val):

        # updates the plot view parameter value (without activating callback)
        self.plot_view.is_init = True
        setattr(self.plot_view, p_str, p_val)
        self.plot_view.is_init = False

    def calc_opt_config(self):

        n_met = len(self.p_met_fin)
        n_row = int(np.floor(math.sqrt(n_met)))

        return n_row, int(np.ceil(n_met / n_row))

    def get_metric_col_index(self, h_str):

        return np.where(self.get_mem_map_field('q_hdr') == h_str)[1][0]