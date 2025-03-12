# module imports
import re
import functools
import numpy as np
from copy import deepcopy

# custom module imports
import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.common_func as cf
from spike_pipeline.info.common import InfoTab
from spike_pipeline.common.common_widget import QLabelEdit, QLabelCombo

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QFrame, QSpinBox, QTabWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QCheckBox, QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QItemDelegate, QListWidget, QGridLayout, QSpacerItem, QSizePolicy, QDialog)
from PyQt6.QtGui import QIcon, QFont, QColor, QTextDocument, QAbstractTextDocumentLayout
from PyQt6.QtCore import QSize, QSizeF

# ----------------------------------------------------------------------------------------------------------------------

# preprocessing task map dictionary
prep_task_map = {
    'Raw': 'raw',
    'Phase Shift': 'phase_shift',
    'Bandpass Filter': 'bandpass_filter',
    'Common Reference': 'common_reference',
    'Whitening': 'whitening',
    'Drift Correction': 'drift_correct',
    'Sorting': 'sorting',
}

# ----------------------------------------------------------------------------------------------------------------------

"""
    SearchMixin:
"""


class HTMLDelegate(QItemDelegate):
    def __init__(self):
        super(HTMLDelegate, self).__init__()

    def paint(self, painter, option, index):

        painter.save()
        doc = QTextDocument()
        doc.setHtml(index.data())
        context = QAbstractTextDocumentLayout.PaintContext()
        doc.setPageSize(QSizeF(option.rect.size()))
        painter.setClipRect(option.rect)
        painter.translate(option.rect.x(), option.rect.y())
        doc.documentLayout().draw(painter, context)
        painter.restore()


