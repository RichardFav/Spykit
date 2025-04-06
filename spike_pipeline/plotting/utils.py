# module imports
import functools
import numpy as np

# custom module imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QLayout, QLayoutItem, QGridLayout, QVBoxLayout, QHBoxLayout,
                             QSizePolicy, QGroupBox, QFrame)
from PyQt6.QtCore import QObject, Qt, QSize, QRect, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QPixmap

# pyqtgraph module imports
import pyqtgraph as pg

# widget dimensions
x_gap = 15
info_width = 400

# parameters
dlg_width = 1650
dlg_height = 900
min_width = 800
min_height = 450

# ----------------------------------------------------------------------------------------------------------------------

"""
    PlotManager: object that controls the plot views within the central
                 main window plot widget
"""


class PlotManager(QWidget):
    # signal functions
    update_id = pyqtSignal()

    # array class fields
    prop_views = ['trace', 'trigger']

    def __init__(self, main_obj, plot_width, session_obj=None):
        super(PlotManager, self).__init__()

        # main class fields
        self.main_obj = main_obj
        self.plot_width = plot_width
        self.session_obj = session_obj

        # field initialisation
        self.n_plot = 0
        self.plots = []
        self.types = {}
        self.i_plot = None
        self.grid_id = None

        # widget setup
        sz_layout = QSize(dlg_width - (info_width + x_gap), dlg_height)
        self.main_layout = PlotLayout(self, sz_hint=sz_layout)
        self.bg_widget = QWidget()

        # initialises the class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the configuration options
        pg.setConfigOptions(antialias=True)

        # sets the main widget properties
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        self.setLayout(self.main_layout)

        # sets the widget layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.bg_widget)

        # creates the background widget
        self.bg_widget.setStyleSheet("background-color: black;")

    # ---------------------------------------------------------------------------
    # Plot View I/O Functions
    # ---------------------------------------------------------------------------

    def add_plot_view(self, p_type, expand_grid=True, show_plot=True):

        # if the plot type exists in the list, then exit
        if p_type in self.types:
            self.clear_plot_view(p_type)
            return

        # increments the plot count
        self.n_plot += 1
        if expand_grid:
            self.expand_grid_indices()

        # removes any currently highlighted plot
        self.remove_plot_highlight()

        # creates new plot type
        plot_constructor = vt.plot_types[p_type]
        plot_new = plot_constructor(self.session_obj)

        # adds the new layout and updates the grid layout
        self.main_layout.addWidget(plot_new)
        self.main_layout.updateID(self.grid_id, False)

        # stores the new plot properties
        self.types[p_type] = self.n_plot
        self.plots.append(plot_new)

        # hides the plot (if not showing)
        if not show_plot:
            plot_new.hide()

        # connects the hide button
        cb_fcn = functools.partial(self.clear_plot_view, p_type)
        plot_new.hide_plot.connect(cb_fcn)

        match p_type:
            case 'probe':
                # case is the probe view
                plot_new.probe_clicked.connect(self.clicked_probe)
                plot_new.reset_highlight.connect(self.trace_highlight)

            case 'trace':
                # case is the trace view
                plot_new.set_gen_props(self.main_obj.prop_manager.get_prop_tab('general'))
                plot_new.set_trace_props(self.main_obj.prop_manager.get_prop_tab('trace'))

            case 'trigger':
                # case is the trigger view
                plot_new.set_gen_props(self.main_obj.prop_manager.get_prop_tab('general'))
                plot_new.set_trig_props(self.main_obj.prop_manager.get_prop_tab('trigger'))

    def get_plot_view(self, p_type, is_add=True, expand_grid=True, show_plot=True):

        # determines if the plot type exists in the view list
        if p_type not in self.types:
            if is_add:
                # if missing, then add the plot type (if required)
                self.add_plot_view(p_type, expand_grid, show_plot)

            else:
                # otherwise, return a None object
                return None

        # returns the plot view
        return self.plots[self.types[p_type] - 1]

    def clear_plot_view(self, p_type):

        # retrieves the configuration tab object
        config_tab = self.main_obj.prop_manager.get_prop_tab('config')

        # removes the current plot from the configuration id array
        p_id = self.types[p_type]
        c_id = config_tab.obj_rconfig.c_id
        c_id[c_id == p_id] = 0

        # sets the region configuration
        self.plots[p_id - 1].hide()
        self.main_obj.prop_manager.set_region_config(c_id)
        self.main_obj.reset_prop_tab_visible(c_id)
        self.update_plot_config(c_id)

    def get_plot_index(self, p_type):

        return self.types[p_type]

    # ---------------------------------------------------------------------------
    # Probe-View Specific Functions
    # ---------------------------------------------------------------------------

    def clicked_probe(self, i_row):

        value = self.session_obj.channel_data.is_selected[i_row]
        self.main_obj.info_manager.update_table_value("Channel Info", i_row, value)
        self.reset_trace_views()

    def trace_highlight(self, is_on, i_contact=None):

        plt_probe = self.plots[self.types['trace'] - 1]
        plt_probe.reset_trace_highlight(is_on, i_contact)

    def reset_probe_views(self):

        plt_probe = self.plots[self.types['probe'] - 1]
        plt_probe.reset_probe_views()

    def reset_trace_views(self, reset_type=0):

        plt_trace = self.plots[self.types['trace'] - 1]

        plt_trace.t_start_ofs = plt_trace.gen_props.get('t_start')
        plt_trace.reset_gen_props()

        plt_trace.reset_trace_view(reset_type)

    def reset_trig_views(self):

        plt_trig = self.plots[self.types['trigger'] - 1]
        plt_trig.delete_all_regions()
        plt_trig.update_trigger_trace(True)

    def get_prop_views(self, c_id):

        # memory allocation
        prop_viewing = []

        # determines which property tab view is currently being viewed
        for pv in self.prop_views:
            if pv not in self.types:
                continue

            i_view = self.types[pv]
            if np.any(c_id == i_view):
                prop_viewing.append(pv)

        return prop_viewing

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def config_reset(self, obj_rcfig):

        # hides all the current plot items
        for items in self.main_layout.items[1:]:
            items.widget().hide()

        # field retrieval
        self.update_plot_config(obj_rcfig.c_id)

    def update_plot_config(self, c_id):

        self.grid_id = c_id
        self.main_layout.updateID(c_id)

    def hide_all_plots(self):

        for x in self.plots:
            x.hide()

    def reset_plot_highlight(self, plot):

        # removes any current highlight
        self.remove_plot_highlight()

        # adds the highlight for the selected plot
        self.i_plot = next(i for i in range(len(self.plots)) if (self.plots[i] == plot))
        self.plots[self.i_plot].reset_groupbox_name('selected')

    def remove_plot_highlight(self):

        if self.i_plot is not None:
            self.plots[self.i_plot].reset_groupbox_name(None)
            self.i_plot = None

    def get_selected_plot(self):

        if self.i_plot is None:
            return None

        else:
            return self.plots[self.i_plot]

    def expand_grid_indices(self):

        # expands the grid ID array to account for the new plot
        if self.grid_id is None:
            # case is the array needs to be initialised
            self.grid_id = np.ones((1, 1), dtype=int)

        elif np.any(self.grid_id == 0):
            # case is there is a free grid space
            grid_free = np.where(self.grid_id == 0)
            self.grid_id[grid_free[0][0], grid_free[0][1]] = self.n_plot

        else:
            # case is new space needs to be created
            grid_new = self.n_plot * np.zeros((self.grid_id.shape[0], 1), dtype=int)
            self.grid_id = np.hstack((self.grid_id, grid_new))
            self.grid_id[0, -1] = self.n_plot


