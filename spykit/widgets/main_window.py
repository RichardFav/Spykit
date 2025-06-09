# module import
import os
# import functools
import time
import glob
import pickle
import shutil
import numpy as np
import pyqtgraph as pg
from pathlib import Path
from copy import deepcopy
from functools import partial as pfcn

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget, QGridLayout,
                             QScrollArea, QMessageBox, QDialog, QMenuBar, QToolBar, QMenu)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction

# custom module import
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.info.utils import InfoManager
from spykit.plotting.utils import PlotManager
from spykit.props.utils import PropManager
from spykit.common.property_classes import SessionWorkBook
from spykit.widgets.open_session import OpenSession
from spykit.info.preprocess import PreprocessSetup, pp_flds
from spykit.threads.utils import ThreadWorker
from spykit.widgets.default_dir import DefaultDir

# spikewrap module import
from spikewrap.configs._backend import canon

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
    # pyqtsignal functions
    start_preprocess = pyqtSignal(object)

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
        if os.environ['COMPUTERNAME'] == "DESKTOP-NLLEH0V":
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
        self.plot_manager.probe_inset_button.connect(self.update_inset_channel)
        self.prop_manager.config_update.connect(self.update_config)

        # connects workbook sig\nal functions
        self.session_obj.session_change.connect(self.new_session)
        self.session_obj.bad_channel_change.connect(self.bad_channel_change)
        self.session_obj.sync_channel_change.connect(self.sync_channel_change)
        self.session_obj.keep_channel_reset.connect(self.keep_channel_reset)
        self.session_obj.worker_job_started.connect(self.worker_job_started)
        self.session_obj.worker_job_finished.connect(self.worker_job_finished)
        self.session_obj.prep_progress_update.connect(self.prep_progress_update)

    # ---------------------------------------------------------------------------
    # Calculation Signal Slot Functions
    # ---------------------------------------------------------------------------

    def new_session(self):

        # disables the trigger/config files
        if self.has_session:
            # if there is a session already loaded, then clear the main window
            self.clear_session()

        if self.session_obj.session is None:
            # if the session has been cleared, then exit
            return

        # adds the widgets to the information panel
        self.info_manager.add_info_widgets()

        # flag that there is session data available
        self.has_session = True

        # -----------------------------------------------------------------------
        # Plot View Setup
        # -----------------------------------------------------------------------

        # adds the general/trace property fields
        prop_type_add = ['general', 'trace']
        self.prop_manager.add_prop_tabs(prop_type_add)
        for pt in prop_type_add:
            self.prop_manager.set_tab_visible(pt, True)

        # sets up the trace/probe views
        for p_view in ['Trace', 'Probe']:
            # if missing, then add the plot type (if required)
            if p_view.lower() in self.plot_manager.types:
                # retrieves the plot view widget
                plot_view = self.plot_manager.get_plot_view(p_view.lower())

                # performs specific view updates
                match p_view.lower():
                    case 'probe':
                        plot_view.probe_rec = self.session_obj.get_current_recording_probe()
                        self.plot_manager.reset_probe_views()

                    case 'trace':
                        pass

            else:
                self.plot_manager.add_plot_view(p_view.lower())

            # adds the configuration view
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
        self.prop_manager.set_config_enabled(True)

        # adds the new property tabs
        self.reset_prop_tab_visible(c_id)

        # -----------------------------------------------------------------------
        # Channel Info Table Setup
        # -----------------------------------------------------------------------

        # sets up the channel information dataframe
        p_dframe = self.session_obj.get_info_data_frame()

        # creates the table model
        self.info_manager.setup_info_table(p_dframe, 'Channel', self.session_obj.c_hdr)
        self.info_manager.init_channel_comboboxes()

        # appends the channel status flags (if available)
        if self.session_obj.session.bad_ch is not None:
            if not np.any([x is None for x in self.session_obj.session.bad_ch]):
                self.bad_channel_change()

        # -----------------------------------------------------------------------
        # House-Keeping Exercises
        # -----------------------------------------------------------------------

        # enables the menubar items
        self.menu_bar.set_menu_enabled_blocks('session-open')

        # resets the session flags
        self.session_obj.state = 1

    def sync_channel_change(self):

        # sets up the trigger channel view (if session is loaded)
        if self.has_session:
            # appends the trigger plot view to the info manager
            self.prop_manager.add_prop_tabs('trigger')

            if 'trigger' in self.plot_manager.types:
                trig_view = self.plot_manager.get_plot_view('trigger')
                trig_view.delete_all_regions()
                trig_view.reset_session_fields(self.session_obj)

            else:
                # appends the trigger plot view to the info manager
                self.plot_manager.get_plot_view('trigger', expand_grid=False, show_plot=False)
                self.prop_manager.set_tab_visible('trigger', False)

            # adds the configuration view field
            self.prop_manager.add_config_view('Trigger')

    def keep_channel_reset(self):

        # retrieves the channel table object
        is_keep = self.session_obj.channel_data.is_keep
        self.info_manager.get_info_tab('channel').keep_channel_reset(is_keep)

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
        channel_tab.update_channel_status(ch_status, self.session_obj.get_keep_channels(), True)

        # resets the status button toggle value (if pressed)
        status_tab = self.info_manager.get_info_tab('status')
        if status_tab.toggle_calc.isChecked():
            status_tab.toggle_calc.setChecked(False)
            status_tab.toggle_calc.setText(status_tab.b_str[0])

        # updates the probe-view
        probe_view = self.plot_manager.get_plot_view('probe')
        probe_view.reset_out_line(ch_status)
        self.plot_manager.reset_probe_views()

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

    def prep_progress_update(self, m_str, pr_val):

        # stops the timeline widget
        self.info_manager.prog_widget.update_prog_message(m_str, pr_val)

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
        self.plot_manager.reset_trace_views(2)

        t_type = self.info_manager.table_tab_lbl[0]
        self.info_manager.update_header_checkbox_state(t_type)

    def update_channel_header(self, is_checked):

        self.session_obj.set_all_channel_states(is_checked)

        t_type = self.info_manager.table_tab_lbl[0]
        is_sel = self.session_obj.channel_data.is_selected
        self.info_manager.reset_table_selections(t_type, is_sel)

        self.plot_manager.reset_probe_views()
        self.plot_manager.reset_trace_views(2)

    def update_inset_channel(self, inset_id):

        self.session_obj.set_channel_indices(inset_id)

        t_type = self.info_manager.table_tab_lbl[0]
        is_sel = self.session_obj.channel_data.is_selected
        self.info_manager.reset_table_selections(t_type, is_sel)

        self.plot_manager.reset_probe_views()
        self.plot_manager.reset_trace_views(2)

    def update_unit(self, i_row):

        a = 1

    def update_unit_header(self, i_state):

        a = 1

    # ---------------------------------------------------------------------------
    # Preprocessing Functions
    # ---------------------------------------------------------------------------

    def on_preprocessing_close(self, has_pp):

        # runs the preprocessing specifc updates
        if has_pp:
            # resets the preprocessing data type combobox
            self.session_obj.reset_current_session(True)
            pp_data_flds = self.session_obj.get_current_prep_data_names()
            task_flds = deepcopy(pp_data_flds[-1].split('-')[1:])

            # if removing channels, then delete this from the preprocessing fields
            task_name = [pp_flds[x] for x in task_flds]
            has_remove = [(x == 'remove_channels') for x in task_flds]
            if np.any(np.asarray(has_remove)):
                # determines the instances where channels were removed
                for i_rmv in np.flip(np.where(has_remove)[0]):
                    pp_data_flds.pop(i_rmv)
                    task_name.pop(i_rmv)

            # updates the channel data types
            channel_tab = self.info_manager.get_info_tab('channel')
            channel_tab.reset_data_types(task_name, pp_data_flds)

        # updates the trace views
        self.plot_manager.reset_trace_views()
        self.menu_bar.set_menu_enabled_blocks('post-process')

    def run_preprocessing_dialog(self, pp_config=None):

        # opens the preprocessing setup
        h_app = PreprocessSetup(self, pp_config)
        h_app.close_preprocessing.connect(self.on_preprocessing_close)
        h_app.show()

    # ---------------------------------------------------------------------------
    # Obsolete Preprocessing Functions
    # ---------------------------------------------------------------------------

    def run_preproccessing(self, prep_obj):

        # runs the session pre-processing
        prep_tab = self.info_manager.get_info_tab('preprocess')
        if isinstance(prep_obj, tuple):
            # case is running from the Preprocessing dialog
            prep_task, prep_opt = prep_obj
            per_shank, concat_runs = prep_opt
            pp_config = prep_tab.setup_config_dict(prep_task)

        else:
            # case is running from loading session
            pp_config = prep_obj.setup_config_dicts()

        # runs the preprocessing
        self.session_obj.session.run_preprocessing(pp_config, per_shank, concat_runs)
        self.session_obj.reset_current_session(True)

        # resets the preprocessing data type combobox
        pp_data_flds = self.session_obj.get_current_prep_data_names()
        task_flds = deepcopy(pp_data_flds[-1].split('-')[1:])

        # if removing channels, then delete this from the preprocessing fields
        task_name = [pp_flds[x] for x in task_flds]
        has_remove = [(x == 'remove_channels') for x in task_flds]
        if np.any(np.asarray(has_remove)):
            # determines the instances where channels were removed
            for i_rmv in np.flip(np.where(has_remove)[0]):
                pp_data_flds.pop(i_rmv)
                task_name.pop(i_rmv)

        # updates the channel data types
        channel_tab = self.info_manager.get_info_tab('channel')
        channel_tab.reset_data_types(task_name, pp_data_flds)
        # self.bad_channel_change()

        # updates the trace views
        self.plot_manager.reset_trace_views()
        self.menu_bar.set_menu_enabled_blocks('post-process')

    def setup_preprocessing_worker(self, prep_task, prep_opt=None, delay_start=False):

        # pauses for things to catch up...
        t_worker = ThreadWorker(self, self.run_preprocessing_worker, (prep_task, prep_opt))
        t_worker.work_finished.connect(self.preprocessing_complete)

        if delay_start:
            QTimer.singleShot(20, pfcn(self.start_preprocessing_timer, t_worker))

        else:
            t_worker.start()

    def run_preprocessing_worker(self, prep_obj):

        self.run_preproccessing(prep_obj)

    def preprocessing_complete(self):

        self.worker_job_finished('preprocess')

    @staticmethod
    def start_preprocessing_timer(t_worker):

        t_worker.start()

    # ---------------------------------------------------------------------------
    # Session Related Functions
    # ---------------------------------------------------------------------------

    def clear_session(self):

        # array fields
        base_tab = ['config']

        # resets the property tab widget/visibility fields
        for t, tt in zip(self.prop_manager.tabs, self.prop_manager.t_types):
            # property specific updates
            match tt:
                case 'config':
                    # case is the configuration tab
                    if self.session_obj.session is None:
                        t.obj_rconfig.clear()

                    else:
                        t.obj_rconfig.reset()

                case 'trigger':
                    # case is the trigger tab
                    trig_view = self.plot_manager.get_plot_view('trigger')
                    trig_view.delete_all_regions()

            # resets the tab visibility
            self.prop_manager.set_tab_visible(tt, tt in base_tab)

        # clears the plot view
        for p_type in self.plot_manager.types:
            # retrieves the plot view object
            p_view = self.plot_manager.get_plot_view(p_type)
            p_view.clear_plot_view()

            # performs the view specific updates
            match p_type:
                case 'probe':
                    pass

                case 'trace':
                    pass

                case 'trigger':
                    pass

            # hides the plot view
            p_view.hide()

        # clears the information tabs
        self.info_manager.tab_group_table.setVisible(False)
        self.menu_bar.set_menu_enabled_blocks('init')

        # resets the session flag
        self.has_session = False

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

        # f_file = "C:/Work/Other Projects/EPhys Project/Code/spykit/spykit/resources/session/tiny_session.ssf"
        # f_file = "C:/Work/Other Projects/EPhys Project/Code/Spykit/spykit/resources/data/z - session files/tiny_example.ssf"
        # f_file = "C:/Work/Other Projects/EPhys Project/Code/Spykit/spykit/resources/data/z - session files/tiny_example (preprocessed).ssf"
        f_file = "C:/Work/Other Projects/EPhys Project/Code/Spykit/spykit/resources/data/z - session files/tiny_example (preprocessed2).ssf"
        # f_file = "C:/Work/Other Projects/EPhys Project/Code/Spykit/spykit/resources/data/z - session files/large_example.ssf"

        self.menu_bar.load_session(f_file)


