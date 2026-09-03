# module import
import os
import time
from pathlib import Path
from copy import deepcopy
from functools import partial as pfcn

# spykit module imports
import spykit.info.preprocess as pp
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.threads.utils import SavePrepThreadWorker

# spikeinterface module imports
import spikeinterface.core as si

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QWidget, QMessageBox, QGroupBox, QListWidget, QFrame)

# ----------------------------------------------------------------------------------------------------------------------

"""
    SavePrep: dialog window for selecting recorder for the preprocessed data output
"""

class SavePrep(QDialog):
    # widget dimensions
    x_gap = 5
    width_dlg = 400
    hght_gbox = 150
    hght_button_frame = 40

    # array class fields
    save_str = ['Save Data', 'Cancel Data Save']

    # widget styles/stylesheets
    border_style = "border: 1px solid;"
    frame_style = QFrame.Shape.Box | QFrame.Shadow.Plain
    frame_border_style = """
        QFrame#saveFrame {
            border: 1px solid;
        }
    """

    def __init__(self, sp_main):
        super(SavePrep, self).__init__(sp_main)

        # input arguments
        self.sp_main = sp_main
        self.session_obj = self.sp_main.session_obj

        # class layouts
        self.main_layout = QVBoxLayout()
        self.prep_layout = QVBoxLayout()
        self.para_layout = QGridLayout()
        self.progress_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        # container class widgets
        self.prep_group = QGroupBox("Completed Preprocessing Steps")
        self.para_group = QGroupBox("Output Parameters")
        self.progress_frame = QFrame(self)
        self.button_frame = QFrame(self)

        # other class widgets
        self.prep_list = QListWidget()
        self.prog_bar = cw.QDialogProgress(font=cw.font_lbl, is_task=True, timer_lbl=True)
        self.cont_button = []

        # field retrieval
        self.pp_steps = self.session_obj.get_preprocessing_steps()
        self.pp_data_flds = self.session_obj.get_current_prep_data_names()
        self.out_run = self.session_obj.get_current_run_index()
        self.run_names = self.session_obj.session.get_run_names()
        self.n_shank = self.session_obj.get_shank_count()

        # boolean class fields
        self.is_running = False
        self.is_updating = False
        self.is_per_shank = self.session_obj.is_per_shank
        self.is_concat_run = self.session_obj.is_concat_run()

        # other class fields
        self.n_worker = 10
        self.t_worker = None
        self.i_sel_pp = len(self.pp_steps)
        self.folder_path_fcn = self.session_obj.setup_folder_path

        # initialises the class fields
        self.init_class_fields()
        self.init_prep_group()
        self.init_para_group()
        self.init_progress_frame()
        self.init_cont_buttons()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the dialog window properties
        self.setFixedWidth(self.width_dlg)
        self.setWindowTitle('Preprocessed Data Output')
        self.setLayout(self.main_layout)
        self.main_layout.setSpacing(self.x_gap)

        # resets the frame object names
        for qf in self.findChildren(QFrame):
            qf.setObjectName('saveFrame')

    def init_prep_group(self):

        # creates the groupbox object
        self.prep_group.setLayout(self.prep_layout)
        self.prep_group.setFixedHeight(self.hght_gbox)
        self.prep_group.setFont(cw.font_panel)
        self.main_layout.addWidget(self.prep_group)

        # creates the preprocessed items listbox
        self.prep_layout.addWidget(self.prep_list)
        self.prep_list.setFont(cw.create_font_obj(size=9))

        # adds the listbox items
        for pp_s in self.pp_steps:
            self.prep_list.addItem(pp.pp_flds[pp_s])

        # sets the other listbox properties
        self.prep_list.setCurrentRow(self.i_sel_pp - 1)
        self.prep_list.itemClicked.connect(self.prep_list_click)

    def init_para_group(self):

        # creates the groupbox object
        self.para_group.setLayout(self.para_layout)
        self.para_group.setFont(cw.font_panel)
        self.main_layout.addWidget(self.para_group)

        # creates the label/editbox object
        tl_work = "Worker Count:"
        obj_lbl_work = cw.QLabelEdit(None, tl_work, self.n_worker, font_lbl=cw.font_lbl, name="n_worker")
        self.para_layout.addWidget(obj_lbl_work.obj_lbl, 0, 0)
        self.para_layout.addWidget(obj_lbl_work.obj_edit, 0, 1)
        cb_fcn_nw = pfcn(self.edit_worker_count, "n_worker")
        obj_lbl_work.connect(cb_fcn_nw)

    def init_progress_frame(self):

        # sets the frame/layout properties
        self.main_layout.addWidget(self.progress_frame)
        self.progress_frame.setContentsMargins(0, 0, 0, 0)
        self.progress_frame.setLayout(self.progress_layout)
        self.progress_frame.setStyleSheet(self.frame_border_style)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(0)

        # creates the progressbar widgets
        self.prog_bar.set_enabled(False)
        self.prog_bar.setContentsMargins(self.x_gap, self.x_gap, self.x_gap, self.x_gap)
        self.prog_bar.lbl_obj.setContentsMargins(0, 2 * (self.x_gap - 1), 0, 0)
        self.progress_layout.addWidget(self.prog_bar)

    def init_cont_buttons(self):

        # initialisations
        but_str = [self.save_str[0], 'Close Window']
        cb_fcn = [self.start_button_click, self.close_window]

        # creates the button group frame
        self.main_layout.addWidget(self.button_frame)

        # sets the button frame properties
        self.button_frame.setContentsMargins(self.x_gap, self.x_gap, self.x_gap, self.x_gap)
        self.button_frame.setLayout(self.button_layout)
        self.button_frame.setStyleSheet(self.frame_border_style)
        # self.button_frame.setFixedHeight(self.hght_button_frame)

        # button group layout properties
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(self.x_gap)

        for bs, cb in zip(but_str, cb_fcn):
            # creates the control button widgets
            obj_but = cw.create_push_button(None, bs, cw.font_lbl)
            self.button_layout.addWidget(obj_but)
            self.cont_button.append(obj_but)

            # sets the button properties
            obj_but.pressed.connect(cb)
            obj_but.setFixedHeight(cf.but_height)
            obj_but.setStyleSheet(self.border_style)
            obj_but.setAutoDefault(False)

        # sets the control button properties
        self.cont_button[0].setCheckable(True)

    # ---------------------------------------------------------------------------
    # Preprocessing Data Output Methods
    # ---------------------------------------------------------------------------

    def setup_save_prep_data_worker(self):

        # creates the threadworker object
        self.t_worker = SavePrepThreadWorker(self.sp_main, self.save_prep_data, None)
        self.t_worker.work_finished.connect(self.save_prep_data_complete)

        # starts the worker object
        self.t_worker.start()

    @staticmethod
    def save_prep_data(pp_rec):

        # field retrieval
        n_run = range(1) if self.is_concat_run else range(len(self.run_names))

        # outputs the preprocessed data for all specified experimental runs
        for i_run in n_run:
            if self.is_per_shank:
                for i_shank in range(self.n_shank):
                    # sets up the output folder
                    out_folder = self.folder_path_fcn(
                        s_type='preprocessing',
                        is_concat_run=self.is_concat_run,
                        i_run=i_run,
                        i_shank=i_shank
                    )

                    # retrieves the recording object
                    run_type = "shank_{0}".format(i_shank)
                    pp_rec = self.session_obj.session.get_session_runs(
                        i_run, run_type, self.pp_data_flds[self.i_sel_pp], i_shank)

                    # out_folder_json = out_folder / "provenance.json"
                    # pp_data = si.load(out_folder_json, relative_paths=False, base_folder=out_folder)
                    # a = 1

                    # outputs the binary file
                    pp_rec.save(
                        format="binary",
                        folder=out_folder,
                        n_jobs=self.n_worker,
                        progres_bar=True,
                        overwrite=True
                    )

            else:
                # sets up the output folder
                out_folder = self.folder_path_fcn(
                    s_type='preprocessing',
                    is_concat_run=self.is_concat_run,
                    i_run=i_run,
                )

                # retrieves the recording object
                pp_rec = self.session_obj.session.get_session_runs(
                            i_run, "grouped", self.pp_data_flds[self.i_sel_pp])

                # outputs the binary file
                pp_rec.save(
                    format="binary",
                    folder=out_folder,
                    n_jobs=self.n_worker,
                    progres_bar=True,
                    overwrite=True
                )

        return []

    def save_prep_data_complete(self, save_flag):

        # stops and updates the progressbar
        self.prog_bar.stop_timer()

        if len(save_msg):
            # Finish Me!
            pass

        else:
            # resets the progressbar
            self.prog_bar.set_label('Data Save Complete')
            self.prog_bar.set_full_prog()

        # resets the other properties
        self.set_dialog_props(True)

    # ---------------------------------------------------------------------------
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

    def prep_list_click(self):

        self.i_sel_pp = self.prep_list.currentRow() + 1

    def edit_worker_count(self, p_str, h_edit):

        # field retrieval
        nw_val = h_edit.text()

        # determines if the new value is valid
        chk_val = cf.check_edit_num(nw_val, min_val=1, max_val=20, is_int=True)
        if chk_val[1] is None:
            # if so, then update the worker count
            self.n_worker = chk_val[0]

        else:
            # otherwise, reset the previous value
            h_edit.setText('%g' % self.n_worker)

    def start_button_click(self):

        # if manually updating, then exit
        if self.is_updating:
            return

        # resets the button state
        time.sleep(0.05)

        if self.is_running:
            # disables the progressbar fields
            self.prog_bar.set_progbar_state(False)

            # resets the other properties
            self.set_dialog_props(True)

            # stops the worker
            self.t_worker.force_quit()
            time.sleep(0.01)

        else:
            # disables the panel properties
            self.set_dialog_props(False)
            self.cont_button[0].setChecked(True)

            # updates the progressbar
            self.prog_bar.set_label("Saving Data")
            self.prog_bar.set_progbar_state(True)
            time.sleep(0.1)

            # saves the preprocessing data
            self.setup_save_prep_data_worker()

        self.is_running ^= True

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_dialog_props(self, state):

        # sets the close button properties
        self.prep_group.setEnabled(state)
        self.para_group.setEnabled(state)
        self.cont_button[1].setEnabled(state)
        self.cont_button[0].setText(self.save_str[not state])

        # pause for update...
        time.sleep(0.01)

    def close_window(self):

        # closes the dialog window
        self.close()