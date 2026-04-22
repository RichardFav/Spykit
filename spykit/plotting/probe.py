# module import
import functools
import numpy as np
from functools import partial as pfcn

# pyqt6 module import
from PyQt6.QtCore import QRectF, QPointF, pyqtSignal, Qt
from PyQt6.QtGui import QPolygonF, QPicture, QPainter, QIcon, QBrush, QColor, QPen

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.plotting.utils import PlotWidget, PlotPara

# pyqtgraph modules
import pyqtgraph as pg
from pyqtgraph import PlotCurveItem, GraphicsObject, ROI, RectROI, CircleROI, TextItem, mkPen, mkBrush, exporters

# plot button fields
b_icon = ['cell', 'tick', 'star', 'toggle', 'save', 'close']
b_type = ['toggle', 'button', 'toggle', 'button', 'button', 'button']
tt_lbl = ['Show Unit Markers', 'Display Inset Traces', 'Highlight Inset Traces',
          'Toggle Selection', 'Save Figure', 'Close ProbeView']


# ----------------------------------------------------------------------------------------------------------------------

"""
    ProbePlot:
"""


class ProbePlot(PlotWidget):
    # pyqtsignal functions
    hide_plot = pyqtSignal()
    probe_roi_moved = pyqtSignal(object)
    probe_clicked = pyqtSignal(object)
    reset_highlight = pyqtSignal(bool, object)
    reset_inset_traces = pyqtSignal(object)
    create_unit_markers = pyqtSignal()

    # parameters
    pw_y = 1.05
    pw_x = 1.05
    p_zoom0 = 0.2
    y_out_dist = 20
    unit_rad = 10

    # list class fields
    add_lbl = ['remove', 'toggle', 'add']
    lbl_tt_str = {
        'cell': ['Show Unit Markers', 'Hide Unit Markers'],
        'star': ['Enable Inset Trace Highlight', 'Disable Inset Trace Highlight'],
        'toggle': ['Remove Selection', 'Toggle Selection', 'Add Selection'],
    }

    def __init__(self, session_info):
        super(ProbePlot, self).__init__('probe', b_icon=b_icon, b_type=b_type, tt_lbl=tt_lbl)

        # main class fields
        self.session_info = session_info

        # probe class fields
        self.probe = None
        self.probe_dframe = None
        self.ch_map = None

        # plotting widget class fields
        self.main_view = None
        self.sub_view = None
        self.vb_sub = None
        self.sub_xhair = None
        self.inset_id = None
        self.i_shank_pr = None
        self.n_shank = session_info.get_shank_count()

        # unit marker objects
        self.l_unit_pen = None
        self.l_unit_brush = None
        self.units = []
        self.unit_sel = None
        self.show_units = False
        self.has_units = False

        # other class fields
        self.i_status = 1
        self.show_out = False
        self.reset_inset_id = False
        self.highlight_inset = False
        self.p_zoom = [1 - self.p_zoom0, 1 + self.p_zoom0]

        # sets up the plot regions
        self.setup_subplots(n_r=2, n_c=1, vb=[None, cw.ROIViewBox()])

        # initialises the other class fields
        self.init_class_fields()

    def init_class_fields(self):

        # sets the event functions
        self.leaveEvent = self.leave_widget

        for i in range(2):
            # sets the plot item properties
            plot_item = self.h_plot[i, 0].getPlotItem()
            plot_item.setMouseEnabled(x=False, y=False)
            plot_item.hideAxis('left')
            plot_item.hideAxis('bottom')
            plot_item.setDefaultPadding(0.05)
            plot_item.hideButtons()

            # sets the view box borders
            self.v_box[i, 0].setBorder((255, 255, 255))

        # main class fields
        self.probe_rec = self.session_info.get_current_recording_probe()

        # sets the inset mouse drag properties
        self.v_box[1, 0].drawing_finished.connect(self.inset_mouse_release)

        # sets the plot button callback functions
        for pb in self.plot_but:
            cb_fcn = pfcn(self.plot_button_clicked, pb.objectName())
            pb.clicked.connect(cb_fcn)

        # disables the unit button
        self.set_button_enable('cell', False)

    def setup_probe_views(self):

        if self.main_view is None:
            # creates the main view
            self.main_view = ProbeView(self.h_plot[0, 0], self.probe, self.session_info)

            # sets the main probe view properties
            self.h_plot[0, 0].addItem(self.main_view)
            self.h_plot[0, 0].scene().sigMouseMoved.connect(pfcn(self.view_mouse_move, True))
            self.h_plot[0, 0].enterEvent = pfcn(self.enter_view, True)
            self.h_plot[0, 0].leaveEvent = pfcn(self.leave_view, True)
            self.main_view.update_roi.connect(self.main_roi_moved)

            # create the main view ROI
            self.main_view.create_inset_roi(is_full=False)
            self.get_new_inset_id()

        else:
            # resets the main probe view
            self.main_view.reset_probe_fields(self.probe)
            self.main_view.reset_inset_roi(is_full=False)

        if self.sub_view is None:
            # creates the inset view
            self.sub_view = ProbeView(self.h_plot[1, 0], self.probe, self.session_info, l_wid=2)

            # sets the inset probe view properties
            self.h_plot[1, 0].addItem(self.sub_view)
            self.h_plot[1, 0].scene().sigMouseMoved.connect(pfcn(self.view_mouse_move, False))
            self.h_plot[1, 0].enterEvent = pfcn(self.enter_view, False)
            self.h_plot[1, 0].leaveEvent = pfcn(self.leave_view, False)
            self.v_box[1, 0].wheelEvent = self.mouse_wheel_move

        else:
            # resets the probe sub-view
            self.sub_view.reset_probe_fields(self.probe)

        # sets up the channel mapping indices
        ch_map = np.empty(self.n_shank, dtype=object)
        self.probe_dframe = self.probe.to_dataframe(complete=True)
        i_sort_ch = self.session_info.channel_data.i_sort

        if self.n_shank == 1:
            # case is there is a single shank
            ch_map[0] = i_sort_ch + 1
        else:
            # case is there are multiple shanks
            for i_shank in range(self.n_shank):
                ii = self.probe_dframe['shank_ids'][i_sort_ch] == str(i_shank + 1)
                ch_map[i_shank] = i_sort_ch[ii] + 1

        # sets up the probe dataframe
        self.main_view.reset_axes_limits(False)
        self.sub_view.reset_axes_limits(False, is_init=True)
        self.sub_view.set_channel_map(ch_map)

    def setup_label_text(self, i_channel):

        probe = self.session_info.get_raw_recording_probe()
        loc_ch = self.session_info.get_channel_location(i_channel, probe)
        status_ch = self.session_info.get_channel_status(i_channel)
        shank_id = self.session_info.get_shank_id(i_channel)

        lbl_str = "Channel ID#: {0}".format(i_channel + 1)
        lbl_str += "\nDepth: {0}".format(loc_ch[1])
        lbl_str += "\nStatus: {0}".format(status_ch)
        lbl_str += "\nShank ID: {0}".format(shank_id)

        return lbl_str

    def setup_init_roi_limits(self):

        a = 1

    # ---------------------------------------------------------------------------
    # Inset View Mouse Event Functions
    # ---------------------------------------------------------------------------

    def enter_view(self, is_main, *_):

        if not is_main:
            if (self.unit_sel is not None):
                # removes any selected unit highlight
                self.unit_sel.set_unit_highlight(False)
                self.unit_sel = None

            if (self.main_view.ch_label is not None):
                # removes contact highlight from main view
                self.remove_contact_highlight(self.main_view)

        elif (self.sub_view.ch_label is not None):
            # removes contact highlight from sub view
            self.remove_contact_highlight(self.sub_view)

    def leave_view(self, is_main, *_):

        if is_main and (self.main_view.ch_label is not None):
            self.remove_contact_highlight(self.main_view)

        elif (self.sub_view.ch_label is not None):
            self.remove_contact_highlight(self.sub_view)

    def leave_widget(self, evnt):

        if self.main_view.ch_label is not None:
            self.remove_contact_highlight(self.main_view)

        elif self.sub_view.ch_label is not None:
            self.remove_contact_highlight(self.sub_view)

    def inset_mouse_release(self, rect):

        rect_p = QPolygonF(rect)
        i_sel = np.where([x.intersects(rect_p) for x in self.sub_view.c_poly])[0]

        if len(i_sel):
            # toggles the selection flag
            self.session_info.toggle_channel_flag(i_sel, self.i_status)

            # resets the probe views
            self.reset_probe_views()
            self.probe_clicked.emit(i_sel)

            if len(i_sel) == 1:
                is_sel_ch = self.session_info.channel_data.is_selected[i_sel[0]]
                self.reset_highlight.emit(bool(is_sel_ch), i_sel[0])

    # ---------------------------------------------------------------------------
    # Plot Button Event Functions
    # ---------------------------------------------------------------------------

    def plot_button_clicked(self, b_str):

        match b_str:
            case 'cell':
                # case is displaying the unit markers
                obj_but = self.findChild(cw.QPushButton, name=b_str)
                self.show_units = obj_but.isChecked()
                obj_but.setToolTip(self.lbl_tt_str[b_str][int(self.show_units)])

                # sets the unit marker visibility
                self.sub_view.set_unit_marker_visibility(self.show_units)

            case 'tick':
                # case displaying only the inset traces

                # updates the highlight toggle tooltip string
                obj_but = self.findChild(cw.QPushButton, name='star')
                obj_but.setChecked(True)
                self.plot_button_clicked('star')

                # resets the inset traces
                self.reset_inset_traces.emit(self.inset_id)

            case 'star':
                # case is the trace toggle button

                # updates the tooltip string
                obj_but = self.findChild(cw.QPushButton, name=b_str)
                self.highlight_inset = obj_but.isChecked()
                obj_but.setToolTip(self.lbl_tt_str[b_str][int(self.highlight_inset)])

                # updates the trace plot
                self.show_view() if self.highlight_inset else self.hide_view()

            case 'toggle':
                # case is the toggle button

                # updates the status flag
                self.i_status = (self.i_status + 1) % 3

                # updates the button icon (based on type)
                icon_name = self.add_lbl[self.i_status]
                obj_but = self.findChild(cw.QPushButton, name=b_str)
                obj_but.setIcon(QIcon(cw.icon_path[icon_name]))
                obj_but.setToolTip(self.lbl_tt_str[b_str][self.i_status])

            case 'save':
                # case is the save button

                # hides the interaction objects
                self.main_view.roi.setVisible(False)

                # outputs the main probe view
                f_path = cf.setup_image_file_name(cw.figure_dir, 'ProbeMainTest.png')
                exp_obj = exporters.ImageExporter(self.h_plot[0, 0].getPlotItem())
                exp_obj.export(f_path)

                # outputs the sub-image probe view
                f_path = cf.setup_image_file_name(cw.figure_dir, 'ProbeInsetTest.png')
                exp_obj = exporters.ImageExporter(self.h_plot[1, 0].getPlotItem())
                exp_obj.export(f_path)

                # hides the interaction objects
                self.main_view.roi.setVisible(True)

            case 'close':
                # case is the close button
                self.probe_roi_moved.emit(None)
                self.hide_plot.emit()

    def set_button_enable(self, b_str, state):

        obj_but = self.findChild(cw.QPushButton, name=b_str)
        obj_but.setEnabled(state)

    # ---------------------------------------------------------------------------
    # Widget Event Functions
    # ---------------------------------------------------------------------------

    def view_mouse_move(self, is_main_view, p_pos, map_coord=True):

        # view-dependent field retrieval
        vb = self.v_box[1 - int(is_main_view), 0]
        p_view = self.main_view if is_main_view else self.sub_view

        # retrieves the mapped position
        if map_coord:
            m_pos = vb.mapSceneToView(p_pos)

        else:
            m_pos = p_pos

        self.display_out_line(p_view, vb, m_pos)

        i_contact = p_view.inside_polygon_single(m_pos)
        if i_contact is not None:
            if p_view.i_sel_contact is None:
                p_view.i_sel_contact = i_contact
                p_view.create_probe_plot()

                # if the contact is selected, then reset the channel highlight
                if self.session_info.channel_data.is_selected[i_contact]:
                    self.reset_highlight.emit(True, i_contact)

                # updates the label properties
                if ((p_view.ch_label is not None) and
                        (is_main_view or (not self.show_units))):
                    p_view.ch_label.setVisible(True)
                    p_view.ch_label.setText(self.setup_label_text(i_contact))
                    p_view.ch_label.update()

            # calculates the label x/y-offsets
            ax_rng = vb.viewRange()
            dx_pos, dy_pos = self.convert_coords(is_main_view, False)
            if dx_pos is None:
                return

            # resets the y-label offset (if near the top)
            if (m_pos.y() + self.pw_y * dy_pos) > ax_rng[1][1]:
                dy_pos = 0

            # resets the x-label offset (if near the right-side)
            if (m_pos.x() + self.pw_x * dx_pos) < ax_rng[0][1]:
                dx_pos = 0

            # resets the label position
            if p_view.ch_label is not None:
                p_view.ch_label.setPos(m_pos + QPointF(-dx_pos, dy_pos))

        else:
            # otherwise, remove the contact highlight
            self.remove_contact_highlight(p_view)

    def main_roi_moved(self, p_pos):

        # updates the x-axis limits
        self.sub_view.x_lim[0] = p_pos[0]
        self.sub_view.x_lim[1] = self.sub_view.x_lim[0] + p_pos[2].x()

        # updates the y-axis limits
        self.sub_view.y_lim[0] = p_pos[1]
        self.sub_view.y_lim[1] = self.sub_view.y_lim[0] + p_pos[2].y()

        # updates the overlapping
        self.get_new_inset_id(p_pos)
        self.probe_roi_moved.emit(self.inset_id)

        # resets the axis limits
        self.sub_view.reset_axes_limits(False)

    def mouse_wheel_move(self, evnt):

        # field retrieval
        reset_xview, reset_yview = False, False
        is_zoom_out = np.sign(evnt.delta()) > 0
        s_scale = self.p_zoom[is_zoom_out] * np.array([1, 1], dtype=float)

        # resets the axis limits
        self.v_box[1, 0].scaleBy(s_scale)

        # retrieves the new viewbox range
        x_range, y_range = self.v_box[1, 0].viewRange()

        # ensures the left side is feasible
        if x_range[0] < self.main_view.x_lim[0]:
            x_range[0], reset_xview = self.main_view.x_lim[0], True

        # ensures the right side is feasible
        if x_range[1] > self.main_view.x_lim[1]:
            x_range[1], reset_xview = self.main_view.x_lim[1], True

        # resets the view x-range (if necessary)
        if reset_xview:
            self.v_box[1, 0].setXRange(x_range[0], x_range[1], padding=0)

        # ensures the bottom side is feasible
        if y_range[0] < self.main_view.y_lim[0]:
            y_range[0], reset_yview = self.main_view.y_lim[0], True

        # ensures the top side is feasible
        if y_range[1] > self.main_view.y_lim[1]:
            y_range[1], reset_yview = self.main_view.y_lim[1], True

        # resets the view y-range (if necessary)
        if reset_yview:
            self.v_box[1, 0].setYRange(y_range[0], y_range[1], padding=0)

        # resets the main view ROI position
        self.main_view.is_updating = True
        self.main_view.roi.setPos(x_range[0], y_range[0])
        self.main_view.roi.setSize([np.diff(x_range), np.diff(y_range)])
        self.main_view.is_updating = False

    # ---------------------------------------------------------------------------
    # Channel Highlight Functions
    # ---------------------------------------------------------------------------

    def show_channel_highlights(self):

        self.main_view.ch_highlight.show()
        self.sub_view.ch_highlight.show()

    def hide_channel_highlights(self):

        self.main_view.ch_highlight.hide()
        self.sub_view.ch_highlight.hide()

    def reset_channel_highlights(self, ch_id):

        bb = self.main_view.c_poly[ch_id].boundingRect()
        p_pos = [bb.x(), bb.y()]

        self.main_view.reset_highlight_pos(p_pos)
        self.sub_view.reset_highlight_pos(p_pos)

    def remove_contact_highlight(self, p_view):

        if p_view.i_sel_contact is None:
            return

        # if not hovering over an object, then disable the label
        p_view.i_sel_contact = None
        p_view.create_probe_plot()

        if p_view.ch_label is not None:
            p_view.ch_label.setVisible(False)

        # disables the trace highlight
        self.reset_highlight.emit(False, None)

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def get_new_inset_id(self, p_pos=None):

        if p_pos is None:
            h_roi = self.main_view.roi
            p_pos = [h_roi.x(), h_roi.y(), h_roi.size()]

        p_poly = self.main_view.pos_to_polygonf(p_pos)
        self.inset_id = [i for i, c in enumerate(self.main_view.c_poly) if c.intersects(p_poly)]

    def reset_probe_views(self):

        # recreates the plot view
        self.main_view.create_probe_plot()
        self.sub_view.create_probe_plot()

        if self.session_info.is_per_shank():
            # case is plotting a specifc shank
            i_shank = self.session_info.get_shank_index()
            self.main_view.reset_axes_limits(False, i_shank=i_shank)
            self.reset_shank_roi(i_shank)

            # resets the previous shank index
            self.i_shank_pr = i_shank

        else:
            # case is plotting all shanks simultaneously
            self.main_view.reset_axes_limits(False)

            # resets the previous shank index
            self.i_shank_pr = None

        self.main_view.roi.setVisible(True)

    def reset_out_line(self, ch_status):

        # determines the "out" channels
        is_out = np.array(list(ch_status.values())) == 'out'

        # calculates the out location
        if np.any(is_out):
            # retrieves the position of the out channels
            probe = self.session_info.get_raw_recording_probe()
            p_loc0 = probe.get_channel_locations()
            p_loc = p_loc0[is_out, 1]

            # determines the out location
            if np.min(p_loc0) in p_loc:
                # case is from the bottom
                y_out = np.max(p_loc)

            else:
                # case is from the top
                y_out = np.min(p_loc)

        else:
            # case is no out channels were detected
            y_out = None

        # resets the sub-view probe out line
        self.main_view.reset_out_line(y_out)
        self.sub_view.reset_out_line(y_out)

    # ---------------------------------------------------------------------------
    # Other Plot View Functions
    # ---------------------------------------------------------------------------

    def clear_plot_view(self):

        # hides the inset ROI object
        self.main_view.roi.setVisible(False)

        # clears the main/inset probe plot views
        self.main_view.clear_probe_plot()
        self.sub_view.clear_probe_plot()

    def show_view(self):

        # resets the inset id flags
        if self.highlight_inset:
            self.get_new_inset_id()
            self.probe_roi_moved.emit(self.inset_id)

        # adds in the probe locations (if calculated)
        if len(self.session_info.post_data.mmap):
            if not self.has_units:
                self.create_unit_markers.emit()

    def hide_view(self):

        # clears the inset id flags
        self.probe_roi_moved.emit(None)

    # ---------------------------------------------------------------------------
    # Unit Marker Functions
    # ---------------------------------------------------------------------------

    def clear_unit_markers(self):

        # sets up the sub-view unit markers
        self.sub_view.clear_view_unit_markers()

        # other field updates
        self.has_units = False

        # updates the highlight toggle tooltip string
        if self.show_units:
            obj_but = self.findChild(cw.QPushButton, name='cell')
            obj_but.setChecked(False)
            self.plot_button_clicked('cell')

        # disables the button
        self.set_button_enable('cell', False)

    def setup_unit_markers(self, unit_tab):

        # field retrieval
        obj_but = self.findChild(cw.QPushButton, name='cell')
        obj_but.setChecked(True)

        # sets up the sub-view unit markers
        self.sub_view.setup_view_unit_markers(unit_tab)

        # other field updates
        self.has_units = True
        self.show_units = True
        self.set_button_enable('cell', True)

    def reset_unit_markers(self):

        # clears the unit markers (if created)
        if self.has_units:
            self.clear_unit_markers()

        # recreates the unit markers
        self.create_unit_markers.emit()

    def reset_selected_unit_highlight(self, i_ch_unit, type_lbl):

        # removes any currently selected highlights
        if self.unit_sel is not None:
            self.unit_sel.set_unit_highlight(False)
            self.unit_sel = None

        # resets the unit highlight
        is_match = self.sub_view.i_ch_units == i_ch_unit
        if np.any(is_match):
            i_unit = np.where(is_match)[0][0]
            self.unit_sel = self.sub_view.units[i_unit][type_lbl]
            self.unit_sel.set_unit_highlight(True)
        else:
            self.unit_sel = None

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def convert_coords(self, is_main, is_out=False):

        # initialisations
        vb = self.v_box[1 - int(is_main), 0]

        # label bounding box retrieval
        try:
            if is_main:
                # case is the main view outside label
                if is_out:
                    lbl_bb = self.main_view.out_label.boundingRect()
                else:
                    lbl_bb = self.main_view.ch_label.boundingRect()

            else:
                if is_out:
                    # case is the sub view outside label
                    lbl_bb = self.sub_view.out_label.boundingRect()
                else:
                    # case is the sub view outside label
                    lbl_bb = self.sub_view.ch_label.boundingRect()

        except AttributeError:
            return None, None

        # retrieves the converted coordinates
        bb_rect = vb.mapSceneToView(lbl_bb).boundingRect()
        return bb_rect.width(), bb_rect.height()

    def display_out_line(self, p_view, vb, m_pos):

        if (p_view.y_out is not None) and self.show_out:
            dy_out = np.abs(m_pos.y() - p_view.y_out)
            if dy_out < self.y_out_dist:
                # calculates the label x/y-offsets
                ax_rng = vb.viewRange()
                dx_pos, dy_pos = self.convert_coords(is_main_view, True)

                # resets the y-label offset (if near the top)
                if (m_pos.y() + self.pw_y * dy_pos) > ax_rng[1][1]:
                    dy_pos = 0

                # resets the x-label offset (if near the right-side)
                if (m_pos.x() + self.pw_x * dx_pos) < ax_rng[0][1]:
                    dx_pos = 0

                # resets the label visibility/position
                p_view.out_label.setVisible(True)
                p_view.out_label.setPos(m_pos + QPointF(-dx_pos, dy_pos))
                return

            else:
                # resets the label visibility
                p_view.out_label.setVisible(False)

    def reset_shank_roi(self, i_shank):

        # retrieves the roi position
        w, h = self.main_view.roi.size()
        x, y = self.main_view.roi.x(), self.main_view.roi.y()

        # retrieves the main viewbox
        x_lim_vb, y_lim_vb = self.main_view.getViewBox().viewRange()

        # determines if the current roi position is within the axis range
        dx_lim = np.array((x + np.array([0, w]) - np.array(x_lim_vb)))
        dy_lim = np.array((y + np.array([0, h]) - np.array(y_lim_vb)))
        if (int(np.prod(np.sign(dx_lim))) != -1) or (int(np.prod(np.sign(dy_lim))) != -1):
            if self.i_shank_pr is None:
                # case is the previous view was full screen
                x_lim_new, y_lim_new = self.main_view.get_init_roi_limits(i_shank)

                # sets the roi coordinates/dimensions
                p_new = [x_lim_new[0], y_lim_new[0]]
                sz_new = [np.diff(x_lim_new), np.diff(y_lim_new)]

            else:
                # case is the preview view was from another shank
                x_lim_pr, y_lim_pr = self.main_view.get_expanded_shank_limits(self.i_shank_pr)

                # sets the roi coordinates/dimensions
                sz_new = [w, h]
                p_new = [x_lim_vb[0] + (x - x_lim_pr[0]), y_lim_vb[0] + (y - y_lim_pr[0])]

            # updates the roi positions
            self.main_view.reset_inset_roi(p_0=p_new, p_sz=sz_new)

    def reset_unit_roi_position(self, i_ch_unit, ch_pos, type_lbl):

        # field retrieval
        r_pos = self.main_view.roi.pos()
        r_sz = self.main_view.roi.size()
        ax_rng = self.h_plot[0, 0].getViewBox().viewRange()

        # calculates the x-location of the probeview ROI
        i_shank = self.session_info.get_shank_index()
        x_lim_new, _ = self.main_view.get_init_roi_limits(i_shank)
        x_roi = np.mean(x_lim_new)

        # resets the ROI position
        r_pos.setX(self.reset_roi_coord(x_roi, r_sz[0], ax_rng[0]))
        r_pos.setY(self.reset_roi_coord(ch_pos[1], r_sz[1], ax_rng[1]))
        self.main_view.roi.setPos(r_pos)

        # removes any currently selected highlights
        i_ch_map = self.sub_view.ch_map[i_shank][i_ch_unit - 1]
        self.reset_selected_unit_highlight(i_ch_map, type_lbl)

    @staticmethod
    def reset_roi_coord(p, r_dim, ax_lim):

        if (p - r_dim / 2) < ax_lim[0]:
            return ax_lim[0]
        elif (p + r_dim / 2) > ax_lim[1]:
            return ax_lim[1] - r_dim
        else:
            return p - r_dim / 2

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_probe(_self):
        _self.probe = _self.probe_rec.get_probe()
        _self.setup_probe_views()

    # trace property observer properties
    probe_rec = cf.ObservableProperty(update_probe)


