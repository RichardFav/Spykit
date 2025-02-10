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
from spike_pipeline.widgets.open_session import OpenSession
import spike_pipeline.common.memory_map as mm
import spike_pipeline.common.spikeinterface_func as sf

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

            case 4:
                # case is the memory mapping test
                return self.run_memory_mapping_test()

            case 5:
                # case is the open session window
                return self.run_open_session_test()

            case 6:
                # case is the directory check test
                return self.run_directory_check_test()

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

    def run_memory_mapping_test(self):

        # creates the parameter panel object
        return mm.MemMapDialog()

    def run_open_session_test(self):

        # creates and returns the dialog window
        return OpenSession()

    def run_directory_check_test(self):

        # # parameters
        f_format = 'spikeglx'
        # f_path = 'C:/Work/Other Projects/EPhys Project/Data/spikeglx/tiny_example'
        f_path = 'C:/Work/Other Projects/EPhys Project/Data/spikeglx'

        # openephys dataset
        # f_format = 'openephys'
        # f_path = 'C:/Work/Other Projects/EPhys Project/Data/openephys/tiny_example'
        # f_path = 'C:/Work/Other Projects/EPhys Project/Data/openephys'

        # sets up t
        obj_chk = sf.DirectoryCheck(f_path, f_format)

        return None
