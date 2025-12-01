# module import
import os
import time
import mmap
import functools
import BombCellPkg
import numpy as np
from pathlib import Path
from copy import deepcopy

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.info.utils import InfoWidgetPara
from spykit.threads.utils import ThreadWorker

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QGroupBox,
                             QTabWidget, QFormLayout, QSizePolicy, QTreeWidget, QFrame, QLineEdit,
                             QCheckBox, QComboBox)
from PyQt6.QtCore import (Qt)
from PyQt6.QtGui import (QFont)

# ----------------------------------------------------------------------------------------------------------------------

"""
    BombCellInfoTab:
"""

class BombCellInfoTab(InfoWidgetPara):
    # parameter field lists
    p_str_d = ['ephys_sample_rate', 'nChannels', 'nSyncChannels', 'ephysMetaFile', 'rawFile']

    # removal parameters
    p_rmv = {
        'verbose': False,
    }

    def __init__(self, t_str, main_obj, p_tab):
        super(BombCellInfoTab, self).__init__(t_str, main_obj, layout=QFormLayout)

        # sets the input arguments
        self.p_tab = p_tab
        self.main_obj = main_obj

        # initialises the major widget groups
        self.setup_prop_fields()
        self.init_filter_edit()
        self.init_property_frame()
        self.init_other_props()

        # other class properties
        self.p_props0 = deepcopy(self.p_props)

        # connects the property update function
        self.prop_updated.connect(self.solver_para_updated)

    def init_other_props(self):

        # disables the listed parameters
        for ps in self.p_str_d:
            h_obj = self.findChild(QLineEdit, name=ps)
            if h_obj is not None:
                h_obj.setEnabled(False)

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_prop_fields(self):

        self.p_map = {}

        # sets up the fields for each parameter group
        for pg, ps in self.p_tab.items():
            # memory allocation
            p_props_g = {}
            self.p_props[pg] = {}

            # sets up the properties for each parameter in the group
            for _ps in ps:
                # removes the parameter from the list (if required)
                if _ps in self.p_rmv:
                    self.main_obj.bc_pkg.BombCellFcn('setParaValue', _ps, self.p_rmv[_ps])
                    continue

                # creates the parameter field
                p_info = self.main_obj.bc_pkg.BombCellFcn('getParaInfo', _ps)
                p_value = self.main_obj.bc_pkg.BombCellFcn('getParaValue', _ps)
                p_desc, p_type = p_info['pDesc'], p_info['pType']

                # sets the parameter-group mapping value
                self.p_map[_ps] = pg

                match p_type:
                    case 'Checkbox':
                        # case is a checkbox
                        p_props_g[_ps] = self.create_para_field(p_desc, 'checkbox', bool(p_value))

                    case 'Popup':
                        # case is a popup menu
                        p_list = p_info['pList']
                        p_value = p_list[int(p_value)]
                        p_props_g[_ps] = self.create_para_field(p_desc, 'combobox', p_value, p_list=p_list)

                    case _:
                        # case is an editbox

                        # parameter specific updates
                        if (p_type == 'Edit'):
                            # case is an integer editbox
                            p_value = int(p_value)

                        elif (p_type == 'EditS') and (len(p_value) == 0):
                            # case is a string editbox with empty value
                            p_value = ''

                        # case is an editbox
                        p_props_g[_ps] = self.create_para_field(p_desc, 'edit', p_value)

                # updates the property value field
                self.p_props[pg][_ps] = p_props_g[_ps]['value']

            # sets the parameter group property fields
            self.p_prop_flds[pg] = {
                'name': self.main_obj.p_map[pg],
                'props': p_props_g,
            }

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def solver_para_updated(self, p_str):

        if self.is_updating:
            return

        # updates the reset parameters button props
        self.main_obj.check_para_reset()

        # updates the model parameter value
        p_value = self.p_props[p_str[0]][p_str[1]]
        p_props = self.p_prop_flds[p_str[0]]['props'][p_str[1]]
        if (p_props['type'] == 'combobox'):
            # case is a combobox
            i_sel = p_props['p_list'].index(p_value)
            self.main_obj.bc_pkg.BombCellFcn('setParaValue', p_str[1], i_sel)

        else:
            # case the other parameter types
            self.main_obj.bc_pkg.BombCellFcn('setParaValue', p_str[1], p_value)

