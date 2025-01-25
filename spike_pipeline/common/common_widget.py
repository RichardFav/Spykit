# module import
import textwrap
import functools
import numpy as np
from copy import deepcopy
from skimage.measure import label, regionprops

# custom module import
import spike_pipeline.common.common_func as cf

# pyqt6 module import
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QGridLayout, QVBoxLayout, QPushButton, QGroupBox, QTabWidget,
                             QFormLayout, QLabel, QCheckBox, QLineEdit, QComboBox, QSizePolicy, QFileDialog,
                             QApplication, QTreeView, QFrame)
from PyQt6.QtGui import QFont, QDrag, QCursor, QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QRect, QMimeData, pyqtSignal

########################################################################################################################


# dimensions
x_gap = 10
gbox_height0 = 25


class QRegionConfig(QWidget):
    config_reset = pyqtSignal()

    def __init__(self, parent=None, font=None, n_row=1, n_col=1):
        super(QRegionConfig, self).__init__(parent)

        # field initialisations
        self.h_rgrid = []
        self.n_row = n_row
        self.n_col = n_col
        self.is_expanded = False
        self.is_mouse_down = False
        self.tr_col = cf.get_colour_value('w')

        self.is_sel = None
        self.g_id = np.zeros((2, 2), dtype=int)
        self.c_id = np.ones((self.n_row, self.n_col), dtype=int)

        # sets up the widget layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # other object initialisations
        self.q_cursor = QCursor()
        self.h_root = cf.get_root_widget(self.parent())

        # ------------------------------- #
        # --- ROW/COLUMN WIDGET SETUP --- #
        # ------------------------------- #

        # field initialisations
        t_lbl = ['Row', 'Column']
        p_str = ['n_row', 'n_col']

        # widget setup
        self.rc_layout = QHBoxLayout()
        self.rc_layout.setSpacing(0)
        self.rc_layout.setContentsMargins(0, 0, 0, 5)

        # widget setup
        self.rc_widget = QWidget()
        self.rc_widget.setLayout(self.rc_layout)

        # creates the row/column widgets
        for tl, ps in zip(t_lbl, p_str):
            # creates the label/editbox object
            tl_lbl = "{0}:".format(tl)
            obj_lbl_edit = QLabelEdit(None, tl_lbl, getattr(self, ps), font_lbl=font)
            self.rc_layout.addWidget(obj_lbl_edit)

            # sets the editbox widget properties
            obj_lbl_edit.obj_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            obj_lbl_edit.obj_lbl.adjustSize()

            # sets the callback function
            cb_fcn_rc = functools.partial(self.edit_dim_update, ps)
            obj_lbl_edit.connect(cb_fcn_rc)

        # adds the combo object
        self.p_list = ['(No Trace)', 'Root Trace']
        self.p_col = [cf.get_colour_value('lg'), cf.get_colour_value(0)]
        self.obj_lbl_combo = QLabelCombo(None, 'Trace Name: ', self.p_list, 'Root Trace', font_lbl=font)

        # sets the label properties
        self.obj_lbl_combo.obj_lbl.setFixedWidth(80)
        self.obj_lbl_combo.connect(self.combo_update_trace)

        # trace index/colour fields
        self.i_trace = self.obj_lbl_combo.obj_cbox.currentIndex()
        self.tr_col = self.p_col[self.i_trace]

        # adds the widgets to the class widget
        self.main_layout.addWidget(self.rc_widget)
        self.main_layout.addWidget(self.obj_lbl_combo)

        # ------------------------------------ #
        # --- REGION SELECTOR WIDGET SETUP --- #
        # ------------------------------------ #

        # initialisations
        self.gbox_rect = QRect(5, 0, 15, 15)

        # creates the groupbox object
        self.obj_gbox = QGroupBox(cf.arr_chr(False))
        self.obj_gbox.setCheckable(False)
        self.obj_gbox.setFont(font)
        self.obj_gbox.setFixedHeight(gbox_height0)
        # self.obj_gbox.setStyleSheet("""
        #     QGroupbox::label {
        #         color: red;
        #     }
        # """)

        # sets up the groupbox layout widget
        self.gb_layout = QGridLayout()
        self.gb_layout.setSpacing(0)
        self.gb_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

        # updates the selector widgets
        self.reset_selector_widgets()

        # sets the groupbox properties
        self.obj_gbox.setLayout(self.gb_layout)
        self.obj_gbox.mousePressEvent = self.panel_group_update

        # adds the widget to the class widget
        self.main_layout.addWidget(self.obj_gbox)

    # ----------------------------- #
    # --- MOUSE EVENT FUNCTIONS --- #
    # ----------------------------- #

    def mouse_clicked(self, i_row, i_col, is_press):
        """

        :param i_row:
        :param i_col:
        :param is_press:
        :return:
        """

        # updates the current flag
        g_idc = np.array([i_row, i_col])
        i_reg = self.get_region_index(i_row, i_col)

        # if pressing the mouse, then set the initial grid coords
        if is_press:
            # case is the mouse-down event

            # updates the selected trace index
            self.is_sel = np.zeros((self.n_row, self.n_col), dtype=bool)

            # sets the initial/final grid locations
            self.g_id[0, :], self.g_id[1, :] = g_idc, g_idc

        elif not np.array_equal(g_idc, self.g_id[1, :]):
            # case is entering a new region
            self.g_id[1, :] = g_idc

        # updates the grid indices and
        self.update_selection_grid(True)

    def mouse_leaving(self, i_row, i_col):
        """

        :param i_row:
        :param i_col:
        :return:
        """

        # initialisations
        update_reqd = False

        # retrieves the current mouse position (wrt the clickable label)
        i_reg = i_row * self.n_col + i_col
        m_pos = self.h_rgrid[i_reg].mapFromGlobal(self.q_cursor.pos())
        i_side = self.get_side_index(m_pos, self.h_rgrid[i_reg].size())

        # case is the cursor is moving left and is to the right of the anchor, OR
        #         the cursor is moving right and is to the left of the anchor
        if ((i_side[0] < 0) and (i_col > self.g_id[0, 1])) or \
                ((i_side[0] > 0) and (i_col < self.g_id[0, 1])):
            self.g_id[1, 1] += i_side[0]
            update_reqd = True

        # case is the cursor is moving up and is below the anchor, OR
        #         the cursor is moving down and is above the anchor
        if ((i_side[1] < 0) and (i_row > self.g_id[0, 0])) or \
                ((i_side[1] > 0) and (i_row < self.g_id[0, 0])):
            self.g_id[1, 0] += i_side[1]
            update_reqd = True

        # updates the selection grid
        if update_reqd:
            self.update_selection_grid(False)

    def mouse_released(self):
        """

        :return:
        """

        # initialisations
        is_feas = True

        # sets up the new temporary index array
        c_id_nw = deepcopy(self.c_id)
        c_id_nw[self.is_sel] = self.i_trace

        # loops through each of the unique
        for cid in np.unique(c_id_nw[c_id_nw > 0]):
            # determines the group id blob properties
            regions = regionprops(label(c_id_nw == cid))
            if len(regions) == 1:
                # if there is a unique blob, then determine if the dimensions are feasible
                if regions[0].area != regions[0].area_bbox:
                    # otherwise, flag an error and exit the loop
                    is_feas = False
                    break

            else:
                # otherwise,
                is_feas = False
                break

        if is_feas:
            # if feasible, then update the parameter fields and other properties
            ind_sel = np.where(self.is_sel)
            for i_r, i_c in zip(ind_sel[0], ind_sel[1]):
                # updates the id flags and
                i_reg = self.get_region_index(i_r, i_c)
                self.c_id[i_r, i_c] = self.i_trace

                # updates the widget stylesheet
                g_col = self.p_col[self.c_id[i_r, i_c]]
                self.set_grid_style_sheet(self.h_rgrid[i_reg], g_col)

            # flag that the plot widgets need updating
            self.config_reset.emit()

        else:
            # otherwise, output an error to screen
            e_str = 'The selected region configuration is infeasible.'
            cf.show_error(e_str, 'Infeasible Configuration')

        # updates the grid object style sheets
        for h in self.h_rgrid:
            h.setObjectName('normal')
            h.setStyleSheet(h.styleSheet())

    # ------------------------------ #
    # --- WIDGET EVENT FUNCTIONS --- #
    # ------------------------------ #

    def panel_group_update(self, evnt):
        """

        :param evnt:
        :return:
        """

        # determines if the mouse-click is on the title
        if self.gbox_rect.contains(evnt.pos()):
            # if so, update the parameters
            self.is_expanded = self.is_expanded ^ True
            self.obj_gbox.setTitle(cf.arr_chr(self.is_expanded))

            # calculates the widget dimensions
            d_hght = (2 * self.is_expanded - 1) * (self.obj_gbox.width() - gbox_height0)

            self.obj_gbox.setFixedHeight(self.obj_gbox.height() + d_hght)

    def edit_dim_update(self, p_str, h_edit):
        """

        :param p_str:
        :param h_edit:
        :return:
        """

        # field retrieval
        nw_val = h_edit.text()

        # resets the update flag
        self.h_root.was_reset = True

        # determines if the new value is valid
        chk_val = cf.check_edit_num(nw_val, min_val=1, max_val=5, is_int=True)
        if chk_val[1] is None:
            # updates the parameter value
            self.reshape_group_ids(chk_val[0], p_str == 'n_row')
            setattr(self, p_str, chk_val[0])
            self.reset_selector_widgets()

            # flag that the plot widgets need updating
            self.config_reset.emit()

        else:
            # otherwise, reset the previous value
            h_edit.setText('%g' % getattr(self, p_str))

    def combo_update_trace(self, h_cbox):
        """

        :param h_cbox:
        :return:
        """

        # trace index/colour fields
        self.i_trace = h_cbox.currentIndex()
        self.tr_col = self.p_col[self.i_trace]

        # updates the grid object style sheets
        for i, h in enumerate(self.h_rgrid):
            # resets the grid-style sheet
            i_row, i_col = self.get_grid_indices(i)
            g_col = self.p_col[self.c_id[i_row, i_col]]
            self.set_grid_style_sheet(h, g_col)

            # resets the colour style
            h_style = h.style()
            h_style.unpolish(h)
            h_style.polish(h)
            h.update()

    # -------------------------- #
    # --- INDEXING FUNCTIONS --- #
    # -------------------------- #

    def get_region_index(self, i_row, i_col):
        """

        :param i_row:
        :param i_col:
        :return:
        """

        return i_row * self.n_col + i_col

    def get_grid_indices(self, i_reg):
        """

        :param i_reg:
        :return:
        """

        return i_reg // self.n_col, i_reg % self.n_col

    def get_side_index(self, m_pos, w_sz):
        """

        :param m_pos:
        :param w_sz:
        :return:
        """

        return [(m_pos.x() >= w_sz.width()) - (m_pos.x() <= 0),
                (m_pos.y() >= w_sz.height()) - (m_pos.y() <= 0)]

    # ------------------------------- #
    # --- MISCELLANEOUS FUNCTIONS --- #
    # ------------------------------- #

    def reset_selector_widgets(self):
        """

        :return:
        """

        # retrieves the
        self.g_id[:] = 0
        self.h_rgrid = []
        obj_ch = self.obj_gbox.findChildren(ClickableRegion)
        n_ch, n_reg = len(obj_ch), self.n_row * self.n_col

        # removes extraneous widgets
        if n_ch > n_reg:
            for i_ch in range(n_reg, n_ch):
                obj_ch[i_ch].setParent(None)

        # creates/resets the label objects
        for i_row in range(self.n_row):
            for i_col in range(self.n_col):
                i_reg = i_row * self.n_col + i_col

                if i_reg < n_ch:
                    # case is the widget already exists
                    h_grid = obj_ch[i_reg]
                    h_grid.set_grid_indices(i_row, i_col)

                else:
                    # case is the grid needs to be created
                    h_grid = ClickableRegion(self, i_row, i_col)
                    h_grid.clicked.connect(self.mouse_clicked)
                    h_grid.release.connect(self.mouse_released)
                    h_grid.leaving.connect(self.mouse_leaving)
                    h_grid.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

                # updates the widget stylesheet
                g_col = self.p_col[self.c_id[i_row, i_col]]
                self.set_grid_style_sheet(h_grid, g_col)

                # appends the widget to the parent widget
                self.gb_layout.addWidget(h_grid, i_row, i_col)
                self.h_rgrid.append(h_grid)

    def update_selection_grid(self, is_add):
        """

        :param is_add:
        :return:
        """

        # sets the selected row/column indices
        xi_r = range(self.g_id[:, 0].min(), self.g_id[:, 0].max() + 1)
        xi_c = range(self.g_id[:, 1].min(), self.g_id[:, 1].max() + 1)

        # determines the new index array
        i_sel_nw = np.zeros((self.n_row, self.n_col), dtype=bool)
        for xc in xi_c:
            i_sel_nw[xi_r, xc] = True

        if is_add:
            # determines the regions that need to be added
            i_sel_add = np.logical_and(np.logical_not(self.is_sel), i_sel_nw)

            # updates the object names for the new regions
            ind_rmv = np.where(i_sel_add)
            for i_row, i_col in zip(ind_rmv[0], ind_rmv[1]):
                i_reg = self.get_region_index(i_row, i_col)
                self.h_rgrid[i_reg].setObjectName('selected')
                self.h_rgrid[i_reg].setStyleSheet(self.h_rgrid[i_reg].styleSheet())
                self.is_sel[i_row, i_col] = True

        else:
            # determines the regions that need to be de-selected
            i_sel_rmv = np.logical_and(self.is_sel, np.logical_not(i_sel_nw))

            # updates the object names for the new regions
            ind_rmv = np.where(i_sel_rmv)
            for i_row, i_col in zip(ind_rmv[0], ind_rmv[1]):
                i_reg = self.get_region_index(i_row, i_col)
                self.h_rgrid[i_reg].setObjectName('normal')
                self.h_rgrid[i_reg].setStyleSheet(self.h_rgrid[i_reg].styleSheet())
                self.is_sel[i_row, i_col] = False

    def reshape_group_ids(self, dim_nw, is_row):
        """

        :param dim_nw:
        :param is_row:
        :return:
        """

        if is_row:
            if dim_nw > self.n_row:
                # case is columns need to be added
                c_id_add = np.zeros((dim_nw - self.n_row, self.n_col), dtype=int)
                self.c_id = np.vstack([self.c_id, c_id_add])

            else:
                # case is rows need removing
                self.c_id = self.c_id[:dim_nw, :]

        else:
            if dim_nw > self.n_col:
                # case is columns need to be added
                c_id_add = np.zeros((self.n_row, dim_nw - self.n_col), dtype=int)
                self.c_id = np.hstack([self.c_id, c_id_add])

            else:
                # case is columns need removing
                self.c_id = self.c_id[:, :dim_nw]

    def set_grid_style_sheet(self, h_grid, n_col):
        """

        :param h_grid:
        :param n_col:
        :return:
        """

        tr_col_f = deepcopy(self.tr_col)
        tr_col_f.setAlpha(128)

        # appends the selection colour (if provided)
        ss_str = textwrap.dedent("""
            QLabel[objectName="normal"] {
                background-color: %s;
                border: 1px solid;
            }
            QLabel[objectName="selected"] {
                background-color: %s;
                border: 1px solid;
            }                        
        """ % (self.get_rgba_string(n_col), self.get_rgba_string(tr_col_f)))

        # updates the object style sheet
        h_grid.setStyleSheet(ss_str)

    def get_rgba_string(self, t_col):
        """

        :param t_col:
        :return:
        """

        return 'rgba({0}, {1}, {2}, {3})'.format(t_col.red(), t_col.green(), t_col.blue(), t_col.alpha())

