# module imports
import re
import functools
import numpy as np
from copy import deepcopy
from collections import ChainMap

# custom module imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.common.common_widget import SearchMixin

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QTreeWidget, QFrame, QCheckBox, QPushButton, QSizePolicy, QVBoxLayout, QGroupBox,
                             QHeaderView, QTreeWidgetItem, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QTableWidget, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

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
    table_tab_lbl = ['Channel Info', 'Unit Info', 'Status Info']
    table_tab_type = ['channel', 'unit']
    tab_type = ['channel', 'preprocess', 'status', 'unit']

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
        self.calc_worker = []

        # boolean class fields
        self.is_updating = False
        self.tab_show = [True, True, True, False]

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

        # module import
        import spike_pipeline.info.info_type as it

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
                        tab_widget.set_update_flag.connect(self.update_flag_change)

                case 'status':
                    tab_widget.start_recalc.connect(self.start_recalc)
                    tab_widget.cancel_recalc.connect(self.cancel_recalc)

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

    def update_flag_change(self, is_updating):

        self.is_updating = is_updating

    def start_recalc(self, p_props):

        status_tab = self.get_info_tab('status')
        p_props_final = dict(ChainMap(*list(p_props.values())))
        status_tab.t_worker = self.session_obj.session.recalc_bad_channel_detect(p_props_final)

    def cancel_recalc(self):

        status_tab = self.get_info_tab('status')
        for t in status_tab.t_worker:
            t.force_quit()

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
        table_obj.horizontalHeader().setSortIndicator(2, Qt.SortOrder.AscendingOrder)
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
        i_row = int(table_obj.item(i_row_s, 2).text())
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

        # module import
        import spike_pipeline.info.info_type as it

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

"""
    InfoWidget: 
"""


class InfoWidget(QWidget):
    #
    x_gap = 5

    # widget stylesheets
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

    def __init__(self, t_lbl, layout=QVBoxLayout):
        super(InfoWidget, self).__init__()

        # field initialisations
        self.table = None
        self.t_lbl = t_lbl

        # field retrieval
        self.tab_layout = layout(self)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.tab_layout)

    def create_table_widget(self):

        # creates the table object
        self.table = QTableWidget(None)

        # sets the table properties
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.table.setObjectName(self.t_lbl)
        self.table.setStyleSheet(self.table_style)
        self.table.verticalHeader().setVisible(False)

        # adds the table to the layout
        self.tab_layout.addWidget(self.table)

        # resets the channel table style
        table_style = cw.CheckBoxStyle(self.table.style())
        self.table.setStyle(table_style)

        # table header setup
        table_header = cw.CheckTableHeader(self.table)
        self.table.setHorizontalHeader(table_header)

# ----------------------------------------------------------------------------------------------------------------------


"""
    InfoWidgetPara: 
"""


