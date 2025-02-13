# module import
import os
import functools
import numpy as np
from copy import deepcopy
from pathlib import Path
from bigtree import dataframe_to_tree, tree_to_dict

# spikewrap modules
import spikewrap as sw

# custom module import
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.spikeinterface_func as sf
from spike_pipeline.common.common_widget import (QLabelEdit, QFileSpec, QLabelCombo, QFolderTree, QLabelCheckCombo)

from spike_pipeline.plotting.probe import ProbePlot

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QWidget, QFormLayout, QSizePolicy, QGridLayout,
                             QGroupBox, QComboBox, QCheckBox, QLineEdit, QTableWidget, QTableWidgetItem, QFrame,
                             QSpacerItem, QTableView, QMainWindow, QHeaderView)
from PyQt6.QtGui import QFont, QIcon, QStandardItem, QKeySequence
from PyQt6.QtCore import Qt, QSize, QSizeF, pyqtSignal

# testing modules
import pyqtgraph as pg

# ----------------------------------------------------------------------------------------------------------------------

# object dimensions
x_gap = 5
x_gap_h = 2
sz_but = 25
dlg_height = 580
dlg_width = 1200
file_width = 480

# dlg_height = 500

# font objects
font_lbl = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold)
font_hdr = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)
font_panel = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

# file path/filter modes
f_mode_ssf = "Spike Pipeline Session File (*.ssf)"

# parameter/resource folder paths
data_dir = "C:\\Work\\Other Projects\\EPhys Project\\Data"
icon_dir = os.path.join(os.getcwd(), 'resources', 'icons')
para_dir = os.path.join(os.getcwd(), 'resources', 'parameters').replace('\\', '/')

# icon paths
icon_path = {
    'open': os.path.join(icon_dir, 'open_icon.png'),
    'restart': os.path.join(icon_dir, 'restart_icon.png'),
    'close': os.path.join(icon_dir, 'close_icon.png'),
}


# OPEN SESSION WIDGET --------------------------------------------------------------------------------------------------


class OpenSession(QMainWindow):
    def __init__(self, parent=None):
        super(OpenSession, self).__init__(parent)

        # class widget setup
        self.main_layout = QGridLayout()
        self.main_widget = QWidget(self)
        self.frame_layout = QGridLayout()
        self.file = SessionFile(self)
        self.probe = SessionProbe(self)

        # other class fields
        self.session = None
        self.probe_width = dlg_width - (file_width + 2 * x_gap)

        # field initialisation
        self.setup_dialog()
        self.init_class_fields()

        # sets the central widget
        self.setCentralWidget(self.main_widget)

        # opens the dialog
        self.show()

    # CLASS INITIALISATION FUNCTIONS -----------------------------------

    def setup_dialog(self):

        # creates the dialog window
        self.setWindowTitle("Session Information")
        self.setFixedHeight(dlg_height)

    def init_class_fields(self):

        # sets up the main layout
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # sets the main widget layout
        self.main_widget.setLayout(self.frame_layout)

        # adds the session information widgets
        self.frame_layout.setSpacing(0)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_layout.addWidget(self.file, 0, 0, 1, 1)
        self.frame_layout.addWidget(self.probe, 0, 1, 1, 1)
        self.frame_layout.setColumnStretch(0, file_width)
        self.frame_layout.setColumnStretch(1, 0)

        # sets the info tab width
        self.file.setFixedWidth(file_width)
        self.file.session_loaded.connect(self.session_load)
        self.file.session_reset.connect(self.session_reset)

        # disables the probe info panel
        self.probe.setVisible(False)
        self.probe.setEnabled(False)

        # reset the dialog width
        self.reset_dialog_width(False)

    def session_load(self):

        # updates the probe properties
        self.probe.update_probe_info()
        self.probe.setEnabled(True)
        self.probe.setVisible(True)

        # resets the dialog width
        self.reset_dialog_width(True)

    def session_reset(self):

        if self.probe.has_probe:
            self.probe.clear_probe_frame()
            self.reset_dialog_width(False)

    def reset_dialog_width(self, is_open):

        p_width = self.probe_width if is_open else 0

        self.setFixedWidth(p_width + file_width)
        self.main_layout.setColumnStretch(1, p_width)

    def get_session_run(self, i_run, r_name):

        rec_probe = self.file.session._runs[i_run]._raw[r_name]
        return rec_probe.get_probe(), rec_probe

    def get_session_files(self):

        exp_f = self.file.new_session.expt_folder
        return exp_f.sub_path.split('/')[-1], exp_f.ses_type

    def keyPressEvent(self, evnt) -> None:

        if evnt.matches(QKeySequence.StandardKey.Cancel):
            self.reject()
        else:
            evnt.ignore()


# SESSION FILE WIDGET --------------------------------------------------------------------------------------------------