########################################################################################################################


# widget stylesheets
tree_style = """
    QTreeView {
        font: Arial 8px;
    }
    
    QTreeView::item {

    }    
            
    QTreeView::branch:open:has-children:has-siblings {

    }        
"""

# widget dimensions
row_height = 20


class QTraceTree(QWidget):
    node_added = pyqtSignal()
    node_deleted = pyqtSignal()

    def __init__(self, parent=None, font=None):
        super(QTraceTree, self).__init__(parent)

        # field initialistions
        self.n_trace = 0
        self.h_node = {}
        self.s_node = {}

        # sets up the widget layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # ------------------------ #
        # --- TEXT LABEL SETUP --- #
        # ------------------------ #

        # creates the text label
        self.obj_txt_lbl = QLabelText(None, 'Trace Count: ', '0', font_lbl=font, name='name')
        self.main_layout.addWidget(self.obj_txt_lbl)

        # sets the label properties
        self.obj_txt_lbl.obj_lbl.setFixedSize(self.obj_txt_lbl.obj_lbl.sizeHint())

        # ------------------------- #
        # --- TREE WIDGET SETUP --- #
        # ------------------------- #

        # sets up the table model
        self.t_model = QStandardItemModel()
        self.t_model.dataChanged.connect(self.node_name_update)

        # creates the tree-view widget
        self.obj_tview = QTreeView()

        # sets the tree-view properties
        self.obj_tview.setModel(self.t_model)
        self.obj_tview.setStyleSheet(tree_style)
        self.obj_tview.setItemsExpandable(False)
        self.obj_tview.setIndentation(10)
        self.obj_tview.setRootIsDecorated(False)
        self.obj_tview.setHeaderHidden(True)
        self.obj_tview.setFrameStyle(QFrame.Shape.WinPanel | QFrame.Shadow.Sunken)

        # appends the widget to the main widget
        self.main_layout.addWidget(self.obj_tview)

    def add_tree_item(self, n_name, parent_id=None):
        """

        :param n_name:
        :param parent_id:
        :return:
        """

        # creates the tree item
        item = QStandardItem(n_name)
        item.setEditable(True)

        if parent_id is None:
            # creates the root tree item
            self.s_node['name'] = 'Root Trace'
            self.h_node['h'] = QStandardItem(self.s_node['name'])
            self.t_model.appendRow(self.h_node['h'])

        else:
            # case is another node type
            d_node, n_node = self.h_node, self.s_node
            for p_id in parent_id:
                d_node, n_node = d_node[str(p_id)], n_node[str(p_id)]

            # appends the widget to the branch node
            d_node['h'].appendRow(item)
            n_ch = len(d_node.keys())

            # appends the widget dictionary
            d_node[str(n_ch)] = {}
            d_node[str(n_ch)]['h'] = item

            # appends the name dictionary
            n_node[str(n_ch)] = {}
            n_node[str(n_ch)]['name'] = n_name

        # increments the counter
        self.n_trace += 1
        self.obj_txt_lbl.set_label(str(self.n_trace))
        
        # resets the tree-viewer properties
        self.reset_tview_props()

    def reset_tview_props(self):
        """

        :return:
        """

        self.obj_tview.setFixedHeight(self.n_trace * row_height + 2)
        self.obj_tview.expandAll()

        # # flag that a new node has been added
        # self.node_added.emit()

    def node_name_update(self, ind_mod_1, ind_mod_2, roles):
        """

        :param ind_mod_1:
        :param ind_mod_2:
        :param roles:
        :return:
        """

        from spike_pipeline.widgets.plot_widget import QPlotPara

        h_plot_para = cf.get_parent_widget(self, QPlotPara)
        h_plot_para.p_props.name = ind_mod_1.data()