# ----------------------------------------------------------------------------------------------------------------------

"""
    BombCellSoln:  class for storing BombCell calculated data 
"""

class BombCellSoln(object):
    # parameter mapping dictionary
    p_map = {
        # array dimensions
        'n_unit': 'nUnit',
        'n_pts': 'nPts',
        'n_ch': 'nCh',
        'n_ch_full': 'nChFull',
        'n_spike': 'nSpike',
        'n_qual_met': 'nQualMet',
        'n_hdr_max': 'nHdrMax',

        # ephys data metrics
        'i_spike': 'iSpike',
        'spk_cluster': 'spkCluster',
        't_wform': 'tWForm',
        't_amp': 'tAmp',
        'ch_pos': 'chPos',
        's_rate': 'sRate',
        'T_wform': 'TWForm',
        't_spike': 'tSpike',

        # quality metrics
        'q_hdr': 'Hdr',
        'q_met': 'Met',

        # raw waveform metrics
        'avg_sig': 'average',
        'pk_ch': 'peakChan',

        # miscellaneous metrics
        'unit_type': 'unitType',
        't_unique': 'tUnique',
    }

    # character/integer parameters
    int_para = ['spk_cluster', 's_rate', 'unit_type', 't_unique']

    def __init__(self, bc_pkg_fcn):
        super(BombCellSoln, self).__init__()

        # ephys data metrics
        self.array_dim = bc_pkg_fcn('getClassField','arrDim')
        self.ephys_data = bc_pkg_fcn('getClassField','ephysData')
        self.q_metric = bc_pkg_fcn('getClassField','qMetric')
        self.raw_form = bc_pkg_fcn('getClassField','rawForm')
        self.unit_type = bc_pkg_fcn('getClassField','unitType')
        self.t_unique = bc_pkg_fcn('getClassField', 'tUnique')

        # other fields
        self.meta_data = bc_pkg_fcn('getClassField','metaData')
        self.gui_data = bc_pkg_fcn('getClassField','guiData')

    def get_para_value(self, p_fld_bc):

        if hasattr(self, p_fld_bc):
            p_val = getattr(self, p_fld_bc)

        else:
            if p_fld_bc in self.p_map:
                p_fld = self.p_map[p_fld_bc]
            else:
                return None

            if p_fld in self.array_dim:
                p_val = self.array_dim[p_fld]

            elif p_fld in self.ephys_data:
                p_val = self.ephys_data[p_fld]

            elif p_fld in self.q_metric:
                p_val = self.q_metric[p_fld]

            elif p_fld in self.raw_form:
                p_val = self.raw_form[p_fld]

        # converts and returns the final values
        if p_fld_bc in self.int_para:
            # case is int32 type
            return np.int32(p_val)

        else:
            # case is float64 type
            return p_val

# ----------------------------------------------------------------------------------------------------------------------

"""
    BombCellSolver: dialog window for running the BombCell solver
"""