# ----------------------------------------------------------------------------------------------------------------------

"""
    ProbeView:
"""


class ProbeView(GraphicsObject):
    # parameters
    dp = 0.1
    pw = 0.05
    n_ar = 3
    p_gap = 0.05
    p_exp_shank = 0.2

    # plot pen widgets
    pen = mkPen(width=2, color='b')
    pen_h = mkPen(width=2, color='g')

    # probe polygon colours
    p_col_probe = cf.get_colour_value('r', 100)
    c_col_probe = cf.get_colour_value('w', 128)
    c_col_hover = cf.get_colour_value('c', 220)
    c_col_selected = cf.get_colour_value('g', 128)

    # pyqtsignal functions
    update_roi = pyqtSignal(object)

    def __init__(self, main_obj, probe, session_info, l_wid=1):
        super(ProbeView, self).__init__()

        # sets the parent object
        self.main_obj = main_obj
        self.setParent(main_obj)

        # other main class fields
        self.ch_map = None
        self.probe = probe
        self.session_info = session_info

        # line pen widgets
        self.pen_sel = mkPen(color='k', width=l_wid)
        self.l_pen_out = mkPen(color=cf.get_colour_value('k'), width=l_wid)
        self.l_pen_highlight = mkPen(color=cf.get_colour_value('y'), width=2 * l_wid)

        # field initialisation
        self.p = None
        self.p_unit = None
        self.roi = None
        self.width = None
        self.height = None
        self.unit_rad = None
        self.x_lim = None
        self.y_lim = None
        self.y_lim_full = None
        self.x_lim_full = None
        self.i_sel_contact = None
        self.i_sel_trace = None
        self.x_lim_shank = None
        self.y_lim_shank = None

        # unit class fields
        self.units = None
        self.unit_tab = None

        # plot widgets
        self.picture = QPicture()

        # out location class widgets
        self.y_out = None
        self.out_line = None
        self.out_label = None
        self.ch_label = None
        self.ch_highlight = None
        self.unit_label = None
        self.unit_highlight = None
        self.show_out = False
        self.is_updating = False

        # sets the probe field
        self.reset_probe_fields(probe)

    def reset_probe_fields(self, probe):

        # field retrieval
        self.n_dim = probe.ndim
        self.n_contact = probe.get_contact_count()
        self.n_shank = probe.get_shank_count()
        self.si_units = probe.si_units

        # contact property fields
        self.c_id = probe.contact_ids
        self.c_index = probe.device_channel_indices
        self.c_pos = probe.contact_positions
        self.c_vert = self.setup_contact_coords(probe.get_contact_vertices())
        self.c_poly = [QPolygonF(x) for x in self.c_vert]

        # separates the shank-contact ID mapping array
        s_id0, idx = np.unique(probe._shank_ids, return_inverse=True)
        self.s_id = [np.where(idx == i)[0] for i in range(len(s_id0))]

        # probe properties
        self.p_title = probe.get_title()
        self.p_vert = self.vert_to_pointf(probe.probe_planar_contour)
        self.p_ax = probe.contact_plane_axes

        # sets up the axes limits
        self.get_axes_limits(probe)

        # creates the probe plot
        self.create_channel_highlight()
        self.create_probe_plot()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_contact_coords(self, vert0):

        # sets up the contact polygon objects
        return [self.vert_to_pointf(v) for v in vert0]

    def create_channel_highlight(self):

        # exit if the label is already initialised
        if self.ch_highlight is not None:
            return

        # pre-calculations\
        bb_rect = self.c_poly[0].boundingRect()
        sz_rect = QPointF(bb_rect.width(), bb_rect.height())

        # creates the channel highlight
        self.ch_highlight = RectROI(
            [0, 0],
            sz_rect,
            movable=False,
            resizable=False,
            rotatable=False,
            removable=False,
        )

        # sets the highlight properties
        self.ch_highlight.setPen(self.l_pen_highlight)
        self.ch_highlight.setZValue(10)
        self.ch_highlight.hide()

        # removes the handles
        for h in self.ch_highlight.getHandles():
            h.hide()

        # ads the ROI to the
        self.main_obj.addItem(self.ch_highlight)

    def create_probe_plot(self):

        if self.p is not None:
            self.clear_probe_plot()

        # polygon setup
        p_poly = QPolygonF(self.p_vert)
        if self.session_info is None:
            is_show = np.zeros(len(self.c_poly), dtype=bool)

        else:
            is_show = np.logical_and(self.session_info.channel_data.is_selected,
                                     self.session_info.channel_data.is_filt)

        # painter object setup
        self.p = QPainter(self.picture)
        pen_p = mkPen(self.c_col_probe)

        # probe shape plot
        self.p.setPen(mkPen(self.p_col_probe))
        self.p.setBrush(mkBrush(self.p_col_probe))
        self.p.drawPolygon(p_poly)

        # probe contact plots
        self.p.setPen(pen_p)
        for i_p, c_p in enumerate(self.c_poly):
            self.p.setPen(pen_p)
            if i_p == self.i_sel_contact:
                # case is the contact is being hovered over
                self.p.setBrush(mkBrush(self.c_col_hover))
                self.p.drawPolygon(c_p)

            if self.session_info is not None:
                # retrieves the channel fill colour
                if is_show[i_p]:
                    # case is the contact is selected
                    self.p.setPen(self.pen_sel)

                ch_status = self.session_info.get_channel_status(i_p)
                self.p.setBrush(mkBrush(cw.p_col_status[ch_status]))

            # case is a normal polygon
            self.p.drawPolygon(c_p)

        # # sets up the unit-markers
        # self.setup_unit_markers()

        # ends the drawing
        self.p.end()
        self.update()

    def clear_probe_plot(self):

        self.p.begin(self.picture)
        self.p.eraseRect(self.boundingRect())
        self.p.end()
        self.update()

    # ---------------------------------------------------------------------------
    # Unit Marker Functions
    # ---------------------------------------------------------------------------

    def clear_view_unit_markers(self):

        if self.units is None:
            return

        for un in self.units:
            for un_g in un.values():
                self.main_obj.removeItem(un_g)

        self.units = None

    def setup_view_unit_markers(self, unit_tab):

        if self.units is not None:
            self.clear_view_unit_markers()

        # field retrieval
        i_shank = self.session_info.get_shank_index()
        unit_types = unit_tab.get_unit_type_labels()
        c_id = np.array(unit_tab.df_unit['Cluster ID#'])

        # sets the channel indices of the peak channels
        pk_ch, ch_pos = unit_tab.i_pk_ch, unit_tab.ch_pos

        # removes any filtered items
        if unit_tab.is_filt is not None:
            is_filt = unit_tab.is_filt[:unit_tab.df_unit.shape[0]]
            c_id = c_id[is_filt]
            pk_ch = pk_ch[is_filt]
            unit_types = unit_types[is_filt]

        # retrieves the unique peak channel counts
        i_pk_ch, i_pk_grp, n_pk_grp = (
            np.unique(pk_ch, return_counts=True, return_inverse=True))
        i_pk_grp = i_pk_grp.flatten()

        # other initialisations
        unit_col = {}
        self.calc_unit_radius()
        self.units = np.empty(len(i_pk_ch), dtype=object)
        self.i_ch_units = np.zeros(len(i_pk_ch), dtype=int)

        for i, i_pk in enumerate(i_pk_ch):
            # determines the types of units common to the current channel
            ind_pk = np.where(i_pk_grp == i)[0]
            ch_unit = ch_pos[int(i_pk - 1), :] - self.unit_rad / 2
            self.i_ch_units[i] = self.ch_map[i_shank][i_pk - 1]

            # determines the unique unit types
            self.units[i] = {}
            unit_types_pk = unit_types[ind_pk]
            unit_types_uniq = np.unique(unit_types_pk)
            n_unit_types = len(unit_types_uniq)

            for i_ut, ut in enumerate(unit_types_uniq):
                # memory allocation
                ut_new = ut.lower()
                if ut_new not in unit_col:
                    unit_col[ut_new] = cw.get_unit_col(ut_new)
                    unit_col[ut_new].setAlpha(255)

                # sets the offset coordinates
                ind_new = c_id[np.array(ind_pk[unit_types_pk == ut])]
                ch_new = ch_unit + self.calc_unit_offset(i_ut, n_unit_types)
                ch_id = self.ch_map[i_shank][i_pk - 1]

                # sets the unit indices
                self.units[i][ut_new] = UnitMarker(
                    self, ch_new, self.unit_rad, ch_id, ut, ind_new, unit_col[ut_new])
                self.main_obj.addItem(self.units[i][ut_new])

    def set_unit_marker_visibility(self, state):

        if self.units is not None:
            for unit in self.units:
                for u_t in unit.values():
                    u_t.setVisible(state)

    # ---------------------------------------------------------------------------
    # Channel Highlight Functions
    # ---------------------------------------------------------------------------

    def reset_highlight_pos(self, p_pos, h_type='channel'):

        if h_type == 'channel':
            self.ch_highlight.setPos(p_pos)
        else:
            self.unit_highlight.setPos(p_pos)

    # ---------------------------------------------------------------------------
    # ROI Functions
    # ---------------------------------------------------------------------------

    def roi_moved(self, h_roi):

        if self.is_updating:
            return

        x0, y0, p_sz = h_roi.x(), h_roi.y(), h_roi.size()
        self.update_roi.emit([x0, y0, p_sz])

    def get_inset_roi_prop(self, is_full, x_lim_s=None, y_lim_s=None):

        if x_lim_s is None:
            x_lim_s, y_lim_s = self.get_init_roi_limits()

        # pre-calculations
        p_0 = [x_lim_s[0], y_lim_s[0]]
        p_sz = [np.diff(x_lim_s)[0], np.diff(y_lim_s)[0]]

        if is_full:
            p_lim = QRectF(self.x_lim_full[0], self.y_lim_full[0], self.width, self.height)

        else:
            p_lim = QRectF(self.x_lim[0], self.y_lim[0], np.diff(self.x_lim)[0], np.diff(self.y_lim)[0])

        return p_0, p_sz, p_lim

    def reset_inset_roi(self, p_0=None, p_sz=None, is_full=True):

        if p_0 is None:
            p_0, p_sz, self.roi.maxBounds = self.get_inset_roi_prop(is_full)

        self.roi.setPos(p_0)
        self.roi.setSize(p_sz)

    def create_inset_roi(self, x_lim_s=None, y_lim_s=None, is_full=True):

        p_0, p_sz, p_lim = self.get_inset_roi_prop(is_full, x_lim_s, y_lim_s)

        # creates the roi object
        self.roi = ROI(p_0, p_sz, pen=self.pen, hoverPen=self.pen_h,
                       handlePen=self.pen, handleHoverPen=self.pen_h, maxBounds=p_lim)
        self.roi.addScaleHandle([0, 0], [0, 0])
        self.roi.addScaleHandle([1, 1], [0, 0])
        self.roi.addScaleHandle([0, 1], [1, 0])
        self.roi.addScaleHandle([1, 0], [0, 1])
        self.roi.sigRegionChanged.connect(self.roi_moved)

        # adds the roi to the parent plot widget
        self.parent().addItem(self.roi)

    # ---------------------------------------------------------------------------
    # Axes Limit Functions
    # ---------------------------------------------------------------------------

    def reset_axes_limits(self, is_full=True, i_shank=None, is_init=False):

        if is_init:
            # case is using domain reduced to a single shank
            _x_lim, _y_lim = self.get_init_roi_limits()

        elif is_full:
            # case is using the full probe domain
            _x_lim, _y_lim = self.x_lim_full, self.y_lim_full

        elif i_shank is not None:
            # case is using the shank domain
            _x_lim, _y_lim = self.get_expanded_shank_limits(i_shank)

        else:
            # case is using domain reduced to a all shanks
            _x_lim, _y_lim = self.x_lim, self.y_lim

        # updates the figure limits
        vb = self.getViewBox()
        vb.setXRange(_x_lim[0], _x_lim[1], padding=0)
        vb.setYRange(_y_lim[0], _y_lim[1], padding=0)

        if is_full:
            vb.setLimits(xMin=_x_lim[0], xMax=_x_lim[1], yMin=_y_lim[0], yMax=_y_lim[1])

        elif self.roi is not None:
            mx_bnds = QRectF(_x_lim[0], _y_lim[0], np.diff(_x_lim)[0], np.diff(_y_lim)[0])
            self.roi.maxBounds = mx_bnds

    def get_axes_limits(self, probe):

        # field retrieval
        c_vert = np.array(probe.get_contact_vertices())

        # calculates the total contact vertex range
        c_vert_tot = np.vstack(c_vert)
        c_min_ex, c_max_ex = self.calc_expanded_limits(c_vert_tot, np.array([0.1, 0.1]))

        # calculates the probe shape vertex range
        p_pos = probe.probe_planar_contour
        p_min_ex, p_max_ex = self.calc_reduced_limits(p_pos, c_min_ex, c_max_ex)

        # sets the contact x/y axes limits
        self.x_lim = cf.resize_limits([c_min_ex[0], c_max_ex[0]], self.p_gap)
        self.y_lim = cf.resize_limits([c_min_ex[1], c_max_ex[1]], self.p_gap)
        self.x_lim_full = [p_min_ex[0], p_max_ex[0]]
        self.y_lim_full = [p_min_ex[1], p_max_ex[1]]

        # sets the shank coordinate limits
        self.x_lim_shank = []
        self.y_lim_shank = []
        for sh in probe.get_shanks():
            c_vert_sh = np.vstack(c_vert[sh.device_channel_indices])
            sh_min_ex, sh_max_ex = self.calc_reduced_limits(c_vert_sh, p_exp=[0.0, 0.0])
            self.x_lim_shank.append([sh_min_ex[0], sh_max_ex[0]])
            self.y_lim_shank.append([sh_min_ex[1], sh_max_ex[1]])

        # calculates the full width/height dimensions
        self.width = self.x_lim_full[1] - self.x_lim_full[0]
        self.height = self.y_lim_full[1] - self.y_lim_full[0]

    def get_shank_axes_limits(self, i_shank):

        x_lim0 = self.x_lim_shank[i_shank]
        y_lim0 = self.y_lim_shank[i_shank]

        dx_lim, dy_lim = np.diff(x_lim0)[0], np.diff(y_lim0)[0]
        if dx_lim < dy_lim:
            dy_lim = np.min([dy_lim, self.n_ar * dx_lim])
            _x_lim, _y_lim = x_lim0, cf.list_add([-dy_lim, 0], y_lim0[1])

        else:
            dx_lim = np.min([dx_lim, self.n_ar * dy_lim])
            _x_lim, _y_lim = cf.list_add([0, dx_lim], x_lim0[0]), y_lim0

        return _x_lim, _y_lim

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_channel_map(self, ch_map_new):

        self.ch_map = ch_map_new

    def get_field(self, p_fld):

        return self.session_info.get_mem_map_field(p_fld)

    def set_out_line_visible(self, is_show):

        self.show_out = is_show
        self.out_line.setVisible(self.show_out)

    def reset_out_line(self, y_out_new):

        # updates the out location
        self.y_out = y_out_new

        # creates the outside line (if not created)
        if self.out_line is None:
            # creates the outside line object
            self.out_line = PlotCurveItem(pen=self.l_pen_out)
            self.main_obj.addItem(self.out_line)

            # sets the outline label properties
            self.out_label = TextItem(color=(0, 0, 0, 255), fill=(255, 255, 255, 255), ensureInBounds=True)
            self.out_label.setVisible(False)
            self.main_obj.addItem(self.out_label)

            # sets the channel label properties
            self.ch_label = TextItem(color=(0, 0, 0, 255), fill=(255, 255, 255, 255), ensureInBounds=True)
            self.ch_label.setVisible(False)
            self.main_obj.addItem(self.ch_label)

            # sets the channel label properties
            self.unit_label = TextItem(color=(0, 0, 0, 255), fill=(255, 255, 255, 255), ensureInBounds=True)
            self.unit_label.setVisible(False)
            self.unit_label.setZValue(30)
            self.main_obj.addItem(self.unit_label)

        # updates the line location
        self.out_line.clear()
        if self.y_out is not None:
            # updates the output label text
            self.out_label.setText('Out Location = {0}'.format(self.y_out))
            self.out_line.setVisible(self.show_out)
            self.out_label.update()

            # updates the line data
            self.out_line.setData(self.x_lim_full, [self.y_out, self.y_out])

    def get_init_roi_limits(self, i_shank=0):

        x_lim0, y_lim0 = self.get_shank_axes_limits(i_shank)
        dx_lim0, dy_lim0 = np.diff(x_lim0)[0], np.diff(y_lim0)[0]

        x_lim = cf.list_add([0, (1 + 2 * self.pw) * dx_lim0], x_lim0[0] - self.pw * dx_lim0)
        y_lim = cf.list_add([0, (1 + 2 * self.pw) * dy_lim0], y_lim0[0] - self.pw * dy_lim0)

        return x_lim, y_lim

    def get_expanded_shank_limits(self, i_shank):

        _x_lim = list(self.calc_expanded_limits(self.x_lim_shank[i_shank], self.p_exp_shank))
        _y_lim = list(self.calc_expanded_limits(self.y_lim_shank[i_shank], self.p_exp_shank))

        return _x_lim, _y_lim

    def calc_reduced_limits(self, p, c_min=None, c_max=None, p_exp=None):

        if p_exp is None:
            p_exp = [0.05, 0.05]

        if c_min is None:
            p_min0 = np.min(p, axis=0)
            p_max0 = np.max(p, axis=0)

        else:
            p_min0 = np.vstack((np.min(p, axis=0), c_min))
            p_max0 = np.vstack((np.max(p, axis=0), c_max))

        p_lim_tot = np.vstack((p_min0, p_max0))
        return self.calc_expanded_limits(p_lim_tot, np.array(p_exp))

    def inside_polygon_single(self, m_pos):

        return next((i for i, cp in enumerate(self.c_poly) if self.has_point(cp, m_pos)), None)

    def calc_unit_radius(self):

        if self.c_poly is not None:
            bb_rect = self.c_poly[0].boundingRect()
            bb_wid, bb_hght = bb_rect.width(), bb_rect.height()
            self.unit_rad = np.min([bb_wid, bb_hght])

    def calc_unit_offset(self, i_unit, n_unit):

        if n_unit == 1:
            return np.zeros(2, dtype=float)

        elif n_unit == 2:
            phi_unit = i_unit * np.pi
            return (self.unit_rad / 2) * np.array([np.cos(phi_unit), np.sin(phi_unit)])

        else:
            phi_unit = np.pi * (1 / 2 + i_unit * 2 / n_unit)
            return (self.unit_rad / 2) * np.array([np.cos(phi_unit), np.sin(phi_unit)])

    # ---------------------------------------------------------------------------
    # Function Overrides
    # ---------------------------------------------------------------------------

    def paint(self, p, *args):

        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):

        return QRectF(self.picture.boundingRect())

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def calc_expanded_limits(y, dy):

        y_min = np.min(y, axis=0)
        y_rng = np.max(y, axis=0) - y_min

        return y_min - np.multiply(dy, y_rng), y_min + np.multiply(1 + dy, y_rng)

    @staticmethod
    def vert_to_pointf(v):

        return [QPointF(x[0], x[1]) for x in v]

    @staticmethod
    def pos_to_polygonf(p):

        x_lim, y_lim = np.array([0, p[2][0]]), np.array([0, p[2][1]])
        x = x_lim[np.array([0, 0, 1, 1])] + p[0]
        y = y_lim[np.array([0, 1, 1, 0])] + p[1]

        return QPolygonF([QPointF(X, Y) for X, Y in zip(x, y)])

    @staticmethod
    def has_point(cp, m_pos):

        return cp.containsPoint(m_pos, Qt.FillRule.OddEvenFill)

