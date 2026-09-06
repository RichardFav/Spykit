# module import
import os
import re
import numpy as np
from glob import glob
from pathlib import Path
from functools import partial as pfcn

# spykit module imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw

# spikeinterface module imports
import spikeinterface.core as si

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QWidget, QMessageBox, QGroupBox, QListWidget, QFrame)

# ----------------------------------------------------------------------------------------------------------------------

"""
    LoadPrepGroup: dialog window for for loading saved preprocessed data
"""

class LoadPrepGroup(object):
    # regular expression fields
    r_run = re.compile(r'run-[0-9]{3}_g0_imec0')
    r_shank = re.compile(r'shank_[0-9]')

    def __init__(self, pp_path0, is_concat):
        super(LoadPrepGroup, self).__init__()

        # sets the run count/indices
        self.is_concat = is_concat
        if self.is_concat:
            # case is a concatenated expt
            self.n_run, r_type = 1, 'Concatenated Run'
            ii_r = np.zeros(len(pp_path0), dtype=int)

        else:
            # case is a non-concatenated expt
            run_name, ii_r = np.unique([self.r_run.findall(str(x)) for x in pp_path0], return_inverse=True)
            self.n_run, r_type = len(run_name), 'Separate Run'

        # sets the shank count/indices
        if pp_path0[0].name.startswith('shank_'):
            # case is a multi-shank expt
            self.is_per_shank = True
            shank_name, ii_s = np.unique([self.r_shank.findall(str(x)) for x in pp_path0], return_inverse=True)
            self.n_shank, s_type = len(shank_name), 'Separate Shank'

        else:
            # case is a grouped shank expt
            self.is_per_shank = False
            self.n_shank, s_type = 1, 'Grouped Shank'
            ii_s = np.zeros(len(pp_path0), dtype=int)

        # sets the preprocessing data folders
        self.pp_path = np.empty((self.n_run, self.n_shank), dtype=object)
        for i_row, i_col, pp_0 in zip(ii_r, ii_s, pp_path0):
            self.pp_path[i_row, i_col] = pp_0

        # other class fields
        self.pp_type = f"{r_type}/{s_type}"

    def get_field(self, p_fld):

        match p_fld:
            case 'n_run':
                # case is the shank count
                if self.is_concat:
                    return 'Concatenated'
                else:
                    return str(self.n_run)

            case 'n_shank':
                # case is the shank count
                if self.is_per_shank:
                    return str(self.n_shank)
                else:
                    return 'Grouped'

# ----------------------------------------------------------------------------------------------------------------------

"""
    LoadPrep: dialog window for for loading saved preprocessed data
"""

