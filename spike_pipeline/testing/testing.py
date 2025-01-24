# package import
import os
import sys
from importlib import reload

# pyqt6 module import
from PyQt6.QtWidgets import QDialog, QVBoxLayout

# other imports
import spike_pipeline.common.misc_func as mf
import spike_pipeline.common.common_widget as cw
from spike_pipeline.widgets.para_dialog import ParaDialog
from spike_pipeline.widgets.plot_widget import QPlotWidgetMain

########################################################################################################################
########################################################################################################################


class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("My Dialog")

########################################################################################################################
########################################################################################################################


class Testing(object):
    def __init__(self, test_type=1):
        self.test_type = test_type

    def run_test(self):
        """

        :return:
        """

        match self.test_type:
            case 0:
                # case is running the parameter test
                return self.run_dialog_test()

            case 1:
                # case is the parameter widget test
                return self.run_para_widget_test()

            case 2:
                # case is the parameter dialog test
                return self.run_para_dialog_test()

            case 3:
                # case is the plot dialog test
                return self.run_plot_dialog_test()

    def run_dialog_test(self, title_str="My Dialog"):
        """

        :return:
        """

        dlg = QDialog()
        dlg.setWindowTitle(title_str)

        return dlg

    def run_para_widget_test(self):
        """

        :return:
        """

        # parameters
        dlg_wid, dlg_hght = 300, 600

        # creates the dialog window
        dlg = self.run_dialog_test("Pre-Processing Parameters")
        dlg.resize(dlg_wid, dlg_hght)
        dlg.setMinimumWidth(dlg_wid)

        # creates the parameter panel object
        h_preproc = cw.PreProcessPara(dlg)

        # creates the layout object
        h_layout = QVBoxLayout()
        h_layout.addWidget(h_preproc)
        dlg.setLayout(h_layout)

        # returns the dialog object
        return dlg

    def run_para_dialog_test(self):
        """

        :return:
        """

        # creates the parameter panel object
        return ParaDialog()

    def run_plot_dialog_test(self):
        """

        :return:
        """

        # creates the parameter panel object
        return QPlotWidgetMain()