########################################################################################################################


# object dimensions
d_height = 5
w_space = 10
txt_height = 16.5

expand_style = """
    text-align:left;
    background-color: rgba(26, 83, 200, 255);
    color: rgba(255, 255, 255, 255);
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
"""

close_style = """
    text-align:left;
    background-color: rgba(26, 83, 200, 255);
    color: rgba(255, 255, 255, 255);
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
"""


class QCollapseGroup(QWidget):
    def __init__(self, parent=None, grp_name=None, is_first=False, f_layout=None):
        super(QCollapseGroup, self).__init__(parent)

        # initialisations
        self.is_expanded = True
        self.panel_hdr = grp_name

        # label/header font objects
        self.font_txt = create_font_obj()
        self.font_hdr = create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

        # creates the panel objects
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(w_space, is_first * w_space, w_space, w_space)

        # creates the expansion button
        self.expand_button = create_push_button(None, '', font=self.font_hdr)
        self.main_layout.addWidget(self.expand_button, 0, Qt.AlignmentFlag.AlignTop)

        # creates the groupbox object
        self.group_panel = QGroupBox()
        self.main_layout.addWidget(self.group_panel)

        # creates the children objects for the current parent object
        self.form_layout = QFormLayout() if f_layout is None else f_layout
        self.form_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # sets the final layout
        self.group_panel.setLayout(self.form_layout)
        self.setLayout(self.main_layout)
        self.set_styling()

        # retrieves the original height
        self.orig_hght = self.group_panel.maximumHeight()
        self.update_button_text()

        # resets the collapse panel size policy
        self.setSizePolicy(QSizePolicy(cf.q_pref, cf.q_fix))

    # ------------------------------ #
    # --- WIDGET SETUP FUNCTIONS --- #
    # ------------------------------ #

    def add_group_row(self, h_obj1, h_obj2):
        """

        :param h_obj1:
        :param h_obj2:
        :return:
        """

        # adds the object to the layout
        self.form_layout.addRow(h_obj1, h_obj2)

    # ----------------------------- #
    # --- PANEL EVENT FUNCTIONS --- #
    # ----------------------------- #

    def connect(self, cb_fcn0=None):

        if cb_fcn0 is None:
            cb_fcn0 = self.expand

        # sets the button click event function
        self.expand_button.clicked.connect(cb_fcn0)

    def expand(self, h_root=None):
        """

        :return:
        """

        if hasattr(self.parent(), 'was_reset') and self.parent().was_reset:
            # hack fix - top panel group wants to collapse when editbox value is reset?
            self.parent().was_reset = False

        else:
            # field retrieval
            self.is_expanded = self.is_expanded ^ True
            self.update_button_text()

            # sets the button style
            f_style = expand_style if self.is_expanded else close_style
            self.expand_button.setStyleSheet(f_style)

    # ------------------------------- #
    # --- MISCELLANEOUS FUNCTIONS --- #
    # ------------------------------- #

    def update_button_text(self):
        """

        :return:
        """

        self.expand_button.setText(' {0} {1}'.format(cf.arr_chr(self.is_expanded), self.panel_hdr))
        self.group_panel.setMaximumHeight(self.is_expanded * self.orig_hght)

    def set_styling(self):
        """

        :return:
        """

        self.group_panel.setStyleSheet("background-color: rgba(240, 240, 255, 255) ;")
        self.expand_button.setStyleSheet(expand_style)


