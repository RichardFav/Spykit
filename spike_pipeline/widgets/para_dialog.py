# module import
import os
import re
import pickle
import functools
from copy import deepcopy

# custom module import
import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.common_func as cf

# pyqt6 module import
import numpy as np
from PyQt6.QtWidgets import (QMainWindow, QWidget, QGroupBox, QTabWidget, QFormLayout, QCheckBox, QLineEdit,
                             QComboBox, QToolBar, QSizePolicy, QMessageBox, QScrollArea, QDialog, QLabel,
                             QHBoxLayout, QMenuBar)
from PyQt6.QtGui import QFont, QIcon, QAction, QMouseEvent
from PyQt6.QtCore import Qt, QSize

# ----------------------------------------------------------------------------------------------------------------------

# file path/filter modes
f_mode_p = "Spike Pipeline Parameter File (*.spp)"
icon_dir = os.path.join(os.getcwd(), 'resources', 'icons')
icon_path = {'pre_processing': os.path.join(icon_dir, 'pre_processing_icon.png'),
             'general': os.path.join(icon_dir, 'general_icon.png'),
             'reset': os.path.join(icon_dir, 'reset_icon.png'),
             'open': os.path.join(icon_dir, 'open_icon.png'),
             'save': os.path.join(icon_dir, 'save_icon.png'),
             'close': os.path.join(icon_dir, 'close_icon.png'),
             'search': os.path.join(icon_dir, 'search_icon')}

# parameter/resource folder paths
para_dir = os.path.join(os.getcwd(), 'resources', 'parameters').replace('\\', '/')
para_file = os.path.join(para_dir, 'test2.spp').replace('\\', '/')

# widget stylesheets
toolbar_style = """
    QToolBar {
        background-color: white;
        spacing : 1px;
    }
    QToolBar QToolButton{
        color: white;
        font-size : 14px;
    }
"""

gbox_style_on = """
    QGroupBox::title {
        background-color: yellow;
    }
"""

gbox_style_off = """
    QGroupBox::title {
    }
"""

# ----------------------------------------------------------------------------------------------------------------------

# parameters
x_gap = 20

# widget dimensions
hdr_height, dlg_height = 63, 450
dlg_width, grp_width = 900, 200
combo_width, edit_width = 200, 200