class SessionFile(QWidget):
    # static class fields
    grp_name = "Recording Data"

    # pyqtsignal functions
    session_reset = pyqtSignal()
    session_loaded = pyqtSignal()

    def __init__(self, parent=None):
        super(SessionFile, self).__init__(parent)

        # class fields
        self.session = None
        self.has_session = False

        # widget setup
        self.root = self.parent()
        self.group_panel = QGroupBox(self.grp_name.upper())
        self.main_layout = QVBoxLayout()
        self.form_layout = QVBoxLayout()

        # session information widgets
        self.file_widget = QWidget(self)
        self.file_layout = QVBoxLayout()

        # other widgets
        self.new_session = SessionNew(self)
        self.exist_session = QFileSpec(None, None, name='session_name')

        # initialises the class fields
        self.init_class_fields()
        self.init_open_file_fields()

        # sets the widget styling
        self.set_styling()

    # CLASS INITIALISATION FUNCTIONS ------------------------------------------

    def init_class_fields(self):

        # creates the panel objects
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(x_gap, x_gap, x_gap_h, x_gap)
        self.main_layout.addWidget(self.group_panel)

        # sets the outer group-box properties
        self.group_panel.setLayout(self.form_layout)
        self.group_panel.setFont(font_panel)
        self.setLayout(self.main_layout)

        # adds the session file/property widgets
        self.form_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.form_layout.addWidget(self.file_widget)
        self.form_layout.setSpacing(0)
        self.form_layout.setContentsMargins(0, 0, 0, 0)

        # sets up the session file widget properties
        self.file_widget.setLayout(self.file_layout)
        self.file_widget.setObjectName('panel')
        self.file_widget.setSizePolicy(QSizePolicy(cf.q_pref, cf.q_exp))
        self.file_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # sets the new session widget properties
        self.new_session.open_session.connect(self.load_session)
        self.new_session.reset_session.connect(self.reset_session)

        # resets the widget size policies
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

    def init_open_file_fields(self):

        # field initialisations
        r_lbl = ['Start New Session', 'Open Existing Session']
        r_name = ['new', 'existing']

        # creates the radio buttons
        h_radio = []
        for _rl, _rn in zip(r_lbl, r_name):
            # creates the new radio button
            h_radio_new = cw.create_radio_button(None, _rl, _rn == 'new', font_lbl, _rn)
            h_radio_new.toggled.connect(self.radio_session_select)

            # appends it to the list
            h_radio.append(h_radio_new)

        # creates the file spec widget
        cb_fcn = functools.partial(self.new_session.prop_update, ['existing', 'f_input'])
        self.exist_session.connect(cb_fcn)
        self.exist_session.setEnabled(False)

        # adds the widget to the layout
        self.file_layout.addWidget(h_radio[0])
        self.file_layout.addWidget(self.new_session)
        self.file_layout.addWidget(h_radio[1])
        self.file_layout.addWidget(self.exist_session)

    def radio_session_select(self):

        # get the radio button
        rb = self.sender()

        # check if the radio button is checked
        if rb.isChecked():
            # updates the tab widget properties
            self.new_session.is_new = rb.objectName() == 'new'
            self.new_session.setEnabled(self.new_session.is_new)
            self.exist_session.setEnabled(not self.new_session.is_new)

            # updates the dialog properties
            self.new_session.update_dialog_props()

    def load_session(self):

        # sets the subject path and run names
        s_obj = self.new_session
        run_names = "all" if np.all(s_obj.use_run) else s_obj.get_session_run_names()

        # creates the spikewrap session object
        self.session = sw.Session(
            subject_path=s_obj.get_subject_path(),
            session_name=s_obj.get_session_type(),
            file_format=s_obj.get_format_type(),
            run_names=run_names,
        )

        # loads the session object
        self.session.load_raw_data()

        # emits the signal function
        self.session_loaded.emit()

    def reset_session(self):

        # emits the signal function
        self.session_reset.emit()

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def set_styling(self):

        a = 1

        # # sets the session file/property widget stylesheet
        # self.group_panel.setStyleSheet("""
        #     QWidget[objectName="panel"] {
        #         border: 1px solid;
        #     }
        # """)

        # # sets the session file/property widget stylesheet
        # self.setStyleSheet("""
        #     QLineEdit {
        #         border: 1px solid;
        #     }
        #     QComboBox {
        #         border: 1px solid;
        #     }
        # """)


# SESSION PROBE WIDGET -------------------------------------------------------------------------------------------------


