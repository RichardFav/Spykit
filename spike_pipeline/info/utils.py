# custom module imports
import spike_pipeline.common.common_func as cf
import spike_pipeline.common.common_widget as cw
import spike_pipeline.plotting.view_type as vt

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QScrollArea, QFormLayout, QStatusBar, QSizePolicy)
from PyQt6.QtCore import QObject, Qt, QSize, QRect, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 15

# ----------------------------------------------------------------------------------------------------------------------

"""
    InfoManager: object that controls the information panels within the central
                 main window information widget
"""


class InfoManager(QWidget):
    # signal functions

    def __init__(self, main_obj, info_width, session_obj=None):
        super(InfoManager, self).__init__()

        # main class fields
        self.main_obj = main_obj
        self.info_width = info_width
        self.session_obj = session_obj

        # boolean class fields
        self.is_updating = False

        # widget layout setup
        self.main_layout = QFormLayout()
        self.scroll_layout = QFormLayout()

        # main widget setup
        self.scroll_area = QScrollArea(self)
        self.scroll_widget = QWidget()
        self.status_bar = QStatusBar()

        # other widget setup
        self.status_lbl = cw.create_text_label(None, 'Waiting for process...', vt.font_lbl, align='left')

        # initialises the class fields
        self.init_class_fields()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the main widget properties
        self.setFixedWidth(self.info_width + x_gap)
        self.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_exp))
        self.setLayout(self.main_layout)

        # sets the widget layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.scroll_area)

        # SCROLL AREA WIDGET SETUP --------------------------------------------

        # sets the scroll area properties
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background-color: rgba(120, 152, 229, 255) ;")
        self.scroll_area.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        self.scroll_area.setWidget(self.scroll_widget)

        # sets the scroll widget layout widget
        self.scroll_widget.setLayout(self.scroll_layout)

        # sets the scroll widget layout properties
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        # creates the text label object
        self.main_layout.addWidget(self.status_lbl)

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def set_styles(self):

        # sets the style sheets
        self.scroll_area.setStyleSheet("background-color: rgba(120, 152, 229, 255) ;")
