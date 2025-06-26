# module import
import os
import re
import pickle
import colorsys
import textwrap
import functools
import time

import numpy as np
from copy import deepcopy
from pathlib import PosixPath
from skimage.measure import label, regionprops

#
from pyqtgraph import ViewBox, RectROI, InfiniteLine, ColorMap, colormap

# custom module import
import spykit.common.common_func as cf

# pyqt6 module import
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QGridLayout, QVBoxLayout, QPushButton, QGroupBox, QTabWidget,
                             QFormLayout, QLabel, QCheckBox, QLineEdit, QComboBox, QSizePolicy, QFileDialog,
                             QApplication, QTreeView, QFrame, QRadioButton, QAbstractItemView, QStylePainter,
                             QStyleOptionComboBox, QStyle, QProxyStyle, QItemDelegate, QTreeWidget, QTreeWidgetItem,
                             QHeaderView, QStyleOptionButton, QTableWidgetItem, QProgressBar, QSpacerItem,
                             QStyledItemDelegate)
from PyQt6.QtCore import (Qt, QRect, QRectF, QMimeData, pyqtSignal, QItemSelectionModel, QAbstractTableModel,
                          QSizeF, QSize, QObject, QVariant, QTimeLine, QEvent)
from PyQt6.QtGui import (QFont, QDrag, QCursor, QStandardItemModel, QStandardItem, QPalette, QPixmap,
                         QTextDocument, QAbstractTextDocumentLayout, QIcon, QColor, QImage, QMouseEvent)

# ----------------------------------------------------------------------------------------------------------------------

# style sheets


# subject/session model flags
sub_flag = QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows
ses_flag = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows

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
edit_style_sheet = """
    border: 1px solid; 
    border-radius: 2px; 
    padding-left: 5px;
"""

# alignment flags
align_flag = {
    'top': Qt.AlignmentFlag.AlignTop,
    'bottom': Qt.AlignmentFlag.AlignBottom,
    'left': Qt.AlignmentFlag.AlignLeft,
    'right': Qt.AlignmentFlag.AlignRight,
    'center': Qt.AlignmentFlag.AlignCenter,
    'vcenter': Qt.AlignmentFlag.AlignVCenter,
}

# file path/filter modes
f_mode = {
    'session': "Spykit Session File (*.ssf)",
    'trigger': "Experiment Trigger File (*.npy)",
    'config': "Spike Pipeline Config File (*.cfig)",
}

f_name = {
    'session': "Session",
    'trigger': "Trigger",
    'config': "Configuration",
}

# parameter/resource folder paths
resource_dir = os.path.join(os.getcwd(), 'spykit', 'resources').replace('\\', '/')
icon_dir = os.path.join(resource_dir, 'icons').replace('\\', '/')
para_dir = os.path.join(resource_dir, 'parameters').replace('\\', '/')
figure_dir = os.path.join(resource_dir, 'figures').replace('\\', '/')
def_file = os.path.join(resource_dir, 'def_dir.pkl').replace('\\', '/')
ssort_para = os.path.join(resource_dir, 'ssort_para.csv').replace('\\', '/')

# icon paths
icon_path = {
    'open': os.path.join(icon_dir, 'open_icon.png'),
    'restart': os.path.join(icon_dir, 'restart_icon.png'),
    'close': os.path.join(icon_dir, 'close_icon.png'),
    'new': os.path.join(icon_dir, 'new_icon.png'),
    'add': os.path.join(icon_dir, 'add_icon.png'),
    'remove': os.path.join(icon_dir, 'remove_icon.png'),
    'save': os.path.join(icon_dir, 'save_icon.png'),
    'toggle': os.path.join(icon_dir, 'toggle_icon.png'),
    'checked_wide': os.path.join(icon_dir, 'checked_wide_icon.png'),
    'unchecked_wide': os.path.join(icon_dir, 'unchecked_wide_icon.png'),
    'datatip_on': os.path.join(icon_dir, 'datatip_on_icon.png'),
    'datatip_off': os.path.join(icon_dir, 'datatip_off_icon.png'),
    'search': os.path.join(icon_dir, 'search_icon.png'),
    'arrow_left': os.path.join(icon_dir, 'arrow_left_icon.png'),
    'arrow_right': os.path.join(icon_dir, 'arrow_right_icon.png'),
    'arrow_up': os.path.join(icon_dir, 'arrow_up_icon.png'),
    'arrow_down': os.path.join(icon_dir, 'arrow_down_icon.png'),
    'tick': os.path.join(icon_dir, 'tick_icon.png'),
    'trace_on': os.path.join(icon_dir, 'trace_on_icon.png'),
    'trace_off': os.path.join(icon_dir, 'trace_off_icon.png'),
    'star_on': os.path.join(icon_dir, 'star_on_icon.png'),
    'star_off': os.path.join(icon_dir, 'star_off_icon.png'),
}

# channel status colour values
p_col_status = {
    'good': cf.get_colour_value('g', 150),
    'dead': cf.get_colour_value('r', 150),
    'noise': cf.get_colour_value('y', 150),
    'out': cf.get_colour_value('m', 150),
    'na': cf.get_colour_value('w', 150),
}

# matplotlib colourmap strings
cmap = {
    # diverging colour maps
    'Diverging': [
        'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu',
        'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic',
        'berlin', 'managua', 'vanimo'
    ],

    # uniform sequential
    'UniformSequential': [
        'viridis', 'plasma', 'inferno', 'magma', 'cividis'
    ],

    # sequential colour maps
    'Sequential': [
        'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
        'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
        'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn'
    ],

    # sequential2 colour maps
    'Sequential2': [
        'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone',
        'pink', 'spring', 'summer', 'autumn', 'winter', 'cool',
        'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper'
    ],

    # cyclic colour maps
    'Cyclic': [
        'twilight', 'twilight_shifted', 'hsv'
    ],

    # qualitative colour maps
    'Qualitative': [
        'Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2',
        'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c'
    ],

    # miscellaneous colour maps
    'Miscellaneous': [
        'flag', 'prism', 'ocean', 'gist_earth', 'terrain',
        'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap',
        'cubehelix', 'brg', 'gist_rainbow', 'rainbow', 'jet',
        'turbo', 'nipy_spectral', 'gist_ncar'
    ],
}

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

# widget dimensions
x_gap = 5
row_height = 16.5
cell_height = 25

# trace span min/max sizes
t_span_min = 0.01
t_span_max = 0.5

def create_font_obj(size=9, is_bold=False, font_weight=QFont.Weight.Normal):
    # creates the font object
    font = QFont()

    # sets the font properties
    font.setPointSize(size)
    font.setBold(is_bold)
    font.setWeight(font_weight)

    # returns the font object
    return font

# ----------------------------------------------------------------------------------------------------------------------
# SPECIAL WIDGETS
# ----------------------------------------------------------------------------------------------------------------------

"""
    QRegionConfig:
"""


