# module imports
import copy

import numpy as np
import functools

# custom module imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QLineEdit, QComboBox, QCheckBox, QPushButton, QSizePolicy, QVBoxLayout, QGroupBox,
                             QHBoxLayout, QFormLayout, QGridLayout, QColorDialog, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5
x_gap2 = 2 * x_gap
x_gap_h = 2

# ----------------------------------------------------------------------------------------------------------------------

"""
    PropManager: object that controls the information panels within the central
                 main window information widget
"""


class PropManager(QWidget):
    # signal functions
    config_update = pyqtSignal(object)
    axes_reset = pyqtSignal(QWidget)

    # widget dimensions
    dx_gap = 15

    # field names
    props_name = 'Plot Properties'
    tab_type = ['config']

    def __init__(self, main_obj, info_width, session_obj=None):
        super(PropManager, self).__init__()

        # main class fields
        self.main_obj = main_obj
        self.info_width = info_width
        self.session_obj = session_obj

        # class property fields
        self.p_info = {}
        self.p_props = None

        # boolean class fields
        self.is_updating = False

        # widget layout setup
        self.tabs = []
        self.t_types = []
        self.main_layout = QVBoxLayout()
        self.props_layout = QVBoxLayout()

        # main widgets setup
        self.group_props = QGroupBox(self.props_name.upper())
        self.tab_group_props = cw.create_tab_group(self)

        # initialises the class fields
        self.init_class_fields()
        self.init_props_group()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the main widget properties
        self.setFixedWidth(self.info_width + self.dx_gap)
        self.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_exp))
        self.setLayout(self.main_layout)

        # sets the widget layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(x_gap2, x_gap2, x_gap2, x_gap2)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.group_props)

        # sets the outer group-box properties
        self.group_props.setLayout(self.props_layout)
        self.group_props.setFont(cw.font_panel)

    def init_props_group(self):

        # sets the property tab group properties
        self.props_layout.setSpacing(0)
        self.props_layout.setContentsMargins(x_gap_h, x_gap_h, x_gap_h, x_gap_h)
        self.props_layout.addWidget(self.tab_group_props)

        # sets up the slot function
        cb_fcn = functools.partial(self.tab_change_props)
        self.tab_group_props.currentChanged.connect(cb_fcn)
        self.tab_group_props.setContentsMargins(0, 0, 0, 0)
        self.tab_group_props.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_min))

        # adds the initial tabs to the tab group
        self.add_prop_tabs(self.tab_type)

    def add_prop_tabs(self, tab_type_new):

        if not isinstance(tab_type_new, list):
            tab_type_new = [tab_type_new]

        # creates the tab-objects
        for t_type in tab_type_new:
            # only add if tab does not exist
            if t_type in self.t_types:
                continue

            # creates the tab widget (based on type)
            t_lbl = pt.prop_names[t_type]
            tab_constructor = pt.prop_types[t_type]
            tab_widget = tab_constructor(self)
            self.tabs.append(tab_widget)

            # adds the tab to the tab group
            self.tab_group_props.addTab(tab_widget, t_lbl)

            # sets the tab specific properties
            self.t_types.append(t_type)
            match t_type:
                case 'config':
                    # sets the region configuration slot function
                    tab_widget.obj_rconfig.config_reset.connect(self.update_config)

    # ---------------------------------------------------------------------------
    # Special Widget Event Functions
    # ---------------------------------------------------------------------------

    def config_reset(self):

        config_tab = self.get_tab('config')
        self.axes_reset.emit(config_tab.obj_rconfig)

    def update_config(self):

        config_tab = self.get_tab('config')
        self.config_update.emit(config_tab.obj_rconfig.c_id)

    def set_region_config(self, c_id):

        self.get_tab('config').set_region_config(c_id)

    def add_config_view(self, v_type):

        self.get_tab('config').add_config_view(v_type)

    def tab_change_props(self):

        pass

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def get_tab(self, tab_type):

        return self.tabs[self.t_types.index(tab_type)]

    def set_tab_enabled(self, i_tab, s_flag):

        if isinstance(i_tab, str):
            i_tab = self.t_types.index(i_tab)

        # updates the table flag
        self.tab_group_props.setTabEnabled(i_tab, s_flag)

    def set_tab_visible(self, i_tab, s_flag):

        if isinstance(i_tab, str):
            i_tab = self.t_types.index(i_tab)

        # updates the table flag
        self.tab_group_props.setTabVisible(i_tab, s_flag)

    def set_styles(self):

        # widget stylesheets
        info_groupbox_style = """
            background-color: rgba(240, 240, 255, 255);
        """

        # sets the group style sheets
        self.tab_group_props.setStyleSheet(info_groupbox_style)
        self.group_props.setStyleSheet(info_groupbox_style)


