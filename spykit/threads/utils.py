# module import
import sys

# pyqt5 module import
from pathos.multiprocessing import ProcessingPool
from PyQt6.QtCore import QObject, QThread, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

"""
    ThreadWorker: 
"""


class ThreadWorker(QThread):
    # pyqtsignal objects
    work_started = pyqtSignal()
    work_progress = pyqtSignal(str, float)
    work_finished = pyqtSignal(object)

    def __init__(self, parent, work_fcn, work_para=None):
        super(ThreadWorker, self).__init__(parent)

        # sets the input arguments
        self.work_fcn = work_fcn
        self.work_para = work_para

        # connects finished slot function
        self.started.connect(self.reset_error_hook)
        self.finished.connect(self.reset_error_hook)
        self.finished.connect(self.deleteLater)

        # class fields
        self.desc = None

        # boolean class fields
        self.is_ok = True
        self.is_running = False

    def run(self):

        # emits the work start signal
        self.is_running = True
        self.work_started.emit()

        # runs the thread job
        thread_data = self.work_fcn(self.work_para)

        # emits the work start signal
        self.is_running = False
        self.work_finished.emit(thread_data)

    def force_quit(self):

        # force quits the thread worker
        self.is_running = False
        self.terminate()

    def reset_error_hook(self):

        if hasattr(self.parent(), 'sp_main'):
            sys.excepthook = self.parent().sp_main.orig_error_hook
        else:
            sys.excepthook = self.parent().orig_error_hook

# ----------------------------------------------------------------------------------------------------------------------

"""
    SaveThreadWorker: 
"""

class SavePrepThreadWorker(QThread):
    # pyqtsignal objects
    work_started = pyqtSignal()
    work_finished = pyqtSignal(bool)

    def __init__(self, parent, work_fcn, work_para=None):
        super(SavePrepThreadWorker, self).__init__(parent)

        # sets the input arguments
        self.work_fcn = work_fcn
        self.work_para = work_para

        # class fields
        self.process = None

        # boolean class fields
        self.is_ok = True
        self.is_running = False

    def run(self):

        # emits the work start signal
        self.is_running = True
        self.work_started.emit()

        # remove me later
        i_run = 0
        i_shank = 0
        ses_obj = self.parent().session_obj
        is_concat_run = ses_obj.is_concat_run()
        pp_steps = ses_obj.get_preprocessing_steps()
        pp_data_flds = ses_obj.get_current_prep_data_names()
        i_sel_pp = len(pp_steps)

        # # sets up the output folder
        # out_folder = ses_obj.setup_folder_path(
        #     s_type='preprocessing',
        #     is_concat_run=is_concat_run,
        #     i_run=i_run,
        #     i_shank=i_shank
        # )
        # run_type = "shank_{0}".format(i_shank)
        # pp_rec = ses_obj.session.get_session_runs(
        #     i_run, run_type, pp_data_flds[i_sel_pp], i_shank)

        # sets up the output folder
        out_folder = ses_obj.setup_folder_path(
            s_type='preprocessing',
            is_concat_run=is_concat_run,
            i_run=i_run,
        )
        pp_rec = ses_obj.session.get_session_runs(
            i_run, 'grouped', pp_data_flds[i_sel_pp])

        # creates the worker process object
        self.process = ProcessingPool()
        self.process.map(self.work_fcn, [pp_rec])
        self.process.close()
        self.process.join()

        # runs the house-keeping functions
        self.is_running = False
        self.work_finished.emit(True)
        self.reset_error_hook()

    def force_quit(self):

        if self.process and self.process.is_alive():
            # terminates the process
            self.process.terminate()
            self.process.join()

            # runs the house-keeping functions
            self.is_running = False
            self.work_finished.emit(False)
            self.reset_error_hook()

    def reset_error_hook(self):

        if hasattr(self.parent(), 'sp_main'):
            sys.excepthook = self.parent().sp_main.orig_error_hook
        else:
            sys.excepthook = self.parent().orig_error_hook