class QRegionConfig(QWidget):
    # signal functions
    config_reset = pyqtSignal()

    # dimensions
    x_gap = 10
    gbox_height0 = 10
    n_col_max = 10

    # array class fields
    p_list_base = ['(No Plot)']

    def __init__(self, parent=None, font=None, is_expanded=False, can_close=True, p_list0=None, gbox_height=None):
        super(QRegionConfig, self).__init__(parent)

        if p_list0 is None:
            p_list0 = []

        # sets up the colour values
        p_col0 = [cf.get_colour_value(x + 1, n_col_new=self.n_col_max) for x in range(self.n_col_max)]
        p_col0 = p_col0[::2] + p_col0[1::2]

        # field initialisations
        self.n_row = 1
        self.n_col = 1
        self.is_sel = None
        self.gbox_height = gbox_height
        self.tr_col = cf.get_colour_value('w')

        # array class fields
        self.h_rgrid = []
        self.g_id = np.zeros((2, 2), dtype=int)
        self.c_id = np.zeros((self.n_row, self.n_col), dtype=int)

        # boolean class fields
        self.is_updating = False
        self.is_mouse_down = False
        self.is_expanded = is_expanded

        # sets up the widget layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # other object initialisations
        self.q_cursor = QCursor()
        self.h_root = cf.get_root_widget(self.parent())

        # ROW/COLUMN WIDGET SETUP ---------------------------------------------

        # field initialisations
        t_lbl = ['Row', 'Column']
        p_str = ['n_row', 'n_col']

        # row/column widget setup
        self.rc_layout = QHBoxLayout()
        self.rc_layout.setSpacing(0)
        self.rc_layout.setContentsMargins(0, 0, 0, 5)

        # region config widget setup
        self.rc_widget = QWidget()
        self.rc_widget.setLayout(self.rc_layout)

        # creates the row/column widgets
        for tl, ps in zip(t_lbl, p_str):
            # creates the label/editbox object
            tl_lbl = "{0}:".format(tl)
            obj_lbl_edit = QLabelEdit(None, tl_lbl, getattr(self, ps), font_lbl=font, name=ps)
            self.rc_layout.addWidget(obj_lbl_edit)

            # sets the editbox widget properties
            obj_lbl_edit.obj_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            obj_lbl_edit.obj_lbl.adjustSize()
            # obj_lbl_edit.obj_lbl.setStyleSheet("padding-left: 5px; padding-top: 5px;")
            obj_lbl_edit.obj_lbl.setStyleSheet("padding-left: 5px;")

            # sets the callback function
            cb_fcn_rc = functools.partial(self.edit_dim_update, ps)
            obj_lbl_edit.connect(cb_fcn_rc)

        # adds the combo object
        self.p_list = self.p_list_base + p_list0
        self.p_col = [cf.get_colour_value('lg')] + p_col0
        self.obj_lbl_combo = QLabelCombo(
            None, 'Plot Type: ', self.p_list, self.p_list[0], font_lbl=font)

        # sets the label properties
        self.obj_lbl_combo.obj_lbl.setFixedWidth(80)
        # self.obj_lbl_combo.obj_lbl.setStyleSheet("padding-top: 5px;")
        self.obj_lbl_combo.connect(self.combo_update_trace)

        # region config widget setup
        self.v_spacer = QSpacerItem(5, 0, cf.q_min, cf.q_exp)

        # trace index/colour fields
        self.i_trace = self.obj_lbl_combo.obj_cbox.currentIndex()
        self.tr_col = self.p_col[self.i_trace]

        # adds the widgets to the class widget
        self.main_layout.addWidget(self.rc_widget)
        self.main_layout.addWidget(self.obj_lbl_combo)

        # REGION SELECTOR WIDGET SETUP ----------------------------------------

        # initialisations
        self.gbox_rect = QRect(5, 0, 10, 15)

        # creates the groupbox object
        self.obj_gbox = QGroupBox(cf.arr_chr(False))
        self.obj_gbox.setCheckable(False)
        self.obj_gbox.setFont(font)

        # adds the widget to the class widget
        self.main_layout.addWidget(self.obj_gbox)
        self.main_layout.addItem(self.v_spacer)

        # sets the initial config groupbox height
        if is_expanded:
            # case is the groupbox is expanded
            self.obj_gbox.setTitle(cf.arr_chr(True))
            if self.gbox_height is None:
                sz_main = self.main_layout.sizeHint()
                self.gbox_height = sz_main.width() - (sz_main.height() - self.gbox_height0)

            self.obj_gbox.setFixedHeight(self.gbox_height)

        else:
            # case is the groupbox is collapsed
            self.obj_gbox.setFixedHeight(self.gbox_height0)

        # sets up the groupbox layout widget
        self.gb_layout = QGridLayout()
        self.gb_layout.setSpacing(0)
        self.gb_layout.setContentsMargins(self.x_gap, 0, self.x_gap, self.x_gap)

        # updates the selector widgets
        self.reset_selector_widgets()
        self.set_enabled(False)

        # sets the groupbox properties
        self.obj_gbox.setLayout(self.gb_layout)
        if can_close:
            self.obj_gbox.mousePressEvent = self.panel_group_update

    # MOUSE EVENT FUNCTIONS ---------------------------------------------------

    def mouse_clicked(self, i_row, i_col, is_press):

        # updates the current flag
        g_idc = np.array([i_row, i_col])

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

    # WIDGET EVENT FUNCTIONS -------------------------------------------------

    def panel_group_update(self, evnt, force_update=False):

        # determines if the mouse-click is on the title
        if self.gbox_rect.contains(evnt.pos()):
            # if so, update the parameters
            self.is_expanded = self.is_expanded ^ True
            self.obj_gbox.setTitle(cf.arr_chr(self.is_expanded))

            # calculates the widget dimensions
            self.reset_config_group_height()

    def edit_dim_update(self, p_str, h_edit):

        if self.is_updating:
            return

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

        if self.is_updating:
            return

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

    # INDEXING FUNCTIONS ------------------------------------------------------

    def get_region_index(self, i_row, i_col):

        return i_row * self.n_col + i_col

    def get_grid_indices(self, i_reg):

        return i_reg // self.n_col, i_reg % self.n_col

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def add_trace_item(self, p_item):

        a = 1

    def reset_config_id(self, c_id_new):

        # set the flag to updating
        self.is_updating = True

        # updates the class fields with the new ID
        self.c_id = c_id_new
        self.n_row, self.n_col = c_id_new.shape

        # resets the grid configuration fields
        for n in ['n_row', 'n_col']:
            h_edit = self.findChild(QLineEdit, name=n)
            h_edit.setText(str(getattr(self, n)))

        # resets the update flag
        self.is_updating = False

    def reset_selector_widgets(self, c_id_new=None):

        # updates the configuration ID's (if provided)
        if c_id_new is not None:
            self.reset_config_id(c_id_new)

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

    def calc_groupbox_height(self):

        return (2 * self.is_expanded - 1) * (self.obj_gbox.width() - self.gbox_height0)

    def reset_config_group_height(self):

        d_hght = self.calc_groupbox_height()
        sz_spacer = self.v_spacer.minimumSize()

        self.v_spacer.changeSize(5, sz_spacer.height() - d_hght)
        self.obj_gbox.setFixedHeight(self.obj_gbox.height() + d_hght)

    def set_enabled(self, state):

        self.obj_lbl_combo.set_enabled(state)

        for p_str in ['n_row', 'n_col']:
            h_obj = self.findChild(QLineEdit, name=p_str)
            h_obj.setEnabled(state)

        for h_lbl in self.findChildren(QLabel):
            h_lbl.setEnabled(state)

    def clear(self):

        # resets the configuration
        self.reset_selector_widgets(np.zeros((1, 1), dtype=int))
        self.config_reset.emit()

        # resets the combobox fiels
        self.reset()

    def reset(self):

        # disables the widget
        self.set_enabled(False)

        # removes the fields from the
        self.is_updating = True
        self.obj_lbl_combo.obj_cbox.clear()
        self.obj_lbl_combo.obj_cbox.addItem(self.p_list_base[0])
        self.is_updating = False

    @staticmethod
    def get_rgba_string(t_col):

        return 'rgba({0}, {1}, {2}, {3})'.format(t_col.red(), t_col.green(), t_col.blue(), t_col.alpha())

    @staticmethod
    def get_side_index(m_pos, w_sz):

        return [(m_pos.x() >= w_sz.width()) - (m_pos.x() <= 0),
                (m_pos.y() >= w_sz.height()) - (m_pos.y() <= 0)]


# ----------------------------------------------------------------------------------------------------------------------

"""
    QAxesLimits:
"""


class QAxesLimits(QWidget):
    # initialisations
    ax_del = 1e-8

    # array class fields
    p_str = ['x_min', 'x_max', 'y_min', 'y_max']

    def __init__(self, parent=None, font=None, p_props=None):
        super(QAxesLimits, self).__init__(parent)

        # array class fields
        self.x_lim = []
        self.y_lim = []

        # widget class fields
        self.h_edit = []
        self.obj_lbl_dur = None

        # field initialisation
        self.font = font
        self.p_props = p_props

        # widget initialisations
        self.main_layout = QVBoxLayout()

        # creates the class field widgets
        self.init_class_fields()

    def init_class_fields(self):

        # sets up the widget layout
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # AXIS LIMIT WIDGETS --------------------------------------------------

        # creates the limit widgets
        lim_widget = QWidget()

        lim_layout = QGridLayout(self)
        lim_layout.setContentsMargins(0, 0, 0, 5)
        lim_widget.setLayout(lim_layout)

        # creates the min/max header labels
        h_lbl_min = create_text_label(None, 'Min', self.font, align='center')
        h_lbl_max = create_text_label(None, 'Max', self.font, align='center')
        h_lbl_min.setFixedHeight(10)
        h_lbl_max.setFixedHeight(10)

        # creates the header row
        lim_layout.addWidget(h_lbl_min, 0, 1, 1, 1)
        lim_layout.addWidget(h_lbl_max, 0, 2, 1, 1)

        # creates the x-axis limit row
        lim_layout.addWidget(create_text_label(None, 'X-Axis:', self.font), 1, 0, 1, 1)
        lim_layout.addWidget(create_text_label(None, 'Y-Axis:', self.font), 2, 0, 1, 1)

        for i in range(2):
            for j in range(2):
                # creates the line edit widget
                h_edit_new = create_line_edit(None, '', name=self.p_str[len(self.h_edit)])
                lim_layout.addWidget(h_edit_new, i + 1, j + 1, 1, 1)

                # sets the editbox event callback function
                cb_fcn = functools.partial(self.edit_limit_para, h_edit_new)
                h_edit_new.editingFinished.connect(cb_fcn)
                h_edit_new.setStyleSheet(edit_style_sheet)

                # appends the widget to the class field
                self.h_edit.append(h_edit_new)

        # adds the widget to the main widget
        self.main_layout.addWidget(lim_widget)

        # OTHER CLASS WIDGETS -------------------------------------------------

        # sets up the label edit widget
        self.obj_lbl_dur = QLabelText(
            None, 'Signal Duration: ', '0', font_lbl=self.font, font_txt=self.font, name='t_dur')
        self.main_layout.addWidget(self.obj_lbl_dur)

    def edit_limit_para(self, h_edit):

        # module import
        from spykit.widgets.plot_widget import QPlotWidgetMain

        # field retrieval
        nw_val = h_edit.text()
        p_str = h_edit.objectName()
        is_xlim_para = p_str.startswith('x_')

        # REMOVE ME LATER
        p_min, p_max = 0, 12

        # resets the main flag
        h_root = cf.get_parent_widget(self, QPlotWidgetMain)
        tr_obj = h_root.get_trace_object()
        h_root.was_reset = True

        # sets the parameter lower/upper limits
        match p_str:
            case 'x_min':
                # case is the lower x-axis limit
                p_min = tr_obj.plot_obj.x_lim0[0]
                p_max = self.p_props.x_max - self.ax_del

            case 'x_max':
                # case is the upper x-axis limit
                p_min = self.p_props.x_min + self.ax_del
                p_max = tr_obj.plot_obj.x_lim0[1]

            case 'y_min':
                # case is the lower y-axis limit
                p_min = tr_obj.plot_obj.y_lim0[0]
                p_max = self.p_props.y_max

            case 'y_max':
                # case is the upper y-axis limit
                p_min = self.p_props.y_min
                p_max = tr_obj.plot_obj.y_lim0[1]

        # determines if the new value is valid
        chk_val = cf.check_edit_num(nw_val, min_val=p_min, max_val=p_max, is_int=False)
        if chk_val[1] is None:
            # case is the value is valid

            # updates the other class field with the new value
            setattr(self.p_props, p_str, chk_val[0])

            # updates the signal duration (if altering x-axis limit value)
            if is_xlim_para:
                t_dur = self.p_props.x_max - self.p_props.x_min
                self.obj_lbl_dur.obj_txt.setText('%g' % t_dur)

                # resets the region limits
                x_lim_new = [self.p_props.x_min, self.p_props.x_max]
                tr_obj.plot_obj.l_reg_p.setRegion(tuple(x_lim_new))

        else:
            # otherwise, reset to the previous valid value
            h_edit.setText('%g' % getattr(self.p_props, p_str))