########################################################################################################################


class FileDialogModal(QFileDialog):
    def __init__(self, parent=None, caption=None, f_filter=None,
                 f_directory=None, is_save=False, dir_only=False, is_multi=False):
        # creates the widget
        super(FileDialogModal, self).__init__(parent=parent, caption=caption, filter=f_filter, directory=f_directory)

        # sets the file dialog parameters
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # sets the file dialog to open if
        if is_save:
            self.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

        # sets the file mode to directory (if directory only)
        if dir_only:
            self.setFileMode(QFileDialog.FileMode.Directory)

        # sets the multi-select flag to true (if required)
        if is_multi:
            self.setFileMode(QFileDialog.FileMode.ExistingFiles)


########################################################################################################################


class ClickableRegion(QLabel):
    clicked = pyqtSignal(int, int, bool)
    leaving = pyqtSignal(int, int)
    release = pyqtSignal()

    def __init__(self, parent=None, i_row=None, i_col=None):
        super().__init__(parent)

        self.i_row = i_row
        self.i_col = i_col

        self.setObjectName('normal')
        self.setAcceptDrops(True)
        self.dragstart = None

    def set_grid_indices(self, i_row, i_col):
        """

        :param i_row:
        :param i_col:
        :return:
        """

        self.i_row, self.i_col = i_row, i_col

    def mousePressEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.dragstart = event.pos()
            self.clicked.emit(self.i_row, self.i_col, True)

    def mouseReleaseEvent(self, event):
        self.dragstart = None
        self.release.emit()

    def mouseMoveEvent(self, event):

        if (self.dragstart is not None and
                event.buttons() & Qt.MouseButton.LeftButton and
                (event.pos() - self.dragstart).manhattanLength() >
                QApplication.startDragDistance()):
            self.dragstart = None
            drag = QDrag(self)
            drag.setMimeData(QMimeData())
            drag.exec(Qt.DropAction.LinkAction)

            self.release.emit()

    def dragEnterEvent(self, event):
        event.acceptProposedAction()
        if event.source() is not self:
            self.clicked.emit(self.i_row, self.i_col, False)

    def dragLeaveEvent(self, event):
        self.leaving.emit(self.i_row, self.i_col)


