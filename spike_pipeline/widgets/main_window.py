# module import
# import os
# import functools
import numpy as np
# import pyqtgraph as pg

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget,
                             QScrollArea, QSizePolicy, QStatusBar, QMenuBar, QToolBar)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QIcon, QAction

# custom module import
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.info.utils import InfoManager
from spike_pipeline.plotting.utils import PlotManager
from spike_pipeline.common.property_classes import SessionWorkBook
from spike_pipeline.widgets.open_session import OpenSession

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

# MAIN WINDOW WIDGET ---------------------------------------------------------------------------------------------------

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
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        # session workbook object
        self.session_obj = SessionWorkBook()

        # sets up the menu bar items
        self.menu_bar = MenuBar(self)

        # sets up the information/plot manager widgets
        self.info_manager = InfoManager(self, info_width, self.session_obj)
        self.plot_manager = PlotManager(self, dlg_width - info_width, self.session_obj)

        # boolean class fields
        self.has_session = False

        # sets up the main window widgets
        self.setup_main_window()
        self.init_class_fields()

        # # REMOVE ME LATER
        # self.testing()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_main_window(self):

        # creates the dialog window
        self.setWindowTitle("Spike Interface Pipeline")
        self.setMinimumSize(min_width, min_height)
        self.resize(dlg_width, dlg_height)

    def init_class_fields(self):

        # plot parameter widget setup
        self.main_layout.addWidget(self.info_manager)
        self.main_layout.addWidget(self.plot_manager)

        # connects workbook signal functions
        self.session_obj.session_change.connect(self.new_session)

    # ---------------------------------------------------------------------------
    # Signal Slot Functions
    # ---------------------------------------------------------------------------

    def new_session(self):

        # if there is a session already loaded, then clear the main window
        if self.has_session:
            a = 1

        # enables the menubar items
        self.menu_bar.set_menu_enabled('save', True)

        # sets up the trace/probe views
        self.plot_manager.get_plot_view('trace')
        self.plot_manager.get_plot_view('probe')

        # resets the plot view to include only the trace/probe views
        i_plot_trace = self.plot_manager.get_plot_index('trace')
        i_plot_probe = self.plot_manager.get_plot_index('probe')
        c_id = np.array([[i_plot_trace, i_plot_trace, i_plot_probe]])
        self.plot_manager.update_plot_config(c_id)

        # resets the session flag
        self.has_session = True

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def testing(self):

        # INFORMATION MANAGER TESTING



        # PLOT MANAGER TESTING

        # adds the plot views
        self.plot_manager.add_plot_view('trace')
        self.plot_manager.add_plot_view('probe')

        # test
        c_id = np.array([[1, 1, 2], [1, 1, 2]])
        self.plot_manager.main_layout.updateID(c_id)

# MENUBAR WIDGET -------------------------------------------------------------------------------------------------------

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
        """

        :return:
        """

        # adds the menubar to the main window
        self.menu_bar = QMenuBar(self.main_obj)
        self.main_obj.setMenuBar(self.menu_bar)

        # parent menu widgets
        h_menu_file = self.menu_bar.addMenu('File')

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

        # ---------------------------------------------------------------------------
        # File Menubar Event Functions
        # ---------------------------------------------------------------------------

        # initialisations
        p_str = ['open', 'save', None, 'close']
        p_lbl = ['Open Session', 'Save Session', None, 'Close Window']
        cb_fcn = [self.open_session, self.save_session, None, self.close_window]

        # menu/toolbar item creation
        for pl, ps, cbf in zip(p_lbl, p_str, cb_fcn):
            if ps is None:
                # adds separators
                self.tool_bar.addSeparator()
                h_menu_file.addSeparator()

            else:
                # creates the menu item
                h_tool = QAction(QIcon(cw.icon_path[ps]), pl, self)
                h_tool.triggered.connect(cbf)
                h_tool.setObjectName(ps)
                self.tool_bar.addAction(h_tool)

                # creates the menu item
                h_menu = QAction(pl, self)
                h_menu.setObjectName(ps)
                h_menu.triggered.connect(cbf)
                h_menu_file.addAction(h_menu)

        # disables the required menu items
        [self.set_menu_enabled(x, False) for x in self.disabled_list]

    # ---------------------------------------------------------------------------
    # File Menubar Functions
    # ---------------------------------------------------------------------------

    def open_session(self):

        self.main_obj.setVisible(False)
        OpenSession(self.main_obj, self.main_obj.session_obj)

    def save_session(self):

        pass

    def close_window(self):

        # closes the window
        self.main_obj.close()

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_menu_enabled(self, menu_name, state):

        h_menu_new = self.get_menu_item(menu_name)
        [x.setEnabled(state) for x in h_menu_new]

    def get_menu_item(self, menu_name):

        return self.findChildren(QAction, name=menu_name)
