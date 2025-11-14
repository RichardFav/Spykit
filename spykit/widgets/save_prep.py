# module import
import os
import functools
from pathlib import Path
from copy import deepcopy

# spike pipeline imports
import spykit.info.preprocess as pp
import spykit.common.common_func as cf
import spykit.common.common_widget as cw

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QWidget, QMessageBox, QGroupBox, QListWidget)

# ----------------------------------------------------------------------------------------------------------------------

"""
    SavePrep: dialog window for selecting recorder for the preprocessed data output
"""

class SavePrep(QDialog):
    # widget dimensions
    x_gap = 5
    width_dlg = 300
    hght_gbox = 300

    # array class fields
    but_str = ['Save Data', 'Cancel']

    def __init__(self, main_obj):
        super(SavePrep, self).__init__(main_obj)

        # input arguments
        self.main_obj = main_obj

        # class widgets
        self.cont_button = []
        self.prep_group = None
        self.para_group = None
        self.prep_list = QListWidget()
        self.button_widget = QWidget()

        # class layouts
        self.main_layout = QVBoxLayout()
        self.prep_layout = QVBoxLayout()
        self.para_layout = QGridLayout()
        self.button_layout = QHBoxLayout()

        # other class fields
        self.pp_steps = self.main_obj.session_obj.get_preprocessing_steps()
        self.pp_data_flds = self.main_obj.session_obj.get_current_prep_data_names()
        self.i_sel_pp = len(self.pp_steps)
        self.user_dir = self.pp_steps[-1]
        self.n_worker = 10

        # initialises the class fields
        self.init_class_fields()
        self.init_prep_group()
        self.init_para_group()
        self.init_cont_buttons()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the dialog window properties
        self.setFixedWidth(self.width_dlg)
        self.setWindowTitle('Default Directory Paths')
        self.setLayout(self.main_layout)
        self.main_layout.setSpacing(self.x_gap)

    def init_prep_group(self):

        # creates the groupbox object
        self.prep_group = QGroupBox("Completed Preprocessing Steps")
        self.prep_group.setLayout(self.prep_layout)
        self.prep_group.setFixedHeight(self.hght_gbox)
        self.prep_group.setFont(cw.font_panel)
        self.main_layout.addWidget(self.prep_group)

        # creates the preprocessed items listbox
        self.prep_layout.addWidget(self.prep_list)
        self.prep_list.setFont(cw.create_font_obj())

        # adds the listbox items
        for pp_s in self.pp_steps:
            self.prep_list.addItem(pp.pp_flds[pp_s])

        # sets the other listbox properties
        self.prep_list.setCurrentRow(self.i_sel_pp - 1)
        self.prep_list.itemClicked.connect(self.prep_list_click)

    def init_para_group(self):

        # creates the groupbox object
        self.para_group = QGroupBox("Completed Preprocessing Steps")
        self.para_group.setLayout(self.para_layout)
        self.para_group.setFont(cw.font_panel)
        self.main_layout.addWidget(self.para_group)

        # creates the label/editbox object
        tl_work = "Worker Count:"
        obj_lbl_work = cw.QLabelEdit(None, tl_work, self.n_worker, font_lbl=cw.font_lbl, name="n_worker")
        self.para_layout.addWidget(obj_lbl_work.obj_lbl, 0, 0)
        self.para_layout.addWidget(obj_lbl_work.obj_edit, 0, 1)
        cb_fcn_nw = functools.partial(self.edit_worker_count, "n_worker")
        obj_lbl_work.connect(cb_fcn_nw)

        # creates the label/editbox object
        tl_dir = "Folder Name:"
        obj_lbl_dir = cw.QLabelEdit(None, tl_dir, self.user_dir, font_lbl=cw.font_lbl, name="user_dir")
        self.para_layout.addWidget(obj_lbl_dir.obj_lbl, 1, 0)
        self.para_layout.addWidget(obj_lbl_dir.obj_edit, 1, 1)
        cb_fcn_fn = functools.partial(self.edit_folder_name, "user_dir")
        obj_lbl_dir.connect(cb_fcn_fn)

    def init_cont_buttons(self):

        # initialisations
        cb_fcn = [self.save_prep_data, self.close_window]

        # sets the button widget/layout properties
        self.main_layout.addWidget(self.button_widget)
        self.button_widget.setLayout(self.button_layout)
        self.button_layout.setSpacing(0)
        self.button_layout.setContentsMargins(0, 0, 0, 0)

        for bs, cb in zip(self.but_str, cb_fcn):
            # creates the control button widgets
            obj_but = cw.create_push_button(None, bs, cw.font_lbl)
            self.button_layout.addWidget(obj_but)
            self.cont_button.append(obj_but)

            # sets the slot function
            obj_but.setAutoDefault(False)
            obj_but.clicked.connect(cb)

    # ---------------------------------------------------------------------------
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

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

    def edit_folder_name(self, p_str, h_edit):

        # field retrieval
        nw_val = h_edit.text()

        # determines if the new value is valid
        chk_val = cf.check_edit_string(nw_val)
        if chk_val[1] is None:
            # if so, then update the worker count
            self.user_dir = chk_val[0]

        else:
            # otherwise, reset the previous value
            h_edit.setText(self.user_dir)

    def prep_list_click(self):

        self.i_sel_pp = self.prep_list.currentRow() + 1

    def save_prep_data(self):

        # sets up the output folder name
        s_props = self.main_obj.session_obj.session._s_props
        p_comp = s_props['subject_path'].split('/')
        sub_dir = p_comp[-1]
        ses_dir = s_props['session_name']
        base_dir = '/'.join(p_comp[:-2])
        out_folder = Path(base_dir) / "preprocessed" / sub_dir / ses_dir / self.user_dir

        # retrieves the recording object
        pp_rec = self.main_obj.session_obj.session.get_session_runs(
                    0, "grouped", pp_type=self.pp_data_flds[self.i_sel_pp])

        # outputs the binary file
        pp_rec.save(format="binary", folder=out_folder, n_jobs=self.n_worker, progres_bar=True)

    def close_window(self):

        # closes the dialog window
        self.close()