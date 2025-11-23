# package import
import numpy as np
import os
# import sys
# from importlib import reload

# Spike only
# os.environ['LD_LIBRARY_PATH'] = '/opt/MATLAB/R2024b/runting/glnxa64:/lib/x86_64-linux-gnu'
os.environ['LD_LIBRARY_PATH'] = '/opt/MATLAB/R2024b/runtime/glnxa64'

# other imports
# import spykit.common.misc_func as mf
import spykit.common.common_widget as cw
# import spykit.common.memory_map as mm
import spykit.common.spikeinterface_func as sf
import spykit.threads.utils as tw
from spykit.widgets.bomb_cell import BombCellSolver
from spykit.info.preprocess import PreprocessInfoTab, PreprocessSetup
from spykit.widgets.spike_sorting import SpikeSortingDialog, SpikeSortPara
import spykit.info.utils as ui

# pyqt6 module import
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QMainWindow, QWidget, QHBoxLayout, QTableWidget

import spikewrap as sw
# from spikeinterface.widgets import

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

            case 7:
                # case is the plot dock test
                return self.run_plot_dock_test()

            case 8:
                # case is the thread calculation test
                return self.run_thread_calc_test()

            case 9:
                # case is checkbox table test
                return self.run_checkbox_table_test()

            case 10:
                # case is the pre-processing test
                return self.run_pre_process_test()

            case 11:
                # case is the property editor test
                return self.run_prop_editor_test()

            case 12:
                # case is the preprocessing setup test
                return self.run_preprocess_setup_test()

            case 13:
                # case is the spike sorting dialog test
                return self.run_spike_sorting_test()

            case 14:
                # case is the spike sorting parameter test
                return self.run_spike_sorting_para_test()

            case 15:
                # case is running the bomb cell solver
                return self.run_bomb_cell()

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

        from spykit.widgets.para_dialog import ParaDialog

        # creates the parameter panel object
        return ParaDialog()

    def run_plot_dialog_test(self):
        """

        :return:
        """

        from spykit.widgets.plot_widget import QPlotWidgetMain

        # creates the parameter panel object
        return QPlotWidgetMain()

    def run_memory_mapping_test(self):

        # creates the parameter panel object
        return mm.MemMapDialog()

    def run_open_session_test(self):

        from spykit.widgets.open_session import OpenSession

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

    def run_plot_dock_test(self):

        from spykit.plotting.utils import PlotManager
        from spykit.info.utils import InfoManager

        # parameters
        dlg_wid, dlg_hght = 1650, 900
        info_wid = 300

        dock_ss = """
            QWidget {
                border: 1px solid;
            }            
        """

        # main window widget
        h_app = QMainWindow()
        h_app.setFixedSize(dlg_wid, dlg_hght)

        # creates the central widget
        h_central = QWidget()
        h_app.setCentralWidget(h_central)

        # creates the plot layout
        h_layout = QHBoxLayout()
        h_layout.setSpacing(0)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_central.setLayout(h_layout)

        # creates the information panel widget
        info_manager = InfoManager(h_app, info_wid)
        plt_manager = PlotManager(h_app, dlg_wid - info_wid)

        # adds the widgets to the layout
        h_layout.addWidget(info_manager)
        h_layout.addWidget(plt_manager)

        # adds the plot views
        plt_manager.add_plot_view('trace')
        plt_manager.add_plot_view('probe')
        plt_manager.add_plot_view('trigger')

        # test
        c_id = np.array([[1, 1, 2], [1, 1, 2], [3, 3, 2]])
        plt_manager.main_layout.updateID(c_id)

        # return the main window widget
        return h_app

    def run_thread_calc_test(self):

        # creates the parameter panel object
        return tw.BlockWorkerTest()

    def run_checkbox_table_test(self):

        table = QTableWidget(None)
        table.setRowCount(4)
        table.setColumnCount(3)

        table_header = cw.CheckTableHeader(table, [0, 2])
        table.setHorizontalHeader(table_header)
        table.setHorizontalHeaderLabels(['', 'Moo', ''])
        table.resizeColumnsToContents()
        table.verticalHeader().setVisible(False)

        table.horizontalHeader().setCheckState(1, 0)
        table.horizontalHeader().setCheckState(2, 2)

        return table

    def run_pre_process_test(self):

        # main window widget
        h_app = QMainWindow()

        # configs
        configs = {
            "preprocessing": {
                "1": ["bandpass_filter", {"freq_min": 300, "freq_max": 6000}],
                "2": ["common_reference", {"operator": "median"}],
            }
        }

        # creates the spikewrap session object
        session = sw.Session(
            subject_path='C:/Work/Other Projects/EPhys Project/Data/spikeglx/tiny_example/rawdata/sub-001',
            session_name='ses-001',
            file_format='spikeglx',
            run_names='all',
            output_path=None,
        )

        # loads and pre-processes the session
        session.load_raw_data()
        session.preprocess(configs=configs)

        plots = session.plot_preprocessed(
            show=True,
            time_range=(0, 0.5),
            show_channel_ids=False,  # also, "mode"="map" or "line"
        )

        return h_app

    def run_prop_editor_test(self):

        # dimensions
        dlg_hght, dlg_wid = 400, 300

        # main window widget
        h_app = QDialog()
        h_app.setFixedSize(dlg_wid, dlg_hght)

        # creates the dialog layout
        main_layout = QVBoxLayout()
        h_app.setLayout(main_layout)

        # creates the button
        h_prep_tab = PreprocessInfoTab('preprocess')
        main_layout.addWidget(h_prep_tab)

        return h_app

    def run_preprocess_setup_test(self):

        # dimensions
        dlg_height, dlg_width = 250, 300

        # # main window widget
        # h_app = QDialog()
        # h_app.setFixedSize(dlg_width, dlg_height)
        #
        # # creates the dialog layout
        # main_layout = QVBoxLayout()
        # h_app.setLayout(main_layout)

        # creates the button
        h_app = PreprocessSetup()
        h_app.setFixedSize(dlg_width, dlg_height)

        return h_app

    def run_spike_sorting_test(self):

        # creates the button
        h_app = SpikeSortingDialog()

        return h_app

    def run_spike_sorting_para_test(self):

        import time

        t0 = time.time()
        ss_para = SpikeSortPara(None)
        print(time.time() - t0)

        return None

    def run_bomb_cell(self):

        h_app = BombCellSolver(None)

        return h_app
