# module imports
import functools

# custom module imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QLineEdit, QComboBox, QCheckBox, QPushButton, QSizePolicy, QVBoxLayout, QGroupBox,
                             QScrollArea, QFormLayout, QGridLayout, QColorDialog)
from PyQt6.QtCore import QObject, Qt, QSize, QRect, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5
x_gap_h = 2

# ----------------------------------------------------------------------------------------------------------------------

"""
    InfoManager: object that controls the information panels within the central
                 main window information widget
"""


class InfoManager(QWidget):
    # signal functions
    axes_reset = pyqtSignal(QWidget)

    # widget dimensions
    dx_gap = 15

    # field names
    props_name = 'Plot Properties'
    table_name = 'Channel/Unit Information'
    props_tab_lbl = ['Region Configuration']
    table_tab_lbl = ['Channel Info', 'Unit Info']
    plot_types = ['Trace', 'Probe']

    def __init__(self, main_obj, info_width, session_obj=None):
        super(InfoManager, self).__init__()

        # main class fields
        self.main_obj = main_obj
        self.info_width = info_width
        self.session_obj = session_obj

        # class property fields
        self.n_para = 0
        self.p_info = {}

        # boolean class fields
        self.is_updating = False

        # widget layout setup
        self.main_layout = QVBoxLayout()
        self.props_layout = QVBoxLayout()
        self.table_layout = QVBoxLayout()
        # self.scroll_layout = QFormLayout()

        # main widget setup
        self.obj_rconfig = cw.QRegionConfig(
            self, font=cw.font_lbl, is_expanded=True, can_close=False, p_list0=self.plot_types)
        self.group_props = QGroupBox(self.props_name.upper())
        self.group_table = QGroupBox(self.table_name.upper())
        self.tab_group_table = cw.create_tab_group(self)
        self.tab_group_props = cw.create_tab_group(self)

        # self.scroll_area = QScrollArea(self)
        # self.scroll_widget = QWidget()
        # self.status_bar = QStatusBar()

        # other widget setup
        self.status_lbl = cw.create_text_label(None, 'Waiting for process...', cw.font_lbl, align='left')

        # initialises the class fields
        self.init_para_info_fields()
        self.init_class_fields()
        self.init_props_group()
        self.init_table_group()

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
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.group_props)
        self.main_layout.addWidget(self.group_table)
        self.main_layout.addWidget(self.status_lbl)

        # sets the outer group-box properties
        self.group_props.setLayout(self.props_layout)
        self.group_props.setFont(cw.font_panel)
        # self.group_props.setContentsMargins(x_gap, 2 * x_gap, x_gap, x_gap)
        self.group_table.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_pref))

        # sets the outer group-box properties
        self.group_table.setLayout(self.table_layout)
        self.group_table.setFont(cw.font_panel)
        self.group_table.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        # self.group_table.setContentsMargins(0, x_gap, 0, 0)

    def init_props_group(self):

        # sets the property tab group properties
        self.props_layout.setSpacing(0)
        self.props_layout.setContentsMargins(x_gap_h, x_gap_h, x_gap_h, x_gap_h)
        self.props_layout.addWidget(self.tab_group_props)

        # sets up the slot function
        cb_fcn = functools.partial(self.tab_change_props)
        self.tab_group_props.currentChanged.connect(cb_fcn)
        self.tab_group_props.setContentsMargins(0, 0, 0, 0)

        # creates the tab-objects
        for p_lbl in self.p_info:
            self.add_prop_tab(self.p_info[p_lbl], p_lbl)

    def add_prop_tab(self, p_info_tab, p_lbl):

        # field retrieval
        tab_type = p_info_tab['type']
        tab_name = p_info_tab['name']
        tab_para = p_info_tab['ch_fld']

        # sets up the property tab layout
        f_layout = QGridLayout() if tab_type == 'g_panel' else QFormLayout()
        if isinstance(f_layout, QGridLayout):
            # sets the column stretch (Grid Layout only)
            for i in range(3):
                f_layout.setColumnStretch(i, 1)

        # creates the parameter objects
        self.n_para = 0
        for ps_ch in tab_para:
            self.create_para_object(f_layout, ps_ch, tab_para[ps_ch], [p_lbl, ps_ch])
            self.n_para += 1

        # adds the widget to the table
        tab_widget = QWidget()
        tab_widget.setLayout(f_layout)
        self.tab_group_props.addTab(tab_widget, tab_name)

    def init_table_group(self):

        # sets the property tab group properties
        self.table_layout.setSpacing(0)
        self.table_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.table_layout.addWidget(self.tab_group_table)

        # sets up the slot function
        cb_fcn = functools.partial(self.tab_change_table)
        self.tab_group_table.currentChanged.connect(cb_fcn)
        self.tab_group_table.setContentsMargins(0, 0, 0, 0)

        # creates the tab-objects
        for t_lbl in self.table_tab_lbl:
            h_tab = QWidget()
            self.tab_group_table.addTab(h_tab, t_lbl)

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_para_info_fields(self):

        # sets up the subgroup fields
        p_tmp = {
            'r_config': self.create_para_field('Region Configuration', 'rconfig', None),
        }

        # updates the class field
        self.p_info['reg_config'] = {'name': 'Configuration', 'type': 'v_panel', 'ch_fld': p_tmp}

    def create_para_object(self, layout, p_name, ps, p_str_l):

        # base callback function
        cb_fcn = self.setup_widget_callback()

        match ps['type']:
            # -------------------------------------------------------------------
            # Standard Widgets
            # -------------------------------------------------------------------

            # case is a text label
            case 'text':
                # creates the label widget combo
                lbl_str = '%g' % (ps['value'])
                obj_lbl = cw.create_text_label(None, '{0}: '.format(ps['name']), font=cw.font_lbl)
                obj_txt = cw.create_text_label(None, lbl_str, name=p_name, align='left', font=cw.font_lbl)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_txt, self.n_para, 1, 1, 2)

                else:
                    # case is another layout type
                    layout.addRow(obj_lbl, obj_lbl)

            # case is an editbox
            case 'edit':
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

                # sets the widget callback function
                obj_lbledit.connect(cb_fcn)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lbledit.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_lbledit.obj_edit, self.n_para, 1, 1, 2)

                else:
                    # case is another layout type
                    layout.addRow(obj_lbledit)

            # case is a combobox
            case 'combobox':
                # creates the label/combobox widget combo
                lbl_str = '{0}: '.format(ps['name'])
                obj_lblcombo = cw.QLabelCombo(None, lbl_str, ps['p_list'], ps['value'], name=p_name,
                                              font_lbl=cw.font_lbl)

                # sets the widget callback function
                obj_lblcombo.connect(cb_fcn)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lblcombo.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_lblcombo.obj_cbox, self.n_para, 1, 1, 2)

                else:
                    # case is another layout type
                    layout.addRow(obj_lblcombo)

            # case is a checkbox
            case 'checkbox':
                # creates the checkbox widget
                obj_checkbox = cw.QCheckboxHTML(
                    None, ps['name'], ps['value'], font=cw.font_lbl, name=p_name)

                # sets up the checkbox callback function
                cb_fcn_chk = self.setup_widget_callback(obj_checkbox.h_chk)
                obj_checkbox.connect(cb_fcn_chk)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_checkbox, self.n_para, 0, 1, 3)

                else:
                    # case is another layout type
                    layout.addRow(obj_checkbox)

            # case is a pushbutton
            case 'pushbutton':
                # creates the button widget
                obj_button = cw.create_push_button(None, ps['name'], cw.font_lbl, name=p_name)

                # sets the callback function
                cb_fcn_but = self.setup_widget_callback(obj_button)
                obj_button.clicked.connect(cb_fcn_but)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_button, self.n_para, 0, 1, 4)

                else:
                    # case is another layout type
                    layout.addRow(obj_button)

            # -------------------------------------------------------------------
            # Special Widgets
            # -------------------------------------------------------------------

            # case is a tree widget
            case 'tree':
                # creates the trace tree widget
                self.obj_ttree = cw.QTraceTree(self, font=cw.font_lbl)

                # sets the layout properties
                layout.setSpacing(0)
                layout.addWidget(self.obj_ttree)

            # case is a region configuration widget
            case 'rconfig':
                # sets the layout properties
                layout.setSpacing(0)
                layout.addWidget(self.obj_rconfig)

                # connects the config widget slot functions
                self.obj_rconfig.config_reset.connect(self.config_reset)

            # case is a colorpick object
            case 'colorpick':
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
                    layout.addWidget(obj_lblbutton.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_lblbutton.obj_but, self.n_para, 1, 1, 2)

                else:
                    # case is another layout type
                    layout.addRow(obj_lblbutton)

            # case is the axes limit widget
            case 'axeslimits':
                # creates the file selection widget
                self.obj_axlim = cw.QAxesLimits(None, font=cw.font_lbl, p_props=self.p_props)
                layout.addRow(self.obj_axlim)

            # case is a file selection widget
            case 'filespec':
                # creates the file selection widget
                obj_fspec = cw.QFileSpec(None, ps['name'], ps['value'], name=p_name, f_mode=ps['p_misc'])
                layout.addRow(obj_fspec)

                # sets up the slot function
                cb_fcn = functools.partial(self.button_file_spec, p_str_l)
                obj_fspec.connect(cb_fcn)

    # ---------------------------------------------------------------------------
    # Widget Event Functions
    # ---------------------------------------------------------------------------

    def widget_para_update(self, h_widget, *_):

        # case is a widget type is not provided
        if isinstance(h_widget, QLineEdit):
            self.edit_para_update(h_widget)

        elif isinstance(h_widget, QComboBox):
            self.combobox_para_update(h_widget)

        elif isinstance(h_widget, QCheckBox):
            self.checkbox_para_update(h_widget)

        elif isinstance(h_widget, QPushButton):
            self.pushbutton_para_update(h_widget)

    def edit_para_update(self, h_edit):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        nw_val = h_edit.text()
        p_str = h_edit.objectName()
        num_para = ['p_width']

        if p_str in num_para:
            # case is a numerical parameters

            # updates the reset flag
            self.main_obj.was_reset = True

            # sets the parameter limiting properties
            p_min, p_max, is_int = -1e6, 1e6, True
            match p_str:
                case 'p_width':
                    # case is the line pen width
                    p_min, p_max = 1, 5

            # determines if the new value is valid
            chk_val = cf.check_edit_num(nw_val, min_val=p_min, max_val=p_max, is_int=is_int)
            if chk_val[1] is None:
                # case is the value is valid
                setattr(self.p_props, p_str, chk_val[0])

            else:
                # otherwise, reset the previous value
                h_edit.setText('%g' % getattr(self.p_props, p_str))

        else:
            # case is the value is valid
            setattr(self.p_props, p_str, nw_val)

    def combobox_para_update(self, h_cbox):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        p_str = h_cbox.objectName()
        nw_val = h_cbox.currentText()

        # updates the parameter field
        setattr(self.p_props, p_str, nw_val)

    def checkbox_para_update(self, h_chk):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        p_str = h_chk.objectName()
        nw_val = h_chk.isChecked()

        # updates the parameter field
        setattr(self.p_props, p_str, nw_val)

    def pushbutton_para_update(self, h_button):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        p_str = h_button.objectName()
        nw_val = (getattr(self.p_props, p_str) + 1) % 2

        # updates the parameter field
        setattr(self.p_props, p_str, nw_val)

    def tab_change_props(self):

        pass

    def tab_change_table(self):

        pass

    # ---------------------------------------------------------------------------
    # Special Widget Event Functions
    # ---------------------------------------------------------------------------

    def config_reset(self):

        self.axes_reset.emit(self.obj_rconfig)

    def button_file_spec(self, p_str_l, h_fspec):

        a = 1

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
            setattr(self.p_props, p_str, p_col)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def setup_widget_callback(self, h_widget=None):

        if h_widget is None:
            return self.widget_para_update

        else:
            return functools.partial(self.widget_para_update, h_widget)

    def set_styles(self):

        pass

        # # sets the style sheets
        # self.scroll_area.setStyleSheet("background-color: rgba(120, 152, 229, 255) ;")

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}
