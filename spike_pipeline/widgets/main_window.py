# module import
# import os
# import functools
import os
import pickle
import numpy as np

import pyqtgraph as pg

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget, QGridLayout,
                             QScrollArea, QMessageBox, QDialog, QMenuBar, QToolBar, QMenu)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QIcon, QAction

# custom module import
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.info.utils import InfoManager
from spike_pipeline.plotting.utils import PlotManager
from spike_pipeline.props.utils import PropManager
from spike_pipeline.common.property_classes import SessionWorkBook
from spike_pipeline.widgets.open_session import OpenSession
from spike_pipeline.info.preprocess import PreprocessSetup, prep_task_map

# widget dimensions
x_gap = 15
info_width = 330

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
        self.main_layout = QGridLayout()

        # main class object setup
        self.session_obj = SessionWorkBook()

        # main class widget setup
        self.menu_bar = MenuBar(self)
        self.info_manager = InfoManager(self, info_width, self.session_obj)
        self.plot_manager = PlotManager(self, dlg_width - info_width, self.session_obj)
        self.prop_manager = PropManager(self, info_width, self.session_obj)

        # boolean class fields
        self.can_close = False
        self.has_session = False

        # sets up the main window widgets
        self.setup_main_window()
        self.init_class_fields()

        # sets the widget style sheets
        self.set_styles()

        # REMOVE ME LATER
        self.testing()

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

        pg.setConfigOption('useOpenGL', False)

    def init_class_fields(self):

        # plot parameter widget setup
        self.main_layout.addWidget(self.prop_manager, 0, 0, 1, 1)
        self.main_layout.addWidget(self.info_manager, 1, 0, 1, 1)
        self.main_layout.addWidget(self.plot_manager, 0, 1, 2, 1)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # connects information manager signal functions
        self.info_manager.unit_check.connect(self.update_unit)
        self.info_manager.unit_header_check.connect(self.update_unit_header)
        self.info_manager.channel_check.connect(self.update_channel)
        self.info_manager.channel_header_check.connect(self.update_channel_header)
        self.prop_manager.config_update.connect(self.update_config)

        # connects workbook sig\nal functions
        self.session_obj.session_change.connect(self.new_session)
        self.session_obj.sync_channel_change.connect(self.sync_channel_change)
        self.session_obj.bad_channel_change.connect(self.bad_channel_change)
        self.session_obj.worker_job_started.connect(self.worker_job_started)
        self.session_obj.worker_job_finished.connect(self.worker_job_finished)

    # ---------------------------------------------------------------------------
    # Calculation Signal Slot Functions
    # ---------------------------------------------------------------------------

    def new_session(self):

        if self.session_obj.session is None:
            # if the session has been cleared, then exit
            return

        elif self.has_session:
            # if there is a session already loaded, then clear the main window
            a = 1

        # adds the widgets to the information panel
        self.info_manager.add_info_widgets()

        # -----------------------------------------------------------------------
        # Plot View Setup
        # -----------------------------------------------------------------------

        # adds the general/trace property fields
        prop_type_add = ['general', 'trace']
        self.prop_manager.add_prop_tabs(prop_type_add)

        # sets up the trace/probe views
        for p_view in ['Trace', 'Probe']:
            self.plot_manager.get_plot_view(p_view.lower())
            self.prop_manager.add_config_view(p_view)

        # initial region configuration
        c_id = np.zeros((4, 3), dtype=int)
        c_id[:, :2] = self.plot_manager.get_plot_index('trace')
        c_id[:, -1] = self.plot_manager.get_plot_index('probe')

        if self.session_obj.session.sync_ch is not None:
            if not np.any([x is None for x in self.session_obj.session.sync_ch]):
                # create the trigger plot view
                self.prop_manager.add_prop_tabs('trigger')
                self.plot_manager.get_plot_view('trigger', expand_grid=False)
                c_id[-1, :2] = self.plot_manager.get_plot_index('trigger')

                # appends the trigger plot view to the prop manager
                self.prop_manager.add_config_view('Trigger')

        # updates the grid plots
        self.plot_manager.update_plot_config(c_id)
        self.prop_manager.set_region_config(c_id)

        # adds the new property tabs
        self.reset_prop_tab_visible(c_id)

        # -----------------------------------------------------------------------
        # Channel Info Table Setup
        # -----------------------------------------------------------------------

        # field retrieval
        c_list = ['keep', 'status', 'channel_ids', 'contact_ids',  'device_channel_indices', 'x', 'y', 'shank_ids']
        c_hdr = ['', 'Keep?', 'Status', 'Channel ID', 'Contact ID', 'Channel Index', 'X-Coord', 'Y-Coord', 'Shank ID']

        # retrieves the necessary channel information data
        ch_info = self.session_obj.get_channel_info()
        ch_keep = self.session_obj.get_keep_channels()
        p_dframe = ch_info[ch_info.columns.intersection(c_list)][c_list[2:]]

        # inserts the "status" column
        n_row, n_col = p_dframe.shape
        p_dframe.insert(0, 'status', np.array(['***'] * n_row))
        p_dframe.insert(0, 'keep', ch_keep)

        # appends the show
        is_show = np.zeros(p_dframe.shape[0], dtype=bool)
        p_dframe.insert(0, "Show", is_show, True)

        # creates the table model
        self.info_manager.setup_info_table(p_dframe, 'Channel', c_hdr)
        self.info_manager.init_channel_comboboxes()

        # appends the channel status flags (if available)
        if self.session_obj.session.bad_ch is not None:
            if not np.any([x is None for x in self.session_obj.session.bad_ch]):
                self.bad_channel_change()

        # -----------------------------------------------------------------------
        # House-Keeping Exercises
        # -----------------------------------------------------------------------

        # enables the menubar items
        self.menu_bar.set_menu_enabled('save', True)
        self.menu_bar.set_menu_enabled('clear', True)
        # self.menu_bar.set_menu_enabled('run_test', True)

        # resets the session flags
        self.session_obj.state = 1
        self.has_session = True

    def sync_channel_change(self):

        # sets up the trigger channel view (if session is loaded)
        if self.has_session:
            # appends the trigger plot view to the info manager
            self.prop_manager.add_prop_tabs('trigger')
            self.plot_manager.get_plot_view('trigger', expand_grid=False, show_plot=False)

            # appends the trigger plot view to the info manager
            self.prop_manager.add_config_view('Trigger')
            self.prop_manager.set_tab_visible('trigger', False)

    def bad_channel_change(self, session=None):

        if session is None:
            # case running session from MainWindow
            i_run = self.session_obj.session.get_run_index(self.session_obj.current_run)
            ch_status = self.session_obj.session.bad_ch[i_run]

        else:
            # case running session from OpenSession
            ch_status = session.bad_ch[0]
            if ch_status is None:
                return

        # updates the channel status flags
        channel_tab = self.info_manager.get_info_tab('channel')
        channel_tab.update_channel_status(ch_status[0][1], self.session_obj.get_keep_channels())

        # resets the status button toggle value (if pressed)
        status_tab = self.info_manager.get_info_tab('status')
        if status_tab.toggle_calc.isChecked():
            status_tab.toggle_calc.setChecked(False)
            status_tab.toggle_calc.setText(status_tab.b_str[0])

        # updates the probe-view
        probe_view = self.plot_manager.get_plot_view('probe')
        probe_view.reset_out_line(ch_status[0][1])
        probe_view.reset_probe_views()

    # ---------------------------------------------------------------------------
    # Progress Worker Slot Functions
    # ---------------------------------------------------------------------------

    def worker_job_started(self, job_name):

        # initialisations
        job_desc = "Error!"

        match job_name:
            case 'bad':
                # case is bad channel detection
                job_desc = "Bad Channel Detection"

            case 'sync':
                # case is trigger channel detection
                job_desc = "Trigger Channel Detection"

            case 'minmax':
                # case is bad channel detection
                job_desc = "Min/Max Signal Calculations"

            case 'preprocess':
                # case is the preprocessing calculations
                job_desc = "Running Preprocessing"

        self.info_manager.add_job(job_name, job_desc)

    def worker_job_finished(self, job_name):

        self.info_manager.delete_job(job_name)

    # ---------------------------------------------------------------------------
    # Signal Slot Functions
    # ---------------------------------------------------------------------------

    def update_config(self, c_id):

        # updates the plot configuration
        self.plot_manager.hide_all_plots()
        self.plot_manager.update_plot_config(c_id)
        self.reset_prop_tab_visible(c_id)

    def reset_prop_tab_visible(self, c_id):

        # resets the tab visibility
        prop_views = self.plot_manager.get_prop_views(c_id)
        for pv in self.plot_manager.prop_views:
            if pv in self.prop_manager.t_types:
                self.prop_manager.set_tab_visible(pv, pv in prop_views)

    def update_channel(self, i_row):

        self.session_obj.toggle_channel_flag(i_row, is_keep=False)
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

        # starts the job worker
        self.worker_job_started('preprocess')

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

        f_file = 'C:/Work/Other Projects/EPhys Project/Data/z - session_files/test_tiny (run1_reduced).ssf'
        # f_file = 'C:/Work/Other Projects/EPhys Project/Data/z - session_files/test_tiny.ssf'
        # f_file = 'C:/Work/Other Projects/EPhys Project/Data/z - session_files/test_large.ssf'
        f_file = 'C:/Work/Other Projects/EPhys Project/Data/z - session_files/Moo.ssf'

        self.menu_bar.load_session(f_file)


