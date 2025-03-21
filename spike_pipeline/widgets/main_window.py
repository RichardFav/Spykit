# module import
# import os
# import functools
import pickle
import numpy as np

# import pyqtgraph as pg

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget,
                             QScrollArea, QSizePolicy, QDialog, QMenuBar, QToolBar)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QIcon, QAction

# custom module import
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.info.utils import InfoManager
from spike_pipeline.plotting.utils import PlotManager
from spike_pipeline.common.property_classes import SessionWorkBook
from spike_pipeline.widgets.open_session import OpenSession
from spike_pipeline.info.preprocess import PreprocessSetup, prep_task_map

# widget dimensions
x_gap = 15
info_width = 300

# object dimensions
dlg_width = 1650
dlg_height = 900
min_width = 800
min_height = 450

# font objects
font_lbl = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold)
font_hdr = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

# ----------------------------------------------------------------------------------------------------------------------

"""
    MainWindow: spike pipeline main GUI window. controls the flow of information/communication
                between the information/plotting managers
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # sets up the main layout
        self.central_widget = QWidget()
        self.main_layout = QHBoxLayout()

        # main class object setup
        self.session_obj = SessionWorkBook()

        # main class widget setup
        self.menu_bar = MenuBar(self)
        self.info_manager = InfoManager(self, info_width, self.session_obj)
        self.plot_manager = PlotManager(self, dlg_width - info_width, self.session_obj)

        # boolean class fields
        self.can_close = False
        self.has_session = False

        # sets up the main window widgets
        self.setup_main_window()
        self.init_class_fields()

        # sets the widget style sheets
        self.set_styles()

        # # REMOVE ME LATER
        # self.testing()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_main_window(self):

        # sets the central widget
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        # creates the dialog window
        self.setWindowTitle("Spike Interface Pipeline")
        self.setMinimumSize(min_width, min_height)
        self.resize(dlg_width, dlg_height)

    def init_class_fields(self):

        # plot parameter widget setup
        self.main_layout.addWidget(self.info_manager)
        self.main_layout.addWidget(self.plot_manager)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # connects information manager signal functions
        self.info_manager.unit_check.connect(self.update_unit)
        self.info_manager.unit_header_check.connect(self.update_unit_header)
        self.info_manager.channel_check.connect(self.update_channel)
        self.info_manager.channel_header_check.connect(self.update_channel_header)
        self.info_manager.config_update.connect(self.update_config)

        # connects workbook sig\nal functions
        self.session_obj.session_change.connect(self.new_session)
        self.session_obj.sync_channel_change.connect(self.sync_channel_change)
        self.session_obj.bad_channel_change.connect(self.bad_channel_change)

    # ---------------------------------------------------------------------------
    # Signal Slot Functions
    # ---------------------------------------------------------------------------

    def new_session(self):

        # if there is a session already loaded, then clear the main window
        if self.has_session:
            a = 1

        # adds the widgets to the information panel
        self.info_manager.add_info_widgets()

        # -----------------------------------------------------------------------
        # Plot View Setup
        # -----------------------------------------------------------------------

        # sets up the trace/probe views
        self.plot_manager.get_plot_view('trace')
        self.plot_manager.get_plot_view('probe')

        # resets the plot view to include only the trace/probe views
        i_plot_trace = self.plot_manager.get_plot_index('trace')
        i_plot_probe = self.plot_manager.get_plot_index('probe')

        c_id = np.zeros((4, 3), dtype=int)
        c_id[:, :2] = i_plot_trace
        c_id[:, -1] = i_plot_probe

        if not np.any([x is None for x in self.session_obj.session.sync_ch]):
            # create the trigger plot view
            self.plot_manager.get_plot_view('trigger', expand_grid=False)

            # appends the trigger plot view to the info manager
            self.info_manager.add_view_item('Trigger')
            self.info_manager.set_tab_enabled('trigger', True)

            # adds the trigger view
            i_plot_trigger = self.plot_manager.get_plot_index('trigger')
            c_id[-1, :2] = i_plot_trigger

        # updates the grid plots
        self.plot_manager.update_plot_config(c_id)
        self.info_manager.set_region_config(c_id)

        # -----------------------------------------------------------------------
        # Info Table Setup
        # -----------------------------------------------------------------------

        # field retrieval
        c_list = ['channel_ids', 'shank_ids', 'contact_ids',  'device_channel_indices', 'x', 'y']
        c_hdr = ['', 'Channel ID', 'Shank ID', 'Contact ID', 'Channel Index', 'X-Coord', 'Y-Coord']

        # retrieves the necessary channel information data
        ch_info = self.session_obj.get_channel_info()
        p_dframe = ch_info[ch_info.columns.intersection(c_list)][c_list]

        # appends the show
        is_show = np.zeros(p_dframe.shape[0], dtype=bool)
        p_dframe.insert(0, "Show", is_show, True)

        # creates the table model
        self.info_manager.setup_info_table(p_dframe, 'Channel', c_hdr)
        self.info_manager.init_channel_comboboxes()

        # -----------------------------------------------------------------------
        # House-Keeping Exercises
        # -----------------------------------------------------------------------

        # enables the menubar items
        self.menu_bar.set_menu_enabled('save', True)
        self.menu_bar.set_menu_enabled('prep_test', True)

        # resets the session flags
        self.session_obj.state = 1
        self.has_session = True

    def sync_channel_change(self):

        # sets up the trigger channel view (if session is loaded)
        if self.has_session:
            # appends the trigger plot view to the info manager
            self.plot_manager.get_plot_view('trigger', expand_grid=False, show_plot=False)

            # appends the trigger plot view to the info manager
            self.info_manager.add_view_item('Trigger')
            self.info_manager.set_tab_enabled('trigger', True)

    def bad_channel_change(self):

        a = 1

    def update_config(self, c_id):

        self.plot_manager.hide_all_plots()
        self.plot_manager.update_plot_config(c_id)

    def update_channel(self, i_row):

        self.session_obj.toggle_channel_flag(i_row)
        self.plot_manager.reset_probe_views()
        self.plot_manager.reset_trace_views()

        t_type = self.info_manager.table_tab_lbl[0]
        self.info_manager.update_header_checkbox_state(t_type)

    def update_channel_header(self, is_checked):

        self.session_obj.set_all_channel_states(is_checked)

        t_type = self.info_manager.table_tab_lbl[0]
        is_sel = self.session_obj.channel_data.is_selected
        self.info_manager.reset_table_selections(t_type, is_sel)

        self.plot_manager.reset_probe_views()
        self.plot_manager.reset_trace_views()

    def update_unit(self, i_row):

        a = 1

    def update_unit_header(self, i_state):

        a = 1

    def run_preproccessing(self, prep_task):

        # runs the session pre-processing
        prep_tab = self.info_manager.get_info_tab('preprocess')
        configs = prep_tab.setup_config_dict(prep_task)

        # runs the preprocessing
        self.session_obj.session.run_preprocessing(configs)

        # resets the preprocessing data type combobox
        pp_data_flds = self.session_obj.get_current_prep_data_names()

        # updates the channel data types
        channel_tab = self.info_manager.get_info_tab('channel')
        channel_tab.reset_data_types(['Raw'] + prep_task, pp_data_flds)
        # self.session_obj.set_prep_type(pp_data_flds[-1])

        # updates the trace views
        self.plot_manager.reset_trace_views()

    # ---------------------------------------------------------------------------
    # Override Functions
    # ---------------------------------------------------------------------------

    def closeEvent(self, evnt):
        if self.can_close:
            super(MainWindow, self).closeEvent(evnt)

        else:
            evnt.ignore()

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_styles(self):

        # # widget stylesheets
        # central_widget_style = """
        #     background-color: rgba(220, 220, 255, 255);
        # """
        #
        # self.central_widget.setStyleSheet(central_widget_style)

        pass

    def testing(self):

        f_file = 'C:/Work/Other Projects/EPhys Project/Data/z - session_files/test.ssf'
        self.menu_bar.load_session(f_file)


