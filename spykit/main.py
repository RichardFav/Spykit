# module import
import os
import sys
import time

# custom module import
from testing.testing import Testing
from spykit.common.common_func import q_yes_no
from spykit.widgets.main_window import MainWindow

# pyqt6 module import
from PyQt6.QtWidgets import (QApplication, QTreeWidget, QTreeWidgetItem, QTreeView, QProxyStyle, QStyleFactory,
                             QWidget, QMessageBox)
from PyQt6.QtGui import QFont

# debugging parameters
is_testing = False
test_type = 15

########################################################################################################################

def error_logger(exctype, value, traceback):

    e_str = (f'The following error has occurred:\n\n '
             f' * Error Type: {exctype.__name__}\n '
             f' * Error Message: {value}\n\nDo you still want to continue?')
    u_choice = QMessageBox.question(None, 'Program Error', e_str, q_yes_no)

    if u_choice == 'No':
        # quit program here?
        pass

# Assign the handler to the system hook
sys.excepthook = error_logger

########################################################################################################################

if __name__ == '__main__':

    app = QApplication(sys.argv)

    if is_testing:
        # case is running testing mode
        test_obj = Testing(test_type)
        h_app = test_obj.run_test()

    else:
        # case is running full program
        h_app = MainWindow()

    # Run the main Qt loop
    h_app.show()
    sys.exit(app.exec())
