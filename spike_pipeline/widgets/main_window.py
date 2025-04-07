# module import
# import os
# import functools
import os
import pickle
import numpy as np
import pyqtgraph as pg
from functools import partial as pfcn

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget, QGridLayout,
                             QScrollArea, QMessageBox, QDialog, QMenuBar, QToolBar, QMenu)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon, QAction

# custom module import
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.info.utils import InfoManager
from spike_pipeline.plotting.utils import PlotManager
from spike_pipeline.props.utils import PropManager
from spike_pipeline.props.general import GeneralPara
from spike_pipeline.props.trigger import TriggerPara
from spike_pipeline.common.property_classes import SessionWorkBook
from spike_pipeline.widgets.open_session import OpenSession
from spike_pipeline.info.preprocess import PreprocessSetup, prep_task_map
from spike_pipeline.threads.utils import ThreadWorker

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
        self.session_obj.bad_channel_change.connect(self.bad_channel_change)
        self.session_obj.sync_channel_change.connect(self.sync_channel_change)
        self.session_obj.keep_channel_reset.connect(self.keep_channel_reset)
        self.session_obj.worker_job_started.connect(self.worker_job_started)
        self.session_obj.worker_job_finished.connect(self.worker_job_finished)

    # ---------------------------------------------------------------------------
    # Calculation Signal Slot Functions
    # ---------------------------------------------------------------------------

    def new_session(self):

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
        channel_tab.update_channel_status(ch_status[0][1], self.session_obj.get_keep_channels())

        # resets the status button toggle value (if pressed)
        status_tab = self.info_manager.get_info_tab('status')
        if status_tab.toggle_calc.isChecked():
            status_tab.toggle_calc.setChecked(False)
            status_tab.toggle_calc.setText(status_tab.b_str[0])

        # updates the probe-view
        probe_view = self.plot_manager.get_plot_view('probe')
        probe_view.reset_out_line(ch_status[0][1])
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

    # ---------------------------------------------------------------------------
    # Preprocessing Functions
    # ---------------------------------------------------------------------------

    def run_preproccessing(self, prep_obj):

        # starts the job worker
        self.worker_job_started('preprocess')

        # runs the session pre-processing
        prep_tab = self.info_manager.get_info_tab('preprocess')
        if isinstance(prep_obj, list):
            # case is running from the Preprocessing dialog
            pp_config = prep_tab.setup_config_dict(prep_obj)

        else:
            # case is running from loading session
            pp_config = prep_obj.setup_config_dicts()

        # runs the preprocessing
        self.session_obj.session.run_preprocessing(pp_config)

        # resets the preprocessing data type combobox
        pp_data_flds = self.session_obj.get_current_prep_data_names()

        # updates the channel data types
        channel_tab = self.info_manager.get_info_tab('channel')
        channel_tab.reset_data_types(['Raw'] + prep_tab.configs.task_name, pp_data_flds)

        # updates the trace views
        self.plot_manager.reset_trace_views()

    def setup_preprocessing_worker(self, prep_task, delay_start=False):

        t_worker = ThreadWorker(self.run_preprocessing_worker, prep_task)
        t_worker.work_finished.connect(self.preprocessing_complete)

        if delay_start:
            QTimer.singleShot(20, pfcn(self.start_timer, t_worker))

        else:
            t_worker.start()

    @staticmethod
    def start_timer(t_worker):

        t_worker.start()

    def run_preprocessing_worker(self, prep_task):

        self.run_preproccessing(prep_task)

    def preprocessing_complete(self):

        self.worker_job_finished('preprocess')

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

        # f_file = 'C:/Work/Other Projects/EPhys Project/Data/z - session_files/test_tiny.ssf'
        f_file = 'C:/Work/Other Projects/EPhys Project/Data/z - session_files/test_large.ssf'
        # f_file = 'C:/Work/Other Projects/EPhys Project/Data/z - session_files/test_large (preprocessed).ssf'

        self.menu_bar.load_session(f_file)