# ----------------------------------------------------------------------------------------------------------------------

"""
    MenuBar: class object that controls the main window menu/toolbars
"""


class MenuBar(QObject):
    # field initialisations
    disabled_list = ['save']

    def __init__(self, main_obj):
        super(MenuBar, self).__init__()

        # field retrieval
        self.main_obj = main_obj

        # tool/menubar setup
        self.menu_bar = None
        self.tool_bar = None

        # initialises the class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # adds the menubar to the main window
        self.menu_bar = QMenuBar(self.main_obj)
        self.main_obj.setMenuBar(self.menu_bar)

        # parent menu widgets
        h_menu_file = self.menu_bar.addMenu('File')
        h_menu_prep = self.menu_bar.addMenu('Preprocessing')

        # ---------------------------------------------------------------------------
        # Toolbar Setup
        # ---------------------------------------------------------------------------

        # creates the toolbar object
        self.tool_bar = QToolBar(self.main_obj)
        self.tool_bar.setMovable(False)
        self.tool_bar.setStyleSheet(cw.toolbar_style)
        self.tool_bar.setIconSize(QSize(cf.but_height + 1, cf.but_height + 1))

        # adds the toolbar to the main window
        self.main_obj.addToolBarBreak()
        self.main_obj.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.tool_bar)
        self.main_obj.contextMenuEvent = self.context_menu_event

        # ---------------------------------------------------------------------------
        # File Menubar Item Setup
        # ---------------------------------------------------------------------------

        # initialisations
        p_str = ['new', 'open', 'save', None, 'close']
        p_lbl = ['New Session', 'Load Session', 'Save Session', None, 'Close Window']
        cb_fcn = [self.new_session, self.load_session, self.save_session, None, self.close_window]

        # adds the file menu items
        self.add_menu_items(h_menu_file, p_lbl, cb_fcn, p_str, True)

        # ---------------------------------------------------------------------------
        # Preprocessing Menubar Item Setup
        # ---------------------------------------------------------------------------

        # initialisations
        p_str = ['run_prep']
        p_lbl = ['Preprocessing Setup']
        cb_fcn = [self.run_preproccessing]

        # adds the preprocessing menu items
        self.add_menu_items(h_menu_prep, p_lbl, cb_fcn, p_str, False)

        # ---------------------------------------------------------------------------
        # House-Keeping Exercises
        # ---------------------------------------------------------------------------

        # disables the required menu items
        [self.set_menu_enabled(x, False) for x in self.disabled_list]

    def add_menu_items(self, h_menu_parent, p_lbl, cb_fcn, p_str, add_tool):

        # menu/toolbar item creation
        for pl, ps, cbf in zip(p_lbl, p_str, cb_fcn):
            if ps is None:
                # adds separators
                h_menu_parent.addSeparator()

                # adds in a separator (if adding to toolbar)
                if add_tool:
                    self.tool_bar.addSeparator()

            else:
                # creates the menu item
                if add_tool:
                    h_tool = QAction(QIcon(cw.icon_path[ps]), pl, self)
                    h_tool.triggered.connect(cbf)
                    h_tool.setObjectName(ps)
                    self.tool_bar.addAction(h_tool)

                # creates the menu item
                h_menu = QAction(pl, self)
                h_menu.setObjectName(ps)
                h_menu.triggered.connect(cbf)
                h_menu_parent.addAction(h_menu)

    # ---------------------------------------------------------------------------
    # File Menubar Functions
    # ---------------------------------------------------------------------------

    def new_session(self):

        self.main_obj.setVisible(False)
        OpenSession(self.main_obj, self.main_obj.session_obj)

    def load_session(self, file_info=None):

        # runs the save file dialog (if file path not given)
        if not isinstance(file_info, str):
            file_dlg = cw.FileDialogModal(None, 'Select Session File', cw.f_mode_ssf, cw.data_dir, is_save=False)
            if file_dlg.exec() == QDialog.DialogCode.Accepted:
                # if successful, then retrieve the file name
                file_info = file_dlg.selectedFiles()[0]

            else:
                # otherwise, exit the function
                return

        # loads data from the file
        with open(file_info, 'rb') as f:
            ses_data = pickle.load(f)

        # creates the session data
        self.main_obj.session_obj.reset_session(ses_data)

    def save_session(self):

        # runs the save file dialog
        file_dlg = cw.FileDialogModal(None, 'Set Session Filename', cw.f_mode_ssf, cw.data_dir, is_save=True)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # retrieves the current session data
            session_data = self.main_obj.session_obj.get_session_save_data()

            # saves the session data to file
            file_info = file_dlg.selectedFiles()
            with open(file_info[0], 'wb') as f:
                pickle.dump(session_data, f)

    def close_window(self):

        # closes the window
        self.main_obj.can_close = True
        self.main_obj.close()

    # ---------------------------------------------------------------------------
    # Preprocessing Menubar Functions
    # ---------------------------------------------------------------------------

    def run_preproccessing(self):

        PreprocessSetup(self.main_obj).exec()

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_menu_enabled(self, menu_name, state):

        h_menu_new = self.get_menu_item(menu_name)
        [x.setEnabled(state) for x in h_menu_new]

    def get_menu_item(self, menu_name):

        return self.findChildren(QAction, name=menu_name)

    def context_menu_event(self, evnt):

        evnt.ignore()