class SessionProbe(QWidget):
    # widget dimensions
    x_gap = 5
    x_gap_h = 2
    sz_roi_min = 5

    # static string fields
    grp_name = "Session Probe"

    # array class fields
    dim_lbl = ['Left:', 'Bottom:', 'Width:', 'Height:']
    def_col = ['contact_ids', 'shank_ids', 'device_channel_indices']
    info_lbl = ['Subject Name', 'Title',
                'Session Name', 'Manufacturer',
                'Frame Count', 'Model',
                'Sampling Freq', 'Shank Count',
                'Channel Count', 'Spatial Units']

    # widget stylesheets
    table_style = """
        QTableView {
            font: Arial 6px;        
            border : 1px solid;
        }    
        QHeaderView {
            font: Arial 6px;
            font-weight: 1000;
        }
    """

    def __init__(self, parent=None):
        super(SessionProbe, self).__init__(parent)

        # field retrieval
        self.p = None
        self.vb = None
        self.p_rec = None
        self.p_dframe = None
        self.plt_probe_sub = None
        self.plt_probe_main = None
        self.root = self.parent()

        # boolean class fields
        self.has_plot = False
        self.has_probe = False
        self.is_updating = False

        # widget setup
        self.form_layout = QGridLayout()
        self.main_layout = QVBoxLayout()
        self.info_layout = QGridLayout()
        self.channel_layout = QVBoxLayout()
        self.plot_layout = QGridLayout()
        self.group_panel = QGroupBox(self.grp_name.upper())

        # panel widget setup
        self.info_frame = QFrame()
        self.channel_frame = QFrame()
        self.plot_frame = QFrame()

        # session/probe information fields
        self.info_text = []
        self.info_lbl_dict = {}

        # channel information widgets
        self.table_col = QLabelCheckCombo(None, lbl='Information Table Columns:', font=font_lbl)
        self.channel_table = QTableView(None)

        # plot frame widgets
        self.edit_dim = []
        self.plot_frame_prop = QFrame()
        self.plot_frame_main = QFrame()
        self.plot_frame_sub = QFrame()
        self.prop_frame_layout = QGridLayout()
        self.plot_main_layout = QVBoxLayout()
        self.plot_sub_layout = QVBoxLayout()

        # main plot widgets
        self.main_plt_widget = pg.PlotWidget()
        self.main_plt_item = self.main_plt_widget.getPlotItem()
        self.main_plt = self.main_plt_widget.plot()

        # inset plot widgets
        self.sub_plt_widget = pg.PlotWidget()
        self.sub_plt_item = self.sub_plt_widget.getPlotItem()
        self.sub_plt = self.sub_plt_widget.plot()

        # initialises the class fields
        self.init_class_fields()

    # CLASS INITIALISATION FUNCTIONS ------------------------------------

    def init_class_fields(self):

        # creates the panel objects
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(x_gap_h, x_gap, x_gap, x_gap)
        self.main_layout.addWidget(self.group_panel)

        self.main_plt_item.hideButtons()
        self.sub_plt_item.hideButtons()

        # self.main_plt_widget.setAspectLocked()
        # self.sub_plt_widget.setAspectLocked()

        # creates the children objects for the current parent object
        self.form_layout.addWidget(self.info_frame, 0, 0, 1, 1)
        self.form_layout.addWidget(self.channel_frame, 1, 0, 1, 1)
        self.form_layout.addWidget(self.plot_frame, 0, 1, 2, 1)
        self.form_layout.setColumnStretch(0, 3)
        self.form_layout.setColumnStretch(1, 2)
        self.form_layout.setRowStretch(0, 1)
        self.form_layout.setRowStretch(1, 4)

        # sets the final layout
        self.group_panel.setLayout(self.form_layout)
        self.group_panel.setFont(font_panel)
        self.setLayout(self.main_layout)

        # probe information frame properties
        self.setup_info_frame()
        self.info_frame.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)

        # channel information frame properties
        self.setup_channel_frame()
        self.channel_frame.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)

        # probe plot frame properties
        self.setup_plot_frame()

    def setup_info_frame(self):

        # sets the frame properties
        self.info_frame.setLayout(self.info_layout)
        self.info_frame.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
        self.info_layout.setSpacing(x_gap)

        # creates the information label/text combo widgets
        for i, d in enumerate(self.info_lbl):
            # creates the text label object
            lbl_str = '{}:'.format(d)
            lbl = cw.QLabelText(None, lbl_str, "", font_lbl=font_lbl, name=d)
            lbl.setContentsMargins(0, 0, 0, 0)

            # adds the widget to the layout
            i_r, i_c = int(i / 2), i % 2
            self.info_layout.addWidget(lbl.obj_lbl, i_r, 2 * i_c, 1, 1)
            self.info_layout.addWidget(lbl.obj_txt, i_r, 2 * i_c + 1, 1, 1)

            # stores the text widget
            self.info_text.append(lbl)

    def setup_channel_frame(self):

        # sets the channel frame properties
        self.channel_frame.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
        self.channel_frame.setLayout(self.channel_layout)

        # sets the channel information table properties
        self.channel_layout.setSpacing(x_gap)
        self.channel_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.channel_layout.addWidget(self.table_col)
        self.channel_layout.addWidget(self.channel_table)

        # sets the table column event function
        self.channel_table.setStyleSheet(self.table_style)
        self.table_col.item_clicked.connect(self.check_table_header)


    def setup_plot_frame(self):

        # sets the plot frame properties
        self.plot_frame.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
        self.plot_frame.setLayout(self.plot_layout)

        # sets the layout properties
        self.plot_layout.addWidget(self.plot_frame_prop, 0, 0, 1, 1)
        self.plot_layout.addWidget(self.plot_frame_main, 1, 0, 1, 1)
        self.plot_layout.addWidget(self.plot_frame_sub, 2, 0, 1, 1)
        self.plot_layout.setRowStretch(0, 10)
        self.plot_layout.setRowStretch(1, 45)
        self.plot_layout.setRowStretch(2, 45)

        # plot property frame properties
        self.plot_frame_prop.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
        self.plot_frame_prop.setLayout(self.prop_frame_layout)
        self.prop_frame_layout.setSpacing(x_gap)

        # creates the roi dimension QLineEdit widgets
        for i, ls in enumerate(self.dim_lbl):
            # row/column index calculations
            iy, ix = int(np.floor(i / 2)), i % 2

            # creates the label/edit combo object
            edit_new = QLabelEdit(self, lbl_str=ls, font_lbl=font_lbl, name=ls.lower())
            edit_new.connect(self.edit_dim_update)
            edit_new.obj_edit.setAlignment(cf.align_type['center'])

            # adds the widgets to the layout
            self.prop_frame_layout.addWidget(edit_new.obj_lbl, iy, 2 * ix, 1, 1)
            self.prop_frame_layout.addWidget(edit_new.obj_edit, iy, 2 * ix + 1, 1, 1)
            self.edit_dim.append(edit_new)

        # main plot frame properties
        self.plot_frame_main.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
        self.plot_frame_main.setLayout(self.plot_main_layout)
        self.main_plt_item.hideAxis('left')
        self.main_plt_item.hideAxis('bottom')
        self.main_plt_item.setDefaultPadding(0.01)

        # plot inset frame properties
        self.plot_frame_sub.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
        self.plot_frame_sub.setLayout(self.plot_sub_layout)
        self.sub_plt_item.setMouseEnabled(x=False, y=False)
        self.sub_plt_item.hideAxis('left')
        self.sub_plt_item.hideAxis('bottom')
        self.sub_plt_item.setDefaultPadding(0.01)

    # CLASS EVENT FUNCTIONS ---------------------------------------------

    def main_roi_moved(self, p_pos):

        # updates the x-axis limits
        self.plt_probe_sub.x_lim[0] = p_pos[0]
        self.plt_probe_sub.x_lim[1] = self.plt_probe_sub.x_lim[0] + p_pos[2].x()

        # updates the y-axis limits
        self.plt_probe_sub.y_lim[0] = p_pos[1]
        self.plt_probe_sub.y_lim[1] = self.plt_probe_sub.y_lim[0] + p_pos[2].y()

        # updates the editboxes
        self.is_updating = True
        self.edit_dim[0].set_text('%g' % p_pos[0])
        self.edit_dim[1].set_text('%g' % p_pos[1])
        self.edit_dim[2].set_text('%g' % p_pos[2].x())
        self.edit_dim[3].set_text('%g' % p_pos[2].y())

        # resets the axis limits
        self.plt_probe_sub.reset_axes_limits(False)
        self.is_updating = False

    def edit_dim_update(self, h_edit):

        # if updating manually, then exit
        if self.is_updating:
            return

        # field retrieval
        nw_val = h_edit.text()
        p_str = h_edit.objectName()[:-1]
        nw_lim = self.get_dim_limit(p_str)

        # determines if the new value is valid
        chk_val = cf.check_edit_num(nw_val, min_val=nw_lim[0], max_val=nw_lim[1])
        if chk_val[1] is None:
            # if so, then update the axes limits
            self.is_updating = True
            self.set_dim_value(p_str, chk_val[0])
            self.is_updating = False

        else:
            # otherwise, revert to the previous valid value
            h_edit.setText('%g' % self.get_dim_value(p_str))

    # ROI DIMENSION FUNCTIONS --------------------------------------------

    def get_dim_limit(self, i_dim):

        pp_s = self.plt_probe_sub

        match i_dim:
            case i_dim if i_dim in ['left', 0]:
                # case is the left roi position
                return [pp_s.x_lim_full[0], (pp_s.width - self.get_dim_value(2))]

            case i_dim if i_dim in ['bottom', 1]:
                # case is the bottom roi position
                return [pp_s.y_lim_full[0], (pp_s.height - self.get_dim_value(3))]

            case i_dim if i_dim in ['width', 2]:
                # case is the roi width
                return [self.sz_roi_min, (pp_s.width - self.get_dim_value(0))]

            case i_dim if i_dim in ['height', 3]:
                # case is the roi height
                return [self.sz_roi_min, (pp_s.height - self.get_dim_value(1))]

    def get_dim_value(self, i_dim):

        vb_rng = self.vb.viewRange()

        match i_dim:
            case i_dim if i_dim in ['left', 0]:
                # case is the left location
                return vb_rng[0][0]

            case i_dim if i_dim in ['bottom', 1]:
                # case is the bottom location
                return vb_rng[1][0]

            case i_dim if i_dim in ['width', 2]:
                # case is the box width
                return np.diff(vb_rng[0])[0]

            case i_dim if i_dim in ['height', 3]:
                # case is the box height
                return np.diff(vb_rng[1])[0]

    def set_dim_value(self, i_dim, p_val):

        pp_s = self.plt_probe_sub
        pp_m = self.plt_probe_main

        match i_dim:
            case i_dim if i_dim in ['left', 0]:
                # case is the left location
                pp_s.x_lim[0] = p_val
                pp_m.roi.setPos(pp_s.x_lim[0], pp_s.y_lim[0])

            case i_dim if i_dim in ['bottom', 1]:
                # case is the bottom location
                pp_s.y_lim[0] = p_val
                pp_m.roi.setPos(pp_s.x_lim[0], pp_s.y_lim[0])

            case i_dim if i_dim in ['width', 2]:
                # case is the box width
                pp_s.x_lim[1] = pp_s.x_lim[0] + p_val
                pp_m.roi.setSize(QSizeF(np.diff(pp_s.x_lim)[0], np.diff(pp_s.y_lim)[0]))

            case i_dim if i_dim in ['height', 3]:
                # case is the box height
                pp_s.y_lim[1] = pp_s.y_lim[0] + p_val
                pp_m.roi.setSize(QSizeF(np.diff(pp_s.x_lim)[0], np.diff(pp_s.y_lim)[0]))

    # MISCELLANEOUS FUNCTIONS --------------------------------------------

    def clear_probe_frame(self):

        # resets the boolean flags
        self.has_plot = False
        self.has_probe = False
        self.is_updating = True

        # clears the information fields
        [x.set_label("") for x in self.info_text]

        # clears the table field
        self.channel_table.reset()
        self.table_col.clear()

        # clears the probe plots
        self.clear_probe_plots()
        self.plot_sub_layout.removeWidget(self.sub_plt_widget)
        self.plot_main_layout.removeWidget(self.main_plt_widget)
        [x.set_text("") for x in self.edit_dim]

        # disables the widget
        self.setEnabled(False)
        self.setVisible(False)

        # resets the update flag
        self.is_updating = False

    def clear_probe_plots(self):

        self.plt_probe_main.roi.deleteLater()
        self.main_plt_widget.removeItem(self.plt_probe_main)
        self.sub_plt_widget.removeItem(self.plt_probe_sub)

    def update_probe_info(self):

        # removes any existing plot objects
        if self.has_plot:
            # removes the plot widgets
            self.clear_probe_plots()

        else:
            self.plot_sub_layout.addWidget(self.sub_plt_widget)
            self.plot_main_layout.addWidget(self.main_plt_widget)

        # probe information retrieval
        self.p, self.p_rec = self.root.get_session_run(0, 'grouped')
        self.p_dframe = self.p.to_dataframe(complete=True)

        # PROBE PLOT SETUP ----------------------------------------------

        # creates the plot probe
        self.plt_probe_main = ProbePlot(self.main_plt_widget, self.p)
        self.plt_probe_sub = ProbePlot(self.sub_plt_widget, self.p)

        # creates the main plot figure
        self.main_plt_widget.addItem(self.plt_probe_main)
        self.plt_probe_main.update_roi.connect(self.main_roi_moved)
        self.plt_probe_main.reset_axes_limits(True)

        # creates the inset figure
        self.sub_plt_widget.addItem(self.plt_probe_sub)
        self.plt_probe_sub.reset_axes_limits(False)
        self.vb = self.plt_probe_sub.getViewBox()

        # create the main image ROI
        self.plt_probe_main.create_inset_roi(self.plt_probe_sub.x_lim, self.plt_probe_sub.y_lim)

        # resets the dimension editbox string
        self.is_updating = True
        for i, h in enumerate(self.edit_dim):
            p_val = self.get_dim_value(i)
            h.set_text('%g' % p_val)

        # CHANNEL INFORMATION UPDATE --------------------------------------

        # creates the table model
        t_model = cw.PandasModel(self.p_dframe)
        self.channel_table.setModel(t_model)

        # adds the items to the combobox
        for i, cl in enumerate(list(self.p_dframe)):
            is_show = cl in self.def_col
            self.table_col.add_item(cl, is_show)
            self.channel_table.setColumnHidden(i, not is_show)

        self.channel_table.resizeColumnsToContents()
        self.channel_table.resizeRowsToContents()

        # INFORMATION FIELD UPDATE ----------------------------------------

        # retrieves the session files
        sub_name, ses_name = self.root.get_session_files()

        # information label dictionary
        self.info_lbl_dict = {
            'Subject Name': sub_name,
            'Session Name': ses_name,
            'Frame Count': self.p_rec.get_num_frames(),
            'Sampling Freq': self.p_rec.get_sampling_frequency(),
            'Channel Count': self.p.get_contact_count(),
            'Title': self.p.get_title(),
            'Manufacturer': self.p.manufacturer,
            'Model': self.p.model_name,
            'Shank Count': self.p.get_shank_count(),
            'Spatial Units': self.p.si_units,
        }

        # resets the information labels
        for h in self.info_text:
            # sets up the label string
            val_lbl = self.info_lbl_dict[h.objectName()]
            if val_lbl is None:
                # case is the field is empty
                val_str = 'N/A'

            elif isinstance(val_lbl, str):
                # case is the property is a string
                val_str = val_lbl

            else:
                # case is the property is numeric
                val_str = '%g' % val_lbl

            # updates the label string
            h.set_label(val_str)

        # resets the manual update flag
        self.has_plot = True
        self.has_probe = True
        self.is_updating = False

    def check_table_header(self, item):

        is_sel = item.checkState() == Qt.CheckState.Checked
        i_col = list(self.p_dframe.columns).index(item.text())
        self.channel_table.setColumnHidden(i_col, not is_sel)
        self.channel_table.resizeColumnToContents(i_col)