# ----------------------------------------------------------------------------------------------------------------------

"""
    QTraceTree:
"""


class QTraceTree(QWidget):
    # signal functions
    node_added = pyqtSignal()
    node_deleted = pyqtSignal()

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

    def __init__(self, parent=None, font=None):
        super(QTraceTree, self).__init__(parent)

        # field initialisations
        self.n_trace = 0
        self.h_node = {}
        self.s_node = {}

        # sets up the widget layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # mouse event function fields
        self.mp_event_dclick = None

        # TEXT LABEL SETUP ----------------------------------------------------

        # creates the text label
        self.obj_txt_lbl = QLabelText(None, 'Trace Count: ', '0', font_lbl=font, name='name')
        self.main_layout.addWidget(self.obj_txt_lbl)

        # sets the label properties
        self.obj_txt_lbl.obj_lbl.setFixedSize(self.obj_txt_lbl.obj_lbl.sizeHint())

        # TREE WIDGET SETUP ---------------------------------------------------

        # sets up the table model
        self.t_model = QStandardItemModel()
        self.t_model.dataChanged.connect(self.node_name_update)

        # creates the tree-view widget
        self.obj_tview = QTreeView()
        self.mp_event_dclick = self.obj_tview.mouseDoubleClickEvent
        self.obj_tview.mouseDoubleClickEvent = self.tree_double_clicked

        # sets the tree-view properties
        self.obj_tview.setModel(self.t_model)
        self.obj_tview.setStyleSheet(self.tree_style)
        self.obj_tview.setItemsExpandable(False)
        self.obj_tview.setIndentation(10)
        self.obj_tview.setHeaderHidden(True)
        self.obj_tview.setFrameStyle(QFrame.Shape.WinPanel | QFrame.Shadow.Sunken)

        # appends the widget to the main widget
        self.main_layout.addWidget(self.obj_tview)

    # TREE ADD/DELETE FUNCTIONS ----------------------------------------------

    def add_tree_item(self, n_name, h_parent=None):

        # creates the tree item
        item = QStandardItem(n_name)
        item.setEditable(n_name != "Main Trace")

        if h_parent is None:
            # case is the root trace
            self.t_model.appendRow(item)

        else:
            # case is a sub-trace
            h_parent.h_tree.appendRow(item)

        # increments the counter
        self.n_trace += 1
        self.obj_txt_lbl.set_label(str(self.n_trace))

        # resets the tree-viewer properties
        self.reset_tview_props()

        # returns the tree item
        return item

    def delete_tree_item(self, item):

        # module import
        from spykit.widgets.plot_widget import QPlotWidgetMain

        # creates the tree item
        if item.parent() is None:
            h_root = cf.get_parent_widget(self, QPlotWidgetMain)
            h_root.obj_para.obj_ttree.t_model.removeRow(item.row())

        else:
            item.parent().removeRow(item.row())

        # increments the counter
        self.n_trace -= 1
        self.obj_txt_lbl.set_label(str(self.n_trace))

        # resets the tree-viewer properties
        self.reset_tview_props()

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def node_name_update(self, ind_mod_1, *_):

        from spykit.widgets.plot_widget import QPlotPara

        h_plot_para = cf.get_parent_widget(self, QPlotPara)
        h_plot_para.p_props.name = ind_mod_1.data()

    def tree_double_clicked(self, evnt):
        """

        :return:
        """

        # module import
        from spykit.widgets.plot_widget import QPlotWidgetMain

        # retrieves the tree item
        item_index = self.obj_tview.selectedIndexes()[0]
        h_tree = item_index.model().itemFromIndex(item_index)

        # determines the index of the currently selected tree item
        h_root = cf.get_parent_widget(self, QPlotWidgetMain)
        i_trace_nw = next((i for i, x in enumerate(h_root.tr_obj) if x.h_tree == h_tree))

        # resets the selected trace (if not matching)
        if h_root.i_trace != i_trace_nw:
            # resets the selected plot
            obj_tr_nw = h_root.tr_obj[i_trace_nw]
            h_root.change_selected_plot(obj_tr_nw)

            # resets the groupbox properties
            g_box = obj_tr_nw.plot_obj.obj_plot_gbox
            g_box.setObjectName('selected')
            g_box.setStyleSheet(g_box.styleSheet())

        self.mp_event_dclick(evnt)

    def reset_tview_props(self):

        self.obj_tview.setFixedHeight(int(self.n_trace * row_height) + 2)
        self.obj_tview.expandAll()


# ----------------------------------------------------------------------------------------------------------------------

"""
    QFolderTree:
"""


class QFolderTree(QWidget):
    # dimensions
    n_row = 14

    # signal functions
    session_changed = pyqtSignal(QStandardItem)
    subject_changed = pyqtSignal(QStandardItem)

    # widget stylesheets
    tree_style = """
        QTreeView {
            font: Arial 8px;
        }
        QTreeView::item:selected {
            color: red;
            background-color: #9fedab;
        }    
    """

    def __init__(self, parent=None, data_dict=None, is_feas_tree=False):
        super(QFolderTree, self).__init__(parent)

        #
        self.bold_highlight = create_font_obj(is_bold=True)

        # field initialisations
        self.t_dict = {}
        self.root = parent
        self.data_dict = data_dict
        self.r_ses = re.compile(r'ses-[0-9]{3}')
        self.r_sub = re.compile(r'sub-[0-9]{3}')

        # sets up the widget layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # TREE WIDGET SETUP ---------------------------------------------------

        # sets up the table model
        self.t_model = QStandardItemModel()

        # creates the tree-view widget
        self.obj_tview = QTreeView()
        if is_feas_tree:
            self.mp_event_dclick = self.obj_tview.mouseDoubleClickEvent
            self.obj_tview.mouseDoubleClickEvent = self.tree_double_clicked

        # sets the tree-view properties
        self.obj_tview.setModel(self.t_model)
        self.obj_tview.setStyleSheet(self.tree_style)
        self.obj_tview.setIndentation(10)
        self.obj_tview.setHeaderHidden(True)
        self.obj_tview.setFrameStyle(QFrame.Shape.WinPanel | QFrame.Shadow.Sunken)
        self.obj_tview.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        # appends the widget to the main widget
        self.main_layout.addWidget(self.obj_tview)
        # self.setFixedHeight(int(self.n_row * row_height))
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

    # TREE ADD/DELETE FUNCTIONS ----------------------------------------------

    def reset_tree_items(self, data_dict_new):

        # updates the data dictionary
        self.data_dict = data_dict_new

        # clears and resets the tree items
        self.t_model.clear()
        self.add_all_tree_items()

    def add_all_tree_items(self):

        # creates the tree widgets
        for dd in self.data_dict:
            self.t_dict[dd] = self.add_tree_item(dd)

    def add_tree_item(self, s_node):

        # splits the node string
        s_sp = s_node.rsplit('/', 1)

        # creates the tree item
        item = QStandardItem(s_sp[1])
        item.setEditable(False)
        item.setData('/'.join(s_sp))

        if len(s_sp[0]):
            # case is the root trace
            self.t_dict[s_sp[0]].appendRow(item)

        else:
            # case is the root trace
            self.t_model.appendRow(item)

        # expands/collapses the tree nodes (so that rawdata folder is the last expanded node)
        if self.r_sub.findall(s_node):
            self.obj_tview.collapse(item.index())

        else:
            self.obj_tview.expand(item.index())

        # returns the tree item
        return item

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def tree_double_clicked(self, evnt):

        # retrieves the tree item
        if type(evnt) == QStandardItem:
            item, item_index = evnt, evnt.index()

        else:
            item_index = self.obj_tview.indexAt(evnt.pos())
            item = item_index.model().itemFromIndex(item_index)

        # performs a sequential search for
        s_path, is_ses_sel = item.data(), False
        if self.r_ses.findall(s_path):
            # case a session (or child node) has been selected

            # determines if a new subject was selected
            sub_path_new = self.get_path(self.r_sub, s_path)
            is_sub_sel = sub_path_new != self.root.sub_path

            # determines if a new session node was selected
            ses_path_new = self.get_path(self.r_ses, s_path)
            is_ses_sel = ses_path_new != self.root.sub_path

        else:
            # otherwise, determine if a raw node
            is_ses_sel = False
            if len(self.r_sub.findall(s_path)):
                sub_path_new = self.get_path(self.r_sub, s_path)
                is_sub_sel = sub_path_new != self.root.sub_path

            else:
                is_sub_sel = False

        if is_sub_sel:
            # resets the path field
            self.root.sub_path = sub_path_new

            # rus the subject changed function
            self.subject_changed.emit(item)
            self.update_tree_highlights()

        if is_ses_sel:
            # resets the path field
            self.root.ses_type = ses_path_new

            # rus the subject changed function
            self.session_changed.emit(item)
            self.update_tree_highlights()

    def update_tree_highlights(self):

        # field retrieval
        t_dict = self.root.h_tab[0].findChild(QFolderTree).t_dict

        # enables the multi-selection property
        self.obj_tview.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        # updates the subject selection
        index_sub = t_dict[self.root.sub_path].index()
        self.obj_tview.selectionModel().select(index_sub, sub_flag)

        # updates the session selection
        item_ses = t_dict['/'.join([self.root.sub_path, self.root.ses_type])].index()
        self.obj_tview.selectionModel().select(item_ses, ses_flag)

        # removes the selection property
        self.obj_tview.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

    @staticmethod
    def get_path(r, text):

        return r.split(text)[0] + r.findall(text)[0]


