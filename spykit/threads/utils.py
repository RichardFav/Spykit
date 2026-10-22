# module import
import sys
import dill
import time
import traceback
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

        # attempts to terminate the worker
        try:
            self.terminate()
        except:
            pass

    def reset_error_hook(self):

        if hasattr(self.parent(), 'sp_main'):
            sys.excepthook = self.parent().sp_main.orig_error_hook
        else:
            sys.excepthook = self.parent().orig_error_hook

# ----------------------------------------------------------------------------------------------------------------------

"""
    ProcessPoolWorker: 
"""

t_period = 100

def save_prep_data(save_para, queue):

    # field retrieval
    pp_rec_bin, pp_para_bin, out_folder, n_worker = save_para

    for i_out, (pp_rb, pp_pb, o_f) in enumerate(zip(pp_rec_bin, pp_para_bin, out_folder)):
        # updates the progressbar label
        queue.put([i_out + 1, len(pp_rec_bin)])

        # outputs the data to file
        pp_r = dill.loads(pp_rb)

        # re-adds drift correction recorder annotations (some fields are lost when using dill)
        if pp_pb is not None:
            pp_r.set_annotation('parameters', dill.loads(pp_pb))

        # outputs the recording to file
        pp_r.save(
            format="binary",
            folder=o_f,
            n_jobs=n_worker,
            verbose=False,
            progress_bar=False,
            overwrite=True,
        )

def run_spike_sort(sort_para, queue):

    # field retrieval
    ses_obj_bin, sort_props_bin = sort_para
    ses_obj, sort_props = dill.loads(ses_obj_bin), dill.loads(sort_props_bin)

    # flag that initialisation is complete
    queue.put([True])

    # runs the spike sorting solver
    try:
        ses_obj.sort(
            sort_props['ss_config'],
            run_sorter_method=sort_props['sorter_method'],
            per_shank=sort_props['per_shank'],
            concat_runs=sort_props['concat_runs']
        )

    except Exception as e:
        # sets up the error message info dictionary
        err_info = {
            'exc_type': type(e).__name__,
            'exe_msg': str(e),
            'exc_args': e.args,
            'tb_details': traceback.extract_tb(e.__traceback__),
        }

        # adds the error dictionary to the queue
        queue.put([err_info])
        time.sleep(2.5 * t_period)

class ProcessPoolWorker(QThread):
    # pyqtsignal objects
    work_started = pyqtSignal()
    work_finished = pyqtSignal(bool)
    work_progress = pyqtSignal(int, int)
    work_init_complete = pyqtSignal()
    work_error = pyqtSignal(dict)

    def __init__(self, parent, sync_manager, work_data, job_type):
        super(ProcessPoolWorker, self).__init__(parent)

        # sets the input arguments
        self.job_type = job_type
        self.work_para = work_data
        self.queue = sync_manager.s_queue

        # class fields
        self.process = None

        # boolean class fields
        self.is_ok = True
        self.is_running = False

        # Set up a timer to periodically check the queue in the GUI thread
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(t_period)

    def run(self):

        # emits the work start signal
        self.is_running = True
        self.work_started.emit()

        match self.job_type:
            case 'save_prep':
                # case is saving preprocessing data
                process_fcn = save_prep_data

            case 'spike_sort':
                # case is spike sorting
                process_fcn = run_spike_sort

        # creates the worker process object
        self.process = ProcessingPool()
        self.process.map(process_fcn, [self.work_para], [self.queue])
        self.process.close()
        self.process.join()
        self.process.clear()

        # runs the house-keeping functions
        self.is_running = False
        self.work_finished.emit(self.is_ok)
        self.reset_error_hook()

    def check_queue(self):

        while not self.queue.empty():
            # retrieves the queue results
            result = self.queue.get()

            # runs the pyqtsignal function based on the job type
            match self.job_type:
                case 'save_prep':
                    # case is saving preprocessing data
                    self.work_progress.emit(result[0], result[1])

                case 'spike_sort':
                    # case is spike sorting
                    if isinstance(result[0], bool):
                        self.work_init_complete.emit()
                    else:
                        self.is_ok = False
                        self.work_error.emit(result[0])

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
