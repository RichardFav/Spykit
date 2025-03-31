# module import
import os
import time
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.props.utils import PropWidget, PropPara

# pyqt imports
from PyQt6.QtWidgets import QTableWidget, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    TableArray:
"""


class TableArray(QObject):
    def __init__(self, n_row=0, n_col=0):
        super(TableArray, self).__init__()

        self.n_row = 0
        self.n_col = None
        self.data = None

    def add_row(self, nw_row):

        if self.n_col is None:
            # case is initialising the data array
            self.n_col = len(nw_row)
            self.data = np.zeros((1, self.n_col))
            self.data[0, :] = np.array(nw_row)

        else:
            # otherwise, append the row to the data array
            self.data = np.vstack((self.data, np.array(nw_row)))

        # increments the row counter
        self.n_row += 1

    def remove_row(self, i_row):

        # removes the table row (decrements the index row where required)
        self.data = np.delete(self.data, i_row, axis=0)
        self.data[(i_row+1):, 0] -= 1

        # decrements the row counter
        self.n_row -= 1

    def set(self, i_row, i_col, value):

        self.data[i_row, i_col] = value

    def get(self, i_row, i_col):

        return self.data[i_row, i_col]

# ----------------------------------------------------------------------------------------------------------------------

"""
    TriggerPara:
"""


class TriggerPara(PropPara):
    # pyqtSignal functions
    pair_update = pyqtSignal()

    def __init__(self, p_info):

        self.t_arr = TableArray()

        self.is_updating = True
        super(TriggerPara, self).__init__(p_info)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    #
    # ---------------------------------------------------------------------------

    def add_row(self, nw_row):

        self.t_arr.add_row(nw_row)
        self.region_index = self.t_arr.data

    def remove_row(self, i_row):

        self.t_arr.remove_row(i_row)
        self.region_index = self.t_arr.data

    def set(self, i_row, i_col, value):

        self.t_arr.set(i_row, i_col, value)
        self.region_index = self.t_arr.data

    def set_arr(self, i_col, values):

        self.t_arr.data[:, i_col] = values
        self.region_index = self.t_arr.data

    def get(self, i_row, i_col):

        return self.t_arr.get(i_row, i_col)

    # ---------------------------------------------------------------------------
    # Observable Property Event Callbacks
    # ---------------------------------------------------------------------------

    @staticmethod
    def _pair_update(_self):

        if not _self.is_updating:
            _self.pair_update.emit()

    # trace property observer properties
    button_flag = cf.ObservableProperty(_pair_update)

# ----------------------------------------------------------------------------------------------------------------------

"""
    TraceProp:
