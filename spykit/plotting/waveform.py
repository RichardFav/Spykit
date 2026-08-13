# module import
import os
import time
import math
import colorsys
import numpy as np
from copy import deepcopy
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.plotting.utils import PlotWidget, setup_default_layout

# pyqt6 module import
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPainterPath

# pyqtgraph modules
import pyqtgraph as pg
from pyqtgraph import TextItem
from pyqtgraph.Qt.QtWidgets import QGraphicsPathItem

# plot button fields
b_icon = ['save', 'close']
b_type = ['button', 'button']
tt_lbl = ['Save Figure', 'Close View']

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    WaveFormPlot:
"""


class WaveFormPlot(PlotWidget):
    # font sizes
    title_size0 = 22

    # parameters
    n_int = 10
    dy_plt_tol = 10

    def __init__(self, sp_main):

        # main class fields
        self.session_obj = sp_main.session_obj

        # creates the class object
        p_layout = setup_default_layout()
        super(WaveFormPlot, self).__init__(
            sp_main, 'waveform', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl, p_layout=p_layout)
        p_layout.setParent(self)

        # field initialisations
        self.is_updating = True
        self.i_unit = 1

        # boolean class fields
        self.has_plot = False
        self.show_grid = False
        self.lbl_showing = False
        self.use_global_lim = True

        # other class fields
        self.i_plt_min = None
        self.i_type_sel = None
        self.bg_widget = QWidget()
        self.trace_col = cf.get_colour_value('g')
        self.unit_col = cf.get_colour_value('r')

        # boolean class fields
        self.update_reqd = False

        # initialises the other class fields
        self.init_class_fields()
        self.init_plot_view()
        self.update_plot()

        # resets the initialisation flag
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # field retrieval
        self.l_size = self.plot_layout.sizeHint()
        self.title_size = '{0}pt'.format(self.title_size0)
        self.h_pen_unit = pg.mkPen(self.unit_col, width=3)

        # time vector setup
        n_pts = self.get_field('n_pts')
        self.t0 = np.array(range(n_pts))
        self.t = np.linspace(0, n_pts, self.n_int * n_pts + 1)

        # field initialisations
        self.unit_lbl = cw.get_unit_labels(self.get_field('splitGoodAndMua_NonSomatic'))

        # memory allocation
        self.n_plt = len(self.unit_lbl)
        self.h_lbl = np.empty(self.n_plt, dtype=object)
        self.y_plt = np.empty(self.n_plt, dtype=object)
        self.p_item = np.empty(self.n_plt, dtype=object)
        self.y_plt_min = np.zeros(self.n_plt, dtype=float)
        self.y_plt_max = np.zeros(self.n_plt, dtype=float)
        self.unit_type = np.ones(self.n_plt, dtype=bool)
        self.i_type_unit = np.empty(self.n_plt, dtype=object)
        self.h_pen_trace = pg.mkPen(self.trace_col, width=1)

        # waveform tab cluster unit index lineedit
        self.wv_props = self.sp_main.prop_manager.get_prop_tab('postprocess').get_tab_view('waveform')
        self.h_unit_edit = self.wv_props.findChild(cw.QLineEdit,name='i_unit')

        # background widget properties
        self.bg_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.plot_layout.addWidget(self.bg_widget)

        # creates the background widget
        self.plot_layout.setSpacing(10)
        self.plot_layout.setDimOffset(36, 1)

        # calculates the overall global limits
        y_spike = np.array(self.get_field('y_spike_unit')).flatten()
        self.y_plt_glob = [np.min(y_spike), np.max(y_spike)]

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = pfcn(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)
            pb.raise_()

    def init_plot_view(self):

        # memory allocation
        d_val = np.zeros(1)
        self.h_plot = np.empty(self.n_plt, dtype=object)
        self.h_plot_sel = np.empty(self.n_plt, dtype=object)

        # creates the waveform subplots
        for i_type in range(self.n_plt):
            # creates the waveform plot widget
            self.h_plot[i_type] = pg.PlotWidget()
            self.h_plot[i_type].hideButtons()
            self.plot_layout.addWidget(self.h_plot[i_type])

            # creates the unit waveform traces
            h_path = pg.arrayToQPath(d_val, d_val)
            h_item = QGraphicsPathItem(h_path)
            self.h_plot[i_type].addItem(h_item)

            # creates the unit selection trace
            h_path_sel = pg.arrayToQPath(d_val, d_val)
            h_item_sel = QGraphicsPathItem(h_path_sel)
            self.h_plot[i_type].addItem(h_item_sel)

            # creates the unit labels
            self.h_lbl[i_type] = TextItem(color=(0, 0, 0, 255),
                                          fill=(255, 255, 255, 255),
                                          anchor=(0,1),
                                          ensureInBounds=True)
            self.h_lbl[i_type].setVisible(False)
            self.h_plot[i_type].addItem(self.h_lbl[i_type])

            # adds the plot widget event functions
            h_plt_scene = self.h_plot[i_type].scene()
            h_plt_scene.sigMouseMoved.connect(pfcn(self.plot_moved, i_type))
            h_plt_scene.sigMouseClicked.connect(pfcn(self.plot_clicked, i_type))
            h_plt_scene.leaveEvent = pfcn(self.plot_leave, i_type)

            # sets the axes properties
            self.p_item[i_type] = self.h_plot[i_type].getPlotItem()
            self.p_item[i_type].showAxes(True, False)
            self.p_item[i_type].layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

            # sets up the viewbox properties
            self.v_box.append(self.p_item[i_type].vb)
            self.v_box[i_type].setXRange(0, self.t[-1])
            self.v_box[i_type].leaveEvent = pfcn(self.plot_leave, i_type)

            for ax_t in ['left', 'bottom', 'right', 'top']:
                # resets the axes properties
                self.h_plot[i_type].getAxis(ax_t).setStyle(tickLength=0)

                # shows the right/top axes
                if ax_t in ['right', 'top']:
                    self.p_item[i_type].showAxis(ax_t)

        # creates the unit type traces
        self.reset_unit_traces()

    def reset_unit_traces(self):

        # field retrieval
        u_type = np.array(self.get_field('unit_type'))
        y_spike = np.array(self.get_field('y_spike_unit'))

        # creates the waveform traces
        for i_type in range(self.n_plt):
            # determines if there are any units of the current type
            is_unit = u_type[:, 0] == i_type
            hp = self.p_item[i_type].items
            if np.any(is_unit):
                # if so, set up the waveform plot points
                self.i_type_unit[i_type] = np.where(is_unit)[0] + 1
                self.y_plt[i_type] = np.apply_along_axis(self.interp_1d, axis=1, arr=y_spike[is_unit, :])

                # sets up the connectivity array
                c_arr = np.ones((sum(is_unit), len(self.t)), dtype=np.ubyte)
                c_arr[:, -1] = 0

                # creates the unit waveform traces
                y_plt_flat = self.y_plt[i_type].flatten()
                hp[0].setPath(pg.arrayToQPath(np.tile(self.t, sum(is_unit)), y_plt_flat, c_arr.flatten()))

                # sets the axes properties
                self.y_plt_min[i_type] = np.min(y_plt_flat)
                self.y_plt_max[i_type] = np.max(y_plt_flat)
            else:
                # otherwise, clear the subplot
                if len(hp):
                    hp[0].setPath(QPainterPath())

        # updates the plot y-axes limits
        self.update_axes_limits()

    # ---------------------------------------------------------------------------
    # PLot View Methods
    # ---------------------------------------------------------------------------

    def update_plot(self):

        # updates the axes grids
        self.update_plot_config()
        self.update_selected_trace()
        self.update_trace_colour()
        self.update_unit_colour()
        self.update_axes_grid()

        # flag that plot update is not required
        self.update_reqd = False

    def update_selected_trace(self):

        # hides the unit (if one is already selected)
        if self.i_type_sel is not None:
            self.p_item[self.i_type_sel].items[1].hide()

        # field retrieval
        u_type = np.array(self.get_field('unit_type'))
        y_spike = np.array(self.get_field('y_spike_unit'))

        # resets the class fields
        self.i_type_sel = u_type[self.i_unit - 1][0]

        # resets the selected trace plot
        hp = self.p_item[self.i_type_sel].items[1]
        hp.setPath(pg.arrayToQPath(self.t, self.interp_1d(y_spike[self.i_unit - 1, :])))
        hp.show()

    def update_plot_config(self):

        # determines the unit configuration
        i_unit = np.where(self.unit_type)[0]
        n_row, n_col = self.get_plot_config(len(i_unit))

        # hides all plots
        for hp in self.h_plot:
            hp.hide()

        # sets/clears the subplot regions
        g_id = np.zeros((n_row, n_col), dtype=int)
        for i, id in enumerate(i_unit):
            i_row, i_col = int(i / n_col), i % n_col
            g_id[i_row, i_col] = id + 1

        # updates the plot layout
        self.plot_layout.updateID(g_id)
        self.plot_layout.activate()

    def update_trace_colour(self):

        # resets the pen colour
        self.h_pen_trace = pg.mkPen(self.trace_col, width=1)

        for pi in self.p_item:
            pi.items[0].setPen(self.h_pen_trace)

    def update_unit_colour(self):

        # resets the pen colour
        self.h_pen_unit = pg.mkPen(self.unit_col, width=3)

        for pi in self.p_item:
            pi.items[1].setPen(self.h_pen_unit)

    def update_axes_grid(self):

        # updates the grid visibility
        for pi in self.p_item:
            pi.showGrid(x=self.show_grid, y=self.show_grid)

    def update_axes_limits(self):

        for it, vb in enumerate(self.v_box):
            if self.use_global_lim:
                vb.setYRange(self.y_plt_glob[0], self.y_plt_glob[1])

            else:
                vb.setYRange(self.y_plt_min[it], self.y_plt_max[it])

    def update_plot_title(self, i_type):

        t_str = '{0} Units'.format(self.unit_lbl[i_type])
        self.h_plot[i_type].setTitle(t_str, size=self.title_size, bold=True)

    def update_plot_cursor(self, i_type, is_show):

        if is_show:
            # sets the cursor to a pointing hand
            self.h_plot[i_type].viewport().setCursor(Qt.CursorShape.PointingHandCursor)

            # shows the label (if currently hiding)
            if not self.lbl_showing:
                self.lbl_showing = True
                self.h_lbl[i_type].setVisible(True)

        else:
            # resets the cursor to an arrow
            self.h_plot[i_type].viewport().setCursor(Qt.CursorShape.ArrowCursor)

            # hides the label (if currently showing)
            if self.lbl_showing:
                self.lbl_showing = False
                self.h_lbl[i_type].setVisible(False)

    def update_unit_type(self, unit_type, i_unit):

        # resets the unit traces
        self.reset_unit_traces()

        # updates the selected trace
        self.update_selected_trace()

    # ---------------------------------------------------------------------------
    # Plot Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'save':
                # case is the figure save button

                # prompts the user for the file name
                f_path = cw.get_image_file_name(cw.get_def_dir("figure"), 'Waveforms')
                if f_path is not None:
                    # saves the image to file
                    p_map = cf.setup_subplot_image(self, self.h_plot)
                    p_map.save(f_path)

            case 'close':
                # case is the close button
                self.hide_plot.emit()

    def plot_moved(self, i_type, s_pos):

        # if there are no plot items, then exit
        if self.y_plt[i_type] is None:
            self.i_plt_min = None
            self.update_plot_cursor(i_type, False)
            return

        # calculates the plot view mouse click coordinates
        m_pos = self.v_box[i_type].mapSceneToView(s_pos)

        # determines if the mouse location is within the plot view range
        if (m_pos.x() >= self.t[0]) and (m_pos.x() <= self.t[-1]):
            # determines the closest plot line to the mouse location
            i_pos_x = int(np.round(m_pos.x() * self.n_int))
            dy_plt = np.abs(self.y_plt[i_type][:, i_pos_x] - m_pos.y())

            # determines if the closest plot line is within range
            dy_plt_min = np.min(dy_plt)
            if dy_plt_min < self.dy_plt_tol:
                # resets the plot line index
                i_plt_new = np.argmin(dy_plt)

                # resets the closest unit index (if changed)
                if self.i_plt_min != i_plt_new:
                    self.i_plt_min = i_plt_new
                    self.h_lbl[i_type].setText(self.get_label_text(i_type))

                # resets the label position and cursor properties
                self.h_lbl[i_type].setPos(m_pos)
                self.update_plot_cursor(i_type, True)

                return

        # otherwise, reset the plot line index and cursor properties
        self.i_plt_min = None
        self.update_plot_cursor(i_type, False)

    def plot_clicked(self, i_type, event):

        # resets the plot unit index (for valid index)
        if self.i_plt_min is not None:
            # retrieves the unit index
            i_unit_new = self.i_type_unit[i_type][self.i_plt_min]

            # resets the selected unit index
            self.h_unit_edit.setText(str(i_unit_new))
            self.wv_props.edit_update('i_unit')

    def plot_leave(self, i_type, event):

        self.update_plot_cursor(i_type, False)

        # self.h_plot[i_type].scene().leaveEvent(event)

    # ---------------------------------------------------------------------------
    # Other Plot View Functions
    # ---------------------------------------------------------------------------

    def clear_plot_view(self):

        pass

    def show_view(self):

        if self.update_reqd:
            self.update_plot()

    def hide_view(self):

        pass

    # ---------------------------------------------------------------------------
    # Class Getter Methods
    # ---------------------------------------------------------------------------

    def get_field(self, p_fld):

        return self.session_obj.get_mem_map_field(p_fld)

    def get_label_text(self, i_type):

        i_unit_new = self.i_type_unit[i_type][self.i_plt_min]
        return f"Unit ID#: {i_unit_new}"

    @staticmethod
    def get_plot_config(n_plt):

        match n_plt:
            case 1:
                return 1, 1
            case 2:
                return 1, 2
            case _:
                return 2, int(np.ceil(n_plt / 2))

    # ---------------------------------------------------------------------------
    # Class Setter Methods
    # ---------------------------------------------------------------------------

    def reset_unit_index(self, i_unit_new):

        # flag manual field update
        self.is_updating = True

        # updates the unit index
        self.i_unit = i_unit_new

        # resets the update flag
        self.is_updating = False

    # ---------------------------------------------------------------------------
    # Widget Event Callback Functions
    # ---------------------------------------------------------------------------

    def resizeEvent(self, event):

        # field retrieval
        new_size = event.size()

        # calculates the proportional height/width
        p_wid = new_size.width() / self.l_size.width()
        p_hght = new_size.height() / self.l_size.height()

        # resets the font object sizes
        self.scale_font_sizes(p_wid, p_hght)

        # resets the plot titles
        for i in range(self.n_plt):
            self.update_plot_title(i)

    def scale_font_sizes(self, p_wid, p_hght):

        # calculates the new scale factor
        p_scl = np.min([p_wid, p_hght])
        f_sz_title = int(np.ceil(self.title_size0 * p_scl))

        # resets the title string
        self.title_size = '{0}pt'.format(f_sz_title)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def interp_1d(self, row):

        return np.interp(self.t, self.t0, row)

    # ---------------------------------------------------------------------------
    # Parameter Field Update Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_para(p_str, _self):
        if _self.is_updating:
            return

        match p_str:
            case 'show_grid':
                _self.update_axes_grid()

            case 'use_global_lim':
                _self.update_axes_limits()

            case 'trace_col':
                _self.update_trace_colour()

            case 'unit_col':
                _self.update_unit_colour()

            case 'i_unit':
                _self.update_selected_trace()

            case _:
                _self.update_plot()

    # trace property observer properties
    i_unit = cf.ObservableProperty(pfcn(update_para, 'i_unit'))
    show_grid = cf.ObservableProperty(pfcn(update_para, 'show_grid'))
    use_global_lim = cf.ObservableProperty(pfcn(update_para, 'use_global_lim'))
    unit_type = cf.ObservableProperty(pfcn(update_para, 'unit_type'))
    trace_col = cf.ObservableProperty(pfcn(update_para, 'trace_col'))
    unit_col = cf.ObservableProperty(pfcn(update_para, 'unit_col'))
