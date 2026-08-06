# module import
import os
import sys
import logging
import traceback
from datetime import datetime

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw

# pyqt6 module import
from PyQt6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, QDialog, QFrame, QPlainTextEdit

# ----------------------------------------------------------------------------------------------------------------------

"""
    ErrorHandlerDlg:
"""

class ErrorHandlerDlg(QDialog):
    # widget dimensions
    x_gap = 5
    dlg_width = 500
    dlg_height = 250
    hght_button_frame = 40

    # array class fields
    but_str = ['Continue Spykit', 'Close Spykit']
    err_lbl = [
        'There following error has been detected within Spykit:',
        'Do you still want to continue running Spykit?'
    ]

    # widget styles
    list_style = "border: 1px solid black; color: red;"
    frame_style = QFrame.Shape.Box | QFrame.Shadow.Plain

    def __init__(self, parent=None):
        super(ErrorHandlerDlg, self).__init__(parent)

        # class layouts
        self.main_layout = QVBoxLayout()
        self.error_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        # class widgets
        self.error_frame = QFrame(self)
        self.button_frame = QFrame(self)
        self.err_list = QPlainTextEdit()

        # initialises the class objects
        self.init_class_fields()
        self.init_error_frame()
        self.init_button_frame()

    def init_class_fields(self):

        # sets the dialog window properties
        self.setFixedSize(self.dlg_width, self.dlg_height)
        self.setWindowTitle('Unexpected Program Error')
        self.setLayout(self.main_layout)
        self.main_layout.setSpacing(self.x_gap)

        # adds the frames to the main widget
        self.main_layout.addWidget(self.error_frame)
        self.main_layout.addWidget(self.button_frame)

    def init_error_frame(self):

        # sets the error frame properties
        self.error_frame.setLayout(self.error_layout)
        self.error_frame.setFrameStyle(self.frame_style)
        self.error_frame.setLineWidth(1)

        # list widget properties
        self.err_list.setStyleSheet(self.list_style)
        self.err_list.setReadOnly(True)

        # creates the text labels
        h_lbl_top = cw.create_text_label(None, self.err_lbl[0], font=cw.font_lbl, align='left')
        h_lbl_bot = cw.create_text_label(None, self.err_lbl[1], font=cw.font_lbl, align='left')

        # adds the widgets to the error layout
        self.error_layout.addWidget(h_lbl_top)
        self.error_layout.addWidget(self.err_list)
        self.error_layout.addWidget(h_lbl_bot)

    def init_button_frame(self):

        # initialisations
        cb_fcn = [self.cont_spykit, self.close_spykit]

        # sets the button frame properties
        self.button_frame.setLayout(self.button_layout)
        self.button_frame.setFixedHeight(self.hght_button_frame)
        self.button_frame.setFrameStyle(self.frame_style)
        self.button_frame.setLineWidth(1)

        # button group layout properties
        self.button_layout.setSpacing(0)
        self.button_layout.setContentsMargins(self.x_gap, self.x_gap, self.x_gap, self.x_gap)

        for bs, cb in zip(self.but_str, cb_fcn):
            # creates the control button widgets
            obj_but = cw.create_push_button(None, bs, cw.font_lbl)
            obj_but.setFixedHeight(self.hght_button_frame - 2 * self.x_gap)
            self.button_layout.addWidget(obj_but)

            # sets the slot function
            obj_but.clicked.connect(cb)

    def set_error_message(self, err_msg):

        self.err_list.setPlainText(err_msg)

    def cont_spykit(self):

        self.accept()

    def close_spykit(self):

        self.reject()

# ----------------------------------------------------------------------------------------------------------------------

"""
    ErrorHandler:
"""

class ErrorHandler:
    # logger properties
    break_str = '*' * 100
    fmt_str = ('[%(asctime)s]\n\n%(message)s\n%(ses_info)s')

    def __init__(self):

        # class field initialisations
        self.main_window = None

        # creates the error handler dialog
        self.err_dlg = ErrorHandlerDlg()

        # ensures the log file directory exists
        if not os.path.exists(cw.log_dir):
            os.mkdir(cw.log_dir)

        # resets the error hook
        sys.excepthook = self.error_logger

    def error_logger(self, et, v, tb):

        err_msg = self.setup_error_msg(et, v, tb)

        # Log the complete error message along with its traceback stack
        logger = self.create_logger()
        logger.error(
            f"{self.break_str}\n\n{err_msg}",
            extra={"ses_info": self.get_session_info()},
        )

        # closes the logger file
        self.close_logger(logger)

        # displays the error message to screen
        self.err_dlg.set_error_message(err_msg)
        if self.err_dlg.exec() == QDialog.DialogCode.Rejected:
            # closes the program if prompted
            self.main_window.can_close = True
            self.main_window.close()

    def create_logger(self):

        # creates error logger
        logger = logging.getLogger('error_logger')
        logger.setLevel(logging.ERROR)

        # creates file handler
        f_handler = logging.FileHandler(self.get_log_file_name())

        # creates formatter and adds to handler
        formatter = logging.Formatter(self.fmt_str)
        f_handler.setFormatter(formatter)
        logger.addHandler(f_handler)

        return logger

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_log_file_name(self):

        now = datetime.now()
        date_str = now.strftime("%Y_%m_%d_%H_%M_%S")

        return os.path.join(cw.log_dir, f"error_log ({date_str}).log")

    def get_session_info(self):

        if self.main_window.session_obj.session is None:
            # case is no session is loaded
            ses_info = "No Session Loaded\n"

        else:
            # sets up the session information object
            s_info = cf.SessionInfo(self.main_window.session_obj)
            ses_info = s_info.get_full_session_info()

        return f"{self.break_str}\n\n{ses_info}\n{self.break_str}"

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def set_main_window(self, main_window):

        # input arguments
        self.main_window = main_window

    @staticmethod
    def close_logger(logger):

        handler = logger.handlers[0]
        handler.close()
        logger.removeHandler(handler)

    # ---------------------------------------------------------------------------
    # String Setup Functions
    # ---------------------------------------------------------------------------

    @staticmethod
    def setup_error_msg(et, v, tb):

        return ''.join(traceback.format_exception(et, v, tb)).replace('\\', '/')