# ----------------------------------------------------------------------------------------------------------------------

"""
    PropPara:
"""


class PropPara(QWidget):
    def __init__(self, prop_fld):
        super(PropPara, self).__init__()

        for pf, pv in prop_fld.items():
            setattr(self, pf, pv['value'])


# ----------------------------------------------------------------------------------------------------------------------

"""
    PropWidget: 
"""


class PropWidget(QWidget):
    # widget dimensions
    lbl_width = 125

    def __init__(self, main_obj, p_type, p_info):
        super(PropWidget, self).__init__()

        # main class fields
        self.p_type = p_type
        self.p_info = p_info
        self.main_obj = main_obj

        # other class fields
        self.n_para = 0
        self.p_props = None

        # boolean class fields
        self.is_init = False
        self.is_updating = False

        # initialises the class fields
        self.init_class_fields()

    def init_class_fields(self):

        if self.p_info is None:
            return

        # field retrieval
        tab_type = self.p_info['type']
        tab_para = self.p_info['ch_fld']

        # sets up the property tab layout
        f_layout = QGridLayout() if tab_type == 'g_panel' else QFormLayout()
        if isinstance(f_layout, QGridLayout):
            # sets the column stretch (Grid Layout only)
            for i in range(3):
                f_layout.setColumnStretch(i, 1)

        # creates the parameter objects
        for ps_ch in tab_para:
            self.create_para_object(f_layout, ps_ch, tab_para[ps_ch], [self.p_type, ps_ch])
            self.n_para += 1

        # adds the widget to the table
        self.setLayout(f_layout)

    # ---------------------------------------------------------------------------
    # Widget Event Functions
    # ---------------------------------------------------------------------------

    def widget_para_update(self, h_widget, *args):

        # case is a widget type is not provided
        if isinstance(h_widget, QLineEdit):
            self.edit_para_update(h_widget)

        elif isinstance(h_widget, QComboBox):
            self.combobox_para_update(h_widget)

        elif isinstance(h_widget, QCheckBox):
            self.checkbox_para_update(h_widget)

        elif isinstance(h_widget, QPushButton):
            self.pushbutton_para_update(h_widget)

        elif isinstance(h_widget, cw.QButtonPair):
            self.buttonpair_para_update(h_widget, args[0])

    def edit_para_update(self, h_edit):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        nw_val = h_edit.text()
        p_str = h_edit.objectName()
        str_para = []

        if p_str in str_para:
            # case is a string parameter
            self.set(p_str, nw_val)

        else:
            # case is a numerical parameters

            # updates the reset flag
            self.main_obj.was_reset = True
            p_min, p_max, is_int = self.get_para_limits(p_str)

            # determines if the new value is valid
            chk_val = cf.check_edit_num(nw_val, min_val=p_min, max_val=p_max, is_int=is_int)
            if chk_val[1] is None:
                # case is the value is valid
                self.set(p_str, chk_val[0])

            else:
                # otherwise, reset the previous value
                h_edit.setText('%g' % self.get(p_str))

    def combobox_para_update(self, h_cbox):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        p_str = h_cbox.objectName()
        nw_val = h_cbox.currentText()

        # updates the parameter field
        self.set(p_str, nw_val)

    def checkbox_para_update(self, h_chk):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        p_str = h_chk.objectName()
        nw_val = h_chk.isChecked()

        # updates the parameter field
        self.set(p_str, nw_val)

    def pushbutton_para_update(self, h_button):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        p_str = h_button.objectName()
        nw_val = (getattr(self.p_props, p_str) + 1) % 2

        # updates the parameter field
        self.set(p_str, nw_val)

    def buttonpair_para_update(self, h_pair, i_button):

        # field retrieval
        p_str = h_pair.objectName()

        # toggles the button value
        self.set(p_str, self.get(p_str) ^ (2 ** i_button))

    def button_color_pick(self, h_button):

        # runs the colour picker dialog
        p_str = h_button.objectName()
        p_col = QColorDialog.getColor()

        if p_col.isValid():
            # if successful, then update the parameter fields
            h_button.setStyleSheet(
                "border: 2px solid;"
                "background-color: {0}".format(p_col.name())
            )

            # updates the parameter field
            self.set(p_str, p_col)

    def button_file_spec(self, p_str_l, h_fspec):

        a = 1

    def create_para_object(self, layout, p_name, ps, p_str_l):

        # base callback function
        i_row = self.n_para
        cb_fcn = self.setup_widget_callback()

        match ps['type']:
            # -------------------------------------------------------------------
            # Standard Widgets
            # -------------------------------------------------------------------

            case 'text':
                # case is a text label

                # creates the label widget combo
                lbl_str = '%g' % (ps['value'])
                obj_lbl = cw.create_text_label(None, '{0}: '.format(ps['name']), font=cw.font_lbl)
                obj_txt = cw.create_text_label(None, lbl_str, name=p_name, align='left', font=cw.font_lbl)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lbl, i_row, 0, 1, 1)
                    layout.addWidget(obj_txt, i_row, 1, 1, 2)

                else:
                    # case is another layout type
                    obj_lbl.setFixedWidth(self.lbl_width)
                    layout.addRow(obj_lbl, obj_txt)

            case 'edit':
                # case is an editbox

                # sets the editbox string
                lbl_str = '{0}: '.format(ps['name'])
                if isinstance(ps['value'], str):
                    # parameter is a string
                    edit_str = ps['value']

                else:
                    # parameter is a number
                    edit_str = '%g' % (ps['value'])

                # creates the label/editbox widget combo
                obj_lbledit = cw.QLabelEdit(None, lbl_str, edit_str, name=p_name, font_lbl=cw.font_lbl)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lbledit.obj_lbl, i_row, 0, 1, 1)
                    layout.addWidget(obj_lbledit.obj_edit, i_row, 1, 1, 2)

                else:
                    # case is another layout type
                    obj_lbledit.obj_lbl.setFixedWidth(self.lbl_width)
                    layout.addRow(obj_lbledit)

                # sets the widget callback function
                obj_lbledit.connect(cb_fcn)

            case 'combobox':
                # case is a combobox

                # creates the label/combobox widget combo
                lbl_str = '{0}: '.format(ps['name'])
                obj_lblcombo = cw.QLabelCombo(None, lbl_str, ps['p_list'], ps['value'], name=p_name,
                                              font_lbl=cw.font_lbl)

                # sets the widget callback function
                obj_lblcombo.connect(cb_fcn)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lblcombo.obj_lbl, i_row, 0, 1, 1)
                    layout.addWidget(obj_lblcombo.obj_cbox, i_row, 1, 1, 2)

                else:
                    # case is another layout type
                    obj_lblcombo.obj_lbl.setFixedWidth(self.lbl_width)
                    layout.addRow(obj_lblcombo)

            case 'checkbox':
                # case is a checkbox

                # creates the checkbox widget
                obj_checkbox = cw.create_check_box(
                    None, ps['name'], ps['value'], font=cw.font_lbl, name=p_name)

                # sets up the checkbox callback function
                cb_fcn_chk = self.setup_widget_callback(obj_checkbox)
                obj_checkbox.stateChanged.connect(cb_fcn_chk)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_checkbox, i_row, 0, 1, 3)

                else:
                    # case is another layout type
                    layout.addRow(obj_checkbox)

            case 'pushbutton':
                # case is a pushbutton

                # creates the button widget
                obj_button = cw.create_push_button(None, ps['name'], cw.font_lbl, name=p_name)

                # sets the callback function
                cb_fcn_but = self.setup_widget_callback(obj_button)
                obj_button.clicked.connect(cb_fcn_but)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_button, i_row, 0, 1, 4)

                else:
                    # case is another layout type
                    layout.addRow(obj_button)

            case 'buttonpair':
                # case is a pushbutton pair

                # creates the wrapper
                pair_obj = cw.QButtonPair(None, ps['name'], font=cw.font_lbl, name=p_name)

                # sets the callback function
                cb_fcn_but = self.setup_widget_callback(pair_obj)
                pair_obj.connect(cb_fcn_but)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(pair_obj, i_row, 0, 1, 3)

                else:
                    # case is another layout type
                    layout.addRow(pair_obj)

            case 'table':
                # case is a table widget

                # creates the table widget
                table_obj = QTableWidget(None)

                # sets the table properties
                table_obj.setRowCount(0)
                table_obj.setColumnCount(0)
                table_obj.setObjectName(p_name)
                table_obj.setStyleSheet(cw.table_style)

                # resets the channel table style
                table_style = cw.CheckBoxStyle(table_obj.style())
                table_obj.setStyle(table_style)

                # adds the widget to the layout
                layout.addWidget(table_obj)

            # -------------------------------------------------------------------
            # Special Widgets
            # -------------------------------------------------------------------

            case 'tree':
                # case is a tree widget

                # creates the trace tree widget
                self.obj_ttree = cw.QTraceTree(self, font=cw.font_lbl)

                # sets the layout properties
                layout.setSpacing(0)
                layout.addWidget(self.obj_ttree)

            case 'rconfig':
                # case is a region configuration widget

                # creates the region configuration widget
                gbox_height = self.main_obj.info_width - 4 * x_gap
                obj_rconfig = cw.QRegionConfig(self, font=cw.font_lbl, is_expanded=True,
                                               p_list0=ps['p_list'], gbox_height=gbox_height)

                # sets the layout properties
                layout.setSpacing(0)
                layout.addWidget(obj_rconfig)

            case 'colorpick':
                # case is a colorpick object

                # creates the label/editbox widget combo
                lbl_str = '{0}: '.format(ps['name'])
                obj_lblbutton = cw.QLabelButton(None, lbl_str, "", name=p_name, font_lbl=cw.font_lbl)
                obj_lblbutton.obj_but.setStyleSheet(
                    "border: 2px solid;"
                    "background-color: {0}".format(ps['value'].name())
                )

                # connects the event function
                obj_lblbutton.connect(self.button_color_pick)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lblbutton.obj_lbl, i_row, 0, 1, 1)
                    layout.addWidget(obj_lblbutton.obj_but, i_row, 1, 1, 2)

                else:
                    # case is another layout type
                    layout.addRow(obj_lblbutton)

            case 'axeslimits':
                # case is the axes limit widget

                # creates the file selection widget
                self.obj_axlim = cw.QAxesLimits(None, font=cw.font_lbl, p_props=self.p_props)
                layout.addRow(self.obj_axlim)

            case 'filespec':
                # case is a file selection widget

                # creates the file selection widget
                obj_fspec = cw.QFileSpec(None, ps['name'], ps['value'], name=p_name, f_mode=ps['p_misc'])
                layout.addRow(obj_fspec)

                # sets up the slot function
                cb_fcn = functools.partial(self.button_file_spec, p_str_l)
                obj_fspec.connect(cb_fcn)

    def setup_widget_callback(self, h_widget=None):

        if h_widget is None:
            return self.widget_para_update

        else:
            return functools.partial(self.widget_para_update, h_widget)

    # ---------------------------------------------------------------------------
    # Parameter Getter/Setter Methods
    # ---------------------------------------------------------------------------

    def get(self, p_fld):

        return getattr(self.p_props, p_fld)

    def set(self, p_fld, p_value):

        setattr(self.p_props, p_fld, p_value)

    def set_n(self, p_fld, p_value):

        self.p_props.is_updating = True
        setattr(self.p_props, p_fld, p_value)
        self.p_props.is_updating = False

    # ---------------------------------------------------------------------------
    # Miscellaneous Methods
    # ---------------------------------------------------------------------------

    def get_para_limits(self, p_str):

        # sets the parameter limiting properties
        p_min, p_max, is_int = -1e6, 1e6, False
        match p_str:
            case 'p_width':
                # case is the line pen width
                p_min, p_max = 1, 5

            case 't_start':
                # case is the start time
                if hasattr(self.p_props, 't_span'):
                    p_min, p_max = 0, self.t_dur - self.get('t_span')

                else:
                    p_min, p_max = 0, self.get('t_finish')

            case 't_finish':
                # case is the start time
                if hasattr(self.p_props, 't_span'):
                    p_min, p_max = self.get('t_span'), self.t_dur

                else:
                    p_min, p_max = self.get('t_start'), self.t_dur

            case 't_span':
                # case is the trace window span
                p_min, p_max = 0.01, 0.5

            case 't_dur':
                # case is the experiment duration
                p_min, p_max = 0.1, self.t_dur - self.get('t_start')

        # returns the limits and integer flag
        return p_min, p_max, is_int

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}


# ----------------------------------------------------------------------------------------------------------------------

# module imports (required here as will cause circular import error otherwise)
import spike_pipeline.props.prop_type as pt