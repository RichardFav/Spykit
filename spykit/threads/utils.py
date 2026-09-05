# module import
import sys
import dill
from multiprocess import Queue
from pathos.multiprocessing import ProcessingPool

# pyqt6 module import
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

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

def save_prep_data(save_para, queue):

    # field retrieval
    pp_rec_bin, out_folder, n_worker = save_para

    for i_out, (pp_rb, o_f) in enumerate(zip(pp_rec_bin, out_folder)):
        # updates the progressbar label
        queue.put([i_out + 1, len(pp_rec_bin)])

        # outputs the data to file
        pp_r = dill.loads(pp_rb)
        pp_r.save(
            format="binary",
            folder=o_f,
            n_jobs=n_worker,
            verbose=False,
            progress_bar=False,
            overwrite=True,
        )

class SavePrepThreadWorker(QThread):
    # pyqtsignal objects
    work_started = pyqtSignal()
    work_finished = pyqtSignal(bool)
    work_progress = pyqtSignal(int, int)

    def __init__(self, parent, sync_manager, save_data):
        super(SavePrepThreadWorker, self).__init__(parent)

        # sets the input arguments
        self.work_para = save_data
        self.queue = sync_manager.s_queue

        # class fields
        self.process = None

        # boolean class fields
        self.is_ok = True
        self.is_running = False

        # Set up a timer to periodically check the queue in the GUI thread
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)

    def run(self):

        # emits the work start signal
        self.is_running = True
        self.work_started.emit()

        # creates the worker process object
        self.process = ProcessingPool()
        self.process.map(save_prep_data, [self.work_para], [self.queue])
        self.process.close()
        self.process.join()
        self.process.clear()

        # runs the house-keeping functions
        self.is_running = False
        self.work_finished.emit(True)
        self.reset_error_hook()

    def check_queue(self):

        while not self.queue.empty():
            result = self.queue.get()
            self.work_progress.emit(result[0], result[1])

    def force_quit(self):

        if self.process and self.is_running:
            # terminates the process
            self.process.terminate()
            self.process.join()
            self.process.clear()

            # runs the house-keeping functions
            self.is_running = False
            self.work_finished.emit(False)
            self.reset_error_hook()

    def reset_error_hook(self):

        if hasattr(self.parent(), 'sp_main'):
            sys.excepthook = self.parent().sp_main.orig_error_hook
        else:
            sys.excepthook = self.parent().orig_error_hook