# ----------------------------------------------------------------------------------------------------------------------

"""
    UnitMarker:
"""

class UnitMarker(pg.QtWidgets.QGraphicsEllipseItem):
    # marker dimensions
    p_wid = 1
    pw_y = 1.05
    pw_x = 1.05

    def __init__(self, view_obj, p, r, i_ch, u_type, i_unit, u_col):
        super().__init__(p[0] + self.p_wid / 2, p[1] + self.p_wid / 2, r - self.p_wid, r - self.p_wid)

        # field initialisations
        self.p0 = QPointF(p[0] + r / 2, p[1] + r / 2)
        self.i_ch = i_ch
        self.i_unit = i_unit
        self.u_type = u_type

        self.view_obj = view_obj
        self.h_lbl = view_obj.unit_label
        self.v_box = view_obj.main_obj.getViewBox()
        self.u_pen = QPen(u_col, self.p_wid)
        self.u_pen_sel = QPen(cf.get_colour_value('k'), self.p_wid)

        # sets widget property fields
        self.setAcceptHoverEvents(True)
        self.setBrush(QBrush(u_col))
        self.setPen(QPen(self.u_pen))

        # other widget properties
        self.setup_label_text()

    def setup_label_text(self):

        # pre-calculations
        unit_str = ", ".join([str(x) for x in self.i_unit])

        # sets the label string
        self.lbl_txt = '\n'.join([
            f'Channel ID: {int(self.i_ch)}',
            f'Unit Type: {self.u_type}',
            f'Unit Count: {len(self.i_unit)}',
            f'Cluster IDs: {unit_str}',
        ])

    def set_unit_highlight(self, is_show):

        self.setPen(self.u_pen_sel if is_show else self.u_pen)

    def hoverEnterEvent(self, event):
        # updates the pen properties
        self.set_unit_highlight(True)

        # object dimensions
        dx_pos, dy_pos = self.convert_coords(event.pos())

        # updates the unit label
        self.h_lbl.setText(self.lbl_txt)
        self.h_lbl.setPos(self.p0 + QPointF(-dx_pos, dy_pos))
        self.h_lbl.setVisible(True)
        self.h_lbl.update()

        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # updates the pen properties
        self.set_unit_highlight(False)

        # updates the unit label
        self.h_lbl.setVisible(False)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def convert_coords(self, m_pos):

        # initialisations
        lbl_bb = self.h_lbl.boundingRect()

        # retrieves the converted coordinates
        bb_rect = self.v_box.mapSceneToView(lbl_bb).boundingRect()
        dx_pos, dy_pos = bb_rect.width(), bb_rect.height()

        # resets the y-label offset (if near the top)
        ax_rng = self.v_box.viewRange()
        if (m_pos.y() - (self.pw_y * dy_pos)) > ax_rng[1][0]:
            dy_pos = 0

        # resets the x-label offset (if near the left-side)
        if (m_pos.x() + (self.pw_x * dx_pos)) < ax_rng[0][1]:
            dx_pos = 0

        return dx_pos, dy_pos

