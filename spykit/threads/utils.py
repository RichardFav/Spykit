# module import
import sys

# pyqt5 module import
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
        self.finished.connect(self.quit)
        self.started.connect(self.reset_error_hook)
        self.finished.connect(self.reset_error_hook)

        # boolean class fields
        self.is_ok = True
        self.is_running = False
        self.desc = None

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
    ThreadWorker: 
"""


