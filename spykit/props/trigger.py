# module import
import os
import time
import numpy as np
from copy import deepcopy
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara

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

        if i_row is None:
            return self.data[:, i_col]

        else:
            return self.data[i_row, i_col]

# ----------------------------------------------------------------------------------------------------------------------

"""
    TriggerPara:
"""


class TriggerPara(PropPara):
    # pyqtSignal functions
    pair_update = pyqtSignal()

    def __init__(self, p_info, n_run):

        # initialises the table arrays
        self.t_arr = self.reset_table_array(n_run)

        # initialises the class parameters
        self.is_updating = True
        super(TriggerPara, self).__init__(p_info, n_run)
        self.is_updating = False

    def reset_prop_para(self, p_info, n_run):

        # initialises the table arrays
        self.t_arr = self.reset_table_array(n_run)

        # initialises the class parameters
        self.is_updating = True
        super(TriggerPara, self).__init__(p_info, n_run)
        self.is_updating = False

    # ---------------------------------------------------------------------------
    #
    # ---------------------------------------------------------------------------

    def add_row(self, i_run, nw_row):

        self.t_arr[i_run].add_row(nw_row)
        self.region_index[i_run] = self.t_arr[i_run].data

    def remove_row(self, i_run, i_row):

        self.t_arr[i_run].remove_row(i_row)
        self.region_index[i_run] = self.t_arr[i_run].data

    def set(self, i_run, i_row, i_col, value):

        self.t_arr[i_run].set(i_row, i_col, value)
        self.region_index[i_run] = self.t_arr[i_run].data

    def set_arr(self, i_run, i_row, i_col, values):

        if i_row is None:
            self.t_arr[i_run].data[:, i_col] = values

        else:
            self.t_arr[i_run].data[i_row, i_col] = values

        self.region_index[i_run] = self.t_arr[i_run].data

    def get(self, i_run, i_row, i_col):

        return self.t_arr[i_run].get(i_row, i_col)

    # ---------------------------------------------------------------------------
    # Table Array Functions
    # ---------------------------------------------------------------------------

    def reset_table_array(self, n_run):

        return [TableArray() for _ in range(n_run)]

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
    # field properties
    type = 'trigger'

    # parameters
    pt_dur = 0.1
    pt_win_min = 0.05

    # array class fields
    xi_col = np.array([1, 2])
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
        self.p_props = TriggerPara(self.p_info['ch_fld'], self.n_run)

        # widget field retrieval
        self.button_pair = self.findChild(cw.QButtonPair)
        self.table_region = self.findChild(QTableWidget)

        # initialises the other class fields
        self.init_other_class_fields()

    def init_other_class_fields(self):

        # connects the slot functions
        self.reset_slot_functions()

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
            self.p_props.set(i_run, self.i_row_sel, self.i_col_sel, chk_val[0])
            self.trig_view.update_region(self.i_row_sel)

        else:
            # otherwise, reset the previous value
            self.is_updating = True
            item_sel.setText('%g' % self.p_props.get(i_run, self.i_row_sel, self.i_col_sel))
            self.is_updating = False

    def pair_update(self):

        # field retrieval
        i_run = self.get_run_index()
        db_state = self.b_state - self.p_props.button_flag[i_run]
        if db_state == 0:
            i_button = 0
        else:
            i_button = int(np.log2(abs(db_state)))

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
        self.b_state = self.p_props.button_flag[i_run]

    def reset_table_data(self):

        for i_run in range(self.n_run):
            self.p_props.t_arr[i_run].data = self.get('region_index', i_run)

    # ---------------------------------------------------------------------------
    # Setter Functions
    # ---------------------------------------------------------------------------

    def set_trig_view(self, trig_view_new):

        self.trig_view = trig_view_new

    def set_table_cell(self, i_row, i_col, value):

        # updates the table data
        i_run = self.get_run_index()
        self.p_props.set(i_run, i_row, i_col, value)

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

        return self.p_props.t_arr[self.get_run_index()].data[i_row, :]

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
        t_win_min = self.pt_win_min * t_dur

        if self.n_row == 1:
            # case is the first region
            ind_row = [0, t_win_min]

        else:
            # case is the other regions
            t_final = self.p_props.get(i_run, self.n_row - 2, 2)
            t_win = t_dur - t_final

            if t_win < t_win_min:
                # insufficient space available for new region
                cf.show_error('Insufficient space for new trigger region.')
                return None

            else:
                # determines the new region size
                dt_win = int(self.pt_dur * t_win)
                t_reg = np.max([t_win_min, dt_win])

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
            # case is the lower limit is being altered
            t_min, t_max = 0, self.p_props.get(i_run, self.i_row_sel, 2)

        else:
            # case is the upper limit is being altered
            t_min, t_max = self.p_props.get(i_run, self.i_row_sel, 1), self.get_run_duration()

        if self.i_row_sel > 0:
            # case is the selected row is not the first
            t_min = self.p_props.get(i_run, self.i_row_sel - 1, 2)

        if (self.i_row_sel + 1) < self.trig_view.n_reg_xs[i_run]:
            # case is the selected row is not the last
            t_max = self.p_props.get(i_run, self.i_row_sel + 1, 1)

        return t_min, t_max

    # ---------------------------------------------------------------------------
    # Linear Region Add/Remove Functions
    # ---------------------------------------------------------------------------

    def add_region(self, i_run, nw_row, add_prop=True):

        self.table_region.setRowCount(self.n_row)
        self.trig_view.add_region(nw_row)

        if add_prop:
            self.p_props.add_row(i_run, nw_row)

        for i_col, c_val in enumerate(nw_row):
            # creates the widget item
            item = cw.QTableWidgetItemSortable(None)
            item.setFont(self.table_font)

            # case is a string field
            item.setFlags(self.item_index if i_col == 0 else self.item_flag)
            if i_col == 0:
                item.setText(str(int(c_val)))
            else:
                item.setText('%g' % c_val)

            # adds the item to the table
            item.setTextAlignment(cf.align_type['center'])
            self.table_region.setItem(self.n_row - 1, i_col, item)

    def delete_region(self, i_run, i_row):

        self.table_region.removeRow(i_row)
        self.p_props.remove_row(i_run, i_row)
        self.trig_view.delete_region(i_row)

    def delete_all_regions(self):

        # initialisations
        change_made = False

        # deletes any regions (if the exist)
        for i_run in range(self.trig_view.n_run):
            if self.trig_view.n_reg_xs[i_run]:
                change_made = True
                for i_reg in np.flip(range(self.trig_view.n_reg_xs[i_run])):
                    self.delete_region(i_run, i_reg)

        # returns the change flag
        return change_made

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def reset_slot_functions(self):

        self.p_props.pair_update.connect(self.pair_update)

    def reset_region_timing(self, t_dur, dt):

        if dt == 0:
            return

        # determines if any trigger region exist for the current run
        i_run = self.get_run_index()
        if self.p_props.region_index[i_run] is None:
            return

        # updates the properties and time-shifts the durationss
        self.p_props.set_arr(i_run, None, self.xi_col, self.p_props.get(i_run, None, self.xi_col) - dt)
        self.time_shift_limits(i_run, t_dur)

        # for each remaining region, reset the region bounds/position
        for i_reg, l_reg in enumerate(self.trig_view.l_reg_xs[i_run]):
            # resets the region bounds
            t_lim = [0, t_dur]

            # case is the region is not the first region
            if i_reg > 0:
                t_lim[0] = self.trig_view.l_reg_xs[i_run][i_reg - 1].getRegion()[1]

            # case is the region is not the last region
            if (i_reg + 1) < self.trig_view.n_reg_xs[i_run]:
                t_lim[1] = self.trig_view.l_reg_xs[i_run][i_reg + 1].getRegion()[0]

            # resets the trigger region bounds
            self.trig_view.is_updating = True
            l_reg.setBounds(t_lim)
            self.trig_view.is_updating = False

            # updates the trigger region position
            self.trig_view.update_region(i_reg)

    def time_shift_limits(self, i_run, t_dur):

        # field retrieval
        n_reg = self.p_props.t_arr[i_run].n_row

        # resets the region limits so that they are feasible
        is_ok = np.ones(n_reg, dtype=bool)
        for i_reg in np.flip(range(n_reg)):
            # determines if regions are feasible wrt the start point
            t_data0 = self.p_props.t_arr[i_run].data[i_reg, 1:]
            s_feas = t_data0 >= 0
            if not np.any(s_feas):
                # case is the region is infeasible
                is_ok[i_reg] = False

            elif not np.all(s_feas):
                # otherwise, reset the parameter values
                t_data0 = np.maximum(0, t_data0)
                self.p_props.set_arr(i_run, i_reg, self.xi_col, t_data0)

            # determines if regions are feasible wrt the start point
            f_feas = t_data0 <= t_dur
            if not np.any(f_feas):
                # case is the region is infeasible
                is_ok[i_reg] = False

            elif not np.all(f_feas):
                # otherwise, reset the parameter values
                t_data0 = np.minimum(t_dur, t_data0)
                self.p_props.set_arr(i_run, i_reg, self.xi_col, t_data0)

            # if the region is infeasible, then remove it
            if not is_ok[i_reg]:
                self.delete_region(i_run, i_reg)

            else:
                # flag that manual field updating is taking place
                self.is_updating = True

                for i_col in range(1, self.p_props.t_arr[i_run].n_col):
                    item = self.table_region.item(i_reg, i_col)
                    item_val = self.p_props.get(i_run, i_reg, i_col)
                    item.setText('%g' % item_val)

                # resets the update flag
                self.is_updating = False

        if any(np.logical_not(is_ok)):
            xi_c = np.array(range(sum(is_ok)))
            self.p_props.set_arr(i_run, None, 0, xi_c + 1)
