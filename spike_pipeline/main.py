# module import
import os
import sys
import time

# custom module import
from testing.testing import Testing

# pyqt6 module import
from PyQt6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QTreeView, QProxyStyle, QStyleFactory, QWidget
from PyQt6.QtCore import QStringListModel, QStringConverter, QAbstractItemModel
from PyQt6.QtGui import QStandardItemModel, QStandardItem

# debugging parameters
is_testing = True
test_type = 3

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

# QTreeView::branch
# {
#     border - image: url(none.png);
# }

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#
#     model = QStandardItemModel()
#     for row in range(5):
#         item = QStandardItem("row {0}".format(row))
#         model.appendRow(item)
#
#         for column in range(4):
#             item_s = QStandardItem("column {0}".format(column))
#             item.appendRow(item_s)
#
#             if row == 1:
#                 for i in range(5):
#                     item_ss = QStandardItem("sub-column {0}".format(i))
#                     item_s.appendRow(item_ss)
#
#     app.setStyle('Windows')
#
#     v = QTreeView()
#     v.setModel(model)
#     v.setStyleSheet(tree_style)
#     v.expandAll()
#     v.setItemsExpandable(False)
#     v.setRootIsDecorated(False)
#     v.setFixedSize(v.sizeHint())
#     v.setHeaderHidden(True)
#
#     v.show()
#
#
#
#     sys.exit(app.exec())

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)

    # app.setStyle('Windows')

    if is_testing:
        # case is running testing mode
        test_obj = Testing(test_type)
        form = test_obj.run_test()
        form.show()

    else:
        # case is running full program
        a = 1

    # Run the main Qt loop
    sys.exit(app.exec())