# ----------------------------------------------------------------------------------------------------------------------

"""
    PlotWidget: 
"""


class PlotWidget(QWidget):
    # pyqtsignal functions
    hide_plot = pyqtSignal()

    # mouse event function fields
    mp_event_release = None
    mp_event_click = None

    # dimensions
    x_gap_plt = 2
    but_height_plt = 24

    # widget stylesheets
    plot_gbox_style = """
        QGroupBox {
            color: white;
            border: 2px solid white;
            border-radius: 5px;
        }
        QGroupBox::title
        {
            padding: 0px 5px;
            background-color: transparent;
        }
        QGroupBox[objectName='selected'] {
            color: white;
            border: 2px solid red;
            border-radius: 5px;
        }                                    
    """

    plot_button_style = """
        QToolTip {
            color: white;                 
        }
    """

    def __init__(self, p_type, b_icon=None, b_type=None, tt_lbl=None):
        super(PlotWidget, self).__init__()

        # main class fields
        self.p_type = p_type
        self.b_icon = b_icon
        self.b_type = b_type
        self.tt_lbl = tt_lbl
        self.p_name = vt.plot_names[p_type]

        # data class field
        self.x = None
        self.y = None
        self.x_lim = []
        self.y_lim = []
        self.n_row = 1
        self.n_col = 1

        # widget fields
        self.h_plot = []
        self.v_box = []
        self.plot_but = []
        self.plt_manager = None

        # boolean class fields
        self.is_updating = False
        self.region_clicked = False

        # class layouts
        self.main_layout = QHBoxLayout()
        self.group_layout = QVBoxLayout()
        self.plot_layout = QGridLayout()

        # class widgets
        self.plot_widget = QWidget()
        self.obj_plot_gbox = QGroupBox(self.p_name, self)

        # sets up the plot widgets
        self.setup_plot_widget()
        self.setup_plot_buttons()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_plot_buttons(self):

        # sets up the
        gb_layout = QHBoxLayout()
        gb_layout.setContentsMargins(0, 0, self.x_gap_plt, 0)

        # creates the checkbox object
        obj_grp = QWidget()
        obj_grp.setLayout(gb_layout)
        obj_grp.setStyleSheet("background-color: transparent;")

        # adds the widgets
        obj_gap = QWidget()
        gb_layout.addWidget(obj_gap)
        obj_gap.setStyleSheet("background-color: transparent;")

        # frame layout
        frm_layout = QHBoxLayout()
        frm_layout.setSpacing(self.x_gap_plt)
        frm_layout.setContentsMargins(self.x_gap_plt, self.x_gap_plt, self.x_gap_plt, self.x_gap_plt)

        # frame widget
        obj_frm = QFrame()
        obj_frm.setLayout(frm_layout)
        obj_frm.setFixedHeight(self.but_height_plt + 3 * self.x_gap_plt)
        obj_frm.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))
        obj_frm.setStyleSheet("border: 1px solid white;")

        # creates the push button objects
        for bi, bt, tt in zip(self.b_icon, self.b_type, self.tt_lbl):
            # creates the button widget
            obj_but = cw.create_push_button(None, "")
            match bt:
                case 'toggle':
                    # case is a toggle button
                    obj_but.setCheckable(True)

                    # creates the togglebar icon
                    toggle_icon = QIcon()
                    toggle_icon.addPixmap(QPixmap(cw.icon_path[bi + '_on']), QIcon.Mode.Normal, QIcon.State.On)
                    toggle_icon.addPixmap(QPixmap(cw.icon_path[bi + '_off']), QIcon.Mode.Normal, QIcon.State.Off)
                    obj_but.setIcon(toggle_icon)

                case 'button':
                    # case is a push button
                    obj_but.setIcon(QIcon(cw.icon_path[bi]))

            # sets the button properties
            obj_but.setIconSize(QSize(self.but_height_plt - 1, self.but_height_plt - 1))
            obj_but.setFixedSize(self.but_height_plt, self.but_height_plt)
            obj_but.setCursor(Qt.CursorShape.PointingHandCursor)
            obj_but.setToolTip(tt)
            obj_but.setObjectName(bi)
            obj_but.setStyleSheet(self.plot_button_style)

            # sets the callback function
            self.plot_but.append(obj_but)

            # adds the widgets
            frm_layout.addWidget(obj_but)

        # adds the plot widget
        gb_layout.addWidget(obj_frm)
        self.group_layout.addWidget(obj_grp)
        self.group_layout.addWidget(self.plot_widget)

    def setup_plot_widget(self):

        # sets the main widget properties
        self.setSizePolicy(QSizePolicy(cf.q_pref, cf.q_exp))
        self.setLayout(self.main_layout)

        # sets the main layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(cw.align_flag['top'])
        self.main_layout.addWidget(self.obj_plot_gbox)

        # sets the groupbox properties
        self.obj_plot_gbox.setObjectName(None)
        self.obj_plot_gbox.setFont(cw.font_hdr)
        self.obj_plot_gbox.setCheckable(False)
        self.obj_plot_gbox.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        self.obj_plot_gbox.setLayout(self.group_layout)
        self.obj_plot_gbox.setStyleSheet(self.plot_gbox_style)

        # sets the plot widget layout
        self.plot_layout.setSpacing(5)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_widget.setLayout(self.plot_layout)

        # sets up the
        cb_fcn = functools.partial(self.click_plot_region, self)
        self.obj_plot_gbox.mousePressEvent = cb_fcn

    def setup_plot_pen(self):

        pen_style = cf.pen_style[self.p_style]
        return pg.mkPen(color=self.p_col, width=self.p_width, style=pen_style)

    def setup_subplots(self, n_r=1, n_c=1, vb=None):

        # memory allocation
        self.n_row, self.n_col = n_r, n_c
        self.v_box = np.empty((n_r, n_c), dtype=object)
        self.h_plot = np.empty((n_r, n_c), dtype=object)

        if vb is None:
            vb = n_r * n_c * [None]

        for i in range(n_r):
            for j in range(n_c):
                # creates the plot widget
                k = i * n_c + j
                if vb[k] is None:
                    self.h_plot[i, j] = pg.PlotWidget()
                    self.v_box[i, j] = self.h_plot[i, j].getViewBox()

                else:
                    self.h_plot[i, j] = pg.PlotWidget(viewBox=vb[k])
                    self.v_box[i, j] = vb[k]

                # adds the plot widget to the layout
                self.h_plot[i, j].setContentsMargins(0, 20, 0, 0)
                self.plot_layout.addWidget(self.h_plot[i, j], i, j, 1, 1)

        if n_r * n_c == 1:
            self.v_box = self.v_box[0, 0]
            self.h_plot = self.h_plot[0, 0]

    # ---------------------------------------------------------------------------
    # Widget Event Functions
    # ---------------------------------------------------------------------------

    def click_plot_region(self, plot, *_):

        if self.region_clicked:
            self.region_clicked = False
            return

        if self.plt_manager is None:
            self.plt_manager = cf.get_parent_widget(self, PlotManager)

        # updates the selected plot to the current
        self.plt_manager.reset_plot_highlight(plot)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def reset_groupbox_name(self, name_new):

        self.obj_plot_gbox.setObjectName(name_new)
        self.obj_plot_gbox.setStyleSheet(self.obj_plot_gbox.styleSheet())