########################################################################################################################


class QFileSpec(QGroupBox):
    def __init__(self, parent=None, grp_hdr=None, file_path=None, name=None, f_mode=None):
        super(QFileSpec, self).__init__(parent)

        # initialisations
        self.f_mode = f_mode
        font_hdr = create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)
        font_but = create_font_obj(size=10, is_bold=True, font_weight=QFont.Weight.Bold)

        # sets the groupbox properties
        self.setTitle(grp_hdr)
        self.setFont(font_hdr)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # creates the editbox widget
        self.h_edit = create_line_edit(None, file_path, align='left', name=name)
        self.layout.addWidget(self.h_edit)
        self.h_edit.setReadOnly(True)
        self.h_edit.setObjectName(name)

        # creates the button widget
        self.h_but = create_push_button(None, '...', font_but)
        self.layout.addWidget(self.h_but)
        self.h_but.setFixedWidth(25)

    def connect(self, cb_fcn0):
        """

        :param cb_fcn0:
        :return:
        """

        cb_fcn = functools.partial(cb_fcn0, self)
        self.h_but.clicked.connect(cb_fcn)


########################################################################################################################


class QLabelText(QWidget):
    def __init__(self, parent=None, lbl_str=None, text_str=None, font_lbl=None, font_txt=None, name=None):
        super(QLabelText, self).__init__(parent)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # creates the label/editbox widget combo
        self.obj_lbl = create_text_label(None, lbl_str, font=font_lbl)
        self.obj_txt = create_text_label(None, text_str, name=name, align='left', font=font_txt)
        self.layout.addWidget(self.obj_lbl)
        self.layout.addWidget(self.obj_txt)

        # sets up the label properties
        self.obj_lbl.adjustSize()

    def set_label(self, txt_str):
        """

        :param txt_str:
        :return:
        """

        self.obj_txt.setText(txt_str)


