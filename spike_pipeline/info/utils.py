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

    # widget dimensions
    dx_gap = 15

    # field names
    table_name = 'Channel/Unit Information'
    table_tab_lbl = ['Channel Info', 'Unit Info']
    table_tab_type = ['channel', 'unit']
    tab_type = ['channel', 'preprocess', 'unit']

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
        self.tab_show = [True, True, False]

        # widget layout setup
        self.tabs = []
        self.t_types = []
        self.main_layout = QVBoxLayout()
        self.table_layout = QVBoxLayout()

        # main widget setup
        self.group_table = QGroupBox(self.table_name.upper())
        self.tab_group_table = cw.create_tab_group(self)

        # other widget setup
        self.status_lbl = cw.create_text_label(None, 'Waiting for process...', cw.font_lbl, align='left')

        # initialises the class fields
        self.init_class_fields()
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
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(x_gap2, 0, x_gap2, x_gap2)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.group_table)
        self.main_layout.addWidget(self.status_lbl)

        # sets the outer group-box properties
        self.group_table.setLayout(self.table_layout)
        self.group_table.setFont(cw.font_panel)
        self.group_table.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

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
        for i_tab, t_type in enumerate(self.tab_type):
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
                        tab_widget.status_change.connect(self.channel_status_update)

            # appends the tab to the tab group
            self.tab_group_table.addTab(tab_widget, t_lbl)
            self.tab_group_table.setTabEnabled(i_tab, self.tab_show[i_tab])

    def add_info_widgets(self):

        self.tab_group_table.setVisible(True)
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
        if tab_obj.data_flds is not None:
            i_data = tab_obj.data_type.current_index()
            self.main_obj.session_obj.set_prep_type(tab_obj.data_flds[i_data])

        # resets the trace view
        self.main_obj.plot_manager.reset_trace_views(False)

    def channel_status_update(self, tab_obj, is_filt):

        self.session_obj.channel_data.set_filter_flag(is_filt)

        probe_view = self.main_obj.plot_manager.get_plot_view('probe')
        probe_view.sub_view.create_probe_plot()

        trace_view = self.main_obj.plot_manager.get_plot_view('trace')
        trace_view.reset_trace_view()

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
                if i_col == 0:
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
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_tab_enabled(self, i_tab, s_flag):

        if isinstance(i_tab, str):
            i_tab = self.t_types.index(i_tab)

        # updates the table flag
        self.tab_show[i_tab] = s_flag
        self.tab_group_table.setTabEnabled(i_tab, s_flag)

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

    def get_info_tab(self, tab_type):

        return self.tabs[self.t_types.index(tab_type)]

    def set_styles(self):

        # widget stylesheets
        info_groupbox_style = """
            background-color: rgba(240, 240, 255, 255);
        """

        # sets the group style sheets
        self.group_table.setStyleSheet(info_groupbox_style)

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
