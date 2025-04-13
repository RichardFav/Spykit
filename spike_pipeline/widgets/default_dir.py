# module import
import os
import pickle
import functools
from pathlib import Path
from copy import deepcopy

# spike pipeline imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox)

# ----------------------------------------------------------------------------------------------------------------------

"""
    DefaultDir: dialog window that provides the means for users to set
                the default directory paths
"""


class DefaultDir(QDialog):
    # widget dimensions
    x_gap = 5
    width_dlg = 600

    # array class fields
    grp_str = ['session', 'trigger', 'configs']
    but_str = ['Update Defaults', 'Reset Defaults', 'Close Window']

    # group mapping fields
    grp_map = {
        "session": "Experiment Session Files",
        "trigger": "Trigger Channel Files",
        "configs": "Preprocessing Configuration Files",
    }

    def __init__(self, main_obj):
        super(DefaultDir, self).__init__(main_obj)

        # input arguments
        self.main_obj = main_obj

        # class widgets
        self.cont_button = []
        self.button_widget = QWidget()

        # class layouts
        self.main_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        # other class fields
        self.def_path = {}
        self.def_path0 = {}

        # boolean class fields
        self.is_change = False

        # initialises the class fields
        self.load_prop_file()
        self.init_class_fields()
        self.init_cont_buttons()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def load_prop_file(self):

        if os.path.exists(cw.def_file):
            # loads the default directory path folders
            with open(cw.def_file, 'rb') as f:
                self.def_path = pickle.load(f)

            # exits the function
            return

        # sets the default directory paths
        for gs in self.grp_str:
            # sets up the default directory path
            self.def_path[gs] = Path(os.path.join(cw.resource_dir, gs))

            # ensures the folders exist
            if not os.path.exists(self.def_path[gs]):
                self.def_path[gs].mkdir(parents=True, exist_ok=True)

        # saves the default directory file
        self.save_def_file()

    def init_class_fields(self):

        # sets the dialog window properties
        self.setFixedWidth(self.width_dlg)
        self.setWindowTitle('Default Directory Paths')
        self.setLayout(self.main_layout)
        self.main_layout.setSpacing(self.x_gap)

        # creates the groupboxes
        for gs in self.grp_str:
            # creates the file spec object
            grp_name = self.grp_map[gs]
            file_name = str(self.def_path[gs]).replace('\\', '/')
            obj_file_spec = cw.QFileSpec(None, grp_name, file_name, name=gs)
            self.main_layout.addWidget(obj_file_spec)

            # sets up the slot functions
            cb_fcn = functools.partial(self.button_file_spec, gs)
            obj_file_spec.connect(cb_fcn)

        # other initialisations
        self.def_path0 = deepcopy(self.def_path)

    def init_cont_buttons(self):

        # initialisations
        cb_fcn = [self.update_default, self.reset_default, self.close_window]

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
            obj_but.clicked.connect(cb)

        # disables the update/reset buttons
        self.update_cont_button_props(False)

    # ---------------------------------------------------------------------------
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

    def button_file_spec(self, p_str, obj_file_spec):

        # file dialog properties
        f_path = str(self.def_path[p_str])
        caption = 'Select {0} File'.format(self.grp_map[p_str])

        # runs the file dialog
        file_dlg = cw.FileDialogModal(caption=caption, f_directory=f_path, dir_only=True)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # if the user accepted, then reset the default path field
            def_path_new = file_dlg.selectedFiles()[0].replace('\\', '/')
            obj_file_spec.h_edit.setText(def_path_new)
            self.def_path[p_str] = Path(def_path_new)

            # flag that there is an outstanding change
            self.is_change = self.def_path != self.def_path0

            # enables the update/reset buttons
            self.update_cont_button_props(self.is_change)

    def update_default(self):

        # re-saves the default directory file
        self.save_def_file()

        # disables the update/reset buttons
        self.is_change = False
        self.update_cont_button_props(False)

    def reset_default(self):

        # resets the fields
        for gs in self.grp_str:
            if self.def_path[gs] != self.def_path0[gs]:
                h_edit = self.findChild(cw.QLineEdit, name=gs)
                f_path0 = str(self.def_path0[gs]).replace('\\', '/')
                h_edit.setText(f_path0)

        # resets the default path
        self.def_path = deepcopy(self.def_path0)

        # disables the update/reset buttons
        self.is_change = False
        self.update_cont_button_props(False)

    def close_window(self):

        if self.is_change:
            # prompts the user if they want to update the outstanding changes
            q_str = 'Do you want to update the outstanding changes?'
            u_choice = QMessageBox.question(self, 'Update Changes?', q_str, cf.q_yes_no_cancel, cf.q_yes)

            match u_choice:
                case cf.q_cancel:
                    # case is the user cancelled
                    return

                case cf.q_yes:
                    # case is the user chose to update
                    self.update_default(False)

        # closes the dialog window
        self.close()

    def save_def_file(self):

        # outputs the default property to file
        with open(cw.def_file, 'wb') as f:
            pickle.dump(self.def_path, f)

    def update_cont_button_props(self, state):

        self.cont_button[0].setEnabled(state)
        self.cont_button[1].setEnabled(state)