# module import
import os
import sys
import logging
import traceback
from datetime import datetime

# spike pipeline imports
import spykit.common.common_widget as cw
from spykit.common.common_func import q_yes_no, q_no

# pyqt6 module import
from PyQt6.QtWidgets import QMessageBox

########################################################################################################################

class ErrorHandler:
    # logger properties
    fmt_str = ('[%(asctime)s]\n\nSession = %(ses_info)s\n\n%(message)s')

    def __init__(self):

        # class field initialisations
        self.main_window = None

        # ensures the log file directory exists
        if not os.path.exists(cw.log_dir):
            os.mkdir(cw.log_dir)

        # resets the error hook
        sys.excepthook = self.error_logger

    def error_logger(self, et, v, tb):

        # Log the complete error message along with its traceback stack
        logger = self.create_logger()
        logger.error(
            "",
            exc_info=(et, v, tb),
            extra={"ses_info": self.get_session_info()}
        )

        # closes the logger file
        self.close_logger(logger)

        # prompts the user if they want to continue
        e_str = (f'The following error has occurred:\n\n '
                 f' * Error Type: {et.__name__}\n '
                 f' * Error Message: {v}\n\nDo you still want to continue?')
        u_choice = QMessageBox.question(None, 'Program Error', e_str, q_yes_no)
        if u_choice == q_no:
            # closes the window
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

    def get_session_info(self):

        if self.main_window.session_obj.session is None:
            return "No Session Loaded"

        else:
            session = self.main_window.session_obj.session
            s_props = session.get_session_props()

            return 'Moo'

    def get_log_file_name(self):

        now = datetime.now()
        date_str = now.strftime("%Y_%m_%d_%H_%M_%S")

        return os.path.join(cw.log_dir, f"error ({date_str}).log")

    def set_main_window(self, main_window):

        # input arguments
        self.main_window = main_window

    @staticmethod
    def close_logger(logger):

        handler = logger.handlers[0]
        handler.close()
        logger.removeHandler(handler)

    @staticmethod
    def setup_error_msg(et, v, tb):

        return ''.join(traceback.format_exception(et, v, tb)).replace('\\', '/')