########################################################################################################################


class QLabelEdit(QWidget):
    def __init__(self, parent=None, lbl_str=None, edit_str=None, font_lbl=None, name=None):
        super(QLabelEdit, self).__init__(parent)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # creates the label/editbox widget combo
        self.obj_lbl = create_text_label(None, lbl_str, font=font_lbl)
        self.obj_edit = create_line_edit(None, edit_str, name=name, align='left')
        self.layout.addWidget(self.obj_lbl)
        self.layout.addWidget(self.obj_edit)

        # sets up the label properties
        self.obj_lbl.adjustSize()
        self.obj_lbl.setStyleSheet('padding-top: 2 px;')

        # sets up the editbox properties
        self.obj_edit.setFixedHeight(cf.edit_height)
        self.obj_edit.setStyleSheet(
            "border: 1px solid; border-radius: 2px; padding-left: 5px;"
        )

    def connect(self, cb_fcn0):
        """

        :param cb_fcn0:
        :return:
        """

        cb_fcn = functools.partial(cb_fcn0, self.obj_edit)
        self.obj_edit.editingFinished.connect(cb_fcn)


########################################################################################################################


class QLabelButton(QWidget):
    def __init__(self, parent=None, lbl_str=None, but_str=None, font_lbl=None, name=None):
        super(QLabelButton, self).__init__(parent)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # creates the label/editbox widget combo
        self.obj_lbl = create_text_label(None, lbl_str, font=font_lbl)
        self.obj_but = create_push_button(None, but_str, name=name)
        self.layout.addWidget(self.obj_lbl)
        self.layout.addWidget(self.obj_but)

        # sets up the label properties
        self.obj_lbl.adjustSize()
        self.obj_lbl.setStyleSheet("padding-top: 3 px;")

        # sets up the editbox properties
        self.obj_but.setFixedHeight(cf.but_height)
        self.obj_but.setCursor(Qt.CursorShape.PointingHandCursor)

    def connect(self, cb_fcn0):
        """

        :param cb_fcn0:
        :return:
        """

        cb_fcn = functools.partial(cb_fcn0, self.obj_but)
        self.obj_but.clicked.connect(cb_fcn)