class SearchMixin:

    def init_search_widgets(self):

        # initialisations
        close_pixmap = QIcon(cw.icon_path['close']).pixmap(QSize(cf.but_height, cf.but_height))
        search_pixmap = QIcon(cw.icon_path['search']).pixmap(QSize(cf.but_height, cf.but_height))

        # creates the pixmap object
        filter_obj = QLabelEdit(None, '', '')

        # filter label properties
        filter_obj.obj_lbl.setPixmap(search_pixmap)
        filter_obj.obj_lbl.setFixedHeight(cf.but_height)
        filter_obj.obj_lbl.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))

        # filter label properties
        close_obj = cw.create_text_label(None, '')
        close_obj.setPixmap(close_pixmap)
        close_obj.setFixedHeight(cf.but_height)
        close_obj.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))
        close_obj.mouseReleaseEvent = self.label_clear_search
        filter_obj.layout.addWidget(close_obj)

        # filter line edit properties
        self.edit_search = filter_obj.obj_edit
        self.edit_search.textChanged.connect(self.edit_search_change)
        self.edit_search.setPlaceholderText("Search Filter")
        self.edit_search.setFixedHeight(cf.but_height)
        self.edit_search.setSizePolicy(QSizePolicy(cf.q_expm, cf.q_exp))

        # sets the object style sheets
        filter_obj.obj_lbl.setStyleSheet("""
            border: 1px solid;
            border-right-style: None;
        """)
        self.edit_search.setStyleSheet("""
            border: 1px solid;                
            border-left-style: None;  
            border-right-style: None;                        
        """)
        close_obj.setStyleSheet("""
            border: 1px solid;                
            border-left-style: None;                     
        """)

        # adds the widget to the layout
        self.tab_layout.addRow(filter_obj)

    def edit_search_change(self):

        # field retrieval
        s_txt = self.edit_search.text().lower()
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
            col = 'yellow' if hg in grp_s else '#A0A0A0'
            t_lbl = cf.set_text_background_colour(self.grp_name[i], col)
            self.h_grp[hg].setText(0, t_lbl)

        # resets the parameter label strings
        for ii, nn, hh in zip(ind_s, self.para_name0, self.h_para):
            # sets the highlighted text string
            for xi0 in np.flip(ii):
                nn = self.add_highlight(nn, xi0, ns_txt)

            # updates the property label text
            hh.setText(0, nn)

    def label_clear_search(self, evnt):

        if len(self.edit_search.text()):
            self.edit_search.setText("")

    @staticmethod
    def add_highlight(s, i0, n):

        return '{0}{1}{2}'.format(s[0:i0], cf.set_text_background_colour(s[i0:(i0 + n)], 'yellow'), s[(i0 + n):])

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

    # """
    #     QTreeWidget::item:!has-children {
    #         background-color: cyan;
    #         color: black;
    #     }
    #
    #     QCheckBox {
    #         background-color: cyan;
    #     }
    #
    #     QCheckBox::indicator {
    #         color: black;
    #         background-color: white;
    #     }
    # """

    # dimensions
    x_gap = 5
    item_row_size = 23

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
                'margin_ms': self.create_para_field('Margin (ms)', 'edit', 5),
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
                'radius_um': self.create_para_field('Radius (um)', 'edit', 100),
            },

            # drift correction parameters
            {
                'preset': self.create_para_field('Preset', 'combobox', preset_list[0], p_list=preset_list),
            },

            # # sparsity option parameters
            # {
            #     'sparse': self.create_para_field('Use Sparsity?', 'checkpanel', True, ch_fld=pp_sp),
            # },
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
        pp_k2 = {'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort2'),
                 'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2')}
        pp_k2_5 = {'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort2_5'),
                   'freq_min': self.create_para_field('Min Frequency', 'edit', 150, p_fld='kilosort2_5'), }
        pp_k3 = {'car': self.create_para_field('Use Common Avg Ref', 'checkbox', False, p_fld='kilosort3'),
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
        self.tree_prop.setAlternatingRowColors(True)
        self.tree_prop.setItemDelegateForColumn(0, HTMLDelegate())

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
        self.tab_layout.addRow(self.tree_prop)

        # resizes the columns to fit, then resets to fixed size
        tree_header = self.tree_prop.header()
        tree_header.setDefaultAlignment(cf.align_type['center'])
        tree_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tree_header.updateSection(0)
        tree_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        tree_header.setStyleSheet("background: rgba(240, 240, 255, 255);")

    def init_sorting_frame(self):

        # initialisations
        self.s_type = 'mountainsort5'

        # sets the frame properties
        self.frame_sort.setLineWidth(1)
        self.frame_sort.setFixedHeight(120)
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
                for k, v in p_val.items():
                    self.create_para_object(layout_para, k, v, v['type'], p_str_p + [k])

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
                obj_combo = QLabelCombo(
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
        spin_val = cf.check_edit_num(h_obj.text(), min_val=0)
        cf.set_multi_dict_value(p, p_str, spin_val[0])

    def sort_tab_change(self):

        i_tab_nw = self.tab_group_sort.currentIndex()
        self.s_type = list(self.s_prop_flds)[i_tab_nw]

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
    # Preprocessing Config Functions
    # ---------------------------------------------------------------------------

    def setup_config_dict(self, prep_task, is_sorting=False):

        # memory allocation
        config = {"preprocessing": {}}

        # sets up the preprocessing fields
        config_pp = config['preprocessing']
        for i, pp_t in enumerate(prep_task):
            pp = prep_task_map[pp_t]
            config_pp[str(i + 1)] = [pp, self.p_props[pp]]

        #
        if is_sorting:
            pass

        # returns the config dictionary
        return config

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}

    def create_child_tree_item(self, props, p_name):

        # initialisations
        lbl_str = '{0}:'.format(props['name'])
        cb_fcn_base = functools.partial(self.prop_update, p_name, False)

        # creates the tree widget item
        item_ch = QTreeWidgetItem(None)
        item_ch.setText(0, lbl_str)

        # #
        # obj_lbl = cw.create_text_label(None, lbl_str, self.item_child_font, align='right')
        # obj_lbl.setAutoFillBackground(False)
        # obj_lbl.setObjectName('child_item')
        # self.tree_prop.setItemWidget(item_ch, 0, obj_lbl)

        match props['type']:
            case 'edit':
                # case is a lineedit
                h_obj = QSpinBox()

                # sets the widget properties
                h_obj.setRange(0, 100000)
                h_obj.setValue(props['value'])

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


class PreprocessSetup(QDialog):
    # parameters
    n_but = 4
    x_gap = 5
    gap_sz = 5
    but_height = 20
    dlg_height = 250
    dlg_width = 300

    # array class fields
    b_icon = ['arrow_right', 'arrow_left', 'arrow_up', 'arrow_down']
    tt_str = ['Add Task', 'Remove Task', 'Move Task Up', 'Move Task Down']
    l_task = ['Bandpass Filter', 'Common Reference', 'Phase Shift']

    # widget stylesheets
    border_style = "border: 1px solid;"
    frame_style = QFrame.Shape.WinPanel | QFrame.Shadow.Plain

    def __init__(self, main_obj=None):
        super(PreprocessSetup, self).__init__()

        # sets the input arguments
        self.main_obj = main_obj
        self.setWindowTitle("Preprocessing Setup")
        self.setFixedSize(self.dlg_width, self.dlg_height)

        # sets the main widget/layout
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()

        # class layouts
        self.list_layout = QGridLayout(self)
        self.button_layout = QVBoxLayout()
        self.control_layout = QHBoxLayout()

        # class widgets
        self.button_control = []
        self.button_frame = QWidget(self)
        self.add_list = QListWidget(None)
        self.task_list = QListWidget(None)
        self.spacer_top = QSpacerItem(20, 60, cf.q_min, cf.q_max)
        self.spacer_bottom = QSpacerItem(20, 60, cf.q_min, cf.q_max)

        # initialises the class fields
        self.init_class_fields()
        self.init_control_buttons()
        self.set_button_props()

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # initialisations
        cb_fcn = [self.button_add, self.button_remove, self.button_up, self.button_down]

        # sets up the main layout
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.main_widget)
        self.main_widget.setLayout(self.list_layout)

        # main layout properties
        self.list_layout.setHorizontalSpacing(self.x_gap)
        self.list_layout.setVerticalSpacing(0)
        self.list_layout.setContentsMargins(self.x_gap, 0, self.x_gap, 0)
        self.setLayout(self.list_layout)

        # added list widget properties
        self.add_list.setStyleSheet(self.border_style)
        self.add_list.itemClicked.connect(self.set_button_props)

        # task list widget properties
        self.task_list.addItems(self.l_task)
        self.task_list.setStyleSheet(self.border_style)
        self.task_list.itemClicked.connect(self.set_button_props)

        # button layout properties
        self.button_layout.setSpacing(self.x_gap)

        # adds the spacers/buttons to the button layout
        self.button_layout.addItem(self.spacer_top)
        for bi, cb, tt in zip(self.b_icon, cb_fcn, self.tt_str):
            # creates the button object
            button_new = cw.create_push_button(self, "")

            # sets the button properties
            button_new.setObjectName(bi)
            button_new.setToolTip(tt)
            button_new.setIcon(QIcon(cw.icon_path[bi]))
            button_new.setIconSize(QSize(self.but_height - 2, self.but_height - 2))
            button_new.setFixedSize(self.but_height, self.but_height)
            button_new.setStyleSheet(self.border_style)

            # sets the button callback
            button_new.pressed.connect(cb)
            self.button_layout.addWidget(button_new)
            self.button_control.append(button_new)

        self.button_layout.addItem(self.spacer_bottom)

        # adds the main widgets to the main layout
        self.list_layout.addWidget(self.task_list, 0, 0, 1, 1)
        self.list_layout.addLayout(self.button_layout, 0, 1, 1, 1)
        self.list_layout.addWidget(self.add_list, 0, 2, 1, 1)
        self.list_layout.addWidget(self.button_frame, 1, 0, 1, 3)

        # set the grid layout column sizes
        self.list_layout.setColumnStretch(0, self.gap_sz)
        self.list_layout.setColumnStretch(1, 1)
        self.list_layout.setColumnStretch(2, self.gap_sz)
        self.list_layout.setRowStretch(0, 5)
        self.list_layout.setRowStretch(1, 1)

    def init_control_buttons(self):

        # initialisations
        b_str = ['Start Preprocessing', 'Close Window']
        cb_fcn = [self.start_preprocess, self.close_window]

        # sets the frame/layout properties
        self.button_frame.setContentsMargins(0, 0, 0, 0)
        self.button_frame.setLayout(self.control_layout)
        self.control_layout.setContentsMargins(0, 0, 0, 0)

        # creates the control buttons
        for bs, cb in zip(b_str, cb_fcn):
            # creates the button object
            button_new = cw.create_push_button(self, bs, font=cw.font_lbl)
            self.control_layout.addWidget(button_new)
            self.button_control.append(button_new)

            # sets the button properties
            button_new.pressed.connect(cb)
            button_new.setFixedHeight(cf.but_height)
            button_new.setStyleSheet(self.border_style)

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def button_add(self):

        # swaps the selected item between lists
        i_index = self.task_list.currentIndex()
        task_item = self.task_list.takeItem(i_index.row())
        self.add_list.addItem(task_item.text())

        # updates the button properties
        self.set_button_props()

    def button_remove(self):

        # swaps the selected item between lists
        i_index = self.add_list.currentIndex()
        add_item = self.add_list.takeItem(i_index.row())
        self.task_list.addItem(add_item)

        # updates the button properties
        self.set_button_props()

    def button_up(self):

        # field retrieval
        i_row_sel = self.add_list.currentRow()
        item_sel = self.add_list.item(i_row_sel)
        item_prev = self.add_list.item(i_row_sel - 1)

        # reorders the items
        name_sel, name_prev = item_sel.text(), item_prev.text()
        item_sel.setText(name_prev)
        item_prev.setText(name_sel)

        # resets the row selection and button properties
        self.add_list.setCurrentRow(i_row_sel - 1)
        self.set_button_props()

    def button_down(self):

        # field retrieval
        i_row_sel = self.add_list.currentRow()
        item_sel = self.add_list.item(i_row_sel)
        item_next = self.add_list.item(i_row_sel + 1)

        # reorders the items
        name_sel, name_next = item_sel.text(), item_next.text()
        item_sel.setText(name_next)
        item_next.setText(name_sel)

        # resets the row selection and button properties
        self.add_list.setCurrentRow(i_row_sel + 1)
        self.set_button_props()

    def start_preprocess(self):

        if self.main_obj is not None:
            # retrieves the selected tasks
            prep_task = []
            for i in range(self.add_list.count()):
                prep_task.append(self.add_list.item(i).text())

            # runs the pre-processing
            self.main_obj.run_preproccessing(prep_task)
            self.close_window()

    def close_window(self):

        self.close()

    def set_button_props(self):

        # field retrieval
        n_added = self.add_list.count() - 1
        i_row_add = self.add_list.currentRow()
        i_row_task = self.task_list.currentRow()
        is_added_sel = i_row_add >= 0

        # updates the button properties
        self.button_control[0].setEnabled(i_row_task >= 0)
        self.button_control[1].setEnabled(i_row_add >= 0)
        self.button_control[2].setEnabled(is_added_sel and (i_row_add > 0))
        self.button_control[3].setEnabled(is_added_sel and (i_row_add < n_added))
        self.button_control[4].setEnabled(n_added >= 0)