class BombCellSolver(QDialog):
    # widget dimensions
    x_gap = 5
    width_dlg = 425
    hght_fspec = 60
    hght_para = 480
    hght_button = 40

    # string class fields
    mmap_name = 'mMapProg.bin'

    # array class fields
    p_str_u = ['ephysMetaFile', 'rawFile']
    tab_str = ['Quality', 'Classification']
    but_str = ['Run Solver', 'Reset Parameters', 'Close Window']

    # stylesheets
    border_style = "border: 1px solid;"
    no_border_style = "border: 0px; padding-top: 3px;"
    frame_border_style = """
        QFrame {
            border: 1px solid;
        }
    """

    def __init__(self, main_obj, expt_dir=None):
        super(BombCellSolver, self).__init__(main_obj)

        # input arguments
        self.main_obj = main_obj
        self.expt_dir = expt_dir

        # class widgets
        self.h_tab_para = []
        self.cont_button = []
        self.fspec_group = QGroupBox("EXPERIMENT PARENT FOLDER")
        self.para_group = QGroupBox("SOLVER PARAMETERS")
        self.para_tab = cw.create_tab_group(None)
        self.prog_bar = cw.QDialogProgress(font=cw.font_lbl, is_task=True, timer_lbl=True)
        self.progress_frame = QFrame()
        self.button_frame = QFrame()

        # class layouts
        self.main_layout = QVBoxLayout()
        self.fspec_layout = QHBoxLayout()
        self.para_layout = QVBoxLayout()
        self.progress_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        # boolean class fields
        self.has_bc = False
        self.init_complete = False
        self.is_updating = False
        self.is_running = False
        self.can_close = False
        self.is_new_soln = False

        # folder/file path fields
        self.mmap_file = None

        # other class fields
        self.i_tab = 0
        self.i_run = 1
        self.bc_pkg = None
        self.bc_para_c = None
        self.solver_flag = None
        self.hght_dlg = 6 * self.x_gap + (self.hght_fspec + self.hght_para + self.hght_button)

        # initialises the class fields
        self.init_class_fields()
        self.init_fspec_group()
        self.init_para_group()
        self.init_progress_frame()
        self.init_cont_buttons()

        # initialises the bombcell fields
        self.init_bomb_cell()

        # sets the widget style sheets
        self.set_style_sheets()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the dialog window properties
        self.setFixedSize(self.width_dlg, self.hght_dlg)
        self.setWindowTitle('BombCell Solver')
        self.setLayout(self.main_layout)

        # adds the main group widgets to the dialog
        self.main_layout.addWidget(self.fspec_group)
        self.main_layout.addWidget(self.para_group)
        self.main_layout.addWidget(self.progress_frame)
        self.main_layout.addWidget(self.button_frame)

    def init_bomb_cell(self):

        # updates the progressbar
        self.prog_bar.set_label("Initialising BombCell")
        self.prog_bar.set_progbar_state(True)
        time.sleep(0.1)

        # creates the threadworker object
        self.t_worker = ThreadWorker(self, self.init_bombcell_solver, None)
        self.t_worker.work_finished.connect(self.bombcell_init_complete)

        # starts the worker object
        self.is_running = True
        self.t_worker.start()

    def init_fspec_group(self):

        # creates the groupbox object
        self.fspec_group.setLayout(self.fspec_layout)
        self.fspec_group.setFont(cw.font_panel)
        self.fspec_group.setFixedHeight(self.hght_fspec)

        # sets up the slot functions
        self.fspec_edit = cw.create_line_edit(None, "", align='right')
        self.fspec_layout.addWidget(self.fspec_edit)
        self.fspec_edit.setFixedHeight(cf.but_height)
        self.fspec_edit.setEnabled(False)
        self.fspec_edit.setReadOnly(True)

    def init_para_group(self):

        # creates the groupbox object
        self.para_group.setLayout(self.para_layout)
        self.para_group.setFont(cw.font_panel)

        # adds the tab object to the parmaeter layout
        self.para_layout.addWidget(self.para_tab)

        # resets the channel table style
        tab_style = cw.CheckBoxStyle(self.para_tab.style())
        self.para_tab.setStyle(tab_style)

    def setup_para_group(self):

        # creates the tab objects
        for ts, p_tab in self.p_grp.items():
            tab_widget = BombCellInfoTab(ts, self, p_tab)
            self.para_tab.addTab(tab_widget, ts)
            self.h_tab_para.append(tab_widget)

        # tab change callback function
        self.para_tab.currentChanged.connect(self.on_tab_changed)

    def init_progress_frame(self):

        # sets the frame/layout properties
        self.progress_frame.setContentsMargins(0, 0, 0, 0)
        self.progress_frame.setLayout(self.progress_layout)
        self.progress_frame.setStyleSheet(self.frame_border_style)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(0)
        self.progress_layout.addWidget(self.prog_bar)

        # creates the progressbar widgets
        self.prog_bar.set_enabled(False)
        self.prog_bar.setContentsMargins(self.x_gap, self.x_gap, self.x_gap, self.x_gap)
        # self.prog_bar.timer_fcn.connect(self.solver_prog_func)

        # progressbar label properties
        self.prog_bar.lbl_obj.setContentsMargins(0, self.x_gap - 1, 0, 0)
        self.prog_bar.lbl_obj.setStyleSheet(self.no_border_style)

    def init_cont_buttons(self):

        # initialisations
        cb_fcn = [self.run_solver, self.reset_para, self.close_window]

        # sets the button widget properties
        self.button_frame.setContentsMargins(self.x_gap, self.x_gap, self.x_gap, self.x_gap)
        self.button_frame.setLayout(self.button_layout)
        self.button_frame.setStyleSheet(self.frame_border_style)

        # sets the layout properties
        self.button_layout.setSpacing(2 * self.x_gap)
        self.button_layout.setContentsMargins(0, 0, 0, 0)

        for ib, (bs, cb) in enumerate(zip(self.but_str, cb_fcn)):
            # creates the control button widgets
            obj_but = cw.create_push_button(None, bs, cw.font_lbl)
            self.button_layout.addWidget(obj_but)
            self.cont_button.append(obj_but)

            # sets the other button properties
            obj_but.clicked.connect(cb)
            obj_but.setEnabled(ib == 2)
            obj_but.setAutoDefault(False)
            obj_but.setFixedHeight(cf.but_height)
            obj_but.setStyleSheet(self.border_style)

        # sets the control button properties
        self.cont_button[0].setCheckable(True)

    def set_style_sheets(self):

        pass

    # ---------------------------------------------------------------------------
    # BombCell Solver Functions
    # ---------------------------------------------------------------------------

    def init_bombcell_solver(self, _):

        # initialises the bombcell package
        self.bc_pkg = BombCellPkg.initialize()
        self.bc_pkg_fcn = self.bc_pkg.BombCellFcn

        # creates the bombcell matlab object
        self.bc_pkg_fcn('initBombCell')

        # retrieves the parameter information/groupings
        self.p_map = self.bc_pkg_fcn('getParaField', 'pMap')
        self.p_grp = self.bc_pkg_fcn('getParaField', 'pGrp')
        self.p_fld = self.bc_pkg_fcn('getClassField', 'pFld')

        # other class field initialisations
        self.bc_pkg_fcn('setClassField', 'useSpykit', True)

    def bombcell_init_complete(self):

        # deermines if the experiment is feasible for analysis (exit if not)
        if not self.check_expt_dir():
            # if not, then close the window
            self.close_window(True)
            return

        # case is the experiment is feasible
        self.fspec_edit.setEnabled(True)
        self.fspec_edit.setText(self.expt_dir)
        self.fspec_edit.setToolTip(self.expt_dir)

        # sets up the memory map file
        self.mmap_file = self.expt_dir + "/" + self.mmap_name
        self.create_solver_mmap()

        # intiialises the parameter groups
        self.setup_para_group()
        self.cont_button[0].setEnabled(True)

        # stops and updates the progressbar
        self.is_running = False
        self.init_complete = True
        self.prog_bar.set_progbar_state(False)

    def run_bombcell_solver(self, _):

        # field retrieval
        is_concat = self.main_obj.session_obj.is_concat_run()
        is_per_shank = self.main_obj.session_obj.is_per_shank()
        n_shank_s = self.main_obj.session_obj.get_shank_count() if is_per_shank else 1

        # memory allocation
        bc_data_nw = np.empty((self.n_run, n_shank_s), dtype=object)
        s_info = {
            "iRun": 1,
            "iShank": 1,
            "isConcat": is_concat,
        }

        for i_run in range(self.n_run):
            # updates the run index
            s_info['iRun'] = i_run + 1
            for i_shank in range(n_shank_s):
                # updates the shank index
                s_info['iShank'] = i_shank + 1

                # runs the bombcell solver
                self.bc_pkg_fcn('runCalc', s_info)
                if self.solver_flag[0]:
                    # if successful, stores the results from the solver
                    bc_data_nw[i_run, i_shank] = BombCellSoln(self.bc_pkg_fcn)

                else:
                    # otherwise, exit the loop
                    return

        # stores the data struct within the class
        self.bc_data = bc_data_nw

    def bombcell_solver_complete(self):

        # stops and updates the progressbar
        self.prog_bar.stop_timer()
        self.prog_bar.set_label('Solver Complete')
        self.prog_bar.set_full_prog()

        # resets the button text
        self.cont_button[0].setChecked(False)
        self.cont_button[0].setText('Run Solver')

        # resets the new solution flag
        self.has_bc = True
        self.is_new_soln = True

        # updates the boolean flags
        self.bc_para_c = deepcopy(self.bc_pkg_fcn('getClassField', 'bcPara'))
        self.set_button_props(True)

    # ---------------------------------------------------------------------------
    # Memory Map Functions
    # ---------------------------------------------------------------------------

    def create_solver_mmap(self):

        # creates the memory mapping file
        if not os.path.exists(self.mmap_file):
            with open(self.mmap_file, 'wb') as f:
                f.truncate(1)

        # sets up the memory map
        with open(self.mmap_file, 'r+b') as f:
            self.mmap = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
            self.solver_flag = np.frombuffer(self.mmap, dtype=np.uint8)
            self.solver_flag[0] = np.uint8(0)

    def delete_solver_mmap(self):

        # deletes the file (if it exists)
        if os.path.exists(self.mmap_file):
            os.remove(self.mmap_file)

    # ---------------------------------------------------------------------------
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

    def on_tab_changed(self):

        self.i_tab = self.para_tab.currentIndex()
        self.h_tab_para[self.i_tab].repaint()

    def check_expt_dir(self):

        # field retrieval
        self.n_run = self.main_obj.session_obj.session.get_run_count()
        s_props = self.main_obj.session_obj.session.get_session_props()

        # experimental information dictionary
        exp_info = {
            "exDir": self.expt_dir,
            "nRun": self.n_run,
            "nShank": self.main_obj.session_obj.get_shank_count(),
            "isConcat": self.main_obj.session_obj.is_concat_run(),
            "isPerShank": self.main_obj.session_obj.is_per_shank(),
            "subName": os.path.split(s_props['subject_path'])[1],
            "sesName": s_props["session_name"],
        }

        # runs the experiment folder diagnosis
        expt_ok = self.bc_pkg_fcn('checkExptDir', exp_info)
        if not expt_ok:
            cf.show_error('The specified folder is not a feasible experiment', 'Error!')

        return expt_ok

    def run_solver(self):

        # resets the button state
        self.is_running = self.cont_button[0].isChecked()
        time.sleep(0.05)

        if self.is_running:
            if not self.check_solver_overwrite():
                # if the user cancelled, then exit the function
                self.is_updating = True
                self.cont_button[0].setChecked(False)
                self.is_updating = False

                # exits the function
                return

            # disables the panel properties
            self.set_button_props(False)
            self.cont_button[0].setChecked(True)
            self.cont_button[0].setText('Cancel Solver')

            # updates the progressbar
            self.prog_bar.set_label("Running Solver")
            self.prog_bar.set_progbar_state(True)
            time.sleep(0.1)

            # flag that the solver is running
            self.solver_flag[0] = np.uint8(1)

            # # creates the memory map file
            # self.create_solver_mmap()

            # creates the threadworker object
            self.t_worker = ThreadWorker(self, self.run_bombcell_solver, None)
            self.t_worker.work_finished.connect(self.bombcell_solver_complete)

            # starts the worker object
            self.t_worker.start()

        else:
            # stops the worker
            self.t_worker.force_quit()
            time.sleep(0.01)

            # deletes the memory map file
            self.solver_flag[0] = np.uint8(0)
            self.set_button_props(True, chk_para=True)

            # disables the progressbar fields
            self.prog_bar.set_progbar_state(False)
            self.cont_button[0].setText('Run Solver')

    def set_button_props(self, state, chk_para=False):

        if state:
            # resets the button properties
            if self.has_bc or chk_para:
                self.check_para_reset(self.bc_para_c)
            else:
                self.check_para_reset()

        else:
            # force disable reset button
            self.cont_button[1].setEnabled(False)

        # sets the close window button
        self.cont_button[2].setEnabled(state)

    def reset_para(self):

        # flag that manual updating is taking place
        self.is_updating = True

        # field retrieval
        bc_para = self.bc_pkg_fcn('getClassField', 'bcPara')
        bc_para0 = self.bc_pkg_fcn('getClassField', 'bcPara0')

        for pf, pv0 in bc_para0.items():
            pv = bc_para[pf]
            if (pv0 != pv) and (not np.isnan(pv)):
                # resets the class object parameter values
                self.bc_pkg_fcn('setParaValue', pf, pv0)

                # resets the parameter field
                h_obj = self.para_tab.findChild(QWidget, name=pf)
                if isinstance(h_obj, QCheckBox):
                    # case is a checkbox
                    h_obj.setChecked(bool(pv0))

                elif isinstance(h_obj, QLineEdit):
                    # case is an editbox
                    p_info = self.bc_pkg_fcn('getParaInfo', pf)
                    if p_info['pType'] == 'EditS':
                        # case is a string editbox
                        h_obj.setText(pv0)

                    elif np.isnan(pv0):
                        # case is a NaN value
                        h_obj.setText(str(pv0))

                    else:
                        # case is a numeric editbox
                        h_obj.setText('%g' % int(pv0))

                elif isinstance(h_obj, QComboBox):
                    # case is a combobox
                    h_obj.setCurrentIndex(int(pv0))

        # disables the button
        self.is_updating = False
        self.cont_button[1].setEnabled(False)

    # ---------------------------------------------------------------------------
    # Other Class Event Functions
    # ---------------------------------------------------------------------------

    def closeEvent(self, event):

        if self.can_close:
            # force close
            event.accept()

        else:
            # user confirmed close
            q_str = "Are you sure you want to close the window?"
            u_choice = QMessageBox.question(
                self, 'Confirm Close?', q_str, cf.q_yes_no, cf.q_yes)
            if u_choice == cf.q_yes:
                event.accept()
            else:
                event.ignore()

    # ---------------------------------------------------------------------------
    # Window I/O Functions
    # ---------------------------------------------------------------------------

    def show_window(self):

        # restarts initialisation (if not complete)
        if not self.init_complete:
            self.init_bomb_cell()

        # makes the window visible
        self.setVisible(True)

    def close_window(self, force_close=False):

        if self.is_running:
            # resets the boolean flags
            self.is_running = False

            # stops the progressbar and thread worker
            self.prog_bar.set_progbar_state(False)
            self.t_worker.force_quit()

        if force_close:
            # terminates the package
            if self.bc_pkg is not None:
                # clears/terminates the bombcell matlab object
                self.bc_pkg_fcn('closeBombCell')
                self.bc_pkg.terminate()
                self.bc_pkg = None

            # closes the dialog window
            self.main_obj.bombcell_dlg = None
            self.can_close = True
            self.close()

        else:
            # initialisations
            t_worker = None

            # check if a new solution has been calculated
            if self.is_new_soln:
                # prompt the user if they want to keep the new data
                q_str = 'Do you want to keep the calculated post-processing data?'
                u_choice = QMessageBox.question(self, 'Update Post-Processing Data?', q_str, cf.q_yes_no, cf.q_yes)
                if u_choice == cf.q_yes:
                    # if so, then update the post processing data
                    t_worker = self.main_obj.setup_postprocessing_worker(self.bc_data, True)

                # resets the new solution flag
                self.is_new_soln = False

            # makes the window invisible again
            self.setVisible(False)

            # starts the memory map output thread worker
            if t_worker is not None:
                t_worker.start()

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def check_solver_overwrite(self, chk_para=True):

        if (not self.has_bc):
            # if there is no solution, then continue
            return True

        else:
            # case is there is a solution
            if chk_para:
                # if the parameters have changed, then continue
                if self.check_para_change(self.bc_para_c):
                    return True

            # otherwise, prompt the user to overwrite
            q_str = 'BombCell solution already calculated. Do you want to overwrite?'
            u_choice = QMessageBox.question(self.main_obj, 'Overwrite Folder?', q_str, cf.q_yes_no, cf.q_yes)
            return u_choice == cf.q_yes

    def check_para_reset(self, bc_para0=None):

        # field retrieval
        self.cont_button[1].setEnabled(self.check_para_change(bc_para0))

    def check_para_change(self, bc_para0=None):

        # retrieves the comparison parameter struct (if not provided)
        if bc_para0 is None:
            bc_para0 = self.bc_pkg_fcn('getClassField', 'bcPara0')

        # checks all current/comparison fields
        bc_para = self.bc_pkg_fcn('getClassField', 'bcPara')
        for pf, pv in bc_para0.items():
            if (isinstance(pv,float) and np.isnan(pv)):
                continue

            elif (pf in self.p_str_u):
                continue

            elif (pv != bc_para[pf]):
                return True

        # flag that there is no difference
        return False