class LoadPrep(QDialog):
    # widget dimensions
    x_gap = 5
    width_dlg = 380
    hght_gbox = 150
    hght_button_frame = 40

    # string class fields
    info_type = ['n_run', 'n_shank']
    info_str = ['Run Count', 'Shank Count']
    load_str = ['Load Data', 'Cancel Data Load']
    cc_path = os.path.join('ephys', 'concat_run')

    # widget stylesheets
    border_style = "border: 1px solid;"
    frame_style = QFrame.Shape.Box | QFrame.Shadow.Plain
    frame_border_style = """
        QFrame#loadFrame {
            border: 1px solid;
        }
    """

    def __init__(self, sp_main):
        super(LoadPrep, self).__init__(sp_main)

        # field retrieval
        self.session_obj = self.parent().session_obj

        # class layouts
        self.main_layout = QVBoxLayout()
        self.prep_layout = QVBoxLayout()
        self.info_layout = QHBoxLayout()
        self.button_layout = QHBoxLayout()

        # container class widgets
        self.prep_group = QGroupBox("Preprocessed Datasets")
        self.info_frame = QFrame(self)
        self.button_frame = QFrame(self)

        # other class widgets
        self.prep_list = QListWidget()
        self.info_lbls = []
        self.cont_button = []

        # other class fields
        self.pp_obj = []
        self.i_sel_pp = 0

        # initialises the class fields/objects
        self.init_class_fields()
        self.init_prep_group()
        self.init_info_group()
        self.init_cont_buttons()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # determines the
        deriv_path = self.session_obj.setup_folder_path()
        search_path = os.path.join("**", 'preprocessing', '**', 'properties')
        pp_path = np.array([folder.parent for folder in deriv_path.rglob(search_path) if folder.is_dir()])

        # sets up the preprocessed load objects
        is_concat = np.array([(self.cc_path in str(x)) for x in pp_path])
        for is_c in np.unique(is_concat):
            ii_c = is_concat == is_c
            self.pp_obj.append(LoadPrepGroup(pp_path[ii_c], is_c))

        # sets the dialog window properties
        self.setFixedWidth(self.width_dlg)
        self.setWindowTitle('Preprocessed Data Load')
        self.setLayout(self.main_layout)
        self.main_layout.setSpacing(self.x_gap)

        # resets the frame object names
        for qf in self.findChildren(QFrame):
            qf.setObjectName('loadFrame')

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
        for i_pp, pp_s in enumerate(self.pp_obj):
            pp_lbl = f'Dataset #{i_pp + 1} ({pp_s.pp_type})'
            self.prep_list.addItem(pp_lbl)

        # sets the other listbox properties
        self.prep_list.setCurrentRow(self.i_sel_pp)
        self.prep_list.itemClicked.connect(self.prep_list_click)

    def init_info_group(self):

        # field retrieval
        txt_font = cw.create_font_obj(size=9)

        # sets the frame/layout properties
        self.main_layout.addWidget(self.info_frame)
        self.info_frame.setContentsMargins(0, self.x_gap, 0, self.x_gap)
        self.info_frame.setLayout(self.info_layout)
        self.info_frame.setStyleSheet(self.frame_border_style)
        self.info_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout.setSpacing(self.x_gap)

        for i_s, i_t, pp in zip(self.info_str, self.info_type, self.pp_obj):
            # creates the text label widget
            info_val = pp.get_field(i_t)
            txt_lbl_nw = cw.QLabelText(
                None, f'{i_s}: ', info_val, font_lbl=cw.font_lbl, font_txt=txt_font, name=i_t)

            # adds the widget
            self.info_layout.addWidget(txt_lbl_nw)
            self.info_lbls.append(txt_lbl_nw)

    def init_cont_buttons(self):

        # initialisations
        but_str = [self.load_str[0], 'Close Window']
        cb_fcn = [self.load_button_click, self.close_window_click]

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
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

    def prep_list_click(self):

        # updates the selected preprocessed dataset
        self.i_sel_pp = self.prep_list.currentRow()

        # updates the text labels
        for i_lbl in self.info_lbls:
            p_val = self.pp_obj[self.i_sel_pp].get_field(i_lbl.objectName())
            i_lbl.set_label(p_val)

    def load_button_click(self):

        pass

    def close_window_click(self):

        # closes the dialog window
        self.close()

    # ---------------------------------------------------------------------------
    # Preprocessing Data Load Methods
    # ---------------------------------------------------------------------------

    def load_prep_data(self):

        # field retrieval
        folder_path_fcn = self.session_obj.setup_folder_path
        i_run = range(1) if self.is_concat_run else range(len(self.run_names))

        for i_run in n_run:
            if self.is_per_shank:
                # case is single shank recording
                for i_shank in range(self.n_shank):
                    # sets up the input folder
                    in_folder = self.folder_path_fcn(
                        s_type='preprocessing',
                        is_concat_run=self.is_concat_run,
                        i_run=i_run,
                        i_shank=i_shank
                    )

            else:
                # case is single shank recording

                # sets up the input folder
                in_folder = self.folder_path_fcn(
                    s_type='preprocessing',
                    is_concat_run=self.is_concat_run,
                    i_run=i_run,
                )