# ----------------------------------------------------------------------------------------------------------------------

"""
    PlotLayout: custom layout object for controlling the placement of 
                individual plot views within the main window plot widget
"""


class PlotLayout(QLayout):
    def __init__(self, parent=None, g_id=None, sz_hint=None):
        super(PlotLayout, self).__init__(parent)

        # field initialisation
        self.g_id = g_id
        self._items = []
        self._sz_hint = sz_hint

    def addItem(self, item: QLayoutItem):
        """Adds an item (widget) to the layout."""
        self._items.append(item)

    def count(self):
        """Returns the number of items in the layout."""
        return len(self._items)

    def sizeHint(self, *args):
        """Returns the number of items in the layout."""
        if self._sz_hint is None:
            return self.parent().size()
        else:
            return self._sz_hint

    def itemAt(self, index: int) -> QLayoutItem:
        """Returns the item at a given index."""
        if index < len(self._items):
            return self._items[index]
        return None

    def setGeometry(self, rect: QRect):
        """Arranges the widgets in a grid-like fashion."""
        d = self.spacing()
        x, y = rect.x() + d, rect.y() + d
        width, height = rect.width() - 2 * d, rect.height() - 2 * d

        # updates the background widget
        rect.adjust(d, d, -2 * d, -2 * d)
        self._items[0].setGeometry(rect)

        # row/column index retrieval
        if self.g_id is None:
            # if there is no grid ID values given, then exit
            return

        else:
            n_rows, n_cols = self.g_id.shape[0], self.g_id.shape[1]

        # Calculate the width and height for each cell in the grid
        c_wid = width // n_cols
        c_hght = height // n_rows

        for i, gid in enumerate(np.unique(self.g_id[self.g_id > 0])):
            widget = self._items[gid].widget()

            if widget:
                # calculates the row/column indices and spans
                id_plt = np.where(self.g_id == gid)
                i_row, i_col = min(id_plt[0]), min(id_plt[1])
                n_row, n_col = len(np.unique(id_plt[0])), len(np.unique(id_plt[1]))

                # Set the geometry of the widget based on the grid's row and column
                widget.show()
                widget.setGeometry(x + i_col * c_wid, y + i_row * c_hght, c_wid * n_col, c_hght * n_row)

        super().setGeometry(rect)

    def invalidate(self):
        """Invalidates the layout, forcing it to recalculate its geometry."""
        super().invalidate()

    def removeAt(self, index: int):
        """Removes an item at a given index."""
        if index < len(self._items):
            del self._items[index]

    def updateID(self, _g_id, force_update=True):
        """Updates the grid ID flags"""
        self.g_id = _g_id

        if force_update:
            self.invalidate()

    @property
    def items(self):
        return self._items


