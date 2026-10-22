# module import
import re
import numpy as np

# spykit module imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw

# pyqt6 module import
from PyQt6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QApplication,
                             QSizePolicy, QPushButton, QDialog, QListWidget, QGroupBox, QPlainTextEdit)
from PyQt6.QtGui import QFontMetrics

# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeSortErrorDialog: dialog window for for loading saved preprocessed data
"""

class SpikeSortErrorDialog(QDialog):
    # pyqtsignal functions

    # widget dimensions
    x_gap = 5
    width_dlg_max = 1200
    width_dlg_default = 800
    hght_trace_listbox = 400
    hght_except_edit = 150
    hght_button_frame = 40

    # string fields
    pat = r"Error: "

    # font objects
    txt_font = cw.create_font_obj(size=9)

    # widget stylesheets
    border_style = "border: 1px solid;"
    frame_style = QFrame.Shape.Box | QFrame.Shadow.Plain
    frame_border_style = """
        QFrame#loadFrame {
            border: 1px solid;
        }
    """

    def __init__(self, err_info):
        super(SpikeSortErrorDialog, self).__init__(None)

        # input arguments
        self.err_info = err_info

        # class layouts
        self.main_layout = QVBoxLayout()
        self.trace_layout = QVBoxLayout()
        self.except_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        # container class widgets
        self.trace_group = QGroupBox("Traceback Error")
        self.except_group = QGroupBox("Exception Error")
        self.button_frame = QFrame(self)

        # other class widgets
        self.trace_list = QListWidget()
        self.except_edit = QPlainTextEdit()

        # other class fields
        self.msg_trace = None
        self.msg_except = None

        # initialises the class fields/objects
        self.init_class_fields()
        self.init_traceback_group()
        self.init_exeception_group()
        self.init_cont_buttons()

        #
        self.setFixedHeight(self.sizeHint().height())

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # sets the dialog window properties
        self.setWindowTitle('Spike Sorting Calculation Error')
        self.setLayout(self.main_layout)
        self.main_layout.setSpacing(self.x_gap)
        self.setModal(True)

        # resets the frame object names
        for qf in self.findChildren(QFrame):
            qf.setObjectName('sortFrame')

        # determines the error string row
        msg_lines = self.err_info['exe_msg'].split('\n')
        i_row = next((i for i, ml in enumerate(msg_lines) if
                      (re.search(self.pat, ml) is not None)), None)

        # sets the traceback/exception error lines
        if i_row is None:
            # case is there is no traceback message
            self.msg_except = msg_lines
            width_dlg = self.width_dlg_default

        else:
            # case is there is a traceback message
            self.msg_trace = msg_lines[:i_row]
            self.msg_except = msg_lines[i_row:]

            # calculates the dialog width
            f_metrics = QFontMetrics(self.txt_font)
            width_txt = [f_metrics.horizontalAdvance(msg_tb) for msg_tb in self.msg_trace]
            width_dlg = np.min([np.max(width_txt) + 2 * self.x_gap, self.width_dlg_max])

        # sets the dialog width
        self.setFixedWidth(width_dlg)

    def init_traceback_group(self):

        # creates the groupbox object
        self.trace_group.setLayout(self.trace_layout)
        self.trace_group.setFixedHeight(self.hght_trace_listbox)
        self.trace_group.setFont(cw.font_panel)
        self.main_layout.addWidget(self.trace_group)

        # sets the button frame properties
        self.trace_group.setLayout(self.button_layout)
        self.trace_group.setStyleSheet(self.frame_border_style)

        # sets the tracback error listbox properties
        self.trace_layout.addWidget(self.trace_list)
        self.trace_list.setFont(cw.create_font_obj(size=9))
        self.trace_list.setStyleSheet(self.border_style)

        # sets the traceback error message
        if self.msg_trace is not None:
            for msg_tb in self.msg_trace:
                self.trace_list.addItem(msg_tb)

    def init_exeception_group(self):

        # creates the groupbox object
        self.except_group.setLayout(self.except_layout)
        self.except_group.setFixedHeight(self.hght_except_edit)
        self.except_group.setFont(cw.font_panel)
        self.main_layout.addWidget(self.except_group)

        # sets the button frame properties
        self.except_group.setLayout(self.button_layout)
        self.except_group.setStyleSheet(self.frame_border_style)

        # sets the tracback error listbox properties
        self.except_layout.addWidget(self.except_edit)
        self.except_edit.setFont(cw.create_font_obj(size=9))
        self.except_edit.setStyleSheet(self.border_style)

        # sets the traceback error message
        if self.msg_except is not None:
            msg_ex = '\n'.join(self.msg_except)
            self.except_edit.setPlainText(msg_ex)

    def init_cont_buttons(self):

        # creates the button group frame
        self.main_layout.addWidget(self.button_frame)

        # sets the button frame properties
        self.button_frame.setContentsMargins(self.x_gap, self.x_gap, self.x_gap, self.x_gap)
        self.button_frame.setLayout(self.button_layout)
        self.button_frame.setStyleSheet(self.frame_border_style)

        # button group layout properties
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(self.x_gap)

        # creates the control button widgets
        obj_but = cw.create_push_button(None, 'Close Window', cw.font_lbl)
        self.button_layout.addWidget(obj_but)

        # sets the button properties
        obj_but.pressed.connect(self.close_window_click)
        obj_but.setFixedHeight(cf.but_height)
        obj_but.setStyleSheet(self.border_style)

    # ---------------------------------------------------------------------------
    # Class Widget Event Functions
    # ---------------------------------------------------------------------------

    def close_window_click(self):

        # closes the dialog window
        self.close()