########################################################################################################################


class QLabelCombo(QWidget):
    def __init__(self, parent=None, lbl_str=None, list_str=None, value=None, font_lbl=None, name=None):
        super(QLabelCombo, self).__init__(parent)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(1)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # creates the label/combobox widget combo
        self.obj_lbl = create_text_label(None, lbl_str, font=font_lbl)
        self.obj_cbox = create_combo_box(None, list_str, name=name)

        self.layout.addWidget(self.obj_lbl)
        self.layout.addWidget(self.obj_cbox)

        # sets up the label properties
        self.obj_lbl.adjustSize()
        self.obj_lbl.setStyleSheet('padding-top: 2 px;')

        # sets up the slot function
        self.obj_cbox.setFixedHeight(cf.combo_height)
        self.obj_cbox.setCurrentText(value)
        self.obj_cbox.setStyleSheet('border-radius: 2px; border: 1px solid')

    def connect(self, cb_fcn0):
        """

        :param cb_fcn0:
        :return:
        """

        cb_fcn = functools.partial(cb_fcn0, self.obj_cbox)
        self.obj_cbox.currentIndexChanged.connect(cb_fcn)


########################################################################################################################


class QCheckboxHTML(QWidget):
    def __init__(self, parent=None, text=None, state=False, font=None, name=None):
        super(QCheckboxHTML, self).__init__(parent)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # creates the checkbox object
        self.h_chk = create_check_box(None, '', state, name=name)
        self.h_chk.adjustSize()
        self.h_chk.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))

        # creates the label object
        self.h_lbl = create_text_label(None, text, font, align='left')
        self.h_lbl.setStyleSheet('padding-bottom: 2px;')
        self.h_lbl.adjustSize()

        # adds the widgets to the layout
        self.layout.addWidget(self.h_chk)
        self.layout.addWidget(self.h_lbl)

    def set_label_text(self, t_lbl):
        """

        :param t_lbl:
        :return:
        """

        self.h_lbl.setText(t_lbl)

    def connect(self, cb_fcn):
        """

        :param cb_fcn:
        :return:
        """

        self.h_chk.stateChanged.connect(cb_fcn)
        self.h_lbl.mousePressEvent = cb_fcn