class InfoWidgetPara(InfoWidget, SearchMixin):
    # pyqtSignal functions
    prop_updated = pyqtSignal()

    # dimensions
    x_gap = 5
    item_row_size = 23

    # array class fields
    tree_hdr = ['Property', 'Value']

    # font objects
    gray_col = QColor(160, 160, 160, 255)
    item_font = cw.create_font_obj(9, True, QFont.Weight.Bold)
    item_child_font = cw.create_font_obj(8)

    # widget stylesheets
    tree_style = """    
        QTreeWidget {
            font: Arial 8px;
        }

        QTreeWidget::item {
            height: 23px;
        }        

        QTreeWidget::item:has-children {
            background: #A0A0A0;
            padding-left: 5px;
            color: white;
        }
    """

    def __init__(self, t_lbl, layout=QVBoxLayout):
        super(InfoWidgetPara, self).__init__(t_lbl, layout)
        SearchMixin.__init__(self)

        # initialisations
        self.p_props = {}
        self.s_props = {}
        self.s_type = None
        self.p_prop_flds = {}
        self.s_prop_flds = None

        # boolean class fields
        self.is_updating = False
        self.is_sort_para = False

        # initialisations
        self.n_grp, self.n_para = 0, 0
        self.h_grp, self.h_para = {}, []
        self.para_name0, self.para_name, self.para_grp, self.grp_name = [], [], [], []

        # property sorting group widgets
        self.edit_search = None
        self.tree_prop = QTreeWidget(self)

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_filter_edit(self):

        # sets the layout properties
        self.tab_layout.setSpacing(5)
        self.tab_layout.setHorizontalSpacing(0)

        # initialises the filter widgets
        self.init_search_widgets()

    def init_property_frame(self):

        # sets the tree-view properties
        self.tree_prop.setLineWidth(1)
        self.tree_prop.setColumnCount(2)
        self.tree_prop.setIndentation(12)
        self.tree_prop.setItemsExpandable(True)
        self.tree_prop.setStyleSheet(self.tree_style)
        self.tree_prop.setHeaderLabels(self.tree_hdr)
        self.tree_prop.setFrameStyle(QFrame.Shape.WinPanel | QFrame.Shadow.Plain)
        self.tree_prop.setAlternatingRowColors(True)
        self.tree_prop.setItemDelegateForColumn(0, cw.HTMLDelegate())

        # creates the full property tree
        for pp_s, pp_h in self.p_prop_flds.items():
            # creates the parent item
            item = QTreeWidgetItem(self.tree_prop)

            # sets the item properties
            item.setText(0, pp_h['name'])
            item.setFont(0, self.item_font)
            item.setFirstColumnSpanned(True)
            item.setExpanded(True)

            # adds the main group to the search widget
            self.append_grp_obj(item, pp_s)

            # adds the tree widget item
            self.tree_prop.addTopLevelItem(item)
            for k, p in pp_h['props'].items():
                # creates the property name field
                item_ch, obj_prop = self.create_child_tree_item(p, [pp_s, k])
                item_ch.setTextAlignment(0, cw.align_flag['right'] | cw.align_flag['vcenter'])
                obj_prop.setFixedHeight(self.item_row_size)

                # adds the child tree widget item
                item.addChild(item_ch)
                self.append_para_obj(item_ch, pp_s)
                self.tree_prop.setItemWidget(item_ch, 1, obj_prop)

        # adds the tree widget to the parent widget
        self.tab_layout.addWidget(self.tree_prop)

        # resizes the columns to fit, then resets to fixed size
        tree_header = self.tree_prop.header()
        tree_header.setDefaultAlignment(cf.align_type['center'])
        tree_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tree_header.updateSection(0)
        tree_header.updateSection(1)
        tree_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        tree_header.setStyleSheet("background: rgba(240, 240, 255, 255);")

    # ---------------------------------------------------------------------------
    # Property Field Functions
    # ---------------------------------------------------------------------------

    def create_para_object(self, layout, p_str, p_val, p_type, p_str_p):

        # retrieves the sort parameter
        is_sort = deepcopy(self.is_sort_para)

        match p_type:
            case 'tab':
                # case is a tab widget

                # creates the tab widget
                obj_tab = QWidget()
                obj_tab.setObjectName(p_str)

                # creates the children objects for the current parent object
                tab_layout = QFormLayout(obj_tab)
                tab_layout.setSpacing(0)
                tab_layout.setContentsMargins(1, 1, 0, 0)
                tab_layout.setLabelAlignment(cf.align_type['right'])

                # creates the panel object
                panel_frame = QFrame()
                panel_frame.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
                panel_frame.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
                tab_layout.addWidget(panel_frame)

                # sets up the parameter layout
                layout_para = QFormLayout(panel_frame)
                layout_para.setLabelAlignment(cf.align_type['right'])
                layout_para.setSpacing(self.x_gap)
                layout_para.setContentsMargins(2 * self.x_gap, 2 * self.x_gap, 2 * self.x_gap, self.x_gap)

                # creates the tab parameter objects
                for k, v in p_val.items():
                    self.create_para_object(layout_para, k, v, v['type'], p_str_p + [k])

                # sets the tab layout
                panel_frame.setLayout(layout_para)
                obj_tab.setLayout(tab_layout)

                # returns the tab object
                return obj_tab

            case 'edit':
                # sets up the editbox string
                lbl_str = '{0}'.format(p_val['name'])
                if p_val['value'] is None:
                    # parameter string is empty
                    edit_str = ''

                elif isinstance(p_val['value'], str):
                    # parameter is a string
                    edit_str = p_val['value']

                else:
                    # parameter is numeric
                    edit_str = '%g' % (p_val['value'])

                # creates the label/editbox widget combo
                obj_edit = cw.QLabelEdit(None, lbl_str, edit_str, name=p_str, font_lbl=cw.font_lbl)
                # obj_edit.obj_lbl.setFixedWidth(self.lbl_width)
                layout.addRow(obj_edit)

                # sets up the label/editbox slot function
                cb_fcn = functools.partial(self.prop_update, p_str_p, is_sort)
                obj_edit.connect(cb_fcn)

            # case is a combobox
            case 'combobox':
                # creates the label/combobox widget combo
                lbl_str = '{0}'.format(p_val['name'])
                obj_combo = cw.QLabelCombo(
                    None, lbl_str, p_val['p_list'], p_val['value'], name=p_str, font_lbl=cw.font_lbl)
                layout.addRow(obj_combo)

                # sets up the slot function
                cb_fcn = functools.partial(self.prop_update, p_str_p, is_sort)
                obj_combo.connect(cb_fcn)
                obj_combo.obj_lbl.setStyleSheet('padding-top: 3 px;')

            # case is a checkbox
            case 'checkbox':
                # creates the checkbox widget
                obj_checkbox = cw.create_check_box(
                    None, p_val['name'], p_val['value'], font=cw.font_lbl, name=p_str)
                obj_checkbox.setContentsMargins(0, 0, 0, 0)

                # adds the widget to the layout
                layout.addRow(obj_checkbox)

                # sets up the slot function
                cb_fcn = functools.partial(self.prop_update, p_str_p, is_sort, obj_checkbox)
                obj_checkbox.stateChanged.connect(cb_fcn)

    def prop_update(self, p_str, is_sort, h_obj):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        if isinstance(h_obj, QCheckBox):
            self.check_prop_update(h_obj, is_sort, p_str)

        elif isinstance(h_obj, QLineEdit):
            self.edit_prop_update(h_obj, is_sort, p_str)

        elif isinstance(h_obj, QComboBox):
            self.combo_prop_update(h_obj, is_sort, p_str)

        elif isinstance(h_obj, QSpinBox):
            self.spinbox_prop_update(h_obj, is_sort, p_str)

        elif isinstance(h_obj, QDoubleSpinBox):
            self.doublespinbox_prop_update(h_obj, is_sort, p_str)

        # flag that the property has been updated
        self.prop_updated.emit()

    def check_prop_update(self, h_obj, is_sort, p_str):

        p = self.get_prop_field(is_sort)
        cf.set_multi_dict_value(p, p_str, h_obj.isChecked())

    def edit_prop_update(self, h_obj, is_sort, p_str):

        # field retrieval
        str_para = []
        nw_val = h_obj.text()
        p = self.get_prop_field(is_sort)

        if p_str in str_para:
            # case is a string field
            cf.set_multi_dict_value(p, p_str, nw_val)

        else:
            # determines if the new value is valid
            chk_val = cf.check_edit_num(nw_val, min_val=0)
            if chk_val[1] is None:
                # case is the value is valid
                cf.set_multi_dict_value(p, p_str, chk_val[0])

            else:
                # otherwise, reset the previous value
                p_val_pr = p[p_str[0]][p_str[1]]
                if (p_val_pr is None) or isinstance(p_val_pr, str):
                    # case is the parameter is empty
                    h_obj.setText('')

                else:
                    # otherwise, update the numeric string
                    h_obj.setText('%g' % p_val_pr)

    def combo_prop_update(self, h_obj, is_sort, p_str):

        p = self.get_prop_field(is_sort)
        cf.set_multi_dict_value(p, p_str, h_obj.currentText())

    def spinbox_prop_update(self, h_obj, is_sort, p_str):

        p = self.get_prop_field(is_sort)
        spin_val = cf.check_edit_num(h_obj.text(), is_int=True)
        cf.set_multi_dict_value(p, p_str, spin_val[0])

    def doublespinbox_prop_update(self, h_obj, is_sort, p_str):

        p = self.get_prop_field(is_sort)
        spin_val = cf.check_edit_num(h_obj.text(), is_int=False)
        cf.set_multi_dict_value(p, p_str, spin_val[0])

    def sort_tab_change(self):

        i_tab_nw = self.tab_group_sort.currentIndex()
        self.s_type = list(self.s_prop_flds)[i_tab_nw]

    def node_value_update(self):

        a = 1

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def get_prop_field(self, is_sort):

        return self.s_props if is_sort else self.p_props

    def get_all_prop_fields(self):

        return self.p_props, self.s_props

    def append_para_obj(self, item, group_name):

        # increments the count
        self.n_para += 1
        p_name_s = re.sub(r'<[^>]*>|[&;]+', '', item.text(0))

        # appends the objects
        self.h_para.append(item)
        self.para_name.append(p_name_s.lower())
        self.para_name0.append(p_name_s)
        self.para_grp.append(group_name)

    def append_grp_obj(self, item, group_str):

        # increments the count
        self.n_grp += 1

        # appends the objects
        self.h_grp[group_str] = item
        self.grp_name.append(item.text(0))

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}

    def create_child_tree_item(self, props, p_name):

        # initialisations
        lbl_str = '{0}'.format(props['name'])
        cb_fcn_base = functools.partial(self.prop_update, p_name, False)

        # creates the tree widget item
        item_ch = QTreeWidgetItem(None)
        item_ch.setText(0, lbl_str)

        match props['type']:
            case 'edit':
                # case is a lineedit
                p_value = props['value']

                # calculates the parameter spinbox step value
                if p_value == 0:
                    # case is the parameter value is zero
                    step = 1

                else:
                    # case is the parameter value is non-zero
                    step = 10 ** np.floor(np.log10(np.abs(p_value)) - 1)

                # creates the spinbox based on the parameter type
                if isinstance(props['value'], int):
                    # case is the parameter is an integer
                    h_obj = QSpinBox()
                    step = int(np.max([1, step]))

                else:
                    # case is the parameter is a float
                    h_obj = QDoubleSpinBox()

                # sets the widget properties
                h_obj.setRange(-1000, 1000)
                h_obj.setValue(props['value'])
                h_obj.setObjectName(p_name[-1])
                h_obj.setSingleStep(step)

                # sets the object callback functions
                cb_fcn = functools.partial(cb_fcn_base, h_obj)
                h_obj.editingFinished.connect(cb_fcn)
                h_obj.textChanged.connect(cb_fcn)

            case 'combobox':
                # case is a comboboxW
                h_obj = QComboBox()

                # adds the combobox items
                for p in props['p_list']:
                    h_obj.addItem(p)

                # sets the widget properties
                i_sel0 = props['p_list'].index(props['value'])
                h_obj.setCurrentIndex(i_sel0)

                # sets the object callback functions
                cb_fcn = functools.partial(cb_fcn_base, h_obj)
                h_obj.currentIndexChanged.connect(cb_fcn)

            case 'checkbox':
                # case is a checkbox
                h_obj = QCheckBox()

                # sets the widget properties
                h_obj.setCheckState(cf.chk_state[props['value']])
                h_obj.setStyleSheet("padding-left: 5px;")

                # sets the object callback functions
                cb_fcn = functools.partial(cb_fcn_base, h_obj)
                h_obj.clicked.connect(cb_fcn)

            case _:
                # default case
                if isinstance(props['value'], str):
                    p_str = props['value']

                else:
                    p_str = "%g" % props['value']

                h_obj = cw.QLabel(p_str)

        # returns the objects
        return item_ch, h_obj

# ----------------------------------------------------------------------------------------------------------------------