# ----------------------------------------------------------------------------------------------------------------------

"""
    MenuBar: class object that controls the main window menu/toolbars
"""


class MenuBar(QObject):
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
        self.set_menu_enabled_blocks('init')

    def add_main_menu_item(self, label):

        h_menu = self.menu_bar.addMenu(label)
        h_menu.setObjectName(label.lower())

        return h_menu

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
        self.main_obj.session_obj.reset_channel_data(channel_data)

        # sets/runs the config field/routines
        if ses_data['configs'] is not None:
            #
            prep_info = self.main_obj.info_manager.get_info_tab('preprocess')
            prep_info.configs = ses_data['configs']

            # runs the preprocessing (if data in config field)
            if len(prep_info.configs.prep_task):
                self.main_obj.setup_preprocessing_worker(prep_info.configs, True)

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

    def clear_session(self):

        # if there is a parameter change, then prompt the user if they want to change
        q_str = 'Are you sure you want to clear the current session?'
        u_choice = QMessageBox.question(self.main_obj, 'Clear Session?', q_str, cf.q_yes_no, cf.q_yes)
        if u_choice == cf.q_no:
            # exit if they cancelled
            return

        self.main_obj.session_obj.session = None

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
            }
        }

        # saves the session file
        self.save_file('session', session_data)

    def save_trigger(self):

        # prompts the user if they want to use the default output path
        q_str = 'Do you want to use the default trigger channel output path?'
        u_choice = QMessageBox.question(self.main_obj, 'Use Default Path?', q_str, cf.q_yes_no_cancel, cf.q_yes)
        if u_choice == cf.q_cancel:
            # exit if the user cancelled
            return

        elif u_choice == cf.q_no:
            # otherwise, prompt the user for the base file name
            trig_file = self.save_file('trigger')
            if trig_file is None:
                return

        # silences the required sections of the trigger channel
        s_freq = self.main_obj.session_obj.session_props.s_freq
        trig_props = self.main_obj.prop_manager.get_prop_tab('trigger')
        for i_run, r_lim in enumerate(trig_props.p_props.region_index):
            # sets up the silencing regions
            s_lim = []
            for i_reg in range(r_lim.shape[0]):
                ind_s = int(np.floor(r_lim[i_reg, 1] * s_freq))
                ind_f = int(np.ceil(r_lim[i_reg, 2] * s_freq))
                s_lim.append((ind_s, ind_f))

            # silences the trigger channel
            self.main_obj.session_obj.session._s.silence_sync_channel(i_run, s_lim)

        # outputs the trigger channel to file
        if cf.q_yes:
            # case is saving to the default location
            self.main_obj.session_obj.session._s.save_sync_channel(True)

        else:
            # saves the session file
            pass


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

        return self.menu_bar.findChild((QWidget, QAction, QMenu), name=menu_name)

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

    def save_file(self, f_type, output_data=None):

        # runs the save file dialog
        f_title = 'Select {0} File'.format(cw.f_name[f_type])
        file_dlg = cw.FileDialogModal(None, f_title, cw.f_mode[f_type], cw.data_dir, is_save=True)
        if file_dlg.exec() == QDialog.DialogCode.Accepted:
            # saves the session data to file
            file_info = file_dlg.selectedFiles()

            if output_data is None:
                return file_info[0]

            else:
                with open(file_info[0], 'wb') as f:
                    pickle.dump(output_data, f)

        elif output_data is None:
            return None

    def set_menu_enabled_blocks(self, m_type):

        # initialisations
        menu_on, menu_off = [], []

        match m_type:
            case 'init':
                # case is initialising
                menu_off = ['save', 'clear', 'preprocessing']

            case 'session-open':
                # case is post session opening
                menu_on = ['save', 'clear', 'preprocessing']

        # resets the menu enabled properties
        [self.set_menu_enabled(m_on, True) for m_on in menu_on]
        [self.set_menu_enabled(m_off, False) for m_off in menu_off]
