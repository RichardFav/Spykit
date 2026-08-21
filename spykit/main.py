# module import
import os
import sys
import time
import threading

# sets the qt API environmental variable
os.environ['QT_API'] = 'pyqt6'

# custom module import
from testing.testing import Testing
from spykit.widgets.main_window import MainWindow
from spykit.common.error_logging import ErrorHandler

# pyqt6 module import
from PyQt6.QtWidgets import (QApplication, QTreeWidget, QTreeWidgetItem, QTreeView, QProxyStyle, QStyleFactory, QWidget)
from PyQt6.QtGui import QFont

########################################################################################################################

# debugging parameters
is_testing = False
test_type = 15

########################################################################################################################

class SafeApplication(QApplication):
    def notify(self, receiver, event):
        try:
            return super().notify(receiver, event)
        except:
            sys.excepthook(*sys.exc_info())
            return False

    def excepthook(self, exc_type, exc_value, exc_traceback):
        custom_excepthook(exc_type, exc_value, exc_traceback)

########################################################################################################################

if __name__ == '__main__':

    # application/error handle setup
    app = QApplication(sys.argv)

    if is_testing:
        # case is running testing mode
        test_obj = Testing(test_type)
        h_app = test_obj.run_test()

    else:
        # case is running full program
        h_app = MainWindow(ErrorHandler())

    # Run the main Qt loop
    h_app.show()
    sys.exit(app.exec())