# ----------------------------------------------------------------------------------------------------------------------

"""
    QCollapseGroup:
"""


class QCollapseGroup(QWidget):
    # object dimensions
    w_space = 10

    # expanded group style-sheet
    expand_style = """
        text-align:left;
        background-color: rgba(26, 83, 200, 255);
        color: rgba(255, 255, 255, 255);
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    """

    # collapsed group style-sheet
    close_style = """
        text-align:left;
        background-color: rgba(26, 83, 200, 255);
        color: rgba(255, 255, 255, 255);
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
    """

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
        self.main_layout.setContentsMargins(self.w_space, is_first * self.w_space, self.w_space, self.w_space)

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

    # WIDGET SETUP FUNCTIONS --------------------------------------------------

    def add_group_row(self, h_obj1, h_obj2):

        # adds the object to the layout
        self.form_layout.addWidget(h_obj1, h_obj2)

    # PANEL EVENT FUNCTIONS ---------------------------------------------------

    def connect(self, cb_fcn0=None):

        if cb_fcn0 is None:
            cb_fcn0 = self.expand

        # sets the button click event function
        self.expand_button.clicked.connect(cb_fcn0)

    def expand(self, *_):

        if hasattr(self.parent(), 'was_reset') and self.parent().was_reset:
            # hack fix - top panel group wants to collapse when editbox value is reset?
            self.parent().was_reset = False

        else:
            # field retrieval
            self.is_expanded = self.is_expanded ^ True
            self.update_button_text()

            # sets the button style
            f_style = self.expand_style if self.is_expanded else self.close_style
            self.expand_button.setStyleSheet(f_style)

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def update_button_text(self):

        self.expand_button.setText(' {0} {1}'.format(cf.arr_chr(self.is_expanded), self.panel_hdr))
        self.group_panel.setMaximumHeight(self.is_expanded * self.orig_hght)

        # resets the button stylesheet
        f_style = self.expand_style if self.is_expanded else self.close_style
        self.expand_button.setStyleSheet(f_style)

    def set_styling(self):

        self.group_panel.setStyleSheet("background-color: rgba(240, 240, 255, 255) ;")
        self.expand_button.setStyleSheet(self.expand_style)


# ----------------------------------------------------------------------------------------------------------------------

"""
    FileDialogModal:
"""


class FileDialogModal(QFileDialog):
    def __init__(self, parent=None, caption=None, f_filter=None,
                 f_directory=None, is_save=False, dir_only=False, is_multi=False):
        # creates the widget
        super(FileDialogModal, self).__init__(parent=parent, caption=caption, filter=f_filter, directory=f_directory)

        # sets the file dialog parameters
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        self.setOption(self.Option.DontUseNativeDialog)

        # sets the file dialog to open if
        if is_save:
            self.setAcceptMode(self.AcceptMode.AcceptSave)

        else:
            self.setAcceptMode(self.AcceptMode.AcceptOpen)

        # sets the file mode to directory (if directory only)
        if dir_only:
            self.setFileMode(self.FileMode.Directory)
            self.setOption(self.Option.ShowDirsOnly)
            self.setOption(self.Option.DontUseNativeDialog)

        else:
            self.setFileMode(self.FileMode.AnyFile)

        # else:
        #     self.setFileMode(self.FileMode.ExistingFiles)

        # sets the multi-select flag to true (if required)
        if is_multi:
            self.setFileMode(self.FileMode.ExistingFiles)

# ----------------------------------------------------------------------------------------------------------------------

"""
    ClickableRegion:
"""


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

    # MOUSE EVENT FUNCTIONS ---------------------------------------------------

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

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def set_grid_indices(self, i_row, i_col):

        self.i_row, self.i_col = i_row, i_col


# ----------------------------------------------------------------------------------------------------------------------

"""
    QFileSpec:
"""


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
        self.layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

        # creates the editbox widget
        self.h_edit = create_line_edit(None, str(file_path), align='left', name=name)
        self.layout.addWidget(self.h_edit)
        self.h_edit.setReadOnly(True)
        self.h_edit.setObjectName(name)
        self.h_edit.setToolTip(str(file_path))

        # creates the button widget
        self.h_but = create_push_button(None, '...', font_but)
        self.layout.addWidget(self.h_but)
        self.h_but.setFixedWidth(25)

    def set_text(self, f_str):
        self.h_edit.setText(f_str)
        self.h_edit.setToolTip(f_str)

    def connect(self, cb_fcn0):
        cb_fcn = functools.partial(cb_fcn0, self)
        self.h_but.clicked.connect(cb_fcn)


# ----------------------------------------------------------------------------------------------------------------------

"""
    HTMLDelegate:
"""


class QColorLabel(QLabel):
    # array class fields
    n_rep = 21

    def __init__(self, parent=None, c_map_name='viridis', name=None, n_pts=175):
        super(QColorLabel, self).__init__(parent)

        # field initialisations
        self.n_pts = n_pts
        self.xi_c = np.linspace(0, 1, self.n_pts)

        # sets the widget properties
        self.setObjectName(name)
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_max))
        self.setStyleSheet("border: 1px solid black;")

        # creates the image map
        self.setup_label_image(c_map_name)

    def setup_label_image(self, c_map_name):

        # sets up the mapped data values
        c_map = colormap.get(c_map_name, source="matplotlib")
        image_map = c_map.mapToByte(self.xi_c)[:, :3]

        # sets up the colormap image
        image_data = np.zeros((self.n_rep, self.n_pts, 3), dtype=np.uint8)
        for i in range(3):
            image_data[:, :, i] = image_map[:, i]

        # sets image pixmap properties
        lbl_image = QImage(bytes(image_data), self.n_pts, self.n_rep, 3 * self.n_pts, QImage.Format.Format_RGB888)
        self.setPixmap(QPixmap(lbl_image))

# ----------------------------------------------------------------------------------------------------------------------

"""
    HTMLDelegate:
"""