# SESSION NEW WIDGET ---------------------------------------------------------------------------------------------------


class SessionNew(QWidget):
    # widget dimensions
    lbl_width = 150
    n_row_table = 4
    row_height = 22

    # field initialisation
    p_list_axis = ['Axis 0', 'Axis 1']
    p_list_type = ['int8', 'int16', 'int32']
    col_hdr = ['Run #', 'Analyse Run?', 'Session Run Name']

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

    # pyqtsignal signal functions
    open_session = pyqtSignal()
    reset_session = pyqtSignal()

    def __init__(self, parent=None):
        super(SessionNew, self).__init__(parent)

        # field initialisations
        self.prop_fld = {}
        self.props = {
            'folder': {},
            'file': {},
            'existing': {'f_input': None},
        }

        # string class fields
        self.n_para = None
        self.f_type = 'folder'

        # widget initialisations
        self.expt_folder = None

        # boolean class fields
        self.use_run = None
        self.is_new = True
        self.is_updating = True

        # main class widgets
        self.main_layout = QFormLayout()
        self.button_group = QWidget()
        self.button_layout = QVBoxLayout()
        self.run_table = QTableWidget(0, 3, None)

        # minor class widgets
        self.button_open = cw.create_push_button(self, '')
        self.button_reset = cw.create_push_button(self, '')
        self.h_tab_grp = cw.create_tab_group(self)

        # initialises the class fields
        self.init_prop_fields()
        self.init_class_fields()

    def init_prop_fields(self):

        # sets up the file tab property fields
        p_tmp_folder = {
            'f_input': self.create_para_field(None, 'exptfolder', None),
        }

        # updates the class field
        self.prop_fld['folder'] = {'name': 'Folder', 'type': 'tab', 'ch_fld': p_tmp_folder}

        # sets up the file tab property fields
        p_tmp_file = {
            'f_input': self.create_para_field('Input File Path', 'filespec', None, p_misc=f_mode_ssf),
            'n_channel': self.create_para_field('Channel Count', 'edit', None),
            's_freq': self.create_para_field('Sampling Frequency (Hz)', 'edit', None),
            'gain_to_uV': self.create_para_field('Signal Gain (uV)', 'edit', None),
            'offset_to_uV': self.create_para_field('Signal Offset (uV)', 'edit', None),
            'd_type': self.create_para_field(
                'Signal Offset (uV)', 'combobox', self.p_list_type[1], p_list=self.p_list_type),
            't_axis': self.create_para_field('Time Axis', 'combobox', self.p_list_axis[0], p_list=self.p_list_axis),
            'is_filtered': self.create_para_field('Recording Filtered?', 'checkbox', False),
        }

        # updates the class field
        self.prop_fld['file'] = {'name': 'File', 'type': 'tab', 'ch_fld': p_tmp_file}

        # initialises the fields for all properties
        for i, pf in enumerate(self.prop_fld):
            for pf_c in self.prop_fld[pf]['ch_fld'].keys():
                self.props[pf][pf_c] = self.prop_fld[pf]['ch_fld'][pf_c]['value']

    def init_class_fields(self):

        # sets the widget layout
        self.setLayout(self.main_layout)

        # sets the widget layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addRow(self.h_tab_grp)
        self.main_layout.addRow(self.run_table, self.button_group)

        # button group properties
        self.button_group.setLayout(self.button_layout)
        self.button_layout.addWidget(self.button_open)
        self.button_layout.addWidget(self.button_reset)
        self.button_layout.setSpacing(0)
        self.button_layout.setContentsMargins(5, 0, 0, 0)

        # open button properties
        self.button_open.setIcon(QIcon(icon_path['open']))
        self.button_open.setIconSize(QSize(sz_but - 2, sz_but - 2))
        self.button_open.setFixedSize(sz_but, sz_but)
        self.button_open.setToolTip('Open Session')
        self.button_open.setStyleSheet("border: 1px solid;")
        self.button_open.clicked.connect(self.button_open_session)
        self.button_open.setDefault(False)
        self.button_open.setAutoDefault(False)

        # reset button properties
        self.button_reset.setIcon(QIcon(icon_path['restart']))
        self.button_reset.setIconSize(QSize(sz_but - 2, sz_but - 2))
        self.button_reset.setFixedSize(sz_but, sz_but)
        self.button_reset.setToolTip('Reset Form')
        self.button_reset.setStyleSheet("border: 1px solid;")
        self.button_reset.clicked.connect(self.button_reset_session)
        self.button_reset.setDefault(False)
        self.button_reset.setAutoDefault(False)

        # sets up the slot function
        cb_fcn = functools.partial(self.tab_change)
        self.h_tab_grp.currentChanged.connect(cb_fcn)
        self.h_tab_grp.setContentsMargins(0, 0, 0, 0)

        # creates the tab-objects
        for ps_t in self.prop_fld:
            h_tab = self.create_para_object(None, ps_t, self.prop_fld[ps_t], [ps_t])
            self.h_tab_grp.addTab(h_tab, self.prop_fld[ps_t]['name'])

        # creates the session run table
        self.create_other_widgets()

    def create_para_object(self, layout, p_name, ps, p_str):

        match ps['type']:
            case 'tab':
                # case is a tab widget

                # creates the tab widget
                obj_tab = QWidget()
                obj_tab.setObjectName(p_name)

                # creates the children objects for the current parent object
                t_layout = QFormLayout(obj_tab)
                t_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
                t_layout.setSpacing(0)
                t_layout.setContentsMargins(0, 0, 0, 0)

                # creates the panel object
                h_panel_frame = QFrame()
                h_panel_frame.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
                # h_panel_frame.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_max))
                t_layout.addWidget(h_panel_frame)

                # creates the tab parameter objects
                ch_fld = deepcopy(ps['ch_fld'])
                if p_str[0] == 'folder':
                    # case is a folder data input
                    layout = QFormLayout(h_panel_frame)
                    layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
                    layout.setSpacing(x_gap)
                    layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

                else:
                    # case is a binary file data input
                    layout = QGridLayout(h_panel_frame)
                    layout.setColumnStretch(0, 4)
                    layout.setColumnStretch(1, 2)
                    layout.setColumnStretch(2, 3)

                # creates the tab parameter objects
                self.n_para = 0
                for ps_t in ch_fld:
                    self.create_para_object(layout, ps_t, ps['ch_fld'][ps_t], p_str=p_str + [ps_t])
                    self.n_para += 1

                if p_str[0] == 'file':
                    sp_item = QSpacerItem(100, 75, cf.q_min, cf.q_max)
                    layout.addWidget(QWidget(), self.n_para, 0, 1, 1)
                    layout.addItem(sp_item)

                # sets the tab layout
                h_panel_frame.setLayout(layout)
                obj_tab.setLayout(t_layout)

                # returns the tab object
                return obj_tab

            case 'edit':
                # sets up the editbox string
                lbl_str = '{0}: '.format(ps['name'])
                if ps['value'] is None:
                    # parameter string is empty
                    edit_str = ''

                elif isinstance(ps['value'], str):
                    # parameter is a string
                    edit_str = ps['value']

                else:
                    # parameter is numeric
                    edit_str = '%g' % (ps['value'])

                # creates the label/editbox widget combo
                obj_edit = QLabelEdit(None, lbl_str, edit_str, name=p_name, font_lbl=font_lbl)
                obj_edit.obj_lbl.setFixedWidth(self.lbl_width)

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(obj_edit)

                else:
                    layout.addWidget(obj_edit.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_edit.obj_edit, self.n_para, 1, 1, 1)

                # sets up the label/editbox slot function
                cb_fcn = functools.partial(self.prop_update, p_str)
                obj_edit.connect(cb_fcn)

            # case is a checkbox
            case 'checkbox':
                # creates the checkbox widget
                obj_checkbox = cw.create_check_box(
                    None, ps['name'], ps['value'], font=font_lbl, name=p_name)

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(obj_checkbox)

                else:
                    layout.addWidget(obj_checkbox, self.n_para, 0, 1, 2)

                # sets up the slot function
                cb_fcn = functools.partial(self.prop_update, p_str)
                obj_checkbox.stateChanged.connect(cb_fcn)

            # case is a combobox
            case 'combobox':
                # creates the label/combobox widget combo
                lbl_str = '{0}: '.format(ps['name'])
                obj_combo = QLabelCombo(None, lbl_str, ps['p_list'], ps['value'], name=p_name,
                                        font_lbl=font_lbl)
                obj_combo.obj_lbl.setFixedWidth(self.lbl_width)

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(obj_combo)

                else:
                    layout.addWidget(obj_combo.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_combo.obj_cbox, self.n_para, 1, 1, 1)

                # sets up the slot function
                cb_fcn = functools.partial(self.prop_update, p_str)
                obj_combo.connect(cb_fcn)

            case 'exptfolder':
                # case is the experiment folder widget

                # creates the file selection widget
                self.expt_folder = ExptFolder(self)
                self.expt_folder.init_class_widgets()

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(self.expt_folder)

                # # sets up the slot function
                # obj_expt_folder.connect(self.prop_update, p_str)

            case 'filespec':
                # case is a file selection widget

                # creates the file selection widget
                obj_file_spec = QFileSpec(None, ps['name'], ps['value'], name=p_name, f_mode=ps['p_misc'])

                # adds the widget to the layout
                if isinstance(layout, QFormLayout):
                    layout.addRow(obj_file_spec)

                else:
                    obj_file_spec.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_max))
                    layout.addWidget(obj_file_spec, self.n_para, 0, 1, 3)

                # sets up the slot function
                cb_fcn = functools.partial(self.prop_update, p_str)
                obj_file_spec.connect(cb_fcn)

    def create_other_widgets(self):

        # sets the table properties
        self.run_table.setFixedWidth(int(file_width - (2 * x_gap + 2 * sz_but)))
        self.run_table.setFixedHeight(int(self.row_height * self.n_row_table) + 2)
        self.run_table.setHorizontalHeaderLabels(self.col_hdr)
        self.run_table.verticalHeader().setVisible(False)
        self.run_table.setStyleSheet(self.table_style)

        # table column resizing
        self.run_table.resizeRowsToContents()
        self.run_table.resizeColumnToContents(0)
        self.run_table.resizeColumnToContents(1)
        self.run_table.horizontalHeader().setStretchLastSection(True)
        # self.run_table.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

        # updates the dialog properties
        self.is_updating = False
        self.update_dialog_props()

    # WIDGET EVENT FUNCTIONS --------------------------------------------------

    def tab_change(self):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        self.f_type = self.h_tab_grp.currentWidget().objectName()
        self.update_dialog_props()

    def prop_update(self, p_str, h_obj):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        if isinstance(h_obj, QFileSpec):
            self.button_file_spec(h_obj, p_str)

        elif isinstance(h_obj, QCheckBox):
            self.check_prop_update(h_obj, p_str)

        elif isinstance(h_obj, QLineEdit):
            self.edit_prop_update(h_obj, p_str)

        elif isinstance(h_obj, QComboBox):
            self.combo_prop_update(h_obj, p_str)

    def edit_prop_update(self, h_obj, p_str):

        # field retrieval
        nw_val = h_obj.text()
        str_para = []

        if p_str in str_para:
            # case is a string field
            cf.set_multi_dict_value(self.props, p_str, nw_val)
            self.update_dialog_props()

        else:
            # determines if the new value is valid
            chk_val = cf.check_edit_num(nw_val, min_val=0)
            if chk_val[1] is None:
                # case is the value is valid
                cf.set_multi_dict_value(self.props, p_str, chk_val[0])
                self.update_dialog_props()

            else:
                # otherwise, reset the previous value
                p_val_pr = self.props[p_str[0]][p_str[1]]
                if (p_val_pr is None) or isinstance(p_val_pr, str):
                    # case is the parameter is empty
                    h_obj.setText('')

                else:
                    # otherwise, update the numeric string
                    h_obj.setText('%g' % p_val_pr)

    def combo_prop_update(self, h_obj, p_str):

        # updates the dictionary field
        cf.set_multi_dict_value(self.props, p_str, h_obj.currentText())
        self.update_dialog_props()

    def check_prop_update(self, h_obj, p_str):

        # updates the dictionary field
        cf.set_multi_dict_value(self.props, p_str, h_obj.isChecked())
        self.update_dialog_props()

    def button_file_spec(self, h_obj, p_str):

        # file dialog properties
        dir_only = h_obj.f_mode is None
        caption = 'Select Directory' if dir_only else 'Select File'

        # sets the initial search path
        f_path = cf.get_multi_dict_value(self.props, p_str)
        if f_path is None:
            f_path = data_dir

        # runs the file dialog
        file_dlg = cw.FileDialogModal(caption=caption, dir_only=dir_only, f_filter=h_obj.f_mode, f_directory=f_path)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # if the user accepted, then update the parameter/widget fields
            file_info = file_dlg.selectedFiles()

            match p_str[0]:
                case 'folder':
                    # case is the folder format

                    # determines if the new folder is feasible
                    f_format = self.props['folder']['f_format']
                    if not sf.check_data_folder_structure(file_info[0], f_format):
                        # if not, output an error message to screen
                        f_error = sf.get_data_folder_structure(f_format)
                        err_str = (
                            'The selected folder does not adhere to the "{0}" directory structure.'.format(f_format),
                            'The directory structure should be as follows:', '', f_error, '',
                            'Either retry with another file format or select a feasible directory.',
                        )
                        cf.show_error('\n'.join(err_str), 'Invalid Data Directory')

                        # exits the function
                        return

                case 'file':
                    # case
                    a = 1

            # updates the property value and editbox string
            cf.set_multi_dict_value(self.props, p_str, file_info[0])
            h_obj.set_text(file_info[0])

            # updates the dialog properties
            self.update_dialog_props()

    def button_open_session(self):

        self.open_session.emit()

    def button_reset_session(self):

        self.expt_folder.button_reset_click()
        self.reset_session.emit()

    def check_run_table(self, h_chk, i_row):

        self.use_run[i_row] = h_chk.isChecked()
        self.button_open.setEnabled(np.any(self.use_run))

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def get_subject_path(self):

        base_dir_sp = self.expt_folder.s_dir.split(os.sep)
        return '/'.join(base_dir_sp) + self.expt_folder.sub_path[2:]

    def get_session_run_names(self):

        # retrieves the subject/session dictionary field
        ex_f = self.expt_folder
        ses_dict = ex_f.obj_dir.sub_dict[ex_f.sub_path][ex_f.ses_type]

        # returns the run-name list
        return [x.split('/')[-1] for x in np.array(ex_f.obj_dir.f_pd[0]['path'])[ses_dict]]

    def get_session_type(self):

        return self.expt_folder.ses_type

    def get_format_type(self):

        return self.expt_folder.format_type

    def reset_session_run_table(self, get_run_names):

        # clears the table
        self.run_table.clear()
        run_name = self.get_session_run_names() if get_run_names else []

        # resets the table dimensions
        n_run = len(run_name)
        self.run_table.setRowCount(n_run)
        self.run_table.setHorizontalHeaderLabels(self.col_hdr)
        self.run_table.resizeRowsToContents()

        # memory allocation
        self.use_run = np.ones(n_run, dtype=bool)
        self.button_open.setEnabled(True)

        # creates the new table widgets
        for i in range(n_run):
            # creates the run index
            h_cell_num = QTableWidgetItem(str(i + 1))
            h_cell_num.setFlags(~Qt.ItemFlag.ItemIsEditable)
            h_cell_num.setTextAlignment(cf.align_type['center'])
            # h_cell_num.setFont(self.table_font)
            self.run_table.setItem(i, 0, h_cell_num)

            # creates the include checkbox
            h_cell_chk = cw.create_check_box(None, '', True)
            h_cell_chk.setStyleSheet("margin-left:50%; margin-right:50%;")
            self.run_table.setCellWidget(i, 1, h_cell_chk)

            # sets the checkbox event
            cb_fcn = functools.partial(self.check_run_table, h_cell_chk, i)
            h_cell_chk.stateChanged.connect(cb_fcn)

            # creates the run name field
            h_cell_run = QTableWidgetItem(run_name[i])
            h_cell_run.setFlags(~Qt.ItemFlag.ItemIsEditable)
            # h_cell_run.setFont(self.table_font)
            self.run_table.setItem(i, 2, h_cell_run)

            self.run_table.setRowHeight(i, self.row_height)

    def update_dialog_props(self):

        if self.is_new:
            # case is a new session is selected

            # determines if all fields have been set correctly
            is_feas = next((False for x in self.props[self.f_type].values() if (x is None)), True)

        else:
            # case is an existing session is selected
            is_feas = self.props['existing']['f_input'] is not None

        # updates the control buttons
        a = 1

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}


