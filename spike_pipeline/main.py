# module import
import os
import sys
import time

#
from PyQt6.QtWidgets import QApplication
from testing.testing import Testing
from importlib import reload

# debugging parameters
is_testing = True
test_type = 2

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)

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

# import sys
# from PyQt5.QtWidgets import QVBoxLayout, QLabel, QDesktopWidget, QWidget, QApplication
# from PyQt5.QtCore import Qt
#
#
# class SpecialBG(QLabel):
#     def __init__(self, parent):
#         QLabel.__init__(self, parent)
#         # mess with border-radius, thatDarklordGuy!
#         self.setStyleSheet("""
#                 color: rgba(237,174,28,100%);
#                 background-color: rgba(0,0,0,100%);
#                 text-align: center;
#                 border-radius: 50px;
#                 border: 1px solid rgba(237,174,28,100%);
#                 padding: 0px;
#                 """)
#
#
# class SimpleRoundedCorners(QWidget):
#     def __init__(self):
#         super(SimpleRoundedCorners, self).__init__()
#         self.initUI()
#
#     def initUI(self):
#         winwidth = 320
#         winheight = 320
#         VBox = QVBoxLayout()
#         roundyround = SpecialBG(self)
#         VBox.addWidget(roundyround)
#         self.setLayout(VBox)
#         # transparency cannot be set for window BG in style sheets, so...
#         # self.setWindowOpacity(0.5)
#         self.setWindowFlags(
#             Qt.FramelessWindowHint  # hides the window controls
#             | Qt.WindowStaysOnTopHint  # forces window to top... maybe
#             | Qt.SplashScreen  # this one hides it from the task bar!
#         )
#         # alternative way of making base window transparent
#         self.setAttribute(Qt.WA_TranslucentBackground, True)  # 100% transparent
#
#         self.setGeometry(0, 0, winwidth, winheight)
#         self.setWindowTitle('Simple Rounded Corners')
#         self.show()
#
#
# def main():
#     app = QApplication(sys.argv)
#     alldone = SimpleRoundedCorners()
#     sys.exit(app.exec_())
#
#
# if __name__ == '__main__':
#     main()