# ----------------------------------------------------------------------------------------------------------------------

"""
    MenuBar: class object that controls the main window menu/toolbars
"""


class MenuBar(QObject):
    # field initialisations
    disabled_list = ['save', 'clear']

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
        p_str = ['new', 'open', 'save', None, 'clear', None, 'close']
        p_lbl = ['New...', 'Load...', 'Save...', None, 'Clear Session', None, 'Close Window']
        cb_fcn = [self.new_session, None, None, None, self.clear_session, None, self.close_window]

        # adds the file menu items
        self.add_menu_items(h_menu_file, p_lbl, cb_fcn, p_str, True)

        # ---------------------------------------------------------------------------
        # Save Menubar Item Setup
        # ---------------------------------------------------------------------------

        # field retrieval
        h_file_open = self.get_menu_item('open')
        p_str = ['load_session', 'load_trigger', 'load_config']
        p_lbl = ['Session', 'Trigger File', 'Config File']
        cb_fcn = [self.load_session, self.load_trigger, self.load_config]

        # adds the file menu items
        self.add_menu_items(h_file_open, p_lbl, cb_fcn, p_str, False)

        # ---------------------------------------------------------------------------
        # Save Menubar Item Setup
        # ---------------------------------------------------------------------------

        # field retrieval
        h_file_save = self.get_menu_item('save')
        p_str = ['save_session', 'save_trigger', 'save_config']
        p_lbl = ['Session', 'Trigger File', 'Config File']
        cb_fcn = [self.save_session, self.save_trigger, self.save_config]

        # adds the file menu items
        self.add_menu_items(h_file_save, p_lbl, cb_fcn, p_str, False)

        # ---------------------------------------------------------------------------
        # Preprocessing Menubar Item Setup
        # ---------------------------------------------------------------------------

        # initialisations
        p_str = ['run_prep', 'run_test']
        p_lbl = ['Preprocessing Setup', 'Run Test']
        cb_fcn = [self.run_preproccessing, self.run_test]

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
                if add_tool and (cbf is not None):
                    if ps in cw.icon_path:
                        h_tool = QAction(QIcon(cw.icon_path[ps]), pl, self)
                        h_tool.triggered.connect(cbf)
                        h_tool.setObjectName(ps)
                        self.tool_bar.addAction(h_tool)

                if cbf is not None:
                    h_menu = QAction(pl, h_menu_parent)
                    h_menu_parent.addAction(h_menu)
                    h_menu.triggered.connect(cbf)

                else:
                    h_menu = QMenu(pl, h_menu_parent)
                    h_menu_parent.addMenu(h_menu)

                # creates the menu item
                h_menu.setParent(h_menu_parent)
                h_menu.setObjectName(ps)

    # ---------------------------------------------------------------------------
    # File Menubar Functions
    # ---------------------------------------------------------------------------

    def new_session(self):

        self.main_obj.setVisible(False)
        OpenSession(self.main_obj, self.main_obj.session_obj)

    def load_session(self, file_info=None):

        # prompts the user for the file name (exit if the user cancels)
        file_info = self.load_file(file_info, 'session')
        if file_info is None:
            return

        # loads data from the file
        with open(file_info, 'rb') as f:
            ses_data = pickle.load(f)

        # field retrieval
        channel_data = ses_data['channel_data']

        # resets the trace start time to 0
        ses_data['prop_para']['trace']['t_start'] = 0
        ses_data['prop_para']['trace']['t_finish'] = ses_data['prop_para']['trace']['t_span']

        # creates the session data
        self.main_obj.session_obj.reset_session(ses_data)
        self.main_obj.session_obj.session.set_bad_channel(channel_data['bad'])
        self.main_obj.session_obj.session.set_sync_channel(channel_data['sync'])

        # updates the channel status table fields
        self.main_obj.bad_channel_change()

        # creates the trigger plot view (if missing)
        if 'trigger' not in self.main_obj.plot_manager.types:
            self.main_obj.sync_channel_change()

        # resets the property/information panel fields
        self.main_obj.prop_manager.set_prop_para(ses_data['prop_para'])
        self.main_obj.info_manager.set_info_para(ses_data['info_para'])

    def clear_session(self):

        # if there is a parameter change, then prompt the user if they want to change
        q_str = 'Are you sure you want to clear the current session?'
        u_choice = QMessageBox.question(self.main_obj, 'Clear Session?', q_str, cf.q_yes_no, cf.q_yes)
        if u_choice == cf.q_no:
            # exit if they cancelled
            return

        a = 1

    def load_trigger(self, file_info=None):

        # prompts the user for the file name (exit if the user cancels)
        file_info = self.load_file(file_info, 'trigger')
        if file_info is None:
            return

        # loads data from the file
        with open(file_info, 'rb') as f:
            trig_data = pickle.load(f)

        # finish me!!
        pass

    def load_config(self, file_info=None):

        # prompts the user for the file name (exit if the user cancels)
        file_info = self.load_file(file_info, 'config')
        if file_info is None:
            return

        # loads data from the file
        with open(file_info, 'rb') as f:
            config_data = pickle.load(f)

        # finish me!!
        pass

    def save_session(self):

        # field retrieval
        ses_obj = self.main_obj.session_obj

        # info/property parameter retrieval
        info_list = ["preprocess", "status"]
        prop_list = ["general", "trace", "trigger"]

        # sets up the session save data dictionary
        session_data = {
            'state': ses_obj.state,
            'session_props': ses_obj.session.get_session_props(),
            'prop_para': self.main_obj.prop_manager.get_prop_para(prop_list),
            'info_para': self.main_obj.info_manager.get_info_para(info_list),
            'channel_data': {
                'bad': ses_obj.session.bad_ch,
                'sync': ses_obj.session.sync_ch,
                'keep': ses_obj.get_keep_channels(),
            }
        }

        # saves the session file
        self.save_file('session', session_data)

    def save_trigger(self):

        # retrieves the output data
        trigger_data = {'Finish': "Me!"}

        # saves the session file
        self.save_file('trigger', trigger_data)

    def save_config(self):

        # retrieves the output data
        config_data = {'Finish': "Me!"}

        # saves the session file
        self.save_file('config', config_data)

    def close_window(self):

        # closes the window
        self.main_obj.can_close = True
        self.main_obj.close()

    # ---------------------------------------------------------------------------
    # Preprocessing Menubar Functions
    # ---------------------------------------------------------------------------

    def run_preproccessing(self):

        PreprocessSetup(self.main_obj).exec()

    def run_test(self):

        import matplotlib
        matplotlib.use('Agg')

        ses = self.main_obj.session_obj.session
        h_fig = ses._s.plot_preprocessed(
            show=True,
            time_range=(0, 0.1),
            show_channel_ids=False,
            mode="map",
        )

        h_fig['run-001_g0_imec0'].savefig('TestHeatmap.png')

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_menu_enabled(self, menu_name, state):

        self.get_menu_item(menu_name).setEnabled(state)

    def get_menu_item(self, menu_name):

        return self.menu_bar.findChild((QWidget, QAction), name=menu_name)

    def context_menu_event(self, evnt):

        evnt.ignore()

    def load_file(self, file_info, f_type):

        # runs the save file dialog (if file path not given)
        if not isinstance(file_info, str):
            f_title = 'Select {0} File'.format(cw.f_name[f_type])
            file_dlg = cw.FileDialogModal(None, f_title, cw.f_mode[f_type], cw.data_dir, is_save=False)
            if file_dlg.exec() == QDialog.DialogCode.Accepted:
                # if successful, then retrieve the file name
                file_info = file_dlg.selectedFiles()[0]

            else:
                # otherwise, exit the function
                return None

        return file_info

    def save_file(self, f_type, output_data):

        # runs the save file dialog
        f_title = 'Select {0} File'.format(cw.f_name[f_type])
        file_dlg = cw.FileDialogModal(None, f_title, cw.f_mode[f_type], cw.data_dir, is_save=True)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # saves the session data to file
            file_info = file_dlg.selectedFiles()
            with open(file_info[0], 'wb') as f:
                pickle.dump(output_data, f)