# ----------------------------------------------------------------------------------------------------------------------

"""
    MenuBar: class object that controls the main window menu/toolbars
"""


class MenuBar(QObject):
    # static class fields
    sync_file_name = canon.saved_sync_filename()
    sync_folder_name = canon.sync_folder()

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
        h_menu_file = self.add_main_menu_item('File')
        h_menu_prep = self.add_main_menu_item('Preprocessing')

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
        p_str = ['new', 'open', 'save', None, 'clear', 'default', None, 'close']
        p_lbl = ['New...', 'Load...', 'Save...', None, 'Clear Session', 'Default Directories', None, 'Close Window']
        has_ch = [False, True, True, False, False, False, False, False]
        cb_fcn = [self.new_session, self.load_session, self.save_session, None,
                  self.clear_session, self.default_dir, None, self.close_window]

        # adds the file menu items
        self.add_menu_items(h_menu_file, p_lbl, cb_fcn, p_str, True, has_ch=has_ch)

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

        # disables the trigger/config files
        self.set_menu_enabled('load_trigger', False)
        self.set_menu_enabled('load_config', False)

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
        p_str = ['run_prep', 'clear_prep', None, 'run_test']
        p_lbl = ['Preprocessing Setup', 'Clear Preprocessing', None, 'Run Test']
        cb_fcn = [self.run_preproccessing, self.clear_preprocessing, None, self.run_test]

        # adds the preprocessing menu items
        self.add_menu_items(h_menu_prep, p_lbl, cb_fcn, p_str, False)

        # ---------------------------------------------------------------------------
        # House-Keeping Exercises
        # ---------------------------------------------------------------------------

        # disables the required menu items
        self.set_menu_enabled_blocks('init')

    def add_main_menu_item(self, label):

        h_menu = self.menu_bar.addMenu(label)
        h_menu.setObjectName(label.lower())

        return h_menu

    def add_menu_items(self, h_menu_parent, p_lbl, cb_fcn, p_str, add_tool, has_ch=None):

        if has_ch is None:
            has_ch = np.zeros(len(p_lbl), dtype=bool)

        # menu/toolbar item creation
        for pl, ps, cbf, hc in zip(p_lbl, p_str, cb_fcn, has_ch):
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
                        h_icon = QIcon(cw.icon_path[ps])
                        h_tool = QAction(h_icon, pl, self)
                        self.tool_bar.addAction(h_tool)

                        h_tool.setParent(self.tool_bar)
                        h_tool.triggered.connect(cbf)
                        h_tool.setObjectName(ps)

                if hc:
                    h_menu = QMenu(pl, h_menu_parent)
                    h_menu_parent.addMenu(h_menu)

                else:
                    h_menu = QAction(pl, h_menu_parent)
                    h_menu_parent.addAction(h_menu)
                    h_menu.triggered.connect(cbf)

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
        session_dir = cw.get_def_dir("session")
        file_info = self.load_file(file_info, 'session', def_dir=session_dir)
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
        self.main_obj.session_obj.reset_channel_data(channel_data)

        # updates the bad/sync channel status table fields
        self.main_obj.bad_channel_change()
        self.main_obj.sync_channel_change()

        # resets the multi-run property fields
        n_run = self.main_obj.session_obj.session.get_run_count()
        for pt in ['general', 'trigger']:
            # retrieves the property tab
            prop_tab = self.main_obj.prop_manager.get_prop_tab(pt)
            prop_tab.p_props.reset_prop_para(prop_tab.p_info['ch_fld'], n_run)

        # resets the property/information panel fields
        self.main_obj.prop_manager.set_prop_para(ses_data['prop_para'])
        self.main_obj.info_manager.set_info_para(ses_data['info_para'])

        # sets/runs the config field/routines
        time.sleep(0.1)
        if ses_data['configs'] is not None:
            # resets the preprocessing configuration fields
            prep_info = self.main_obj.info_manager.get_info_tab('preprocess')
            prep_info.configs.clear()
            prep_info.configs = ses_data['configs']

            # runs the preprocessing (if data in config field)
            prep_task = prep_info.configs.task_name
            if len(prep_task):
                # if there is preprocessed data, prompt the user if they would like to re-run the calculations
                t_str = 'Re-run Preprocessing?'
                q_str = 'The loaded session has preprocessed tasks. Would you like to re-run these tasks?'
                u_choice = QMessageBox.question(self.main_obj, 'Use Default Files?', q_str, cf.q_yes_no, cf.q_yes)
                if u_choice == cf.q_no:
                    # if not, then exit
                    return

                # sets the menu enabled properties
                self.set_menu_enabled_blocks('post-process')

                # runs the preprocessing dialog window
                prep_opt = tuple(prep_info.configs.prep_opt.values())
                self.main_obj.run_preprocessing_dialog((prep_task, prep_opt))

    def load_trigger(self, file_info=None):

        # field retrieval
        sync_dir_base = None
        raw_runs = self.main_obj.session_obj.session._s._raw_runs

        # determines if the default sync channel trace exists
        has_def, def_sync_dir = True, []
        for i_run, rr in enumerate(raw_runs):
            def_sync_dir = self.get_sync_output_dir(rr, None)
            if not def_sync_dir.is_dir():
                # if not, then flag that the default files do not exist
                has_def = False
                break

        if has_def:
            # if the default file exist, prompt the user if they want to use them
            q_str = 'Do you want to use the default trigger channel files?'
            u_choice = QMessageBox.question(self.main_obj, 'Use Default Files?', q_str, cf.q_yes_no_cancel, cf.q_yes)
            if u_choice == cf.q_cancel:
                # case is the user cancelled
                return
            else:
                # case is user chose yes/no
                use_def = u_choice == cf.q_yes

        else:
            # if not, then user is force to use the custom trigger trace folder
            use_def = False

        if not use_def:
            # if using a custom path, prompt the user for said path
            trigger_dir = cw.get_def_dir("trigger")
            base_dir = self.load_file('trigger', dir_only=True, def_dir=trigger_dir)
            if base_dir is None:
                # case is the user cancelled
                return

            else:
                # sets the output directory
                sync_dir_base = base_dir
                if not self.check_custom_sync_dir(raw_runs, sync_dir_base):
                    return

        # trigger file load and data storage
        for i_run, rr in enumerate(raw_runs):
            # sets up the file name
            sync_dir = self.get_sync_output_dir(rr, sync_dir_base)
            sync_run = np.load(sync_dir / self.sync_file_name)

            # determines if the signal matches the run duration
            n_sample_run = rr._raw[list(rr._raw.keys())[0]].get_num_samples()
            if len(sync_run) == n_sample_run:
                # if so, then update the trace
                self.main_obj.session_obj.session.sync_ch[i_run] = sync_run

            else:
                # otherwise, output an error to screen
                err_str = 'The trigger channel file does not match '
                cf.show_error(err_str, 'Invalid Trigger Channel File')
                return

        # more field retrieval
        change_made = False
        trig_props = self.main_obj.prop_manager.get_prop_tab('trigger')
        trig_view = self.main_obj.plot_manager.get_plot_view('trigger')

        # resets the trigger view
        if trig_props.delete_all_regions():
            trig_view.reset_trace_values()
            trig_view.update_trigger_trace()

    def load_config(self, file_info=None):

        # prompts the user for the file name (exit if the user cancels)
        config_dir = cw.get_def_dir("configs")
        file_info = self.load_file(file_info, 'config', def_dir=config_dir)
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
        prep_tab = self.main_obj.info_manager.get_info_tab('preprocess')

        # info/property parameter retrieval
        info_list = ["preprocess", "status"]
        prop_list = ["general", "trace", "trigger"]

        # sets up the session save data dictionary
        session_data = {
            'state': ses_obj.state,
            'configs': prep_tab.configs,
            'session_props': ses_obj.session.get_session_props(),
            'prop_para': self.main_obj.prop_manager.get_prop_para(prop_list),
            'info_para': self.main_obj.info_manager.get_info_para(info_list),
            'channel_data': {
                'bad': ses_obj.session.bad_ch,
                'sync': ses_obj.session.sync_ch,
                'keep': ses_obj.get_keep_channels(),
                'removed': ses_obj.get_removed_channels(),
            }
        }

        # saves the session file
        session_dir = cw.get_def_dir("session")
        self.save_file('session', session_data, def_dir=session_dir)

    def save_trigger(self):

        # initialisations
        output_dir_base = None

        # prompts the user if they want to use the default output path
        q_str = 'Do you want to use the default trigger channel output path?'
        u_choice = QMessageBox.question(self.main_obj, 'Use Default Path?', q_str, cf.q_yes_no_cancel, cf.q_yes)
        if u_choice == cf.q_cancel:
            # exit if the user cancelled
            return

        else:
            use_def = u_choice == cf.q_yes
            if not use_def:
                # if using a custom path, prompt the user for said path
                trigger_dir = cw.get_def_dir("trigger")
                base_dir = self.save_file('trigger', dir_only=True, def_dir=trigger_dir)
                if base_dir is None:
                    # case is the user cancelled
                    return

                else:
                    # sets the output directory
                    output_dir_base = base_dir / self.main_obj.session_obj.session._session_name

        # field/object retrieval
        s_freq = self.main_obj.session_obj.session_props.s_freq
        sync_ch = deepcopy(self.main_obj.session_obj.session.sync_ch)
        trig_props = self.main_obj.prop_manager.get_prop_tab('trigger')
        trig_view = self.main_obj.plot_manager.get_plot_view('trigger')
        raw_runs = self.main_obj.session_obj.session._s._raw_runs

        # trigger trace silencing
        for i_run, r_lim in enumerate(trig_props.p_props.region_index):
            for i_reg in np.flip(range(trig_view.n_reg_xs[i_run])):
                ind_s = int(np.floor(r_lim[i_reg, 1] * s_freq))
                ind_f = int(np.ceil(r_lim[i_reg, 2] * s_freq))
                sync_ch[i_run][ind_s:ind_f] = 0

        # trigger trace output
        for i_run, rr in enumerate(raw_runs):
            # sets up the file name
            sync_dir = self.get_sync_output_dir(rr, output_dir_base)

            # ensures the output directory (if it exists) is empty
            if sync_dir.is_dir():
                shutil.rmtree(sync_dir)

            # creates the sync channel folder and outputs the file
            sync_dir.mkdir(parents=True, exist_ok=True)
            np.save(sync_dir / self.sync_file_name, sync_ch[i_run])

    def save_config(self):

        # retrieves the output data
        config_data = {'Finish': "Me!"}

        # saves the session file
        config_dir = cw.get_def_dir("configs")
        self.save_file('config', config_data, def_dir=config_dir)

    def clear_session(self):

        # if there is a parameter change, then prompt the user if they want to change
        q_str = 'Are you sure you want to clear the current session?'
        u_choice = QMessageBox.question(self.main_obj, 'Clear Session?', q_str, cf.q_yes_no, cf.q_yes)
        if u_choice == cf.q_no:
            # exit if they cancelled
            return

        self.main_obj.session_obj.session = None
        self.main_obj

    def default_dir(self):

        DefaultDir(self.main_obj).show()

    def close_window(self):

        # closes the window
        self.main_obj.can_close = True
        self.main_obj.close()

    # ---------------------------------------------------------------------------
    # Preprocessing Menubar Functions
    # ---------------------------------------------------------------------------

    def run_preproccessing(self):

        self.main_obj.run_preprocessing_dialog()

    def clear_preprocessing(self):

        # prompts the user if they want to clear
        q_str = "Are you sure you want to clear the existing processing?"
        u_choice = QMessageBox.question(self.main_obj, 'Clear Preprocessing?', q_str, cf.q_yes_no, cf.q_yes)
        if u_choice == cf.q_no:
            # exit if the user cancelled
            return

        # resets the channel data fields
        self.main_obj.session_obj.channel_data.is_keep[:] = True
        self.main_obj.session_obj.channel_data.is_selected[:] = False
        self.main_obj.session_obj.clear_preprocessing()

        # resets the preprocessing tab properties
        prep_tab = self.main_obj.info_manager.get_info_tab('preprocess')
        prep_tab.configs.clear()

        # resets the combobox fields
        channel_tab = self.main_obj.info_manager.get_info_tab('channel')
        channel_tab.reset_combobox_fields('data', ["Raw"])
        self.main_obj.info_manager.channel_combobox_update('data', channel_tab)

        # disable menu item
        self.set_menu_enabled('clear_prep', False)

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

    def set_tool_enabled(self, tool_name, state):

        self.get_tool_item(tool_name).setEnabled(state)

    def get_menu_item(self, menu_name):

        return self.menu_bar.findChild((QWidget, QAction, QMenu), name=menu_name)

    def get_tool_item(self, tool_name):

        return self.tool_bar.findChild(QAction, name=tool_name)

    def context_menu_event(self, evnt):

        evnt.ignore()

    def load_file(self, file_info, f_type, dir_only=False, def_dir=None):

        # runs the save file dialog (if file path not given)
        if not isinstance(file_info, str):
            if def_dir is None:
                def_dir = cw.get_def_dir("data")

            f_mode = cw.f_mode[f_type]
            f_suffix = 'Directory' if dir_only else 'File'
            f_title = 'Select {0} {1}'.format(cw.f_name[f_type], f_suffix)

            file_dlg = cw.FileDialogModal(
                None, f_title, f_mode, str(def_dir), is_save=False, dir_only=dir_only,
            )
            if file_dlg.exec() == QDialog.DialogCode.Accepted:
                # if successful, then retrieve the file name
                file_info = file_dlg.selectedFiles()[0]

            else:
                # otherwise, exit the function
                return None

        return file_info

    def save_file(self, f_type, output_data=None, dir_only=False, def_dir=None):

        # sets the default directory path (if not provided)
        if def_dir is None:
            def_dir = cw.get_def_dir("data")

        # runs the save file dialog
        f_mode = None if dir_only else cw.f_mode[f_type]
        f_title = 'Set {0} Output {1}'.format(cw.f_name[f_type], 'Directory' if dir_only else 'File')

        file_dlg = cw.FileDialogModal(None, f_title, f_mode, str(def_dir), is_save=True, dir_only=dir_only)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # saves the session data to file
            file_path = cf.get_selected_file_path(file_dlg, f_mode)

            if output_data is None:
                return Path(file_path)

            else:
                with open(file_path, 'wb') as f:
                    pickle.dump(output_data, f)

        elif output_data is None:
            return None

    def set_menu_enabled_blocks(self, m_type):

        # initialisations
        menu_on, menu_off = [], []
        tool_on, tool_off = [], []

        match m_type:
            case 'init':
                # case is initialising
                tool_off = ['save']
                menu_off = ['save', 'clear', 'preprocessing', 'clear_prep', 'load_trigger', 'load_config']

            case 'session-open':
                # case is post session opening
                tool_on = ['save']
                menu_on = ['save', 'clear', 'preprocessing', 'load_trigger', 'load_config']

            case 'post-process':
                # case is post preprocessing
                menu_on = ['clear_prep']

        # resets the menu enabled properties
        [self.set_menu_enabled(m_on, True) for m_on in menu_on]
        [self.set_menu_enabled(m_off, False) for m_off in menu_off]
        [self.set_tool_enabled(t_on, True) for t_on in tool_on]
        [self.set_tool_enabled(t_off, False) for t_off in tool_off]

    def get_sync_output_dir(self, rr, output_dir_base):

        if output_dir_base is None:
            # case is using the default path
            return rr._sync_output_path / self.sync_folder_name

        else:
            # case is using the custom path
            return output_dir_base / rr._run_name

    def check_custom_sync_dir(self, raw_runs, dir_base):

        # initialisations
        err_str = None

        for i_run, rr in enumerate(raw_runs):
            # retrieves the sync folder name (for the current run)
            sync_dir = self.get_sync_output_dir(rr, dir_base)
            if not sync_dir.is_dir():
                # case is the correct sync folder doesn't exist
                err_str = 'The sync folder structure is invalid (run name incorrect)'
                break

            else:
                # otherwise, determine
                sync_file = glob.glob(str(sync_dir / '*.npy'))
                match len(sync_file):
                    case 0:
                        # case is no matches were made
                        err_str = 'Trigger channel file is missing for Run #{0}'.format(i_run + 1)
                        break

                    case 1:
                        # case is a unique match
                        pass

                    case _:
                        # case is multiple matches
                        err_str = 'Multiple trigger channel files exist for Run #{0}?'.format(i_run + 1)
                        break

        if err_str is None:
            # case is the directory is feasible
            return True

        else:
            # case is the directory is infeasible
            cf.show_error(err_str, 'Invalid Trigger File Directory')
            return False