class ParaDialog(QMainWindow):
    def __init__(self, p_dict0=None):
        super(ParaDialog, self).__init__()

        # field initialisation
        self.p_info = {}
        self.h_tab_grp = {}
        self.was_reset = False
        self.is_updating = False
        self.p_dict, self.p_dict0 = p_dict0, None

        # sets up the main layout
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        # widget setup
        self.group_scroll = QScrollArea(self)
        self.h_widget_group = QWidget()
        self.group_layout = QFormLayout()
        self.h_widget_para = QWidget(self)
        self.para_layout = QFormLayout()
        self.search_dlg = QSearchWidget()

        # label/header font objects
        self.font_lbl = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold)
        self.font_hdr = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

        # initialises the class fields
        self.init_class_fields()

        # sets up the objects for each parameter group
        for i, p in enumerate(self.p_info):
            self.setup_group_objects(p, i)

        # initialises the group fields
        self.setup_dialog()
        self.setup_toolbar()

        # resets the selected group/parameter index
        self.selected_group = list(self.p_info.keys())[0]
        self.selected_para = list(self.p_info[self.selected_group]['ch_fld'].keys())[0]

        # sets the first group as the parameter tab
        self.para_layout.addWidget(self.h_tab_grp[self.selected_group])
        self.setCentralWidget(self.group_scroll)

        # sets the object style sheets
        self.set_styles()

    # CLASS INITIALISATION FUNCTIONS ------------------------------------------

    def init_class_fields(self):

        # initialises the parameter information fields
        self.setup_para_info_fields()

        if self.p_dict is None:
            # case is the parameter dictionary has not been initialised
            self.init_para_dict_fields()

        else:
            # case is the parameter dictionary is initialised
            self.p_dict0 = deepcopy(self.p_dict)
            self.reset_para_info_value(self.p_info, self.p_dict)

        # sets the group layout properties
        self.group_layout.setSpacing(0)
        self.group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.group_layout.setContentsMargins(0, 0, 0, 0)
        self.h_widget_group.setLayout(self.group_layout)

        # sets the scroll area properties
        self.group_scroll.setWidgetResizable(True)
        self.group_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.group_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.group_scroll.setFixedWidth(grp_width + x_gap)
        self.group_scroll.setWidget(self.h_widget_group)

        # sets the parameter tab layout properties
        self.para_layout.setSpacing(0)
        self.para_layout.setContentsMargins(0, hdr_height, 0, 0)

        # sets the parameter widget properties
        self.h_widget_para.setGeometry(grp_width + x_gap, 0, dlg_width - (x_gap + grp_width), dlg_height + hdr_height)
        self.h_widget_para.setLayout(self.para_layout)

        # sets up the search widget
        self.search_dlg.setFixedWidth(grp_width)
        self.group_layout.addRow(self.search_dlg)

    def setup_dialog(self):

        # creates the dialog window
        self.setFixedSize(dlg_width, dlg_height + hdr_height)
        self.setWindowTitle("SpikeInterface Parameters")

    def setup_toolbar(self):

        # creates the menubar object
        h_menubar = QMenuBar(self)
        self.setMenuBar(h_menubar)
        h_menu_file = h_menubar.addMenu('File')

        # creates the toolbar object
        h_toolbar = QToolBar('ToolBar', self)
        h_toolbar.setMovable(False)
        h_toolbar.setStyleSheet(toolbar_style)
        h_toolbar.setIconSize(QSize(cf.but_height + 1, cf.but_height + 1))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, h_toolbar)
        self.addToolBarBreak()

        # initialisations
        p_str = ['reset', 'open', 'save', None, 'close']
        p_lbl = ['Reset Parameters', 'Open Parameters', 'Save Parameters', None, 'Close Window']
        cb_fcn = [self.menu_reset_para, self.menu_open_para, self.menu_save_para, None, self.close_window]

        # menu/toolbar item creation
        for pl, ps, cbf in zip(p_lbl, p_str, cb_fcn):
            if ps is None:
                # adds separators
                h_toolbar.addSeparator()
                h_menu_file.addSeparator()

            else:
                # creates the menu item
                h_tool = QAction(QIcon(icon_path[ps]), pl, self)
                h_tool.triggered.connect(cbf)
                h_toolbar.addAction(h_tool)

                # creates the menu item
                h_menu = QAction(pl, self)
                h_menu.triggered.connect(cbf)
                h_menu_file.addAction(h_menu)

    def setup_group_objects(self, p, i_tab):

        # retrieves the group properties
        grp_name = self.p_info[p]['name']
        grp_info = self.p_info[p]['ch_fld']

        # creates the collapsible group object
        h_panel_c = cw.QCollapseGroup(self.group_scroll, grp_name, i_tab == 0)
        h_panel_c.connect()

        # adds the subgroups to the
        for ch_grp in grp_info:
            # creates the text links
            h_gap, h_txt = self.create_group_text_link(ch_grp, grp_info[ch_grp]['name'])

            # sets the text label properties
            h_panel_c.add_group_row(h_gap, h_txt)
            self.search_dlg.append_grp_obj(h_txt, ch_grp, grp_info[ch_grp]['name'])

        # readjusts the panel height
        h_panel_c.adjustSize()
        h_panel_c.orig_hght = h_panel_c.size().height()

        self.set_panel_events(h_panel_c)
        self.group_layout.addRow(h_panel_c)

        # sets the collapsible panel object properties
        h_panel_c.setObjectName(p)
        h_panel_c.expand_button.setIcon(QIcon(icon_path[p]))
        h_panel_c.expand_button.setIconSize(QSize(24, 24))
        h_panel_c.expand_button.setFixedHeight(25)

        # creates the tab group
        self.h_tab_grp[p] = cw.create_tab_group(None, name=p)

        # creates the tab objects
        for gn in grp_info:
            # create the tab object
            h_tab = self.create_para_tab(gn, grp_info[gn], p)
            self.h_tab_grp[p].addTab(h_tab, grp_info[gn]['name'])

        # sets the callback function
        cb_fcn = functools.partial(self.para_tab_change, p)
        self.h_tab_grp[p].currentChanged.connect(cb_fcn)

    # COLLAPSIBLE PANEL EVENT FUNCTIONS ---------------------------------------

    def set_panel_events(self, h_panel_c, *_):

        # sets the label click event function
        for h_txt in h_panel_c.findChildren(QLabel):
            h_txt.mousePressEvent = functools.partial(self.link_click, h_txt)

    def link_click(self, h_txt, *_):

        # field retrieval
        h_grpc = cf.get_parent_widget(h_txt, cw.QCollapseGroup)
        p_str_l, p_str_g = h_txt.objectName(), h_grpc.objectName()

        # resets the tab group object (if different group selected)
        if self.selected_group != p_str_g:
            # resets the selected group
            self.swap_para_tab_group(p_str_g)

        # resets the parameter tab
        ch_list = list(self.p_info[p_str_g]['ch_fld'].keys())
        i_tab = ch_list.index(p_str_l)
        self.selected_para = ch_list[i_tab]
        self.h_tab_grp[self.selected_group].setCurrentIndex(i_tab)

    # TOOLBAR/MENUBAR EVENT FUNCTIONS -----------------------------------------

    def menu_reset_para(self):

        # prompts the user if they want to reset all the fields
        u_choice = QMessageBox.question(self, 'Reset Parameters?', "Are you sure you want to reset the parameters?",
                                        cf.q_yes_no, QMessageBox.StandardButton.Yes)
        if u_choice == QMessageBox.StandardButton.No:
            # exit if they cancelled
            return

        # re-initialises the parameter information fields
        self.setup_para_info_fields()
        self.init_para_dict_fields()

        # resets the parameter fields
        self.reset_para_fields(self.p_dict, [], is_init=True)

    def menu_open_para(self):

        # file dialog properties
        f_path = para_dir
        caption = 'Select Parameter File'

        # runs the file dialog
        file_dlg = cw.FileDialogModal(caption=caption, f_filter=f_mode_p, f_directory=f_path)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # if the user didn't cancel, then output the dictionary to file
            file_info = file_dlg.selectedFiles()
            with open(file_info[0], 'rb') as f:
                self.p_dict = pickle.load(f)

            # resets the original dictionary
            self.p_dict0 = deepcopy(self.p_dict)

            # resets the parameter fields
            self.reset_para_fields(self.p_dict, [], is_init=True)

    def menu_save_para(self):

        # file dialog properties
        f_path = para_dir
        caption = 'Set Parameter Filename'

        # prompts the user for the output filename
        file_dlg = cw.FileDialogModal(caption=caption, f_filter=f_mode_p, f_directory=f_path, is_save=True)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # if the user didn't cancel, then output the dictionary to file
            file_info = file_dlg.selectedFiles()
            with open(file_info[0], 'wb') as f:
                pickle.dump(self.p_dict, f)

            # resets the original dictionary
            self.p_dict0 = deepcopy(self.p_dict)

    def close_window(self):

        if (self.p_dict != self.p_dict0) and (self.p_dict0 is not None):
            # if there is a parameter change, then prompt the user if they want to change
            q_str = 'There are outstanding changes which have not been save.\nDo you still want to close the window?'
            u_choice = QMessageBox.question(self, 'Reset Parameters?', q_str, cf.q_yes_no, cf.q_yes)
            if u_choice == QMessageBox.StandardButton.No:
                # exit if they cancelled
                return

        # closes the window
        self.close()

    # WIDGET SETUP FUNCTIONS --------------------------------------------------

    def create_para_tab(self, grp_name, grp_info, sect_name):

        # creates the tab widget
        h_tab = QWidget()
        h_tab.setObjectName(grp_name)

        # creates the children objects for the current parent object
        tab_layout = QFormLayout(h_tab)
        self.create_para_object(tab_layout, grp_name, grp_info, [sect_name, grp_name])

        # returns the tab object
        return h_tab

    def create_para_object(self, layout, p_name, ps, p_str_l):

        match ps['type']:
            # CONTAINER OBJECTS -----------------------------------------------

            # case is a regular panel
            case 'panel':
                # creates the panel object
                h_panel_para = QGroupBox()
                layout.addWidget(h_panel_para)

                # sets the panel properties
                h_panel_para.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

                # creates the tab parameter objects
                layout = QFormLayout(h_panel_para)
                layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

            # case is a checkbox panel
            case 'checkpanel':
                # initialisations
                font_panel = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

                # creates the groupbox widget
                h_panel = QGroupBox(ps['name'])
                h_panel.setCheckable(True)
                h_panel.setFont(font_panel)
                h_panel.setObjectName(p_name)

                # sets the panel event function
                p_fcn = functools.partial(self.group_panel_click, h_panel, p_str_l)
                h_panel.clicked.connect(p_fcn)

                # adds the groupbox panel to the parent object
                layout.addRow(h_panel)
                p_str_l = p_str_l[0:-1]

                # creates the children objects for the current parent object
                layout = QFormLayout()
                layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
                h_panel.setLayout(layout)

                # appends the parameter search
                self.search_dlg.append_para_obj(h_panel, ps['name'], p_str_l[1])

                # self.group_panel_click(h_panel, p_str_l)

            # case is a tabgroup
            case 'tabgroup':
                # creates the tab-group widget
                obj_tab_grp = cw.create_tab_group(None)
                obj_tab_grp.setObjectName(p_name)

                # adds the tab group to the layout
                layout.addRow(obj_tab_grp)

                # creates the tab-objects
                for ps_t in ps['ch_fld']:
                    h_tab = self.create_para_object(None, ps_t, ps['ch_fld'][ps_t], p_str_l + [ps_t])
                    obj_tab_grp.addTab(h_tab, ps['ch_fld'][ps_t]['name'])

                if ps['value'] is not None:
                    h_tab = obj_tab_grp.findChildren(QWidget, ps['value'])[0]
                    obj_tab_grp.setCurrentWidget(h_tab)

                # sets up the slot function
                cb_fcn = functools.partial(self.tab_change, obj_tab_grp, p_str_l)
                obj_tab_grp.currentChanged.connect(cb_fcn)

                # exits the function
                return

            # case is a tab widget
            case 'tab':
                # creates the tab widget
                obj_tab = QWidget()
                obj_tab.setObjectName(p_name)

                # creates the children objects for the current parent object
                t_layout = QFormLayout(obj_tab)
                t_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

                # creates the panel object
                h_panel_tab = QGroupBox()
                t_layout.addWidget(h_panel_tab)

                # sets the panel properties
                h_panel_tab.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

                # creates the tab parameter objects
                layout = QFormLayout(h_panel_tab)
                layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

                # creates the tab parameter objects
                for ps_t in ps['ch_fld']:
                    self.create_para_object(layout, ps_t, ps['ch_fld'][ps_t], p_str_l=p_str_l + [ps_t])

                # sets the tab layout
                obj_tab.setLayout(t_layout)

                # returns the tab object
                return obj_tab

            # OTHER WIDGETS ---------------------------------------------------

            # case is a editbox
            case 'edit':
                # creates the label/editbox widget combo
                obj_lbl = cw.create_text_label(None, '{0}: '.format(ps['name']), font=self.font_lbl)
                obj_edit = cw.create_line_edit(None, '%g' % (ps['value']), name=p_name, align='left')
                layout.addRow(obj_lbl, obj_edit)

                # sets up the label/editbox slot function
                cb_fcn = functools.partial(self.edit_para_change, obj_edit, p_str_l)
                obj_edit.editingFinished.connect(cb_fcn)
                obj_edit.setFixedSize(edit_width, cf.edit_height)
                obj_lbl.setStyleSheet('padding-top: 2 px;')

                # appends the parameter search objects
                self.search_dlg.append_para_obj(obj_lbl, ps['name'], p_str_l[1])

                # self.edit_para_change(obj_edit, p_str_l)

            # case is a combobox
            case 'combobox':
                # creates the label/combobox widget combo
                obj_lbl = cw.create_text_label(None, '{0}: '.format(ps['name']), font=self.font_lbl)
                obj_cbox = cw.create_combo_box(None, ps['p_list'], name=p_name)
                obj_cbox.setCurrentText(ps['value'])
                layout.addRow(obj_lbl, obj_cbox)

                # sets up the slot function
                cb_fcn = functools.partial(self.combobox_para_change, obj_cbox, p_str_l)
                obj_cbox.currentIndexChanged.connect(cb_fcn)
                obj_cbox.setFixedSize(combo_width, cf.combo_height)
                obj_lbl.setStyleSheet('padding-top: 3 px;')

                # appends the parameter search objects
                self.search_dlg.append_para_obj(obj_lbl, ps['name'], p_str_l[1])

                # self.combobox_para_change(obj_cbox, p_str_l)

            # case is a checkbox
            case 'checkbox':
                # creates the checkbox widget
                obj_checkbox = cw.QCheckboxHTML(
                    None, ps['name'], ps['value'], font=self.font_lbl, name=p_name)
                layout.addRow(obj_checkbox)

                # sets up the slot function
                cb_fcn = functools.partial(self.checkbox_para_change, obj_checkbox, p_str_l)
                obj_checkbox.connect(cb_fcn)

                # appends the parameter search objects
                self.search_dlg.append_para_obj(obj_checkbox, ps['name'], p_str_l[1])

                # self.checkbox_para_change(obj_checkbox, p_str_l)

            # case is a file selection widget
            case 'filespec':
                # creates the file selection widget
                obj_fspec = cw.QFileSpec(None, ps['name'], ps['value'], name=p_name, f_mode=ps['p_misc'])
                layout.addRow(obj_fspec)

                # sets up the slot function
                cb_fcn = functools.partial(self.button_file_spec, p_str_l)
                obj_fspec.connect(cb_fcn)

                # appends the parameter search objects
                self.search_dlg.append_para_obj(obj_fspec, ps['name'], p_str_l[1])

                # self.button_file_spec(h_filespec, p_str_l)

        # creates any children objects
        if ps['ch_fld'] is not None:
            for ps_ch in ps['ch_fld']:
                self.create_para_object(layout, ps_ch, ps['ch_fld'][ps_ch], p_str_l=p_str_l + [ps_ch])

    # WIDGET EVENT FUNCTIONS --------------------------------------------------

    def tab_change(self, h_tab_grp, p_str_l):

        # updates the selected tab value
        p_tab_sel = h_tab_grp.currentWidget().objectName()
        cf.set_multi_dict_value(self.p_dict, p_str_l + [p_str_l[-1]], p_tab_sel)

    def para_tab_change(self, p_str):

        self.selected_para = self.h_tab_grp[p_str].currentWidget().objectName()

    def swap_para_tab_group(self, p_str_g):

        # resets the select group flag
        self.h_tab_grp[self.selected_group].setParent(None)
        self.selected_group = p_str_g

        # resets the visible tab group
        self.para_layout.addWidget(self.h_tab_grp[p_str_g])

    def edit_para_change(self, h_edit, p_str_l):

        # field retrieval
        nw_val = h_edit.text()

        # determines if the new value is valid
        chk_val = cf.check_edit_num(nw_val, min_val=0)
        if chk_val[1] is None:
            # if so, updates the parameter field
            cf.set_multi_dict_value(self.p_dict, p_str_l, chk_val[0])

        else:
            # resets the update flag
            self.was_reset = True

            # otherwise, reset the previous value
            p_val = cf.get_multi_dict_value(self.p_dict, p_str_l)
            h_edit.setText('%g' % p_val)

    def combobox_para_change(self, h_combo, p_str_l):

        # field retrieval
        p_val = h_combo.currentText()

        # updates the parameter dictionary
        cf.set_multi_dict_value(self.p_dict, p_str_l, p_val)

    def checkbox_para_change(self, h_check, p_str_l, evnt=None):

        # if manually updating, then exit
        if self.is_updating:
            return

        # field retrieval
        if isinstance(evnt, QMouseEvent):
            # case is updating from the label
            p_val = h_check.h_chk.isChecked() ^ True

            # resets the checkbox mark
            self.is_updating = True
            h_check.h_chk.setChecked(p_val)
            self.is_updating = False

        else:
            # case is updating from the checkbox
            p_val = h_check.h_chk.isChecked()

        # updates the parameter dictionary
        cf.set_multi_dict_value(self.p_dict, p_str_l, p_val)

    def button_file_spec(self, p_str_l, h_fspec):

        # file dialog properties
        dir_only = h_fspec.f_mode is None
        caption = 'Select Directory' if dir_only else 'Select File'
        f_path = cf.get_multi_dict_value(self.p_dict, p_str_l)

        # runs the file dialog
        file_dlg = cw.FileDialogModal(caption=caption, dir_only=dir_only, f_filter=h_fspec.f_mode, f_directory=f_path)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # if the user accepted, then update the parameter/widget fields
            file_info = file_dlg.selectedFiles()
            cf.set_multi_dict_value(self.p_dict, p_str_l, file_info[0])
            h_fspec.h_edit.setText(file_info[0])

    def group_panel_click(self, h_panel, p_str_l):

        # field retrieval
        is_chk = h_panel.isChecked()

        # updates the parameter dictionary
        cf.set_multi_dict_value(self.p_dict, p_str_l, is_chk)

        # updates the object enabled flags
        for h_child in h_panel.children():
            if hasattr(h_child, 'setEnabled'):
                h_child.setEnabled(is_chk)

    # PARAMETER FIELD FUNCTIONS -----------------------------------------------

    def setup_para_info_fields(self):

        # PRE-PROCESSING OBJECTS ----------------------------------------------

        # subgroup properties
        pp_str = ['phase_shift', 'bandpass_filter', 'common_reference', 'whitening', 'drift_correct', 'sorting']
        pp_hdr = ['Phase Shift', 'Bandpass Filter', 'Common Reference', 'Whitening', 'Drift Correction', 'Sorting']
        pp_type = ['panel', 'panel', 'panel', 'panel', 'panel', 'tabgroup']

        # sets up the subgroup fields
        p_tmp = {}
        for pp_s, pp_h, pp_t in zip(pp_str, pp_hdr, pp_type):
            p_tmp[pp_s] = self.create_para_field(pp_h, pp_t, None)

        # phase shift parameters
        p_tmp[pp_str[0]]['ch_fld'] = {
            'margin_ms': self.create_para_field('Margin (ms)', 'edit', 40),
        }

        # bandpass filter parameters
        p_tmp[pp_str[1]]['ch_fld'] = {
            'freq_min': self.create_para_field('Min Frequency', 'edit', 300),
            'freq_max': self.create_para_field('Max Frequency', 'edit', 6000),
            'margin_ms': self.create_para_field('Border Margin (ms)', 'edit', 5),
        }

        # common reference parameters
        operator_list = ['median', 'average']
        reference_list = ['global', 'single', 'local']
        p_tmp[pp_str[2]]['ch_fld'] = {
            'operator': self.create_para_field('Operator', 'combobox', operator_list[0], p_list=operator_list),
            'reference': self.create_para_field('Reference', 'combobox', reference_list[0], p_list=reference_list),
        }

        # whitening parameters
        mode_list = ['global', 'local']
        p_tmp[pp_str[3]]['ch_fld'] = {
            'apply_mean': self.create_para_field('Subtract Mean', 'checkbox', False),
            'mode': self.create_para_field('Mode', 'combobox', mode_list[0], p_list=mode_list),
            'radius_um': self.create_para_field('Reference Radius (um)', 'edit', 100),
        }

        # drift correction parameters
        preset_list = ['dredge', 'dredge_fast', 'nonrigid_accurate',
                       'nonrigid_fast_and_accurate', 'rigid_fast', 'kilosort_like']
        p_tmp[pp_str[4]]['ch_fld'] = {
            'preset': self.create_para_field('Preset', 'combobox', preset_list[0], p_list=preset_list),
        }

        # sets up the sorting tab parameter fields
        pp_k2 = {'car': self.create_para_field('Use Common Avg Reference', 'checkbox', False, p_fld='kilosort2'),
                 'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2')}
        pp_k2_5 = {'car': self.create_para_field('Use Common Avg Reference', 'checkbox', False, p_fld='kilosort2_5'),
                   'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2_5'), }
        pp_k3 = {'car': self.create_para_field('Use Common Avg Reference', 'checkbox', False, p_fld='kilosort3'),
                 'freq_min': self.create_para_field('Min Frequency', 'edit', 300, p_fld='kilosort3'), }
        pp_m5 = {'scheme': self.create_para_field('Scheme', 'edit', 2, p_fld='mountainsort5'),
                 'filter': self.create_para_field('Filter', 'checkbox', False, p_fld='mountainsort5'), }

        # sets the sorting tab group parameter fields
        p_tmp[pp_str[5]]['ch_fld'] = {
            'kilosort2': self.create_para_field('Kilosort 2', 'tab', None, ch_fld=pp_k2),
            'kilosort2_5': self.create_para_field('Kilosort 2.5', 'tab', None, ch_fld=pp_k2_5),
            'kilosort3': self.create_para_field('Kilosort 3', 'tab', None, ch_fld=pp_k3),
            'mountainsort5': self.create_para_field('Mountainsort 5', 'tab', None, ch_fld=pp_m5),
        }

        # updates the class field
        self.p_info['pre_processing'] = {'name': 'Pre-Processing', 'type': 'group', 'ch_fld': p_tmp}

        # PRE-PROCESSING OBJECTS ----------------------------------------------

        # subgroup properties
        pp_str = ['waveforms', 'sparce_opt', 'testing']
        pp_hdr = ['Wave Forms', 'Sparsity Options', 'Testing']

        # sets up the subgroup fields
        p_tmp = {}
        for pp_s, pp_h in zip(pp_str, pp_hdr):
            p_tmp[pp_s] = self.create_para_field(pp_h, 'panel', None)

        # waveform parameter fields
        p_tmp[pp_str[0]]['ch_fld'] = {
            'ms_before': self.create_para_field('Time Before (ms)', 'edit', 2),
            'ms_after': self.create_para_field('Time After (ms)', 'edit', 2),
            'max_spikes_per_unit': self.create_para_field('Max Spikes/Unit', 'edit', 500),
            'return_scaled': self.create_para_field('Scale Results', 'checkbox', True),
        }

        # set up the sparsity option fields
        method_list = ['radius']
        peak_sign_list = ['neg', 'pos']
        pp_sp = {'peak_sign': self.create_para_field('Operator', 'combobox', peak_sign_list[0], p_list=peak_sign_list),
                 'method': self.create_para_field('Method', 'combobox', method_list[0], p_list=method_list),
                 'radius_um': self.create_para_field('Radius (um)', 'edit', 75), }

        # sets the sparsity
        p_tmp[pp_str[1]]['ch_fld'] = {
            'sparse': self.create_para_field('Use Sparsity?', 'checkpanel', True, ch_fld=pp_sp),
        }

        # sets the sparsity
        p_tmp[pp_str[2]]['ch_fld'] = {
            'dir_path': self.create_para_field('Test Default Directory', 'filespec', para_dir),
            'dir_file': self.create_para_field('Test Default File', 'filespec', para_file, p_misc=f_mode_p),
        }

        # updates the class field
        self.p_info['general'] = {'name': 'General', 'type': 'group', 'ch_fld': p_tmp}

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def init_para_dict_fields(self):

        # field initialisation
        self.p_dict = {}

        for g in self.p_info:
            # memory allocation
            self.p_dict[g] = {}

            # recursively sets up group parameter fields
            self.init_group_para_fields(self.p_info[g]['ch_fld'], [g])

    def init_group_para_fields(self, ps_info, k):

        for ps in ps_info:
            # initialises the dictionary field
            ks = k + [ps]

            # updates the dictionary based on the node type
            if ps_info[ps]['value'] is None:
                # case is a branch node
                cf.set_multi_dict_value(self.p_dict, ks, {})

            else:
                # case is a leaf node
                cf.set_multi_dict_value(self.p_dict, ks, ps_info[ps]['value'])

            # sets the children nodes (if any)
            if ps_info[ps]['ch_fld'] is not None:
                if ps_info[ps]['type'] == 'checkpanel':
                    # case is a checkpanel widget
                    self.init_group_para_fields(ps_info[ps]['ch_fld'], k)

                else:
                    # case is another widget type
                    self.init_group_para_fields(ps_info[ps]['ch_fld'], ks)

                    # appends the parameter fields for tab groups
                    if ps_info[ps]['type'] == 'tabgroup':
                        # initialises the value field (if empty)
                        if ps_info[ps]['value'] is None:
                            ps_info[ps]['value'] = list(ps_info[ps]['ch_fld'].keys())[0]

                        # appends the parameter value to the dictionary
                        cf.set_multi_dict_value(self.p_dict, ks + [ps], ps_info[ps]['value'])

    def reset_para_info_value(self, ps, pd):

        for k in ps.keys():
            # continue if there is not matching parameter field
            if k not in pd:
                continue

            if ps[k]['type'] == 'checkpanel':
                # case is a checkbox panel object
                ps[k]['value'] = pd[k]
                self.reset_para_info_value(ps[k]['ch_fld'], pd)

            elif ps[k]['type'] == 'tabgroup':
                # case is a tabgroup object
                ps[k]['value'] = pd[k][k]
                self.reset_para_info_value(ps[k]['ch_fld'], pd[k])

            elif isinstance(pd[k], dict):
                # case is a parent branch field
                self.reset_para_info_value(ps[k]['ch_fld'], pd[k])

            else:
                # case is a parameter field
                ps[k]['value'] = pd[k]

    def reset_para_fields(self, d, kp, h_obj=None, is_init=False):

        for k in d.keys():
            # case is the root parameter field
            if is_init:
                h_obj_c = [self.h_tab_grp[k]]

            else:
                # finds the associated children objects
                h_obj_c = h_obj.findChildren(QWidget, k)

            if len(h_obj_c) == 0:
                # if there are no matches, then continue
                continue

            elif isinstance(d[k], dict):
                # subfield is a dictionary field
                self.reset_para_fields(d[k], kp + [k], h_obj_c[0])

            else:
                # subfield is a widget field
                p_val = cf.get_multi_dict_value(self.p_dict, kp + [k])
                if isinstance(h_obj_c[0], QLineEdit):
                    # case is a lineedit widget
                    if isinstance(p_val, str):
                        h_obj_c[0].setText(p_val)
                    else:
                        h_obj_c[0].setText('%g' % p_val)

                elif isinstance(h_obj_c[0], QCheckBox):
                    # case is a checkbox widget
                    h_obj_c[0].setChecked(p_val)

                elif isinstance(h_obj_c[0], QComboBox):
                    # case is a combobox widget
                    h_obj_c[0].setCurrentText(p_val)

                elif isinstance(h_obj_c[0], QGroupBox):
                    # case is a groupbox widget
                    h_obj_c[0].setChecked(p_val)
                    h_obj_c[0].clicked.emit()

                elif isinstance(h_obj_c[0], QTabWidget):
                    # case is a tabgroup widget
                    h_tab_sel = h_obj_c[0].findChildren(QWidget, p_val)[0]
                    h_obj_c[0].setCurrentWidget(h_tab_sel)

    def set_styles(self):

        # sets the style sheets
        self.group_scroll.setStyleSheet("background-color: rgba(120, 152, 229, 255) ;")

    @staticmethod
    def create_group_text_link(name, lbl_name):

        # creates the text labels
        h_gap = cw.create_text_label(None, '', name=name)
        h_txt = cw.create_text_label(None, lbl_name, align='left', name=name)

        # sets the label properties
        h_txt.adjustSize()
        h_txt.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))
        h_txt.setStyleSheet("""
            QLabel {
                color: rgba(26, 83, 200, 255) ;
            }
            QLabel:hover {
                color: rgba(255, 0, 0, 255) ;
            }""")

        # sets the gap object properties
        h_gap.setFixedWidth(5)
        h_gap.setStyleSheet("background-color: rgba(240, 240, 255, 255) ;")

        # returns the objects
        return h_gap, h_txt

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}

