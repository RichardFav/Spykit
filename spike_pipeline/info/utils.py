# module imports
import numpy as np
import functools

# custom module imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QLineEdit, QComboBox, QCheckBox, QPushButton, QSizePolicy, QVBoxLayout, QGroupBox,
                             QHeaderView, QFormLayout, QGridLayout, QColorDialog, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5
x_gap2 = 2 * x_gap
x_gap_h = 2

# ----------------------------------------------------------------------------------------------------------------------

"""
    InfoManager: object that controls the information panels within the central
                 main window information widget
"""


class InfoManager(QWidget):
    # signal functions
    unit_check = pyqtSignal(object)
    unit_header_check = pyqtSignal(object)
    channel_check = pyqtSignal(object)
    channel_header_check = pyqtSignal(object)
    config_update = pyqtSignal(object)
    axes_reset = pyqtSignal(QWidget)

    # widget dimensions
    dx_gap = 15

    # field names
    props_name = 'Plot Properties'
    table_name = 'Channel/Unit Information'
    props_tab_lbl = ['Region Configuration']
    plot_types = ['Trace', 'Probe']
    table_tab_lbl = ['Channel Info', 'Unit Info']
    table_tab_type = ['channel', 'unit']

    # font types
    table_font = cw.create_font_obj(size=8)
    table_hdr_font = cw.create_font_obj(size=8, is_bold=True, font_weight=QFont.Weight.Bold)

    # table cell item flags
    norm_item_flag = Qt.ItemFlag.ItemIsEnabled
    check_item_flag = norm_item_flag | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable

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
        self.tabs = []
        self.t_types = []
        self.main_layout = QVBoxLayout()
        self.props_layout = QVBoxLayout()
        self.table_layout = QVBoxLayout()

        # main widget setup
        gbox_height = self.info_width - 4 * x_gap
        self.obj_rconfig = cw.QRegionConfig(self, font=cw.font_lbl, is_expanded=True,
                                            p_list0=self.plot_types, gbox_height=gbox_height)
        self.group_props = QGroupBox(self.props_name.upper())
        self.group_table = QGroupBox(self.table_name.upper())
        self.tab_group_table = cw.create_tab_group(self)
        self.tab_group_props = cw.create_tab_group(self)

        # other widget setup
        self.status_lbl = cw.create_text_label(None, 'Waiting for process...', cw.font_lbl, align='left')

        # initialises the class fields
        self.init_para_info_fields()
        self.init_class_fields()
        self.init_props_group()
        self.init_table_group()

        # sets the class stylesheets
        self.set_styles()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the main widget properties
        self.setFixedWidth(self.info_width + self.dx_gap)
        self.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_exp))
        self.setLayout(self.main_layout)

        # sets the widget layout properties
        self.main_layout.setSpacing(x_gap)
        self.main_layout.setContentsMargins(x_gap2, x_gap2, x_gap2, x_gap2)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.group_props)
        self.main_layout.addWidget(self.group_table)
        self.main_layout.addWidget(self.status_lbl)

        # sets the outer group-box properties
        self.group_props.setLayout(self.props_layout)
        self.group_props.setFont(cw.font_panel)

        # sets the outer group-box properties
        self.group_table.setLayout(self.table_layout)
        self.group_table.setFont(cw.font_panel)
        self.group_table.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

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

        # creates the tab-objects
        for p_lbl in self.p_info:
            self.add_prop_tab(self.p_info[p_lbl], p_lbl)

        # sets the region configuration slot function
        self.obj_rconfig.config_reset.connect(self.update_config)

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
        self.tab_group_table.setVisible(False)

        # sets the property tab group properties
        self.table_layout.setSpacing(0)
        self.table_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.table_layout.addWidget(self.tab_group_table)

        # sets up the slot function
        cb_fcn = functools.partial(self.tab_change_table)
        self.tab_group_table.currentChanged.connect(cb_fcn)
        self.tab_group_table.setContentsMargins(0, 0, 0, 0)

        # creates the tab-objects
        tab_type = ['channel', 'unit', 'preprocess']
        for t_type in tab_type:
            # creates the tab widget (based on type)
            t_lbl = it.info_names[t_type]
            tab_constructor = it.info_types[t_type]
            tab_widget = tab_constructor(t_lbl)
            self.tabs.append(tab_widget)

            # sets the
            self.t_types.append(t_type)
            match t_type:
                case t_type if t_type in ['channel', 'unit']:
                    # connects the
                    cb_fcn = functools.partial(self.header_check_update, t_lbl)
                    # tab_widget.set_check_update(cb_fcn)
                    tab_widget.table.horizontalHeader().check_update.connect(cb_fcn)

                    # performs tab specific updates
                    if t_type == 'channel':
                        # case is the channel tab
                        tab_widget.data_change.connect(self.channel_combobox_update)
                        tab_widget.run_change.connect(self.channel_combobox_update)

            # appends the tab to the tab group
            self.tab_group_table.addTab(tab_widget, t_lbl)

    def add_info_widgets(self):

        self.tab_group_table.setVisible(True)
        self.tab_group_props.setVisible(True)
        # self.main_layout.addWidget(self.status_lbl)

    # ---------------------------------------------------------------------------
    # Channel Tab Event Functions
    # ---------------------------------------------------------------------------

    def channel_combobox_update(self, tab_obj):

        # if manually updating the combobox, then exit
        if self.is_updating:
            return

        # updates the current run flag
        new_run = tab_obj.run_type.current_text()
        self.main_obj.session_obj.set_current_run(new_run)

        # updates the current preprocessing data type
        i_data = tab_obj.data_type.current_index()
        self.main_obj.session_obj.set_prep_type(tab_obj.data_flds[i_data])

        # resets the trace view
        self.main_obj.plot_manager.reset_trace_views()

    def init_channel_comboboxes(self):

        # combobox fields
        data_list = ['Raw']
        run_list = self.session_obj.session.get_run_names()

        # flag that manual updating is taking place
        self.is_updating = True

        # resets the combobox fields
        channel_tab = self.get_info_tab('channel')
        channel_tab.reset_combobox_fields('data', data_list)
        channel_tab.reset_combobox_fields('run', run_list)

        # resets the update flag
        self.is_updating = False

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

    def setup_info_table(self, data, t_type, c_hdr):

        # retrieves the table widget
        table_obj = self.get_table_widget(t_type)

        # clears the table model
        table_obj.clear()
        table_obj.setRowCount(data.shape[0])
        table_obj.setColumnCount(data.shape[1])

        # sets the table header view
        table_obj.setHorizontalHeaderLabels(c_hdr)

        for i_col in range(data.shape[1]):
            # updates the table header font
            table_obj.horizontalHeaderItem(i_col).setFont(self.table_hdr_font)

            for i_row in range(data.shape[0]):
                # creates the widget item
                item = cw.QTableWidgetItemSortable()
                item.setFont(self.table_font)

                # sets the item properties (based on the field values)
                value = data.iloc[i_row][data.columns[i_col]]
                if isinstance(value, np.bool_):
                    # case is a boolean field
                    item.setFlags(self.check_item_flag)
                    item.setCheckState(cf.chk_state[value])

                else:
                    # case is a string field
                    item.setFlags(self.norm_item_flag)
                    item.setText(str(value))

                # ads the item to the table
                item.setTextAlignment(cf.align_type['center'])
                table_obj.setItem(i_row, i_col, item)

        # resizes the table to the contents
        table_obj.setSortingEnabled(True)
        table_obj.horizontalHeader().setSortIndicator(1, Qt.SortOrder.AscendingOrder)
        # table_obj.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # table_obj.resizeRowsToContents()
        # table_obj.resizeColumnsToContents()

        # sets the checkbox callback function
        cb_fcn = functools.partial(self.table_cell_changed, t_type)
        table_obj.cellChanged.connect(cb_fcn)

    def table_cell_changed(self, t_type, i_row_s, i_col):

        # if manually updating, then exit
        if self.is_updating:
            return

        # retrieves the table widget
        table_obj = self.get_table_widget(t_type)
        i_row = int(table_obj.item(i_row_s, 1).text())
        self.update()

        match t_type.lower():
            case 'channel':
                # case is the channel information tab
                self.channel_check.emit(i_row)

            case 'unit':
                # case is the unit information tab
                self.unit_check.emit(i_row)

            case 'preprocess':
                # case is the preprocessing information tab
                pass

    def get_table_widget(self, t_type):

        info_c = it.info_types[t_type.split()[0].lower()]
        i_tab = next(i for i, x in enumerate(self.tabs) if isinstance(x, info_c))
        return self.tabs[i_tab].findChild(QTableWidget)

    def get_column_values(self, t_type, i_col):

        # retrieves the table widget
        table_obj = self.get_table_widget(t_type)

        a = 1

    def update_table_value(self, t_type, i_row, value):

        # flag that updating is taking place
        self.is_updating = True

        # updates the channel item checkmark
        table_channel = self.get_table_widget(t_type)
        for i_r, val in zip(i_row, value):
            table_channel.item(i_r, 0).setCheckState(cf.chk_state[val])

        # updates the header checkbox tri-state value
        self.update_header_checkbox_state(t_type)

        # resets the update flag
        self.is_updating = False

    def update_header_checkbox_state(self, t_type):

        # sets the status flag based on the current selections
        i_sel_ch = self.session_obj.get_selected_channels()
        if len(i_sel_ch) == 0:
            # case is no channels have been selected
            i_status = 0

        else:
            # case is at least one channel has been selecte
            i_status = 1 + (len(i_sel_ch) == self.session_obj.get_channel_count())

        # resets the table header checkbox value
        table_obj = self.get_table_widget(t_type)
        table_obj.horizontalHeader().setCheckState(i_status)

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

    def header_check_update(self, t_type, i_state, i_col):

        match t_type:
            case 'Channel':
                # case is the channel information table
                self.channel_header_check.emit(i_state == 2)

            case 'Unit':
                # case is the unit information table
                self.unit_header_check.emit(i_state == 2)

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

    def update_config(self):

        self.config_update.emit(self.obj_rconfig.c_id)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def reset_table_selections(self, t_type, is_sel):

        # sets the update flag
        self.is_updating = True

        # retrieves and clears the table object
        table_obj = self.get_table_widget(t_type)

        # resets the checkbox state
        for i_row, state in enumerate(is_sel):
            table_obj.item(i_row, 0).setCheckState(cf.chk_state[state])

        # resets the update flag
        self.is_updating = False

    def get_region_config(self):

        return self.obj_rconfig.c_id

    def set_region_config(self, c_id):

        self.obj_rconfig.reset_selector_widgets(c_id)

    def get_info_tab(self, tab_type):

        return self.tabs[self.t_types.index(tab_type)]

    def setup_widget_callback(self, h_widget=None):

        if h_widget is None:
            return self.widget_para_update

        else:
            return functools.partial(self.widget_para_update, h_widget)

    def set_styles(self):

        # widget stylesheets
        info_groupbox_style = """
            background-color: rgba(240, 240, 255, 255);
        """

        # sets the group style sheets
        self.tab_group_props.setStyleSheet(info_groupbox_style)
        self.group_props.setStyleSheet(info_groupbox_style)
        self.group_table.setStyleSheet(info_groupbox_style)

        pass

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}

# ----------------------------------------------------------------------------------------------------------------------

# module imports (required here as will cause circular import error otherwise)
import spike_pipeline.info.info_type as it