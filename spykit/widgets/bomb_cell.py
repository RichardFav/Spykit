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

    def __init__(self, t_str, main_obj, p_tab):
        super(BombCellInfoTab, self).__init__(t_str, main_obj, layout=QFormLayout)

        # sets the input arguments
        self.main_obj = main_obj
        self.p_tab = p_tab

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
    BombCellSolver: dialog window for running the BombCell solver
"""

class BombCellSolver(QDialog):
    # widget dimensions
    x_gap = 5
    width_dlg = 400
    hght_fspec = 50
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

    def __init__(self, main_obj):
        super(BombCellSolver, self).__init__(main_obj)

        # input arguments
        self.main_obj = main_obj

        # class widgets
        self.h_tab_para = []
        self.cont_button = []
        self.fspec_group = cw.QFileSpec(None, "EXPERIMENT PARENT FOLDER", "")
        self.para_group = QGroupBox("SOLVER PARAMETERS")
        self.progress_frame = QFrame()
        self.button_frame = QFrame()
        self.para_tab = cw.create_tab_group(None)
        self.prog_bar = cw.QDialogProgress(font=cw.font_lbl, is_task=True, timer_lbl=True)

        # class layouts
        self.main_layout = QVBoxLayout()
        self.fspec_layout = QHBoxLayout()
        self.para_layout = QVBoxLayout()
        self.progress_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        # boolean class fields
        self.has_bc = False
        self.is_updating = False
        self.is_running = False
        self.can_close = False

        # folder/file path fields
        self.mmap_file = None

        # other class fields
        self.i_tab = 0
        self.bc_para_c = None
        self.solver_flag = None
        self.hght_dlg = 6 * self.x_gap + (self.hght_fspec + self.hght_para + self.hght_button)

        # initialises the class fields
        self.init_bomb_cell()
        self.init_class_fields()
        self.init_fspec_group()
        self.init_para_group()
        self.init_progress_frame()
        self.init_cont_buttons()

        # sets the widget style sheets
        self.set_style_sheets()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_bomb_cell(self):

        # initialises the bombcell package
        self.bc_pkg = BombCellPkg.initialize()
        self.bc_pkg.BombCellFcn('initBombCell')

        # retrieves the parameter information/groupings
        self.p_map = self.bc_pkg.BombCellFcn('getParaField', 'pMap')
        self.p_grp = self.bc_pkg.BombCellFcn('getParaField', 'pGrp')
        self.p_fld = self.bc_pkg.BombCellFcn('getClassField', 'pFld')

    def init_class_fields(self):

        # sets the dialog window properties
        self.setFixedSize(self.width_dlg, self.hght_dlg)
        self.setWindowTitle('BombCell Solver')
        self.setLayout(self.main_layout)

        self.main_layout.addWidget(self.fspec_group)
        self.main_layout.addWidget(self.para_group)
        self.main_layout.addWidget(self.progress_frame)
        self.main_layout.addWidget(self.button_frame)

    def init_fspec_group(self):

        # creates the groupbox object
        self.fspec_group.setLayout(self.fspec_layout)
        self.fspec_group.setFont(cw.font_panel)
        self.fspec_group.setFixedHeight(self.hght_fspec)

        # sets up the slot functions
        self.fspec_group.connect(self.button_file_spec)

    def init_para_group(self):

        # creates the groupbox object
        self.para_group.setLayout(self.para_layout)
        self.para_group.setFont(cw.font_panel)

        # adds the tab object to the parmaeter layout
        self.para_layout.addWidget(self.para_tab)

        # resets the channel table style
        tab_style = cw.CheckBoxStyle(self.para_tab.style())
        self.para_tab.setStyle(tab_style)

        # creates the tab objects
        for ts, p_tab in self.p_grp.items():
            #
            tab_widget = BombCellInfoTab(ts, self, p_tab)
            self.para_tab.addTab(tab_widget, ts)
            self.h_tab_para.append(tab_widget)

        # tab change callback function
        self.para_tab.currentChanged.connect(self.on_tab_changed)
        self.para_group.setEnabled(False)

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

    def run_solver(self):

        # resets the button state
        self.is_running = self.cont_button[0].isChecked()
        time.sleep(0.05)

        if self.is_running:
            if not self.check_sort_overwrite():
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

            # creates the memory map file
            self.create_solver_mmap()

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
            self.set_button_props(True)

            # disables the progressbar fields
            self.prog_bar.set_progbar_state(False)
            self.cont_button[0].setText('Run Solver')

    def set_button_props(self, state):

        if state:
            # resets the button properties
            if self.has_bc:
                self.check_para_reset(self.bc_para_c)
            else:
                self.check_para_reset()

        else:
            # force disable reset button
            self.cont_button[1].setEnabled(False)

        # sets the close window button
        self.cont_button[2].setEnabled(state)

    def run_bombcell_solver(self, _):

        # starts running the bombcell solver
        self.bc_pkg.BombCellFcn('runCalc')

    def bombcell_solver_complete(self):

        # stops and updates the progressbar
        self.prog_bar.stop_timer()
        self.prog_bar.set_label('Solver Complete')
        self.prog_bar.set_full_prog()

        # resets the button text
        self.cont_button[0].setChecked(False)
        self.cont_button[0].setText('Run Solver')

        # updates the boolean flags
        self.has_bc = True
        self.bc_para_c = deepcopy(self.bc_pkg.BombCellFcn('getClassField', 'bcPara'))
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
            self.solver_flag[0] = np.uint8(1)

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

    def button_file_spec(self, h_fspec):

        # file dialog properties
        f_path = str(cw.get_def_dir("data"))
        caption = 'Set Experimental Data Folder'

        # runs the file dialog
        file_dlg = cw.FileDialogModal(caption=caption, f_directory=f_path, dir_only=True)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # if the user accepted, then check the experiment folder is valid
            def_path_new = file_dlg.selectedFiles()[0].replace('\\', '/')
            expt_ok = self.bc_pkg.BombCellFcn('setExptDir', def_path_new)

            if expt_ok:
                # case is the folder is feasible
                self.fspec_group.h_edit.setText(def_path_new)
                self.fspec_group.h_edit.setToolTip(def_path_new)
                self.cont_button[0].setEnabled(expt_ok)

                for ps in self.p_str_u:
                    h_obj = self.para_group.findChild(QLineEdit, name=ps)
                    f_file = self.bc_pkg.BombCellFcn('getParaValue', ps)
                    f_name = os.path.split(f_file)[1]

                    h_obj.setText(f_name)
                    h_obj.setToolTip(f_file)

                # other field/object updates
                self.para_group.setEnabled(True)
                self.mmap_file = def_path_new + "/" + self.mmap_name

            else:
                # if not, then output an error to screen
                cf.show_error('The specified folder is not a feasible experiment', 'Error!')

        # removes selection from the button
        h_fspec.h_but.setDefault(False)

    def reset_para(self):

        # flag that manual updating is taking place
        self.is_updating = True

        # field retrieval
        bc_para = self.bc_pkg.BombCellFcn('getClassField', 'bcPara')
        bc_para0 = self.bc_pkg.BombCellFcn('getClassField', 'bcPara0')

        for pf, pv0 in bc_para0.items():
            pv = bc_para[pf]
            if (pv0 != pv) and (not np.isnan(pv)):
                # resets the class object parameter values
                self.bc_pkg.BombCellFcn('setParaValue', pf, pv0)

                # resets the parameter field
                h_obj = self.para_tab.findChild(QWidget, name=pf)
                if isinstance(h_obj, QCheckBox):
                    # case is a checkbox
                    h_obj.setChecked(bool(pv0))

                elif isinstance(h_obj, QLineEdit):
                    # case is an editbox
                    p_info = self.bc_pkg.BombCellFcn('getParaInfo', pf)
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

        # makes the window visible
        self.setVisible(True)

    def close_window(self, force_close=False):

        if (self.main_obj is None) or force_close:
            # closes the dialog window
            self.can_close = True
            self.close()

        else:
            # makes the window invisible again
            self.setVisible(False)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def check_sort_overwrite(self):

        if (not self.has_bc):
            # if there is no solution, then continue
            return True

        else:
            # case is there is a solution
            if self.check_para_change(self.bc_para_c):
                # if the parameters have changed, then continue
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
            bc_para0 = self.bc_pkg.BombCellFcn('getClassField', 'bcPara0')

        # checks all current/comparison fields
        bc_para = self.bc_pkg.BombCellFcn('getClassField', 'bcPara')
        for pf, pv in bc_para0.items():
            if (isinstance(pv,float) and np.isnan(pv)):
                continue

            elif (pv != bc_para[pf]):
                return True

        # flag that there is no difference
        return False