# module import
import os
import functools
import numpy as np
import pyqtgraph as pg
from pathlib import Path
from bigtree import dataframe_to_tree, tree_to_dict

# custom module import
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.spikeinterface_func as sf
from spike_pipeline.common.common_widget import (QLabelEdit, QCheckboxHTML, QFileSpec, QLabelCombo, QFolderTree)

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QWidget, QFormLayout, QSizePolicy, QGridLayout,
                             QGroupBox, QComboBox, QCheckBox, QLineEdit, QTableWidget, QTableWidgetItem)
from PyQt6.QtGui import QFont, QIcon, QStandardItem
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QItemSelectionModel

# ----------------------------------------------------------------------------------------------------------------------

# object dimensions
x_gap = 5
x_gap_h = 2
sz_but = 25
dlg_width = 800
# dlg_height = 500

# font objects
font_lbl = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold)
font_hdr = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)
font_panel = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

# file path/filter modes
f_mode_ssf = "Spike Pipeline Session File (*.ssf)"

# parameter/resource folder paths
data_dir = "C:\\Work\\Other Projects\\EPhys Project\\Data"
icon_dir = os.path.join(os.getcwd(), 'resources', 'icons')
para_dir = os.path.join(os.getcwd(), 'resources', 'parameters').replace('\\', '/')

# icon paths
icon_path = {
    'open': os.path.join(icon_dir, 'open_icon.png'),
    'restart': os.path.join(icon_dir, 'restart_icon.png'),
    'close': os.path.join(icon_dir, 'close_icon.png'),
}


# OPEN SESSION WIDGET --------------------------------------------------------------------------------------------------


class OpenSession(QDialog):
    def __init__(self, parent=None):
        super(OpenSession, self).__init__(parent)

        # class widget setup
        self.main_layout = QHBoxLayout()
        self.info = SessionFile(self)
        self.probe = SessionProbe(self)

        # field initialisation
        self.setup_dialog()
        self.init_class_fields()

        # opens the dialog
        self.show()

    # CLASS INITIALISATION FUNCTIONS -----------------------------------

    def setup_dialog(self):
        # creates the dialog window
        self.setWindowTitle("Session Information")
        self.setFixedWidth(dlg_width)

    def init_class_fields(self):
        # sets up the main layout
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # adds the session information widget
        self.main_layout.addWidget(self.info)
        self.main_layout.addWidget(self.probe)

        # disables the probe info panel
        self.probe.setEnabled(False)


# SESSION FILE WIDGET --------------------------------------------------------------------------------------------------