class QColorMapChooser(QFrame):
    # pyqtsignal functions
    colour_selected = pyqtSignal(str)

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

    # parameters
    col_wid = 105
    lbl_width = 85
    item_row_size = 23

    # font objects
    gray_col = QColor(160, 160, 160, 255)
    item_font = create_font_obj(9, True, QFont.Weight.Bold)
    item_child_font = create_font_obj(8)
    cmap_type = ['Diverging', 'UniformSequential', 'Sequential', 'Sequential2']

    def __init__(self, parent=None, c_map='viridis', name=None):
        super(QColorMapChooser, self).__init__(parent)

        if name is not None:
            self.setObjectName(name)

        # input arguments
        self.c_map = c_map

        # initialisations
        self.n_grp, self.n_para = 0, 0
        self.h_grp, self.h_para = {}, []
        self.para_grp, self.grp_name = [], []
        self.para_name0, self.para_name = [], []

        # property sorting group widgets
        self.main_layout = QVBoxLayout()
        self.select_layout = QHBoxLayout()

        # class widget setup
        self.select_widget = QWidget()
        self.tree_prop = QTreeWidget(self)
        self.select_lbl = create_text_label(None, 'Colour Map:', font_lbl, align='right')
        self.select_name = create_text_label(None, c_map, align='right')
        self.select_colour = QColorLabel(None, c_map_name=c_map, n_pts=self.col_wid)

        # initialises the class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the widget properties
        self.setLayout(self.main_layout)
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_min))
        self.setFrameStyle(QFrame.Shape.WinPanel | QFrame.Shadow.Plain)

        # adds the tree widget to the parent widget
        self.main_layout.setSpacing(x_gap)
        self.main_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.select_layout.setSpacing(x_gap)
        self.select_layout.setContentsMargins(0, 0, 0, 0)

        # add the widgets to the main layout
        self.main_layout.addWidget(self.select_widget)
        self.main_layout.addWidget(self.tree_prop)

        # add the widgets to the colourmap selection layout
        self.select_widget.setLayout(self.select_layout)
        self.select_layout.addWidget(self.select_lbl)
        self.select_layout.addWidget(self.select_name)
        self.select_layout.addWidget(self.select_colour)
        self.select_lbl.setSizePolicy(QSizePolicy(cf.q_min, cf.q_exp))

        # sets the selection widget properties
        self.select_name.setFixedWidth(self.lbl_width)
        self.select_colour.setFixedWidth(self.col_wid)
        self.select_lbl.setContentsMargins(0, 3, 0, 0)
        self.select_name.setContentsMargins(0, 3, 0, 0)

        # sets the tree-view properties
        self.tree_prop.setLineWidth(1)
        self.tree_prop.setColumnCount(2)
        self.tree_prop.setIndentation(10)
        self.tree_prop.setHeaderHidden(True)
        self.tree_prop.setStyleSheet(self.tree_style)
        self.tree_prop.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.tree_prop.setAlternatingRowColors(False)
        self.tree_prop.setItemDelegateForColumn(0, HTMLDelegate())
        self.tree_prop.header().setStretchLastSection(True)
        self.tree_prop.doubleClicked.connect(self.tree_double_clicked)

        # initialises the tree fields
        self.init_tree_fields()

    def init_tree_fields(self):

        for cm_type in self.cmap_type:
            # creates the parent item
            cm_grp = cmap[cm_type]
            item = QTreeWidgetItem(self.tree_prop)

            # sets the item properties
            item.setText(0, cm_type)
            item.setFont(0, self.item_font)
            item.setFirstColumnSpanned(True)
            item.setExpanded(True)

            # adds the main group to the search widget
            self.append_grp_obj(item, cm_type)

            # adds the tree widget item
            self.tree_prop.addTopLevelItem(item)
            for cm in cm_grp:
                # creates the property name field
                item_ch, obj_prop = self.create_child_tree_item(cm)
                item_ch.setTextAlignment(0, align_flag['right'] | align_flag['vcenter'])

                # adds the child tree widget item
                item.addChild(item_ch)
                self.append_para_obj(item_ch, cm)

                if obj_prop is not None:
                    self.tree_prop.setItemWidget(item_ch, 1, obj_prop)

    def create_child_tree_item(self, props):

        # creates the tree widget item
        item_ch = QTreeWidgetItem(None)
        item_ch.setText(0, props)

        # creates the colourmap label
        h_obj = QColorLabel(None, c_map_name=props)
        h_obj.setFixedHeight(self.item_row_size)

        # returns the objects
        return item_ch, h_obj

    def append_grp_obj(self, item, group_str):

        # increments the count
        self.n_grp += 1

        # appends the objects
        self.h_grp[group_str] = item
        self.grp_name.append(item.text(0))

    def append_para_obj(self, item, group_name):

        # increments the count
        self.n_para += 1
        p_name_s = re.sub(r'<[^>]*>|[&;]+', '', item.text(0))

        # appends the objects
        self.h_para.append(item)
        self.para_name.append(p_name_s.lower())
        self.para_name0.append(p_name_s)
        self.para_grp.append(group_name)

    def tree_double_clicked(self, index):

        # resets the property values
        c_map_new = self.tree_prop.itemFromIndex(index).text(0)
        self.select_colour.setup_label_image(c_map_new)
        self.select_name.setText(c_map_new)

        # updates the colour map field
        self.colour_selected.emit(c_map_new)

# ----------------------------------------------------------------------------------------------------------------------

"""
    HTMLDelegate:
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


# ----------------------------------------------------------------------------------------------------------------------

"""
    SearchMixin:
"""

class SearchMixin:

    def init_search_widgets(self):

        # initialisations
        close_pixmap = QIcon(icon_path['close']).pixmap(QSize(cf.but_height, cf.but_height))
        search_pixmap = QIcon(icon_path['search']).pixmap(QSize(cf.but_height, cf.but_height))

        # creates the pixmap object
        filter_obj = QLabelEdit(None, '', '')

        # filter label properties
        filter_obj.obj_lbl.setPixmap(search_pixmap)
        filter_obj.obj_lbl.setFixedHeight(cf.but_height)
        filter_obj.obj_lbl.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))

        # filter label properties
        close_obj = create_text_label(None, '')
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
        self.edit_search.setSizePolicy(QSizePolicy(cf.q_expm, cf.q_min))

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
        self.tab_layout.addWidget(filter_obj)

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
# BASE WIDGET COMBINATIONS
# ----------------------------------------------------------------------------------------------------------------------

"""
    QLabelText:
"""


class QLabelText(QWidget):
    def __init__(self, parent=None, lbl_str=None, text_str=None, font_lbl=None, font_txt=None, name=None):
        super(QLabelText, self).__init__(parent)

        if name is not None:
            self.setObjectName(name)

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
        self.obj_txt.setText(txt_str)


# ----------------------------------------------------------------------------------------------------------------------

"""
    QLabelEdit:
"""


class QLabelEdit(QWidget):
    def __init__(self, parent=None, lbl_str=None, edit_str=None, font_lbl=None, name=None):
        super(QLabelEdit, self).__init__(parent)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # creates the label/editbox widget combo
        self.obj_lbl = create_text_label(None, lbl_str, font=font_lbl)
        self.obj_edit = create_line_edit(None, edit_str, name=name, align='left')
        self.layout.addWidget(self.obj_lbl)
        self.layout.addWidget(self.obj_edit)

        # sets up the label properties
        self.obj_lbl.adjustSize()
        self.obj_lbl.setStyleSheet('padding-top: 4px;')

        # sets up the editbox properties
        self.obj_edit.setFixedHeight(cf.edit_height)
        self.obj_edit.setStyleSheet(edit_style_sheet)

    def get_text(self):
        return self.obj_edit.text()

    def set_text(self, edit_str):
        self.obj_edit.setText(edit_str)

    def set_tooltip(self, tt_str):
        self.obj_lbl.setToolTip(tt_str)

    def connect(self, cb_fcn0):
        cb_fcn = functools.partial(cb_fcn0, self.obj_edit)
        self.obj_edit.editingFinished.connect(cb_fcn)


# ----------------------------------------------------------------------------------------------------------------------

"""
    QLabelButton:
"""


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
        cb_fcn = functools.partial(cb_fcn0, self.obj_but)
        self.obj_but.clicked.connect(cb_fcn)


# ----------------------------------------------------------------------------------------------------------------------

"""
    QButtonPair:
"""


class QButtonPair(QWidget):
    def __init__(self, parent=None, but_str=None, font=None, name=None):
        super(QButtonPair, self).__init__(parent)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # sets the other widget properties
        self.setObjectName(name)
        self.setLayout(self.layout)

        # creates the label/editbox widget combo
        self.obj_but = []
        for i, bs in enumerate(but_str):
            # creates the button widgets
            obj_but_new = create_push_button(None, bs, font=font, name=name)
            obj_but_new.setFixedHeight(cf.but_height)
            obj_but_new.setCursor(Qt.CursorShape.PointingHandCursor)

            # adds the objects to the button
            self.obj_but.append(obj_but_new)
            self.layout.addWidget(obj_but_new)

    def connect(self, cb_fcn):

        for i, b in enumerate(self.obj_but):
            b.clicked.connect(functools.partial(cb_fcn, i))

    def set_enabled(self, i_button, state):

        self.obj_but[i_button].setEnabled(state)


# ----------------------------------------------------------------------------------------------------------------------

"""
    QLabelCombo:
"""


class QLabelCombo(QWidget):
    def __init__(self, parent=None, lbl_str=None, list_str=None, value=None, font_lbl=None, name=None):
        super(QLabelCombo, self).__init__(parent)

        if value is None:
            value = []

        if name is not None:
            self.setObjectName(name)

        # boolean class fields
        self.is_connected = False

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
        self.obj_lbl.setStyleSheet('padding-top: 3 px;')

        # sets up the slot function
        self.obj_cbox.setFixedHeight(cf.combo_height)
        self.obj_cbox.setStyleSheet('border-radius: 2px; border: 1px solid')

        # if p_col is not None:
        #     cb_model = self.obj_cbox.model()
        #     for i_c, p_c in enumerate(p_col):
        #         cb_model.setData(cb_model.index(i_c, 0), p_c, Qt.ItemDataRole.BackgroundRole)

        if len(value):
            self.obj_cbox.setCurrentText(value)
        else:
            self.obj_cbox.setEnabled(False)

    def current_text(self):

        return self.obj_cbox.currentText()

    def current_index(self):

        return self.obj_cbox.currentIndex()

    def set_current_text(self, c_text):

        self.obj_cbox.setCurrentText(c_text)

    def set_current_index(self, i_sel):

        self.obj_cbox.setCurrentIndex(i_sel)

    def set_enabled(self, state):

        self.obj_lbl.setEnabled(state)
        self.obj_cbox.setEnabled(state)

    def count(self):

        return self.obj_cbox.count()

    def clear(self):

        if self.count() > 0:
            self.obj_cbox.clear()
            self.obj_cbox.setEnabled(False)

    def connect(self, cb_fcn, add_widget=True):

        if self.is_connected:
            return

        elif add_widget:
            cb_fcn = functools.partial(cb_fcn, self.obj_cbox)

        self.is_connected = True
        self.obj_cbox.currentIndexChanged.connect(cb_fcn)

    def addItem(self, item):

        self.obj_cbox.addItem(item)

    def addItems(self, items, clear_items=False):

        if clear_items:
            self.clear()

        for t in items:
            self.addItem(t)


# ----------------------------------------------------------------------------------------------------------------------

"""
    QCheckCombo:
"""


class QCheckCombo(QComboBox):
    # pyqtsignal functions
    item_clicked = pyqtSignal(QStandardItem)

    def __init__(self, parent=None):
        super(QCheckCombo, self).__init__(parent)
        self.view().pressed.connect(self.item_press)
        self.view().clicked.connect(self.item_click)

        # field initialisation
        self.n_item = 0
        self.n_sel = 0
        self.is_updating = False
        self._title = '0 Items Selected'

        # sets the widget model and event functions
        self.combo_model = QStandardItemModel(self)

        # creates the checkbox object
        self.setFixedHeight(cf.combo_height)
        self.setStyleSheet('border-radius: 2px; border: 1px solid;')

        self.setModel(self.combo_model)

    def item_click(self, index):

        if self.is_updating:
            return

        item = self.combo_model.itemFromIndex(index)
        if item.checkState() == Qt.CheckState.Checked:
            self.n_sel += 1
        else:
            self.n_sel -= 1

        # runs the clicked item
        self.reset_title()
        self.item_clicked.emit(item)

    def item_press(self, index):

        # flag that a manual update is taking place
        self.is_updating = True

        # updates the checkbox state
        item = self.combo_model.itemFromIndex(index)
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)

        # resets the update flag
        self.is_updating = False

        # runs the clicked item
        self.reset_title()
        self.item_clicked.emit(item)

    def get_selected_items(self):

        s_list = []
        for i in range(self.n_item):
            item = self.combo_model.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                s_list.append(item.text())

        return s_list

    def add_item(self, t, state=False):

        # adds the item to the combobox
        self.addItem('     {0}'.format(t))

        # sets the item properties
        item = self.model().item(self.n_item, 0)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setData(Qt.CheckState.Checked if state else Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        item.setEditable(False)

        # increments the item/selection counters
        self.n_item += 1
        self.n_sel += int(state)
        self.reset_title()

        # returns the widget
        return item

    def reset_title(self):

        # resets the title
        self._title = '{0} Items Selected'.format(self.n_sel)
        self.repaint()

    def title(self):

        return self._title

    def paintEvent(self, event):

        painter = QStylePainter(self)
        painter.setPen(self.palette().color(QPalette.ColorRole.Text))
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        opt.currentText = self._title
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt)
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, opt)

    def clear(self):

        # removes all items from the combobox
        for i in range(self.n_item):
            self.removeItem(0)

        # resets the other fields
        self.n_item = 0
        self.n_sel = 0


# ----------------------------------------------------------------------------------------------------------------------

"""
    QLabelCheckCombo:
"""


class QLabelCheckCombo(QWidget):
    # pyqtsignal functions
    item_clicked = pyqtSignal(QStandardItem)

    def __init__(self, parent=None, lbl=None, text=None, index_on=None, font=None, name=None):
        super(QLabelCheckCombo, self).__init__(parent)

        # field initialisation
        self._title = 'Finish Me!'
        self.index_on = index_on

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # creates the label object
        self.h_lbl = create_text_label(None, lbl, font, align='right')
        self.h_lbl.setStyleSheet('padding-top: 3px;')
        self.h_lbl.adjustSize()

        # sets the widget model and event functions
        self.combo_model = QStandardItemModel(self)

        # creates the checkbox object
        self.h_combo = QCheckCombo(self)
        self.h_combo.item_clicked.connect(self.check_update)

        # adds the widgets to the layout
        self.layout.addWidget(self.h_lbl)
        self.layout.addWidget(self.h_combo)

    def add_item(self, t, state=False):
        self.h_combo.add_item(t, state)

    def get_selected_items(self):
        return [x.strip() for x in self.h_combo.get_selected_items()]

    def check_update(self, item):
        self.item_clicked.emit(item)

    def setEnabled(self, state):
        self.h_lbl.setEnabled(state)
        self.h_combo.setEnabled(state)

    def clear(self):
        self.h_combo.clear()


# ----------------------------------------------------------------------------------------------------------------------

"""
    QCheckboxHTML:
"""


class QCheckboxHTML(QWidget):
    def __init__(self, parent=None, text=None, state=False, font=None, name=None):
        super(QCheckboxHTML, self).__init__(parent)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        if name is not None:
            self.setObjectName(name)

        # creates the label object
        self.h_lbl = create_text_label(None, text, font, align='left')
        self.h_lbl.setStyleSheet('padding-bottom: 2px;')
        self.h_lbl.adjustSize()

        # creates the checkbox object
        self.h_chk = create_check_box(None, '', state, name=name)
        self.h_chk.adjustSize()
        self.h_chk.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))

        # adds the widgets to the layout
        self.layout.addWidget(self.h_chk)
        self.layout.addWidget(self.h_lbl)

    def connect(self, cb_fcn):
        self.h_chk.stateChanged.connect(cb_fcn)
        self.h_lbl.mousePressEvent = self.label_clicked

    def label_clicked(self, evnt):
        self.h_chk.setChecked(not self.h_chk.isChecked())

    def set_label_text(self, t_lbl):
        self.h_lbl.setText(t_lbl)

    def set_enabled(self, state):
        self.h_lbl.setEnabled(state)
        self.h_chk.setEnabled(state)

    def set_check(self, state):
        self.h_chk.setChecked(state)

    def get_check(self):
        return self.h_chk.isChecked()


# ----------------------------------------------------------------------------------------------------------------------

"""
    QProgressWidget:
"""


class QProgressWidget(QWidget):
    # static string fields
    dp_max = 10
    p_max = 1000
    t_period = 1000
    lbl_width = 170
    wait_lbl = "No Session Data Loaded"

    prog_style = """
        QProgressBar {
            border: 2px solid black;
            border-radius: 5px;
            background-color: #E0E0E0;
        }
        QProgressBar::chunk {
            background-color: #19e326;
            width: 10px; 
            margin: 0.25px;
        }
    """

    def __init__(self, parent=None, font=None):
        super(QProgressWidget, self).__init__(parent)

        # field retrieval
        self.session_obj = parent.session_obj

        # widget setup
        self.layout = QHBoxLayout(self)
        self.lbl_obj = create_text_label(self, self.wait_lbl, font, align='right')
        self.prog_bar = QProgressBar(self, minimum=0, maximum=self.p_max, textVisible=False)
        self.time_line = QTimeLine(self.t_period)

        # other class fields
        self.n_jobs = 0
        self.pr_max = 1.0
        self.job_name = []
        self.job_desc = []
        self.is_running = False
        self.p_max_r = self.p_max + 2 * self.dp_max

        # initialises the class fields
        self.init_class_fields()

    def init_class_fields(self):

        # sets up the layout properties
        self.layout.setSpacing(x_gap)
        self.layout.setContentsMargins(0, x_gap, 0, 0)
        self.setLayout(self.layout)

        # adds the widgets to the layout
        self.layout.addWidget(self.lbl_obj)
        self.layout.addWidget(self.prog_bar)

        # sets the label properties
        self.lbl_obj.setContentsMargins(0, x_gap, 0, 0)
        self.lbl_obj.setFixedWidth(self.lbl_width)
        self.lbl_obj.setToolTip(self.get_next_task())

        # sets the progressbar properties
        self.prog_bar.setStyleSheet(self.prog_style)

        # sets the timeline properties
        self.time_line.setLoopCount(int(1e6))
        self.time_line.setFrameRange(0, self.p_max)
        self.time_line.setUpdateInterval(50)
        self.time_line.frameChanged.connect(self.prog_update)

    def prog_update(self):

        pr_scl = self.p_max_r * self.pr_max
        p_val = int(pr_scl * self.time_line.currentValue()) - self.dp_max
        p_val = np.min([self.p_max, np.max([0, p_val])])
        self.prog_bar.setValue(p_val)

    def add_job(self, job_name_add, job_desc_add):

        # appends the new name/description
        self.job_name.append(job_name_add)
        self.job_desc.append(job_desc_add)

        # increments the job counter
        self.n_jobs += 1
        self.update_message_label()

        # stops the progressbar (if there are no more jobs)
        if not self.is_running:
            self.set_progbar_state(True)

    def delete_job(self, job_name_del):

        if job_name_del not in self.job_name:
            return

        # removes the job name/description
        i_del = self.job_name.index(job_name_del)
        self.job_name.pop(i_del)
        self.job_desc.pop(i_del)

        # decrements the job counter
        self.n_jobs -= 1
        self.update_message_label()

        # stops the progressbar (if there are no more jobs)
        if self.n_jobs == 0:
            self.set_progbar_state(False)

    def update_prog_message(self, desc_txt, pr_val):

        # updates the progressbar value
        self.pr_max = pr_val

        # updates the text/tooltip strings
        self.lbl_obj.setText(desc_txt)
        self.lbl_obj.setToolTip(desc_txt)

    def set_progbar_state(self, state=None):

        if state is None:
            state = self.is_running

        if state:
            # starts the timeline widget
            self.start_timer()

        else:
            # stops the timeline widget
            self.stop_timer()

            # resets the progressbar
            self.prog_bar.setValue(self.p_max)
            time.sleep(0.25)
            self.prog_bar.setValue(0)

            # resets the text label
            self.lbl_obj.setText(self.get_status_text())
            self.lbl_obj.setToolTip(self.get_next_task())

    def toggle_progbar_state(self):

        self.is_running ^= True
        self.set_progbar_state()

    def update_message_label(self):

        # initialisations
        desc_tt = None

        match self.n_jobs:
            case 0:
                # case is there are no jobs running
                desc_txt = self.get_status_text()
                desc_tt = self.get_next_task()

            case 1:
                # case is only one job is running
                desc_txt = self.job_desc[0]
                desc_tt = 'Job #{0}: {1}'.format(1, desc_txt)

            case _:
                # case is only multiple jobs are running
                desc_txt = '{0} Jobs Currently Running...'.format(self.n_jobs)
                desc_tt = '\n'.join(['Job #{0}: {1}'.format(i + 1, job) for i, job in enumerate(self.job_desc)])


        # updates the text/tooltip strings
        self.lbl_obj.setText(desc_txt)
        self.lbl_obj.setToolTip(desc_tt)


    def get_status_text(self):

        if self.session_obj.has_pp_runs():
            # case is data has been preprocessed
            return 'Session Data Preprocessed'

        elif self.session_obj.session is not None:
            # case is data is loaded
            return 'Session Data Loaded'

        else:
            # case is the default case
            return self.wait_lbl

    def get_next_task(self):

        curr_state = self.get_status_text()

        if self.session_obj.has_pp_runs():
            # case is preprocessed has been conducted
            next_task = 'Run Spike Sorting or further Preprocess Session'

        elif self.session_obj.session is not None:
            # case is data is loaded
            next_task = 'Run Session Preprocessing'

        else:
            # case is the default case
            next_task = 'Load Experimental Session'

        # returns the task string
        return 'Current State: {0}\nNext Task: {1}'.format(curr_state, next_task)

    def start_timer(self):

        self.is_running = True
        self.time_line.start()

    def stop_timer(self):

        self.time_line.stop()
        self.is_running = False

# ----------------------------------------------------------------------------------------------------------------------
# TABLE WIDGET CUSTOM MODEL CLASSES
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------

"""
    QDialogProgress:
"""


class QDialogProgress(QWidget):
    # static string fields
    dp_max = 10
    p_max = 1000
    t_period = 1000
    lbl_width = 200
    wait_lbl = 'Waiting For User Input...'

    prog_style = """
        QProgressBar {
            border: 2px solid black;
            border-radius: 5px;
            background-color: #E0E0E0;
        }
        QProgressBar::chunk {
            background-color: #19e326;
            width: 10px; 
            margin: 0.25px;
        }
    """

    def __init__(self, parent=None, font=None, is_task=True):
        super(QDialogProgress, self).__init__(parent)

        # input arguments
        self.is_task = is_task

        # widget setup
        self.layout = QHBoxLayout(self)
        self.lbl_obj = create_text_label(self, self.wait_lbl, font, align='right')
        self.prog_bar = QProgressBar(self, minimum=0, maximum=self.p_max, textVisible=False)
        self.time_line = QTimeLine(self.t_period) if is_task else None

        # other class fields
        self.n_jobs = 0
        self.pr_max = 1.0
        self.is_running = False
        self.p_max_r = self.p_max + 2 * self.dp_max

        # initialises the class fields
        self.init_class_fields()

    def init_class_fields(self):

        # sets up the layout properties
        self.layout.setSpacing(x_gap)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # adds the widgets to the layout
        self.layout.addWidget(self.lbl_obj)
        self.layout.addWidget(self.prog_bar)

        # sets the label properties
        self.lbl_obj.setContentsMargins(0, x_gap, 0, 0)
        self.lbl_obj.setFixedWidth(self.lbl_width)

        # sets the progressbar properties
        self.prog_bar.setStyleSheet(self.prog_style)

        # sets the timeline properties
        if self.is_task:
            self.time_line.setLoopCount(int(1e6))
            self.time_line.setFrameRange(0, self.p_max)
            self.time_line.setUpdateInterval(50)
            self.time_line.frameChanged.connect(self.prog_timer)

    # ---------------------------------------------------------------------------
    # Timer Functions
    # ---------------------------------------------------------------------------

    def prog_timer(self):

        pr_scl = self.p_max_r * self.pr_max
        p_val = int(pr_scl * self.time_line.currentValue()) - self.dp_max
        p_val = np.min([self.p_max, np.max([0, p_val])])
        self.prog_bar.setValue(p_val)

    def start_timer(self):

        if self.time_line is not None:
            self.is_running = True
            self.time_line.start()

    def stop_timer(self):

        if self.time_line is not None:
            self.time_line.stop()
            self.is_running = False

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def update_prog_fields(self, m_str, pr_val):

        if not self.is_task:
            # case is the overall progress
            p_val = int(pr_val * self.p_max) - self.dp_max
            self.prog_bar.setValue(p_val)

        # updates the message label
        if m_str is not None:
            self.lbl_obj.setText(m_str)

        # pauses for a little bit
        time.sleep(0.005)

    def set_progbar_state(self, state):

        if state:
            # starts the timeline widget
            self.start_timer()
            self.set_enabled(True)

        else:
            # stops the timeline widget
            self.stop_timer()

            # resets the progressbar
            self.prog_bar.setValue(self.p_max)
            time.sleep(0.25)
            self.prog_bar.setValue(0)

            # resets the text label
            self.lbl_obj.setText(self.wait_lbl)
            self.set_enabled(False)

    def set_enabled(self, state):

        self.lbl_obj.setEnabled(state)
        self.prog_bar.setEnabled(state)



"""
    PandasModel: 
"""


class PandasModel(QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """

    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):

        return len(self._data.values)

    def columnCount(self, parent=None):

        return self._data.columns.size

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):

        if index.isValid():
            # current cell value
            if role == Qt.ItemDataRole.DisplayRole:
                value = self._data.iloc[index.row()][self._data.columns[index.column()]]
                return str(value)

        return None

    def headerData(self, col, orientation, role):

        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._data.columns[col]

        return None


# ----------------------------------------------------------------------------------------------------------------------

"""
    InfoTableModel: 
"""