# ----------------------------------------------------------------------------------------------------------------------


class QSearchWidget(QWidget):
    def __init__(self, parent=None):
        super(QSearchWidget, self).__init__(parent)

        # initialisations
        self.n_grp, self.n_para = 0, 0
        self.h_grp, self.h_para = {}, []
        self.para_name0, self.para_name, self.para_grp, self.grp_name = [], [], [], []

        # main widget layout
        self.main_layout = QFormLayout()

        # other widget setup
        self.h_lbl = cw.create_text_label(None, '', None)
        self.h_edit = cw.create_line_edit(None, '', align='left')

        # sets the widget properties
        self.setFixedHeight(cf.but_height)

        # initialises the class fields and objects
        self.init_class_fields()
        self.init_class_widgets()

    def init_class_fields(self):

        # creates the layout
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def init_class_widgets(self):

        # creates the button object
        self.main_layout.addRow(self.h_lbl, self.h_edit)

        # sets the icon label properties
        q_pixmap = QIcon(icon_path['search']).pixmap(QSize(cf.but_height, cf.but_height))
        self.h_lbl.setPixmap(q_pixmap)
        self.h_lbl.setContentsMargins(0, 0, 0, 0)
        self.h_lbl.setFixedSize(cf.but_height, cf.but_height)

        # sets the editbox properties
        self.h_edit.setContentsMargins(0, 0, 0, 0)
        self.h_edit.setFixedHeight(cf.but_height)
        self.h_edit.setPlaceholderText('Search')
        self.h_edit.textChanged.connect(self.edit_search_change)

        # sets the stylesheet properties
        self.setStyleSheet("background-color: rgba(255, 255, 255, 255) ;")
        self.h_edit.setStyleSheet("background-color: rgba(255, 255, 255, 255) ;"
                                  "qproperty-frame: False")

    def edit_search_change(self):

        # field retrieval
        s_txt = self.h_edit.text().lower()
        ns_txt = len(s_txt)

        if ns_txt:
            ind_s = [[m.start() for m in re.finditer(s_txt, n)] for n in self.para_name]
        else:
            ind_s = [[] for _ in range(self.n_para)]

        # determines the groups which have a match
        has_s = np.array([len(x) > 0 for x in ind_s])
        grp_s = np.unique(np.array(self.para_grp)[has_s])

        # updates the group text labels
        for i, hg in enumerate(self.h_grp):
            col = 'yellow' if hg in grp_s else 'rgba(240, 240, 255, 255)'
            t_lbl = cf.set_text_background_colour(self.grp_name[i], col)
            self.h_grp[hg].setText(t_lbl)

        # resets the parameter label strings
        for ii, nn, hh in zip(ind_s, self.para_name0, self.h_para):
            # sets the text highlight
            for xi0 in np.flip(ii):
                nn = self.add_highlight(nn, xi0, ns_txt)

            # updates the parameter label text
            if isinstance(hh, QGroupBox):
                t_style = gbox_style_on if len(ii) else gbox_style_off
                hh.setStyleSheet(t_style)

            elif isinstance(hh, cw.QCheckboxHTML):
                hh.set_label_text(nn)

            else:
                hh.setText(nn)

    def append_para_obj(self, h_obj, p_name, g_name):

        # increments the count
        self.n_para += 1
        p_name_s = re.sub(r'\<[^>]*\>|[&;]+','', p_name)

        # appends the objects
        self.h_para.append(h_obj)
        self.para_name.append(p_name_s.lower())
        self.para_name0.append(p_name_s)
        self.para_grp.append(g_name)

    def append_grp_obj(self, h_obj, g_str, g_name):

        # increments the count
        self.n_grp += 1

        # appends the objects
        self.h_grp[g_str] = h_obj
        self.grp_name.append(g_name)

    @staticmethod
    def add_highlight(s, i0, n):

        return '{0}{1}{2}'.format(s[0:i0], cf.set_text_background_colour(s[i0:(i0 + n)], 'yellow'), s[(i0 + n):])