class SessionFile(QWidget):
    grp_name = "Recording Data"

    def __init__(self, parent=None):
        super(SessionFile, self).__init__(parent)

        # widget setup
        self.group_panel = QGroupBox(self.grp_name.upper())
        self.main_layout = QVBoxLayout()
        self.form_layout = QVBoxLayout()

        # session information widgets
        self.file_widget = QWidget(self)
        self.file_layout = QVBoxLayout()

        # session information widgets
        self.prop_widget = QWidget(self)
        self.prop_layout = QVBoxLayout()

        # other widgets
        self.h_file_tab = SessionNew(self)
        self.h_file_spec = QFileSpec(None, None, name='session_name')

        # initialises the class fields
        self.init_class_fields()
        self.init_open_file_fields()

        # sets the widget styling
        self.set_styling()

    # CLASS INITIALISATION FUNCTIONS ------------------------------------------

    def init_class_fields(self):

        # creates the panel objects
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(x_gap, x_gap, x_gap_h, x_gap)
        self.main_layout.addWidget(self.group_panel)

        # sets the outer group-box properties
        self.group_panel.setLayout(self.form_layout)
        self.group_panel.setFont(font_panel)
        self.setLayout(self.main_layout)

        # adds the session file/property widgets
        self.form_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.form_layout.addWidget(self.file_widget)
        self.form_layout.setSpacing(0)
        self.form_layout.setContentsMargins(0, 0, 0, 0)

        # sets up the session file widget properties
        self.file_widget.setLayout(self.file_layout)
        self.file_widget.setObjectName('panel')
        self.file_widget.setSizePolicy(QSizePolicy(cf.q_pref, cf.q_exp))
        self.file_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # resets the widget size policies
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

    def init_open_file_fields(self):

        # field initialisations
        r_lbl = ['Start New Session', 'Open Existing Session']
        r_name = ['new', 'existing']

        # creates the radio buttons
        h_radio = []
        for _rl, _rn in zip(r_lbl, r_name):
            # creates the new radio button
            h_radio_new = cw.create_radio_button(None, _rl, _rn == 'new', font_lbl, _rn)
            h_radio_new.toggled.connect(self.radio_session_select)

            # appends it to the list
            h_radio.append(h_radio_new)

        # creates the file spec widget
        cb_fcn = functools.partial(self.h_file_tab.prop_update, ['existing', 'f_input'])
        self.h_file_spec.connect(cb_fcn)
        self.h_file_spec.setEnabled(False)

        # adds the widget to the layout
        self.file_layout.addWidget(h_radio[0])
        self.file_layout.addWidget(self.h_file_tab)
        self.file_layout.addWidget(h_radio[1])
        self.file_layout.addWidget(self.h_file_spec)

    def radio_session_select(self):

        # get the radio button
        rb = self.sender()

        # check if the radio button is checked
        if rb.isChecked():
            # updates the tab widget properties
            self.h_file_tab.is_new = rb.objectName() == 'new'
            self.h_file_tab.setEnabled(self.h_file_tab.is_new)
            self.h_file_spec.setEnabled(not self.h_file_tab.is_new)

            # updates the dialog properties
            self.h_file_tab.update_dialog_props()

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def set_styling(self):

        a = 1

        # # sets the session file/property widget stylesheet
        # self.group_panel.setStyleSheet("""
        #     QWidget[objectName="panel"] {
        #         border: 1px solid;
        #     }
        # """)

        # # sets the session file/property widget stylesheet
        # self.setStyleSheet("""
        #     QLineEdit {
        #         border: 1px solid;
        #     }
        #     QComboBox {
        #         border: 1px solid;
        #     }
        # """)


# SESSION PROBE WIDGET -------------------------------------------------------------------------------------------------


class SessionProbe(QWidget):
    x_gap = 5
    x_gap_h = 2
    grp_name = "Session Probe"

    def __init__(self, parent=None):
        super(SessionProbe, self).__init__(parent)

        # widget setup
        self.form_layout = QFormLayout()
        self.main_layout = QVBoxLayout()
        self.group_panel = QGroupBox(self.grp_name.upper())

        # initialises the class fields
        self.init_class_fields()

    def init_class_fields(self):

        # creates the panel objects
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(x_gap_h, x_gap, x_gap, x_gap)
        self.main_layout.addWidget(self.group_panel)

        # creates the children objects for the current parent object
        self.form_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # sets the final layout
        self.group_panel.setLayout(self.form_layout)
        self.group_panel.setFont(font_panel)
        self.setLayout(self.main_layout)

        # resets the collapse panel size policy
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))


# SESSION NEW WIDGET ---------------------------------------------------------------------------------------------------