class InfoTableModel(QAbstractTableModel):
    chk_col = 0

    def __init__(self, data, c_hdr, parent=None):
        QAbstractTableModel.__init__(self, parent)

        self.c_hdr = c_hdr
        self.ch_select = data[:, self.chk_col]
        self._array = data[:, 1:]

        self.header_icon = None
        self.setHeaderIcon()

    def rowCount(self, _parent=None):

        return self._array.shape[0]

    def columnCount(self, _parent=None):

        return self._array.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):

        if not index.isValid():
            return None

        if index.column() == self.chk_col:
            value = ''
        else:
            value = QVariant('%g' % self._array[index.row(), index.column()])

        if role == Qt.ItemDataRole.EditRole:
            return value

        elif role == Qt.ItemDataRole.DisplayRole:
            return value

        elif role == Qt.ItemDataRole.CheckStateRole:
            if index.column() == self.chk_col:
                return cf.chk_state[self.ch_select[index.row()]]

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return cf.align_type['center']

        return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):

        if not index.isValid():
            return False

        if role == Qt.ItemDataRole.CheckStateRole and (index.column() == self.chk_col):
            self.ch_select[index.row()] ^= True
            # if value == cf.chk_state[True]:
            #     self.ch_select[index.row()] = True
            # else:
            #     self.ch_select[index.row()] = False

            self.setHeaderIcon()

        elif role == Qt.ItemDataRole.EditRole and (index.column() != self.chk_col):
            row = index.row()
            col = index.column()
            if value.isdigit():
                self._array[row, col] = value

        return True

    def flags(self, index):

        if not index.isValid():
            return None

        flag_enable = Qt.ItemFlag.ItemIsEnabled
        if index.column() == self.chk_col:
            return flag_enable | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable
        else:
            return flag_enable

    def headerData(self, index, orientation, role):

        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DecorationRole:
            if index == self.chk_col:
                return QVariant(QPixmap(self.header_icon).scaled(
                    100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if index != self.chk_col:
                return QVariant(self.c_hdr[index])

        return QVariant()

    def toggleCheckState(self, index):

        if index == self.chk_col:
            if not np.any(self.ch_select):
                self.ch_select.fill(True)

            else:
                self.ch_select.fill(False)

            top_left = self.index(0, self.chk_col)
            bottom_right = self.index(self.rowCount(), self.chk_col)
            self.dataChanged.emit(top_left, bottom_right)
            self.setHeaderIcon()

    def setHeaderIcon(self):

        if np.all(self.ch_select):
            self.header_icon = icon_path['new']
            # self.header_icon = 'checked.png'

        elif not np.any(self.ch_select):
            self.header_icon = icon_path['close']
            # self.header_icon = 'unchecked.png'

        else:
            self.header_icon = icon_path['restart']
            # self.header_icon = 'intermediate.png'

        self.headerDataChanged.emit(Qt.Orientation.Horizontal, self.chk_col, 3)


# ----------------------------------------------------------------------------------------------------------------------
# TABLE WIDGET PROPERTY CLASSES
# ----------------------------------------------------------------------------------------------------------------------


"""
    ROIViewBox: 
"""


class ROIViewBox(ViewBox):
    drawing_finished = pyqtSignal(QRectF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing = True
        self.constructionROI = None
        self.pos = None

    def mouseMoveEvent(self, evnt):
        if self.drawing:
            delta = self.mapSceneToView(self.pos) - self.mapSceneToView(evnt.pos())
            self.constructionROI.setSize([self._adjustValue(- delta.x()), self._adjustValue(- delta.y())])
            self.update()
            evnt.accept()
        else:
            super().mouseMoveEvent(evnt)

    def mouseReleaseEvent(self, evnt):
        if self.drawing:
            # deletes the ROI and runs the signal function
            self.constructionROI.deleteLater()

            pos_0 = self.mapSceneToView(self.pos)
            pos_1 = self.mapSceneToView(evnt.pos())

            d_pos = pos_0 - pos_1
            x = min([pos_0.x(), pos_1.x()])
            y = min([pos_0.y(), pos_1.y()])
            self.drawing_finished.emit(QRectF(x, y, abs(d_pos.x()), abs(d_pos.y())))

            # clears the other fields
            self.pos = None
            self.drawing = False
            self.constructionROI = None
            evnt.accept()
        else:
            super().mouseReleaseEvent(evnt)

    def mousePressEvent(self, evnt):
        if evnt.button() == Qt.MouseButton.LeftButton:
            # flag that drawing is taking place
            self.drawing = True
            self.pos = evnt.pos()

            # creates the ROI object
            self.constructionROI = RectROI(self.mapSceneToView(self.pos), (1, 1), removable=True, invertible=True)
            self.addItem(self.constructionROI)
            self.update()
            evnt.accept()
        else:
            super().mousePressEvent(evnt)

    def drawRect(self, action):
        self.drawing = True

    @staticmethod
    def _adjustValue(x):
        if -1 < x < 1:
            return -1 if x < 0 else 1
        return x


# ----------------------------------------------------------------------------------------------------------------------

"""
    CheckTableHeader: 
"""


class CheckTableHeader(QHeaderView):
    sz_chk = 5
    check_update = pyqtSignal(int, int)

    def __init__(self, parent=None, i_col=None):
        super(CheckTableHeader, self).__init__(Qt.Orientation.Horizontal, parent)

        self.i_state = []
        self.hdr_chk = []
        self.sort_index = 1
        self.is_ascend = True

        if i_col is None:
            self.i_col_chk = [0]

        else:
            self.i_col_chk = i_col

        for _ in self.i_col_chk:
            self.i_state.append(0)
            self.hdr_chk.append(QStyleOptionButton())

    def setCheckState(self, state, i_col=0):

        if i_col not in self.i_col_chk:
            return

        self.i_state[self.i_col_chk.index(i_col)] = state
        self.update()

    def paintSection(self, painter, rect, index):

        try:
            painter.save()
            QHeaderView.paintSection(self, painter, rect, index)
            painter.restore()

        except:
            return

        if index in self.i_col_chk:
            i_col = self.i_col_chk.index(index)
            left = int(rect.width() / 2 - self.sz_chk)
            top = int(rect.height() / 2 - self.sz_chk)
            self.hdr_chk[i_col].rect = QRect(rect.left() + left, top, 2 * self.sz_chk, 2 * self.sz_chk)

            match self.i_state[i_col]:
                case 0:
                    # case is the checkbox is off
                    self.hdr_chk[i_col].state = QStyle.StateFlag.State_Off

                case 1:
                    # case is the checkbox is mixed
                    self.hdr_chk[i_col].state = QStyle.StateFlag.State_NoChange

                case 2:
                    # case is the checkbox is on
                    self.hdr_chk[i_col].state = QStyle.StateFlag.State_On

            self.setSectionResizeMode(index, self.ResizeMode.ResizeToContents)
            self.style().drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorCheckBox, self.hdr_chk[i_col], painter)

        else:
            # left = rect.x() + 20 * (index > self.sort_index)
            # width = self.sectionSize(index) + 20 * (index == self.sort_index)
            # self.resizeSection(index, width)
            #
            # # rect.setX(left)
            # # rect.setWidth(width)
            QHeaderView.paintSection(self, painter, rect, index)

    def mousePressEvent(self, evnt):

        i_col = next(
            (i for i, h in enumerate(self.hdr_chk) if h.rect.contains(evnt.pos())), None)

        if i_col is not None:
            if self.i_state[i_col] in [1, 2]:
                self.i_state[i_col] = 0

            else:
                self.i_state[i_col] = 2

            self.update()
            self.check_update.emit(self.i_state[i_col], i_col)
            QHeaderView.mousePressEvent(self, evnt)

        else:
            # retrieves the column index
            index = self.logicalIndexAt(evnt.pos())

            # updates the ascend flag
            if index == self.sort_index:
                self.is_ascend ^= True
            else:
                self.sort_index = index

            # resets the sort indicator
            self.setSortIndicator(index, cf.ascend_flag[self.is_ascend])

# ----------------------------------------------------------------------------------------------------------------------

"""
    QTableWidgetItemSortable:
"""


class QTableWidgetItemSortable(QTableWidgetItem):
    def __init__(self, parent=None):
        super(QTableWidgetItemSortable, self).__init__(parent)

    def __lt__(self, other):

        return self.convert_text(self.text()) < self.convert_text(other.text())

    def __gt__(self, other):

        return self.convert_text(self.text()) > self.convert_text(other.text())

    @staticmethod
    def convert_text(t_str):

        try:
            t_value = float(t_str)
            return t_value

        except ValueError:
            return t_str


# ----------------------------------------------------------------------------------------------------------------------
# WIDGET STYLE CLASSES
# ----------------------------------------------------------------------------------------------------------------------


"""
    CheckBoxStyle: 
"""


class CheckBoxStyle(QProxyStyle):
    def subElementRect(self, element, option, widget=None):
        r = super().subElementRect(element, option, widget)
        if element == QStyle.SubElement.SE_ItemViewItemCheckIndicator.SE_ItemViewItemCheckIndicator:
            r.moveCenter(option.rect.center())
        return r


# ----------------------------------------------------------------------------------------------------------------------
# OTHER SPECIAL WIDGETS
# ----------------------------------------------------------------------------------------------------------------------

"""
    PlotCrossHair: 
"""


class PlotCrossHair(QObject):
    def __init__(self, h_plot, v_box):
        super(PlotCrossHair, self).__init__()

        # main class fields
        self.h_plot = h_plot
        self.v_box = v_box

        # creates the vertical/horizontal lines
        self.h_line = InfiniteLine(angle=0, movable=False)
        self.v_line = InfiniteLine(angle=90, movable=False)

        # adds the lines to the plot
        self.h_plot.addItem(self.v_line, ignoreBounds=True)
        self.h_plot.addItem(self.h_line, ignoreBounds=True)

        # disables the crosshair
        self.set_visible(False)

    def set_position(self, m_pos):
        self.v_line.setPos(m_pos.x())
        self.h_line.setPos(m_pos.y())

    def set_visible(self, state):
        self.h_line.setVisible(state)
        self.v_line.setVisible(state)


# ----------------------------------------------------------------------------------------------------------------------
# BASE WIDGET SETUP FUNCTIONS
# ----------------------------------------------------------------------------------------------------------------------

def create_text_label(parent, text, font=None, align='right', name=None):
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


def create_line_edit(parent, text, font=None, align='center', name=None):
    # sets the label font properties
    if font is None:
        font = create_font_obj()

    # sets the text string (if None)
    if text is None:
        text = " "

    elif isinstance(text, int) or isinstance(text, PosixPath):
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

    # sets the object name string
    if name is not None:
        h_combo.setObjectName(name)

    # returns the object
    return h_combo


def create_check_box(parent, text, state, font=None, name=None):
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


def create_radio_button(parent, text, state, font=None, name=None):
    # sets the label font properties
    if font is None:
        font = create_font_obj()

    # creates the listbox object
    h_radio = QRadioButton(parent)

    # sets the object properties
    h_radio.setText(text)
    h_radio.setFont(font)
    h_radio.setChecked(state)

    # sets the object name string
    if name is not None:
        h_radio.setObjectName(name)

    # returns the object
    return h_radio


def create_tab_group(parent, font=None, name=None):
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


def setup_colour_map(n_lvl):

    p_rgb = []
    for i_lvl in range(n_lvl):
        p_hsv = (0.5 - (i_lvl / (2 * n_lvl)), 0.5, 0.5)
        p_rgb.append([int(255 * x) for x in list(colorsys.hsv_to_rgb(*p_hsv))])

    return ColorMap(pos=np.linspace(0.0, 1.0, n_lvl), color=p_rgb)


def get_def_dir(d_type):
    # data directory retrieval
    if os.path.exists(def_file):
        # if the default file does exist, then load it
        with open(def_file, 'rb') as f:
            def_data = pickle.load(f)

        # data directory retrieval
        if d_type in def_data:
            # case is the data directory field does exist
            return def_data[d_type]

        else:
            # case is the data directory field does not exist
            return resource_dir

    else:
        # case is the default file doesn't exist
        return resource_dir

# ----------------------------------------------------------------------------------------------------------------------

# label/header font objects
font_lbl = create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold)
font_hdr = create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)
font_panel = create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)