########################################################################################################################


def create_text_label(parent, text, font=None, align='right', name=None):
    """

    :param parent: parent object
    :param text:
    :param font:
    :param align: alignment flag (left, centre or right)
    :param name: object name
    :return:
    """

    # sets the label font properties
    if font is None:
        font = create_font_obj()

    # creates the label object
    h_lbl = QLabel(parent)

    # sets the label properties
    h_lbl.setText(text)
    h_lbl.setAlignment(cf.align_type[align])

    # sets the object font
    if font is not None:
        h_lbl.setFont(font)

    # sets the object name string
    if name is not None:
        h_lbl.setObjectName(name)

    # returns the label object
    return h_lbl


def create_line_edit(parent, text, font=None, align='centre', name=None):
    """

    :param parent:
    :param text:
    :param font:
    :param align:
    :param name:
    :return:
    """

    # sets the label font properties
    if font is None:
        font = create_font_obj()

    # sets the text string (if None)
    if text is None:
        text = " "

    elif isinstance(text, int):
        text = str(text)

    # creates the line edit object
    h_ledit = QLineEdit(parent)

    # sets the label properties
    h_ledit.setFont(font)
    h_ledit.setText(text)
    h_ledit.setAlignment(cf.align_type[align])

    # sets the object name string
    if name is not None:
        h_ledit.setObjectName(name)

    # returns the object
    return h_ledit


def create_push_button(parent, text, font=None, name=None):
    """

    :param parent:
    :param text:
    :param font:
    :param name:
    :return:
    """

    # creates a default font object (if not provided)
    if font is None:
        font = create_font_obj()

    # creates the button object
    h_button = QPushButton(parent)

    # sets the button properties
    h_button.setFont(font)
    h_button.setText(text)

    # sets the object name string
    if name is not None:
        h_button.setObjectName(name)

    # returns the button object
    return h_button


def create_combo_box(parent, text=None, font=None, name=None):
    """

    :param parent:
    :param text:
    :param font:
    :param name:
    :return:
    """

    # creates a default font object (if not provided)
    if font is None:
        font = create_font_obj()

    # creates the listbox object
    h_combo = QComboBox(parent)

    # sets the combobox object properties
    h_combo.setFont(font)

    # sets the combobox text (if provided)
    if text is not None:
        for i, t in enumerate(text):
            h_combo.addItem(t)

            # if colour is not None:
            #     c_model.setData(c_model.index(i, 0), colour[i], Qt.ItemDataRole.BackgroundRole)

    # sets the object name string
    if name is not None:
        h_combo.setObjectName(name)

    # returns the object
    return h_combo


def create_check_box(parent, text, state, font=None, name=None):
    """

    :param parent:
    :param text:
    :param state:
    :param font:
    :param name:
    :return:
    """

    # sets the label font properties
    if font is None:
        font = create_font_obj()

    # creates the listbox object
    h_chk = QCheckBox(parent)

    # sets the object properties
    h_chk.setText(text)
    h_chk.setFont(font)
    h_chk.setChecked(state)

    # sets the object name string
    if name is not None:
        h_chk.setObjectName(name)

    # returns the object
    return h_chk


def create_tab_group(parent, font=None, name=None):
    """

    :param parent:
    :param font:
    :param name:
    :return:
    """

    # creates a default font object (if not provided)
    if font is None:
        font = create_font_obj()

    # creates the tab object
    h_tab_grp = QTabWidget(parent)

    # sets the listbox object properties
    h_tab_grp.setFont(font)

    # sets the object name string
    if name is not None:
        h_tab_grp.setObjectName(name)

    # returns the tab object
    return h_tab_grp


def create_font_obj(size=9, is_bold=False, font_weight=QFont.Weight.Normal):
    """

    :param size:
    :param is_bold:
    :param font_weight:
    :return:
    """

    # creates the font object
    font = QFont()

    # sets the font properties
    font.setPointSize(size)
    font.setBold(is_bold)
    font.setWeight(font_weight)

    # returns the font object
    return font