class SessionNew(QWidget):
    # widget dimensions
    lbl_width = 150
    n_row_table = 4
    row_height = 22
    n_col_grid = 4

    # field initialisation
    p_list_axis = ['Axis 0', 'Axis 1']
    p_list_type = ['int8', 'int16', 'int32']
    col_hdr = ['Run #', 'Analyse Run?', 'Session Run Name']

    table_style = """
        QTableWidget {
            font: Arial 6px;
            border: 1px solid;
        }
        QHeaderView {
            font: Arial 6px;
            font-weight: 1000;
        }
    """

    def __init__(self, parent=None):
        super(SessionNew, self).__init__(parent)

        # field initialisations
        self.prop_fld = {}
        self.props = {
            'folder': {},
            'file': {},
            'existing': {'f_input': None},
        }

        # string class fields
        self.n_para = None
        self.f_type = 'folder'

        # boolean class fields
        self.use_run = None
        self.is_new = True
        self.is_updating = True

        # main class widgets
        self.main_layout = QFormLayout()
        self.button_group = QWidget()
        self.button_layout = QVBoxLayout()
        self.run_table = QTableWidget(0, 3, None)

        # minor class widgets
        self.button_open = cw.create_push_button(None, '')
        self.button_reset = cw.create_push_button(None, '')
        self.h_tab_grp = cw.create_tab_group(None)

        # initialises the class fields
        self.init_prop_fields()
        self.init_class_fields()

    def init_prop_fields(self):

        # sets up the file tab property fields
        p_tmp_folder = {
            'f_input': self.create_para_field(None, 'exptfolder', None),
            # 'f_run': self.create_para_field('Input Folder Paths', 'checktable', None),
            # 'f_output': self.create_para_field('Output Folder Path', 'filespec', None),
        }

        # updates the class field
        self.prop_fld['folder'] = {'name': 'Folder', 'type': 'tab', 'ch_fld': p_tmp_folder}

        # sets up the file tab property fields
        p_tmp_file = {
            'f_input': self.create_para_field('Input File Path', 'filespec', None, p_misc=f_mode_ssf),
            'n_channel': self.create_para_field('Channel Count', 'edit', None),
            's_freq': self.create_para_field('Sampling Frequency (Hz)', 'edit', None),
            'gain_to_uV': self.create_para_field('Signal Gain (uV)', 'edit', None),
            'offset_to_uV': self.create_para_field('Signal Offset (uV)', 'edit', None),
            'd_type': self.create_para_field(
                'Signal Offset (uV)', 'combobox', self.p_list_type[1], p_list=self.p_list_type),
            't_axis': self.create_para_field('Time Axis', 'combobox', self.p_list_axis[0], p_list=self.p_list_axis),
            'is_filtered': self.create_para_field('Recording Filtered?', 'checkbox', False),
        }

        # updates the class field
        self.prop_fld['file'] = {'name': 'File', 'type': 'tab', 'ch_fld': p_tmp_file}

        # initialises the fields for all properties
        for i, pf in enumerate(self.prop_fld):
            for pf_c in self.prop_fld[pf]['ch_fld'].keys():
                self.props[pf][pf_c] = self.prop_fld[pf]['ch_fld'][pf_c]['value']

    def init_class_fields(self):

        # sets the widget layout
        self.setLayout(self.main_layout)

        # sets the widget layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        # self.main_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.main_layout.addRow(self.h_tab_grp)
        self.main_layout.addRow(self.run_table, self.button_group)

        # button group properties
        self.button_group.setLayout(self.button_layout)
        self.button_layout.addWidget(self.button_open)
        self.button_layout.addWidget(self.button_reset)
        self.button_layout.setSpacing(0)
        self.button_layout.setContentsMargins(5, 0, 0, 0)

        # open button properties
        self.button_open.setIcon(QIcon(icon_path['open']))
        self.button_open.setIconSize(QSize(sz_but - 2, sz_but - 2))
        self.button_open.setFixedSize(sz_but, sz_but)
        self.button_open.setToolTip('Open Session')
        self.button_open.setStyleSheet("border: 1px solid;")
        self.button_open.clicked.connect(self.button_open_session)

        # reset button properties
        self.button_reset.setIcon(QIcon(icon_path['restart']))
        self.button_reset.setIconSize(QSize(sz_but - 2, sz_but - 2))
        self.button_reset.setFixedSize(sz_but, sz_but)
        self.button_reset.setToolTip('Reset Form')
        self.button_reset.setStyleSheet("border: 1px solid;")
        self.button_reset.clicked.connect(self.button_reset_session)

        # sets up the slot function
        cb_fcn = functools.partial(self.tab_change)
        self.h_tab_grp.currentChanged.connect(cb_fcn)
        self.h_tab_grp.setContentsMargins(0, 0, 0, 0)

        # creates the tab-objects
        for ps_t in self.prop_fld:
            h_tab = self.create_para_object(None, ps_t, self.prop_fld[ps_t], [ps_t])
            self.h_tab_grp.addTab(h_tab, self.prop_fld[ps_t]['name'])

        # creates the session run table
        self.create_other_widgets()

    def create_para_object(self, layout, p_name, ps, p_str):

        match ps['type']:
            case 'tab':
                # case is a tab widget

                # creates the tab widget
                obj_tab = QWidget()
                obj_tab.setObjectName(p_name)

                # creates the children objects for the current parent object
                t_layout = QFormLayout(obj_tab)
                t_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
                t_layout.setSpacing(0)
                t_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

                # creates the panel object
                h_panel_tab = QGroupBox()
                t_layout.addWidget(h_panel_tab)

                # sets the panel properties
                h_panel_tab.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

                # creates the tab parameter objects
                if p_str[0] == 'folder':
                    layout = QFormLayout(h_panel_tab)
                    layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

                    layout.setSpacing(x_gap)
                    layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

                else:
                    layout = QGridLayout(h_panel_tab)
                    layout.setColumnStretch(0, 4)
                    layout.setColumnStretch(1, 2)
                    layout.setColumnStretch(2, 3)

                    # layout.setSpacing(0)
                    # layout.setContentsMargins(x_gap, 0, x_gap, 0)

                    # layout.setRowStretch(0, 3)
                    # for i in range(1, 7):
                    #     layout.setRowStretch(i, 2)

                # creates the tab parameter objects
                self.n_para = 0
                for ps_t in ps['ch_fld']:
                    self.create_para_object(layout, ps_t, ps['ch_fld'][ps_t], p_str=p_str + [ps_t])
                    self.n_para += 1

                # sets the tab layout
                obj_tab.setLayout(t_layout)

                # returns the tab object
                return obj_tab

            case 'edit':
                # sets up the editbox string
                lbl_str = '{0}: '.format(ps['name'])
                if ps['value'] is None:
                    # parameter string is empty
                    edit_str = ''

                elif isinstance(ps['value'], str):
                    # parameter is a string
                    edit_str = ps['value']

                else:
                    # parameter is numeric
                    edit_str = '%g' % (ps['value'])

                # creates the label/editbox widget combo
                obj_edit = QLabelEdit(None, lbl_str, edit_str, name=p_name, font_lbl=font_lbl)
                obj_edit.obj_lbl.setFixedWidth(self.lbl_width)

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(obj_edit)

                else:
                    layout.addWidget(obj_edit.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_edit.obj_edit, self.n_para, 1, 1, 1)

                # sets up the label/editbox slot function
                cb_fcn = functools.partial(self.prop_update, p_str)
                obj_edit.connect(cb_fcn)

            # case is a checkbox
            case 'checkbox':
                # creates the checkbox widget
                obj_checkbox = cw.create_check_box(
                    None, ps['name'], ps['value'], font=font_lbl, name=p_name)

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(obj_checkbox)

                else:
                    layout.addWidget(obj_checkbox, self.n_para, 0, 1, 2)

                # sets up the slot function
                cb_fcn = functools.partial(self.prop_update, p_str)
                obj_checkbox.stateChanged.connect(cb_fcn)

            # case is a combobox
            case 'combobox':
                # creates the label/combobox widget combo
                lbl_str = '{0}: '.format(ps['name'])
                obj_combo = QLabelCombo(None, lbl_str, ps['p_list'], ps['value'], name=p_name,
                                        font_lbl=font_lbl)
                obj_combo.obj_lbl.setFixedWidth(self.lbl_width)

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(obj_combo)

                else:
                    layout.addWidget(obj_combo.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_combo.obj_cbox, self.n_para, 1, 1, 1)

                # sets up the slot function
                cb_fcn = functools.partial(self.prop_update, p_str)
                obj_combo.connect(cb_fcn)

            case 'exptfolder':
                # case is the experiment folder widget

                # creates the file selection widget
                self.expt_folder = ExptFolder(self)

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(self.expt_folder)

                # # sets up the slot function
                # obj_expt_folder.connect(self.prop_update, p_str)

            case 'filespec':
                # case is a file selection widget

                # creates the file selection widget
                obj_file_spec = QFileSpec(None, ps['name'], ps['value'], name=p_name, f_mode=ps['p_misc'])

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(obj_file_spec)

                else:
                    obj_file_spec.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_max))
                    layout.addWidget(obj_file_spec, self.n_para, 0, 1, 3)

                # sets up the slot function
                cb_fcn = functools.partial(self.prop_update, p_str)
                obj_file_spec.connect(cb_fcn)

    def create_other_widgets(self):

        # sets the table properties
        self.run_table.setFixedWidth(int(dlg_width/2 - 2 * x_gap + sz_but))
        self.run_table.setFixedHeight(int(self.row_height * self.n_row_table) + 2)
        self.run_table.setHorizontalHeaderLabels(self.col_hdr)
        self.run_table.verticalHeader().setVisible(False)
        self.run_table.setStyleSheet(self.table_style)

        # table column resizing
        self.run_table.resizeRowsToContents()
        self.run_table.resizeColumnToContents(0)
        self.run_table.resizeColumnToContents(1)
        self.run_table.horizontalHeader().setStretchLastSection(True)
        # self.run_table.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

        # updates the dialog properties
        self.is_updating = False
        self.update_dialog_props()

    # WIDGET EVENT FUNCTIONS --------------------------------------------------

    def tab_change(self):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        self.f_type = self.h_tab_grp.currentWidget().objectName()
        self.update_dialog_props()

    def prop_update(self, p_str, h_obj):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        if isinstance(h_obj, QFileSpec):
            self.button_file_spec(h_obj, p_str)

        elif isinstance(h_obj, QCheckBox):
            self.check_prop_update(h_obj, p_str)

        elif isinstance(h_obj, QLineEdit):
            self.edit_prop_update(h_obj, p_str)

        elif isinstance(h_obj, QComboBox):
            self.combo_prop_update(h_obj, p_str)

    def edit_prop_update(self, h_obj, p_str):

        # field retrieval
        nw_val = h_obj.text()
        str_para = []

        if p_str in str_para:
            # case is a string field
            cf.set_multi_dict_value(self.props, p_str, nw_val)
            self.update_dialog_props()

        else:
            # determines if the new value is valid
            chk_val = cf.check_edit_num(nw_val, min_val=0)
            if chk_val[1] is None:
                # case is the value is valid
                cf.set_multi_dict_value(self.props, p_str, chk_val[0])
                self.update_dialog_props()

            else:
                # otherwise, reset the previous value
                p_val_pr = self.props[p_str[0]][p_str[1]]
                if (p_val_pr is None) or isinstance(p_val_pr, str):
                    # case is the parameter is empty
                    h_obj.setText('')

                else:
                    # otherwise, update the numeric string
                    h_obj.setText('%g' % p_val_pr)

    def combo_prop_update(self, h_obj, p_str):

        # updates the dictionary field
        cf.set_multi_dict_value(self.props, p_str, h_obj.currentText())
        self.update_dialog_props()

    def check_prop_update(self, h_obj, p_str):

        # updates the dictionary field
        cf.set_multi_dict_value(self.props, p_str, h_obj.isChecked())
        self.update_dialog_props()

    def button_file_spec(self, h_obj, p_str):

        # file dialog properties
        dir_only = h_obj.f_mode is None
        caption = 'Select Directory' if dir_only else 'Select File'

        # sets the initial search path
        f_path = cf.get_multi_dict_value(self.props, p_str)
        if f_path is None:
            f_path = data_dir

        # runs the file dialog
        file_dlg = cw.FileDialogModal(caption=caption, dir_only=dir_only, f_filter=h_obj.f_mode, f_directory=f_path)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # if the user accepted, then update the parameter/widget fields
            file_info = file_dlg.selectedFiles()

            match p_str[0]:
                case 'folder':
                    # case is the folder format

                    # determines if the new folder is feasible
                    f_format = self.props['folder']['f_format']
                    if not sf.check_data_folder_structure(file_info[0], f_format):
                        # if not, output an error message to screen
                        f_error = sf.get_data_folder_structure(f_format)
                        err_str = (
                            'The selected folder does not adhere to the "{0}" directory structure.'.format(f_format),
                            'The directory structure should be as follows:', '', f_error, '',
                            'Either retry with another file format or select a feasible directory.',
                        )
                        cf.show_error('\n'.join(err_str), 'Invalid Data Directory')

                        # exits the function
                        return

                case 'file':
                    # case
                    a = 1

            # updates the property value and editbox string
            cf.set_multi_dict_value(self.props, p_str, file_info[0])
            h_obj.set_text(file_info[0])

            # updates the dialog properties
            self.update_dialog_props()

    def button_open_session(self):

        print('Opening Session...')

    def button_reset_session(self):

        self.expt_folder.button_reset_click()


    def check_run_table(self, h_chk, i_row):

        self.use_run[i_row] = h_chk.isChecked()
        self.button_open.setEnabled(np.any(self.use_run))

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def reset_session_run_table(self, run_name):

        # clears the table
        self.run_table.clear()

        # resets the table dimensions
        n_run = len(run_name)
        self.run_table.setRowCount(n_run)
        self.run_table.setHorizontalHeaderLabels(self.col_hdr)
        self.run_table.resizeRowsToContents()

        # memory allocation
        self.use_run = np.ones(n_run, dtype=bool)
        self.button_open.setEnabled(True)

        # creates the new table widgets
        for i in range(n_run):
            # creates the run index
            h_cell_num = QTableWidgetItem(str(i + 1))
            h_cell_num.setFlags(~Qt.ItemFlag.ItemIsEditable)
            h_cell_num.setTextAlignment(cf.align_type['center'])
            # h_cell_num.setFont(self.table_font)
            self.run_table.setItem(i, 0, h_cell_num)

            # creates the include checkbox
            h_cell_chk = cw.create_check_box(None, '', True)
            h_cell_chk.setStyleSheet("margin-left:50%; margin-right:50%;")
            self.run_table.setCellWidget(i, 1, h_cell_chk)

            # sets the checkbox event
            cb_fcn = functools.partial(self.check_run_table, h_cell_chk, i)
            h_cell_chk.stateChanged.connect(cb_fcn)

            # creates the run name field
            h_cell_run = QTableWidgetItem(run_name[i])
            h_cell_run.setFlags(~Qt.ItemFlag.ItemIsEditable)
            # h_cell_run.setFont(self.table_font)
            self.run_table.setItem(i, 2, h_cell_run)

            self.run_table.setRowHeight(i, self.row_height)

    def update_dialog_props(self):

        if self.is_new:
            # case is a new session is selected

            # determines if all fields have been set correctly
            is_feas = next((False for x in self.props[self.f_type].values() if (x is None)), True)

        else:
            # case is an existing session is selected
            is_feas = self.props['existing']['f_input'] is not None

        # updates the control buttons
        a = 1

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}


