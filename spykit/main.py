# module import
import os
import sys
import time

# custom module import
from testing.testing import Testing
from spykit.widgets.main_window import MainWindow

# pyqt6 module import
from PyQt6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QTreeView, QProxyStyle, QStyleFactory, QWidget
# from PyQt6.QtCore import QStringListModel, QStringConverter, QAbstractItemModel
# from PyQt6.QtGui import QStandardItemModel, QStandardItem

# debugging parameters
is_testing = False
test_type = 7

data = {"Project A": ["file_a.py", "file_a.txt", "something.xls"],
        "Project B": ["file_b.csv", "photo.jpg"],
        "Project C": []}

# widget stylesheets
tree_style = """
    QTreeView {
        font: Arial 10px;
    }
    QTreeView::branch:open:has-children:has-siblings {
        
    }        
"""

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
