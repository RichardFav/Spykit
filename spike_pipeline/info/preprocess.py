# module imports
import re
import functools
from copy import deepcopy

# custom module imports
import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.common_func as cf
from spike_pipeline.info.common import InfoTab
from spike_pipeline.common.common_widget import QLabelEdit, QLabelCombo

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QFrame, QTreeView, QTabWidget, QVBoxLayout, QFormLayout, QSizePolicy,
                             QCheckBox, QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem, QHeaderView)
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont
from PyQt6.QtCore import QSize, QModelIndex

# ----------------------------------------------------------------------------------------------------------------------

"""
    SearchMixin:
"""


class SearchMixin:

    def init_search_widgets(self):

        # initialisations
        edit_pixmap = QIcon(cw.icon_path['search']).pixmap(QSize(cf.but_height, cf.but_height))

        # creates the pixmap object
        filter_obj = QLabelEdit(None, '', '')

        # filter label properties
        filter_obj.obj_lbl.setPixmap(edit_pixmap)
        filter_obj.obj_lbl.setFixedHeight(cf.but_height)

        # filter line edit properties
        self.edit_search = filter_obj.obj_edit
        self.edit_search.textChanged.connect(self.edit_search_change)
        self.edit_search.setPlaceholderText("Search Filter")
        self.edit_search.setFixedHeight(cf.but_height)

        # sets the object style sheets
        filter_obj.obj_lbl.setStyleSheet("""
            border: 1px solid;
            border-right-style: None;
        """)
        self.edit_search.setStyleSheet("""
            border: 1px solid;                
            border-left-style: None;            
        """)

        # adds the widget to the layout
        self.tab_layout.addRow(filter_obj.obj_lbl, self.edit_search)

    def edit_search_change(self):

        # field retrieval
        s_txt = self.edit_search.text().lower()
        ns_txt = len(s_txt)


# ----------------------------------------------------------------------------------------------------------------------

"""
    PreprocessInfoTab:
"""