# EXPERIMENT FOLDER WIDGET ---------------------------------------------------------------------------------------------


class ExptFolder(QWidget):
    # list fields
    f_format = ['spikeglx', 'openephys']
    tab_name = ['Feasible', 'Infeasible']

    def __init__(self, parent=None):
        super(ExptFolder, self).__init__(parent)

        # class fields
        self.ses_type = None
        self.sub_path = None
        self.s_dir = data_dir
        self.f_form = self.f_format[0]
        self.obj_dir = sf.DirectoryCheck(self.s_dir, self.f_form)

        # class layout setup
        self.h_tab = []
        self.h_root = self.parent()
        self.main_layout = QVBoxLayout()
        self.tab_layout = QVBoxLayout()
        self.para_layout = QHBoxLayout()

        # class widget setup
        self.main_widget = QWidget(self)
        self.para_group = QWidget(self)
        self.tab_group = cw.create_tab_group(None)
        self.file_spec = QFileSpec(None, 'Parent Search Folder', file_path=self.s_dir, name='data_folder')
        self.f_type = QLabelCombo(None, 'Recording Format:', self.f_format, self.f_form, font_lbl)
        self.s_type = QLabelCombo(None, 'Session Name:', [], [], font_lbl)

        # boolean class fields
        self.is_updating = False

        # initialises the class fields
        self.init_class_fields()
        self.init_class_widgets()

        # # sets the widget styling
        # self.set_styling()

    def init_class_fields(self):

        # sets the widget layout
        self.setLayout(self.main_layout)
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

        # creates the panel objects
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.main_widget)

        # sets the main widget layout
        self.main_widget.setLayout(self.tab_layout)

        # creates the tab layout
        self.tab_layout.setSpacing(0)
        self.tab_layout.setContentsMargins(x_gap_h, x_gap_h, x_gap_h, x_gap_h)

        # sets the file selection properties
        self.file_spec.connect(self.button_parent_dir)

    def init_class_widgets(self):

        # sets up the other property objects
        self.setup_other_para()

        # sets up the tab widgets
        for tn in self.tab_name:
            self.h_tab.append(self.setup_tab_widget(tn))

        # determines the feasible folders
        self.setup_folder_tree_views()

        # adds the other widgets
        self.tab_layout.addWidget(self.tab_group)
        self.tab_layout.addWidget(self.para_group)
        self.tab_layout.addWidget(self.file_spec)

        # resets the collapse panel size policy
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

    def setup_tab_widget(self, tab_name):

        # creates the folder tree object
        is_feas_tree = tab_name == self.tab_name[0]
        h_folder_tree = QFolderTree(self, is_feas_tree=is_feas_tree)
        if is_feas_tree:
            h_folder_tree.subject_changed.connect(self.subject_changed)
            h_folder_tree.session_changed.connect(self.session_changed)

        # creates the tab widget
        obj_tab = QWidget()
        obj_tab.setObjectName(tab_name)
        # h_folder_tree.setStyleSheet("border: 1px solid;")

        # creates the tab widget layout
        t_layout = QVBoxLayout(obj_tab)
        t_layout.setSpacing(0)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.addWidget(h_folder_tree)
        obj_tab.setLayout(t_layout)

        # adds the tab object to the group
        self.tab_group.addTab(obj_tab, tab_name)

        # returns the widget
        return obj_tab

    def setup_other_para(self):

        # initialisations
        self.para_group.setLayout(self.para_layout)
        self.para_group.setContentsMargins(0, 0, 0, 0)

        # adds the file format combo box
        self.para_layout.setSpacing(0)
        self.para_layout.addWidget(self.f_type)
        # self.f_type.obj_cbox.setFixedWidth(95)
        self.f_type.setContentsMargins(0, 0, 0, 0)
        self.f_type.connect(self.combo_format_change)

        # adds the file format combo box
        self.para_layout.addWidget(self.s_type)
        self.s_type.set_enabled(False)
        # self.s_type.obj_cbox.setFixedWidth(80)
        self.s_type.setContentsMargins(0, 0, 0, 0)
        self.s_type.connect(self.session_changed, False)

    def setup_folder_tree_views(self):

        # determines all the feasible folders (for the current search path/file format)
        self.obj_dir.det_all_feas_folders()

        for i, (ht, fd) in enumerate(zip(self.h_tab, self.obj_dir.f_pd)):
            # retrieves the tree widget
            obj_tree = ht.findChild(QFolderTree)

            # clears/resets the tree items
            if len(fd):
                data_dict = tree_to_dict(dataframe_to_tree(fd))
                obj_tree.reset_tree_items(data_dict)

                # for the feasible folders, set the first feasible folder
                if ht.objectName() == self.tab_name[0]:
                    # updates the tree highlight
                    sub_path0 = list(self.obj_dir.sub_dict.keys())[0]
                    self.reset_selected_subject(obj_tree, sub_path0)

                else:
                    for row in fd.itertuples():
                        item = obj_tree.t_dict['/' + row.path]
                        item.setText('{}*'.format(item.text()))
                        item.setForeground(cf.get_colour_value('r'))
                        item.setToolTip(row.err)

                    obj_tree.obj_tview.expandAll()

            else:
                # creates the tree object
                obj_tree.t_model.clear()
                if i == 0:
                    # clears the subject/session fields
                    self.h_root.sub_path = None
                    self.h_root.ses_type = None

                    # clears the session/run table widgets
                    self.is_updating = True
                    self.s_type.obj_cbox.clear()
                    self.h_root.reset_session_run_table([])
                    self.is_updating = False

            # updates the enabled properties
            self.tab_group.setTabEnabled(i, len(fd) > 0)

    # WIDGET EVENT FUNCTIONS ---------------------------------------------

    def combo_format_change(self, h_obj):

        if self.is_updating:
            return

        # updates the format string
        self.f_form = h_obj.currentText()
        self.obj_dir.set_format(self.f_form)

        # resets the folder trees
        self.setup_folder_tree_views()

    def button_reset_click(self):

        # resets the class fields
        self.sub_path = None
        self.ses_type = None

        # resets the folder trees
        self.setup_folder_tree_views()

    def button_parent_dir(self, h_obj):

        # runs the file dialog
        file_dlg = cw.FileDialogModal(caption='Set Search Folder', dir_only=True, f_directory=str(self.obj_dir.f_path))
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # if the user accepted, then update the parameter/widget fields
            file_info = file_dlg.selectedFiles()
            self.obj_dir.set_path(Path(file_info[0]))
            self.file_spec.set_text(file_info[0])

            # resets the folder trees
            self.setup_folder_tree_views()

    def subject_changed(self, item=None):

        # field retrieval
        sub_dict = self.obj_dir.sub_dict[self.sub_path]

        # resets the session type combobox
        self.is_updating = True
        self.s_type.obj_cbox.clear()
        for ses in sub_dict.keys():
            self.s_type.obj_cbox.addItem(ses)

        # sets the session type combobox properties
        self.is_updating = False
        self.s_type.set_enabled(len(sub_dict) > 1)
        self.s_type.obj_cbox.setCurrentIndex(0)

        # updates the session run table
        self.session_changed()

    def session_changed(self, item=None):

        # if manually updating, then exit
        if self.is_updating:
            return

        elif isinstance(item, QStandardItem):
            self.s_type.set_current_text(item.text())

        # updates the session type
        self.ses_type = self.s_type.current_text()
        ses_dict = self.obj_dir.sub_dict[self.sub_path][self.ses_type]

        # resets the session run table
        run_name = [x.split('/')[-1] for x in np.array(self.obj_dir.f_pd[0]['path'])[ses_dict]]
        self.h_root.reset_session_run_table(run_name)

        # updates the tree highlight (if combobox was update)
        if not isinstance(item, QStandardItem):
            obj_tree = self.h_tab[0].findChild(QFolderTree)
            obj_tree.update_tree_highlights()

    def connect(self, cb_fcn, p_str):

        a = 1

    # MISCELLANEOUS FUNCTIONS ---------------------------------------------

    def reset_selected_subject(self, obj_tree, sub_path):

        # updates the subject path
        obj_tree.tree_double_clicked(obj_tree.t_dict[sub_path])
