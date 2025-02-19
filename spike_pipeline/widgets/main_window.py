# module import
import os
import functools
import numpy as np
import pyqtgraph as pg

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget,
                             QScrollArea, QSizePolicy, QStatusBar, QMenuBar)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QAction

# custom module import
import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.common_func as cf
from spike_pipeline.widgets.open_session import OpenSession

# widget dimensions
x_gap = 15
grp_width = 250

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

        # field initialisation


        # sets up the main layout
        self.central_widget = QWidget()
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        # sets up the information/display panel widgets
        self.obj_info = InfoPanel(self)
        self.obj_disp = DisplayPanel(self)

        # sets up the main window widgets
        self.setup_main_window()
        self.init_class_fields()

    # CLASS INITIALISATION FUNCTIONS -----------------------------------

    def setup_main_window(self):

        # creates the dialog window
        self.setWindowTitle("Spike Interface Pipeline")
        self.setMinimumSize(min_width, min_height)
        self.resize(dlg_width, dlg_height)

    def init_class_fields(self):

        # plot parameter widget setup
        self.main_layout.addWidget(self.obj_info)
        self.main_layout.addWidget(self.obj_disp)

        # sets up the menu bar items
        self.setMenuBar(MenuBar(self))

# INFORMATION PANEL WIDGET ---------------------------------------------------------------------------------------------


class InfoPanel(QWidget):
    def __init__(self, parent=None):
        super(InfoPanel, self).__init__(parent)

        # boolean class fields
        self.is_updating = False

        # field initialisation
        self.h_main = cf.get_parent_widget(self, MainWindow)

        # widget setup
        self.main_layout = QFormLayout()
        self.h_scroll = QScrollArea(self)
        self.h_widget_scroll = QWidget()
        self.scroll_layout = QFormLayout()
        self.status_bar = QStatusBar()

        # initialises the class fields
        self.init_class_fields()

    # CLASS INITIALISATION FUNCTIONS ------------------------------------------

    def init_class_fields(self):

        # # initialises the parameter information fields
        # self.setup_para_info_fields()

        # sets the main widget properties
        self.setFixedWidth(grp_width + x_gap)
        self.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_exp))
        self.setLayout(self.main_layout)

        # sets the widget layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.h_scroll)

        # SCROLL AREA WIDGET SETUP --------------------------------------------

        # sets the scroll area properties
        self.h_scroll.setWidgetResizable(True)
        self.h_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.h_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.h_scroll.setStyleSheet("background-color: rgba(120, 152, 229, 255) ;")
        self.h_scroll.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        self.h_scroll.setWidget(self.h_widget_scroll)

        # sets the scroll widget layout widget
        self.h_widget_scroll.setLayout(self.scroll_layout)

        # sets the scroll widget layout properties
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        # creates the text label object
        self.h_status = cw.create_text_label(None, 'Waiting for process...', font_lbl, align='left')
        self.main_layout.addWidget(self.h_status)

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def set_styles(self):

        # sets the style sheets
        self.h_scroll.setStyleSheet("background-color: rgba(120, 152, 229, 255) ;")


# DISPLAY PANEL WIDGET -------------------------------------------------------------------------------------------------


class DisplayPanel(QWidget):
    def __init__(self, parent=None):
        super(DisplayPanel, self).__init__(parent)

        # field initialisation
        self.h_main = cf.get_parent_widget(self, MainWindow)

        # widget setup
        self.main_layout = QHBoxLayout(self)
        self.bg_widget = QWidget()

        # initialises the class fields
        self.init_class_fields()

    # CLASS INITIALISATION FUNCTIONS -----------------------------------

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


# MENUBAR WIDGET -------------------------------------------------------------------------------------------------------

class MenuBar(QMenuBar):
    def __init__(self, parent=None):
        super(MenuBar, self).__init__(parent)

        # field retrieval
        self.h_main = cf.get_parent_widget(self, MainWindow)

        # initialises the class fields
        self.init_class_fields()

    def init_class_fields(self):
        """

        :return:
        """

        # parent menu widgets
        h_menu_file = self.addMenu('File')

        # FILE MENU ITEMS -----------------------------------------------------------------------------

        # initialisations
        p_str = ['test', None, 'close']
        p_lbl = ['Testing', None, 'Close Window']
        cb_fcn = [self.menu_testing, None, self.close_window]

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

    def menu_testing(self):

        self.h_main.setVisible(False)
        OpenSession(self.h_main)

    def close_window(self):

        # closes the window
        self.h_main.close()