class PreprocessInfoTab(SearchMixin, InfoTab):
    # array class fields
    tree_hdr = ['Property', 'Value']
    pp_flds = {
        'bandpass_filter': 'Bandpass Filter',
        'common_reference': 'Common Reference',
        'phase_shift': 'Phase Shift',
        'whitening': 'Whitening',
        'drift_correct': 'Drift Correction',
        'waveforms': 'Wave Forms',
        'sparce_opt': 'Sparsity Options',
    }

    # font objects
    item_font = cw.create_font_obj(9, True, QFont.Weight.Bold)

    # widget stylesheets
    tree_style = """
        QTreeWidget {
            font: Arial 8px;
        }
        
        QTreeWidget::item {
            background: #A0A0A0;
            color: white;   
        }    

        QTreeWidget::branch:open:has-children:has-siblings {

        }              
    """

    # dimensions
    x_gap = 5

    def __init__(self, t_str):
        super(PreprocessInfoTab, self).__init__(t_str, layout=QFormLayout)
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

        # sorting group widgets
        self.frame_sort = QFrame(self)
        self.tab_group_sort = QTabWidget(self)
        self.layout_sort = QVBoxLayout()

        # initialises the major widget groups
        self.setup_prop_fields()
        self.init_filter_edit()
        self.init_property_frame()
        self.init_sorting_frame()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_prop_fields(self):

        # -----------------------------------------------------------------------
        # Preprocessing Properties
        # -----------------------------------------------------------------------

        # list arrays
        mode_list = ['global', 'local']
        operator_list = ['median', 'average']
        reference_list = ['global', 'single', 'local']
        preset_list = ['dredge', 'dredge_fast', 'nonrigid_accurate',
                       'nonrigid_fast_and_accurate', 'rigid_fast', 'kilosort_like']

        # sets up the parameter fields
        pp_str = [
            # bandpass filter parameters
            {
                'freq_min': self.create_para_field('Min Frequency', 'edit', 300),
                'freq_max': self.create_para_field('Max Frequency', 'edit', 6000),
                'margin_ms': self.create_para_field('Border Margin (ms)', 'edit', 5),
            },

            # common reference parameters
            {
                'operator': self.create_para_field('Operator', 'combobox', operator_list[0], p_list=operator_list),
                'reference': self.create_para_field('Reference', 'combobox', reference_list[0], p_list=reference_list),
            },

            # phase shift parameters
            {
                'margin_ms': self.create_para_field('Margin (ms)', 'edit', 40),
            },

            # whitening parameters
            {
                'apply_mean': self.create_para_field('Subtract Mean', 'checkbox', False),
                'mode': self.create_para_field('Mode', 'combobox', mode_list[0], p_list=mode_list),
                'radius_um': self.create_para_field('Reference Radius (um)', 'edit', 100),
            },

            # drift correction parameters
            {
                'preset': self.create_para_field('Preset', 'combobox', preset_list[0], p_list=preset_list),
            },
        ]

        # sets up the property fields for each section
        for pp_k, pp_s in zip(self.pp_flds.keys(), pp_str):
            # sets up the parent fields
            self.p_props[pp_k] = {}
            self.p_prop_flds[pp_k] = {
                'name': self.pp_flds[pp_k],
                'props': pp_s,
            }

            # sets the children properties
            for k, p in pp_s.items():
                self.p_props[pp_k][k] = p['value']

        # -----------------------------------------------------------------------
        # Sorting Properties
        # -----------------------------------------------------------------------

        # sets up the sorting tab parameter fields
        pp_k2 = {'car': self.create_para_field('Use Common Avg Ref.', 'checkbox', False, p_fld='kilosort2'),
                 'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2')}
        pp_k2_5 = {'car': self.create_para_field('Use Common Avg Ref.', 'checkbox', False, p_fld='kilosort2_5'),
                   'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2_5'), }
        pp_k3 = {'car': self.create_para_field('Use Common Avg Ref.', 'checkbox', False, p_fld='kilosort3'),
                 'freq_min': self.create_para_field('Min Frequency', 'edit', 300, p_fld='kilosort3'), }
        pp_m5 = {'scheme': self.create_para_field('Scheme', 'edit', 2, p_fld='mountainsort5'),
                 'filter': self.create_para_field('Filter', 'checkbox', False, p_fld='mountainsort5'), }

        # stores the sorting properties
        self.s_prop_flds = {
            'kilosort2': {'name': 'KiloSort 2', 'props': pp_k2},
            'kilosort2_5': {'name': 'KiloSort 2.5', 'props': pp_k2_5},
            'kilosort3': {'name': 'KiloSort 3', 'props': pp_k3},
            'mountainsort5': {'name': 'MountainSort 5', 'props': pp_m5},
        }

        # initialises the fields for all properties
        self.is_sort_para = True
        for kp, vp in self.s_prop_flds.items():
            # sets up the parent field
            self.s_props[kp] = {}

            # sets the children properties
            for k, p in vp['props'].items():
                self.s_props[kp][k] = p['value']

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
        self.tree_prop.setIndentation(10)
        self.tree_prop.setItemsExpandable(True)
        self.tree_prop.setStyleSheet(self.tree_style)
        self.tree_prop.setHeaderLabels(self.tree_hdr)
        self.tree_prop.setFrameStyle(QFrame.Shape.WinPanel | QFrame.Shadow.Plain)

        # creates the full property tree
        i_row = 0
        i_row_p = 0
        for pp_s, pp_h in self.p_prop_flds.items():
            # creates the parent item
            item = QTreeWidgetItem(self.tree_prop)

            # sets the item properties
            item.setText(0, pp_h['name'])
            item.setFont(0, self.item_font)
            item.setFirstColumnSpanned(True)
            item.setExpanded(True)

            for k, v in pp_h['props'].items():
                # creates the property name field
                item_name = QTreeWidgetItem(None)
                item_name.setText(0, v['name'])
                # self.tree_prop.setItemWidget(item_name, 0)

                # adds the child tree widget item
                item.addChild(item_name)
                i_row += 1

            # adds the tree widget item
            self.tree_prop.addTopLevelItem(item)

        # adds the tree widget to the parent widget
        self.tab_layout.addRow(self.tree_prop)

        # resizes the columns to fit, then resets to fixed size
        tree_header = self.tree_prop.header()
        tree_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tree_header.updateSection(0)
        tree_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

    def init_sorting_frame(self):

        # initialisations
        self.s_type = 'mountainsort5'

        # sets the frame properties
        self.frame_sort.setLineWidth(1)
        self.frame_sort.setFixedHeight(100)
        self.frame_sort.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.WinPanel)
        # self.frame_sort.setStyleSheet("border: 1px solid;")

        # adds the tab group to the layout
        self.frame_sort.setLayout(self.layout_sort)
        self.layout_sort.setSpacing(0)
        self.layout_sort.setContentsMargins(0, 0, 0, 0)
        self.layout_sort.addWidget(self.tab_group_sort)

        # creates the tab group object
        for k, v in self.s_prop_flds.items():
            tab_layout = QVBoxLayout()
            obj_tab = self.create_para_object(tab_layout, k, v['props'], 'tab', [k])
            self.tab_group_sort.addTab(obj_tab, v['name'])

        # tab-group change callback function
        i_tab0 = list(self.s_props.keys()).index(self.s_type)
        self.tab_group_sort.setCurrentIndex(i_tab0)
        self.tab_group_sort.currentChanged.connect(self.sort_tab_change)

        # adds the frame to the parent widget
        self.tab_layout.addRow(self.frame_sort)

    def node_value_update(self):

        a = 1

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
                self.n_para = 0
                for k, v in p_val.items():
                    self.create_para_object(layout_para, k, v, v['type'], p_str_p + [k])
                    self.n_para += 1

                # sets the tab layout
                panel_frame.setLayout(layout_para)
                obj_tab.setLayout(tab_layout)

                # returns the tab object
                return obj_tab

            case 'edit':
                # sets up the editbox string
                lbl_str = '{0}: '.format(p_val['name'])
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
                obj_edit = QLabelEdit(None, lbl_str, edit_str, name=p_str, font_lbl=cw.font_lbl)
                # obj_edit.obj_lbl.setFixedWidth(self.lbl_width)
                layout.addRow(obj_edit)

                # sets up the label/editbox slot function
                cb_fcn = functools.partial(self.prop_update, p_str_p, is_sort)
                obj_edit.connect(cb_fcn)

            # case is a combobox
            case 'combobox':
                # creates the label/combobox widget combo
                lbl_str = '{0}: '.format(p_val['name'])
                obj_combo = QLabelCombo(None, lbl_str, p_val['p_list'], p_val['value'], name=p_str, font_lbl=cw.font_lbl)
                layout.addRow(obj_combo)

                # sets up the slot function
                cb_fcn = functools.partial(self.prop_update, p_str_p, is_sort)
                obj_combo.connect(cb_fcn)
                obj_combo.obj_lbl.setStyleSheet('padding-top: 3 px;')

                # # appends the parameter search objects
                # self.search_dlg.append_para_obj(obj_lbl, ps['name'], p_str_l[1])

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

    def sort_tab_change(self):

        i_tab_nw = self.tab_group_sort.currentIndex()
        self.s_type = list(self.s_prop_flds)[i_tab_nw]

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def get_prop_field(self, is_sort):

        return self.s_props if is_sort else self.p_props

    def append_para_obj(self, h_obj, p_name, g_name):

        # increments the count
        self.n_para += 1
        p_name_s = re.sub(r'<[^>]*>|[&;]+', '', p_name)

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

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}
