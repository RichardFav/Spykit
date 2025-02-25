# module import
import os
import functools
import numpy as np
import pyqtgraph as pg

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget,
                             QScrollArea, QSizePolicy, QStatusBar, QMenuBar, QDockWidget)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QIcon, QAction

# custom module import
import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.common_func as cf
from spike_pipeline.plotting.utils import PlotManager
from spike_pipeline.info.utils import InfoManager
from spike_pipeline.common.property_classes import SessionWorkBook
from spike_pipeline.widgets.open_session import OpenSession

# widget dimensions
x_gap = 15
info_width = 250

# object dimensions
dlg_width = 1650
dlg_height = 900
min_width = 800
min_height = 450

# font objects
font_lbl = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold)
font_hdr = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

# MAIN WINDOW WIDGET ---------------------------------------------------------------------------------------------------


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

        # sets up the information/plot manager widgets
        self.info_manager = InfoManager(self, info_width, self.session_obj)
        self.plot_manager = PlotManager(self, dlg_width - info_width, self.session_obj)

        # boolean class fields
        self.has_session = False

        # sets up the main window widgets
        self.setup_main_window()
        self.init_class_fields()

        # REMOVE ME LATER
        self.testing()

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

        # sets up the menu bar items
        self.setMenuBar(MenuBar(self))

    # ---------------------------------------------------------------------------
    # Signal Slot Functions
    # ---------------------------------------------------------------------------

    def new_session(self):

        # if there is a session already loaded, then clear the main window
        if self.has_session:
            a = 1

        #


        # resets the session flag
        self.has_session = True

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def testing(self):

        # adds the plot views
        self.plot_manager.add_plot_view('trace')
        self.plot_manager.add_plot_view('probe')

        # test
        c_id = np.array([[1, 1, 2],[1, 1, 2]])
        self.plot_manager.main_layout.updateID(c_id)

# MENUBAR WIDGET -------------------------------------------------------------------------------------------------------


class MenuBar(QMenuBar):
    def __init__(self, main_obj):
        super(MenuBar, self).__init__()

        # field retrieval
        self.main_obj = main_obj

        # initialises the class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):
        """

        :return:
        """

        # parent menu widgets
        h_menu_file = self.addMenu('File')

        # FILE MENU ITEMS -----------------------------------------------------------------------------

        # initialisations
        p_str = ['open_session', None, 'close']
        p_lbl = ['Open Session', None, 'Close Window']
        cb_fcn = [self.open_session, None, self.close_window]

        # menu/toolbar item creation
        for pl, ps, cbf in zip(p_lbl, p_str, cb_fcn):
            if ps is None:
                # adds separators
                h_menu_file.addSeparator()

            else:
                # creates the menu item
                h_menu = QAction(pl, self)
                h_menu.triggered.connect(cbf)
                h_menu_file.addAction(h_menu)

    # ---------------------------------------------------------------------------
    # File Menubar Functions
    # ---------------------------------------------------------------------------

    def open_session(self):

        self.main_obj.setVisible(False)
        OpenSession(self.main_obj)

    def close_window(self):

        # closes the window
        self.main_obj.close()