"""


class TriggerProps(PropWidget):
    # parameters
    pt_dur = 0.1
    t_win_min = 5

    # array class fields
    b_str = ['Add Row', 'Remove Row']
    c_hdr = ['Region', 'Start (s)', 'Finish (s)']
    item_index = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    item_flag = item_index | Qt.ItemFlag.ItemIsEditable

    # font types
    table_font = cw.create_font_obj(size=8)
    table_hdr_font = cw.create_font_obj(size=8, is_bold=True, font_weight=QFont.Weight.Bold)

    def __init__(self, main_obj):
        # sets the input arguments
        self.main_obj = main_obj

        # field initialisation
        self.n_row = 0
        self.b_state = 0
        self.i_row_sel = None
        self.i_col_sel = None
        self.trig_view = None
        self.n_run = self.main_obj.session_obj.session.get_run_count()

        # initialises the property widget
        self.setup_prop_fields()
        super(TriggerProps, self).__init__(self.main_obj, 'trigger', self.p_info)

        # memory allocation
        self.p_props = [TriggerPara(self.p_info['ch_fld']) for _ in range(self.n_run)]

        # widget field retrieval
        self.button_pair = self.findChild(cw.QButtonPair)
        self.table_region = self.findChild(QTableWidget)

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # connects the slot functions
        for i_run in range(self.n_run):
            self.p_props[i_run].pair_update.connect(self.pair_update)

        # resets the table properties
        n_col = len(self.c_hdr)
        self.table_region.setColumnCount(n_col)
        self.table_region.setHorizontalHeaderLabels(self.c_hdr)
        self.table_region.verticalHeader().setVisible(False)
        self.table_region.cellChanged.connect(self.table_changed)
        self.table_region.cellClicked.connect(self.table_selected)

        # sets the button properties
        self.button_pair.set_enabled(1, False)

        # resets the section resize mode
        horz_hdr = self.table_region.horizontalHeader()
        horz_hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for i_col in range(n_col):
            # updates the table header font
            self.table_region.horizontalHeaderItem(i_col).setFont(self.table_hdr_font)

        # flag initialisation is complete
        self.is_init = True

    def setup_prop_fields(self):

        # sets up the subgroup fields
        p_tmp = {
            'button_flag': self.create_para_field(self.b_str, 'buttonpair', 0),
            'region_index': self.create_para_field('Region Indices', 'table', None),
        }

        # updates the class field
        self.p_info = {'name': 'Trigger', 'type': 'v_panel', 'ch_fld': p_tmp}

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    def table_selected(self):

        self.i_row_sel = self.get_current_row()
        self.i_col_sel = self.table_region.currentColumn()
        self.button_pair.set_enabled(1, True)

    def table_changed(self):

        # if manually updating, then exit the function
        if self.is_updating:
            return

        # field retrieval
        i_run = self.get_run_index()
        t_min, t_max = self.get_time_limits(i_run)
        item_sel = self.table_region.item(self.i_row_sel, self.i_col_sel)

        chk_val = cf.check_edit_num(item_sel.text(), min_val=t_min, max_val=t_max)
        if chk_val[1] is None:
            # updates the table data array
            self.p_props[i_run].set(self.i_row_sel, self.i_col_sel, chk_val[0])
            self.trig_view.update_region(self.i_row_sel)

        else:
            # otherwise, reset the previous value
            self.is_updating = True
            item_sel.setText('%g' % self.p_props[i_run].get(self.i_row_sel, self.i_col_sel))
            self.is_updating = False

    def pair_update(self):

        # field retrieval
        i_run = self.get_run_index()
        i_button = int(np.log2(abs(self.b_state - self.p_props[i_run].button_flag)))

        # resets the table row count
        self.is_updating = True
        self.n_row += 1 - 2 * (i_button == 1)

        if i_button == 0:
            # case is adding a new row
            nw_row = self.get_new_table_row()
            if nw_row is None:
                return

            # adds the new region/table item
            self.add_region(i_run, nw_row)

        else:
            # case is removing a row
            for i_row in range((self.i_row_sel + 1), (self.n_row + 1)):
                item = self.table_region.item(i_row, 0)
                item.setText(str(i_row))

            # resets the other properties
            self.button_pair.set_enabled(1, False)
            self.delete_region(i_run, self.i_row_sel)
            self.i_row_sel = None

        # resets the button state
        self.is_updating = False
        self.b_state = self.p_props[i_run].button_flag

    # ---------------------------------------------------------------------------
    # Setter Functions
    # ---------------------------------------------------------------------------

    def set_trig_view(self, trig_view_new):

        self.trig_view = trig_view_new

    def set_table_cell(self, i_row, i_col, value):

        # updates the table data
        i_run = self.get_run_index()
        self.p_props[i_run].set(i_row, i_col, value)

        # updates the table cell string
        self.is_updating = True
        item = self.table_region.item(i_row, i_col)
        item.setText(str(value))
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Getter Functions
    # ---------------------------------------------------------------------------

    def get_run_index(self):

        curr_run = self.main_obj.session_obj.current_run
        return self.main_obj.session_obj.session.get_run_index(curr_run)

    def get_table_row(self, i_row):

        return self.p_props[self.get_run_index()].t_arr.data[i_row, :]

    def get_run_duration(self):

        if self.trig_view is None:
            return self.main_obj.session_obj.session_props.t_dur

        else:
            return self.trig_view.gen_props.get('t_dur')

    def get_new_table_row(self):

        from scipy.ndimage import distance_transform_edt

        # pre-calculations
        i_run = self.get_run_index()
        t_dur = self.get_run_duration()

        if self.n_row == 1:
            # case is the first region
            ind_row = [0, int(self.pt_dur * t_dur)]

        else:
            # case is the other regions
            t_final = self.p_props[i_run].get(self.n_row - 2, 2)
            t_win = t_dur - t_final

            if t_win < self.t_win_min:
                # insufficient space available for new region
                cf.show_error('Insufficient space for new trigger region.')
                return None

            else:
                # determines the new region size
                dt_win = int(self.pt_dur * t_win)
                t_reg = np.max([self.t_win_min, dt_win])

                # calculates the new region start/finish times
                t_ofs = np.min([t_win - t_reg, t_reg]) + t_final
                ind_row = cf.list_add([0, t_reg], t_ofs)

        # returns the table row
        return [self.n_row] + ind_row

    def get_current_row(self):

        i_row = self.table_region.currentRow()
        return None if (i_row < 0) else i_row

    def get_time_limits(self, i_run):

        # limit initialisation
        if self.i_col_sel == 1:
            t_min, t_max = 0, self.p_props[i_run].get(self.i_row_sel, 2)

        else:
            t_min, t_max = self.p_props[i_run].get(self.i_row_sel, 1), self.get_run_duration()

        if self.i_row_sel > 0:
            t_min = self.p_props[i_run].get(self.i_row_sel - 1, 2)

        if (self.i_row_sel + 1) < self.trig_view.n_reg_xs[i_run]:
            t_max = self.p_props[i_run].get(self.i_row_sel + 1, 1)

        return t_min, t_max

    # ---------------------------------------------------------------------------
    # Linear Region Add/Remove Functions
    # ---------------------------------------------------------------------------

    def add_region(self, i_run, nw_row):

        self.table_region.setRowCount(self.n_row)
        self.p_props[i_run].add_row(nw_row)
        self.trig_view.add_region(nw_row)

        for i_col, c_val in enumerate(nw_row):
            # creates the widget item
            item = cw.QTableWidgetItemSortable(None)
            item.setFont(self.table_font)

            # case is a string field
            item.setFlags(self.item_index if i_col == 0 else self.item_flag)
            if i_col == 0:
                item.setText(str(int(c_val)))
            else:
                item.setText(str(c_val))

            # adds the item to the table
            item.setTextAlignment(cf.align_type['center'])
            self.table_region.setItem(self.n_row - 1, i_col, item)

    def delete_region(self, i_run, i_row):

        self.table_region.removeRow(i_row)
        self.p_props[i_run].remove_row(i_row)
        self.trig_view.delete_region(i_row)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def reset_region_timing(self, t_dur, dt):

        # updates the table data
        xi_col = np.array([1, 2])
        i_run = self.get_run_index()
        n_reg = self.p_props[i_run].t_arr.n_row

        # resets the table data
        self.p_props[i_run].set_arr(xi_col, self.p_props[i_run].t_arr.data[:, 1:] - dt)

        #
        is_ok = np.ones(n_reg, dtype=bool)
        for i_reg in np.flip(range(n_reg)):
            # determines if regions are feasible wrt the start point
            s_feas = self.p_props[i_run].t_arr.data[i_reg, 1:] >= 0
            if not np.any(s_feas):
                # case is the region is infeasible
                is_ok[i_reg] = False

            elif not np.all(s_feas):
                # otherwise, reset the parameter values
                self.p_props[i_run].set_arr(xi_col, np.maximum(0, self.p_props[i_run].t_arr.data[i_reg, 1:]))

            # determines if regions are feasible wrt the start point
            f_feas = self.p_props[i_run].t_arr.data[i_reg, 1:] <= t_dur
            if not np.any(f_feas):
                # case is the region is infeasible
                is_ok[i_reg] = False

            elif not np.all(f_feas):
                # otherwise, reset the parameter values
                self.p_props[i_run].set_arr(xi_col, np.minimum(t_dur, self.p_props[i_run].t_arr.data[i_reg, 1:]))

            # removes the
            if not is_ok[i_reg]:
                self.delete_region(i_run, i_reg)

            else:
                # flag that manual field updating is taking place
                self.is_updating = True

                for i_col in range(1, self.p_props[i_run].t_arr.n_col):
                    item = self.table_region.item(i_reg, i_col)
                    item_val = self.p_props[i_run].get(i_reg, i_col)
                    item.setText(str(item_val))

                    self.trig_view.update_region(i_reg)

                # resets the update flag
                self.is_updating = False

        # resets the linear region bounds
        for l_reg in self.trig_view.l_reg_xs[i_run]:
            self.trig_view.xtrig_region_moved(l_reg)