# ----------------------------------------------------------------------------------------------------------------------

"""
    PlotParaBase: 
"""


class PlotParaBase(QWidget):
    def __init__(self, tr_name):
        super(PlotParaBase, self).__init__(tr_name)

        # initialisations
        self.has_init = False

        # trace property fields
        self.name = tr_name
        self.p_width = 1
        self.p_style = 'Solid'
        self.p_col = QColor(255, 255, 255)
        self.g_style = 'Both Directions'

        # x/y-axes limit fields
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None

        # trace operation fields
        self.show_child = False
        self.show_parent = False
        self.create_trace = 0
        self.clip_trace = 0
        self.delete_trace = 0
        self.delete_children = 0

        # flag reset
        self.has_init = True


# ----------------------------------------------------------------------------------------------------------------------

"""
    PlotPara: 
"""


class PlotPara(PlotParaBase):
    # signal functions
    update_props = pyqtSignal(str)
    trace_operation = pyqtSignal(str)
    update_limits = pyqtSignal(str)

    def __init__(self, tr_name):
        super(PlotPara, self).__init__(tr_name)

    # ---------------------------------------------------------------------------
    # Parameter Update Event Functions
    # ---------------------------------------------------------------------------

    @staticmethod
    def para_change(p_str, _self):

        if _self.has_init:
            _self.update_props.emit(p_str)

    @staticmethod
    def prop_update(p_str, _self):

        if _self.has_init:
            _self.trace_operation.emit(p_str)

    @staticmethod
    def limit_change(p_str, _self):

        if _self.has_init:
            _self.update_limits.emit(p_str)

    # ---------------------------------------------------------------------------
    # Parameter Observer Properties
    # ---------------------------------------------------------------------------

    # trace property observer properties
    name = cf.ObservableProperty(functools.partial(para_change, 'name'))
    p_width = cf.ObservableProperty(functools.partial(para_change, 'p_width'))
    p_style = cf.ObservableProperty(functools.partial(para_change, 'p_style'))
    p_col = cf.ObservableProperty(functools.partial(para_change, 'p_col'))
    g_style = cf.ObservableProperty(functools.partial(para_change, 'g_style'))

    # trace property observer properties
    x_min = cf.ObservableProperty(functools.partial(limit_change, 'x_min'))
    x_max = cf.ObservableProperty(functools.partial(limit_change, 'x_max'))
    y_min = cf.ObservableProperty(functools.partial(limit_change, 'y_min'))
    y_max = cf.ObservableProperty(functools.partial(limit_change, 'y_max'))

    # trace operation observer properties
    show_child = cf.ObservableProperty(functools.partial(prop_update, 'show_child'))
    show_parent = cf.ObservableProperty(functools.partial(prop_update, 'show_parent'))
    create_trace = cf.ObservableProperty(functools.partial(prop_update, 'create_trace'))
    clip_trace = cf.ObservableProperty(functools.partial(prop_update, 'clip_trace'))
    delete_trace = cf.ObservableProperty(functools.partial(prop_update, 'delete_trace'))
    delete_children = cf.ObservableProperty(functools.partial(prop_update, 'delete_children'))


# ----------------------------------------------------------------------------------------------------------------------

# module imports (required here as will cause circular import error otherwise)
import spike_pipeline.plotting.view_type as vt