# EXPERIMENT FOLDER WIDGET ---------------------------------------------------------------------------------------------


class ExptFolder(QWidget):
    # list fields
    f_format = ['spikeglx', 'openephys']
    tab_name = ['Feasible', 'Infeasible']

    def __init__(self, parent=None):
        super(ExptFolder, self).__init__(parent)

        # class fields
        self.ses_type = None
        self.sub_path = None
        self.s_dir = data_dir
        self.format_type = self.f_format[0]
        self.obj_dir = sf.DirectoryCheck(self.s_dir, self.format_type)

        # class layout setup
        self.h_tab = []
        self.h_root = self.parent()
        self.main_layout = QVBoxLayout()
        self.tab_layout = QVBoxLayout()
        self.para_layout = QHBoxLayout()

        # class widget setup
        self.main_widget = QWidget(self)
        self.para_group = QWidget(self)
        self.tab_group = cw.create_tab_group(None)
        self.file_spec = QFileSpec(None, 'Parent Search Folder', file_path=self.s_dir, name='data_folder')
        self.f_type = QLabelCombo(None, 'Recording Format:', self.f_format, self.format_type, font_lbl)
        self.s_type = QLabelCombo(None, 'Session Name:', [], [], font_lbl)

        # boolean class fields
        self.is_updating = False

        # initialises the class fields
        self.init_class_fields()

        # # sets the widget styling
        # self.set_styling()

    def init_class_fields(self):

        # sets the widget layout
        self.setLayout(self.main_layout)
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

        # creates the panel objects
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.main_widget)

        # sets the main widget layout
        self.main_widget.setLayout(self.tab_layout)

        # creates the tab layout
        self.tab_layout.setSpacing(0)
        self.tab_layout.setContentsMargins(x_gap_h, x_gap_h, x_gap_h, x_gap_h)

        # sets the file selection properties
        self.file_spec.connect(self.button_parent_dir)

    def init_class_widgets(self):

        # sets up the other property objects
        self.setup_other_para()

        # sets up the tab widgets
        for tn in self.tab_name:
            self.h_tab.append(self.setup_tab_widget(tn))

        # determines the feasible folders
        self.setup_folder_tree_views()

        # adds the other widgets
        self.tab_layout.addWidget(self.tab_group)
        self.tab_layout.addWidget(self.para_group)
        self.tab_layout.addWidget(self.file_spec)

        # resets the collapse panel size policy
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))

    def setup_tab_widget(self, tab_name):

        # creates the folder tree object
        is_feas_tree = tab_name == self.tab_name[0]
        h_folder_tree = QFolderTree(self, is_feas_tree=is_feas_tree)
        if is_feas_tree:
            h_folder_tree.subject_changed.connect(self.subject_changed)
            h_folder_tree.session_changed.connect(self.session_changed)

        # creates the tab widget
        obj_tab = QWidget()
        obj_tab.setObjectName(tab_name)

        # creates the tab widget layout
        t_layout = QVBoxLayout(obj_tab)
        t_layout.setSpacing(0)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.addWidget(h_folder_tree)
        obj_tab.setLayout(t_layout)

        # adds the tab object to the group
        self.tab_group.addTab(obj_tab, tab_name)

        # returns the widget
        return obj_tab

    def setup_other_para(self):

        # initialisations
        self.para_group.setLayout(self.para_layout)
        self.para_group.setContentsMargins(0, 0, 0, 0)

        # adds the file format combo box
        self.para_layout.setSpacing(0)
        self.para_layout.addWidget(self.f_type)
        # self.f_type.obj_cbox.setFixedWidth(95)
        self.f_type.setContentsMargins(0, 0, 0, 0)
        self.f_type.connect(self.combo_format_change)

        # adds the file format combo box
        self.para_layout.addWidget(self.s_type)
        self.s_type.set_enabled(False)
        # self.s_type.obj_cbox.setFixedWidth(80)
        self.s_type.setContentsMargins(0, 0, 0, 0)
        self.s_type.connect(self.session_changed, False)

    def setup_folder_tree_views(self):

        # determines all the feasible folders (for the current search path/file format)
        self.obj_dir.det_all_feas_folders()

        for i, (ht, fd) in enumerate(zip(self.h_tab, self.obj_dir.f_pd)):
            # retrieves the tree widget
            obj_tree = ht.findChild(QFolderTree)

            # clears/resets the tree items
            if len(fd):
                data_dict = tree_to_dict(dataframe_to_tree(fd))
                obj_tree.reset_tree_items(data_dict)

                # for the feasible folders, set the first feasible folder
                if ht.objectName() == self.tab_name[0]:
                    # updates the tree highlight
                    sub_path0 = list(self.obj_dir.sub_dict.keys())[0]
                    self.reset_selected_subject(obj_tree, sub_path0)

                else:
                    for row in fd.itertuples():
                        item = obj_tree.t_dict['/' + row.path]
                        item.setText('{}*'.format(item.text()))
                        item.setForeground(cf.get_colour_value('r'))
                        item.setToolTip(row.err)

                    obj_tree.obj_tview.expandAll()

            else:
                # creates the tree object
                obj_tree.t_model.clear()
                if i == 0:
                    # clears the subject/session fields
                    self.h_root.sub_path = None
                    self.h_root.ses_type = None

                    # clears the session/run table widgets
                    self.is_updating = True
                    self.s_type.obj_cbox.clear()
                    self.h_root.reset_session_run_table(False)
                    self.is_updating = False

            # updates the enabled properties
            self.tab_group.setTabEnabled(i, len(fd) > 0)

    # WIDGET EVENT FUNCTIONS ---------------------------------------------

    def combo_format_change(self, h_obj):

        if self.is_updating:
            return

        # updates the format string
        self.format_type = h_obj.currentText()
        self.obj_dir.set_format(self.format_type)

        # resets the folder trees
        self.setup_folder_tree_views()

    def button_reset_click(self):

        # resets the class fields
        self.sub_path = None
        self.ses_type = None

        # resets the folder trees
        self.setup_folder_tree_views()

    def button_parent_dir(self, h_obj):

        # runs the file dialog
        file_dlg = cw.FileDialogModal(caption='Set Search Folder', dir_only=True, f_directory=str(self.obj_dir.f_path))
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # if the user accepted, then update the parameter/widget fields
            file_info = file_dlg.selectedFiles()

            # field reset
            self.s_dir = file_info[0]
            self.obj_dir.set_path(Path(self.s_dir))
            self.file_spec.set_text(self.s_dir)

            # resets the folder trees
            self.setup_folder_tree_views()

    def subject_changed(self, item=None):

        # field retrieval
        sub_dict = self.obj_dir.sub_dict[self.sub_path]

        # resets the session type combobox
        self.is_updating = True
        self.s_type.obj_cbox.clear()
        for ses in sub_dict.keys():
            self.s_type.obj_cbox.addItem(ses)

        # sets the session type combobox properties
        self.is_updating = False
        self.s_type.set_enabled(len(sub_dict) > 1)
        self.s_type.obj_cbox.setCurrentIndex(0)

        # updates the session run table
        self.session_changed()

    def session_changed(self, item=None):

        # if manually updating, then exit
        if self.is_updating:
            return

        elif isinstance(item, QStandardItem):
            self.s_type.set_current_text(item.text())

        # updates the session type
        self.ses_type = self.s_type.current_text()

        # resets the session run table
        self.h_root.reset_session_run_table(True)

        # updates the tree highlight (if combobox was update)
        if not isinstance(item, QStandardItem):
            obj_tree = self.h_tab[0].findChild(QFolderTree)
            obj_tree.update_tree_highlights()

    # MISCELLANEOUS FUNCTIONS ---------------------------------------------

    @staticmethod
    def reset_selected_subject(obj_tree, sub_path):

        # updates the subject path
        obj_tree.tree_double_clicked(obj_tree.t_dict[sub_path])
