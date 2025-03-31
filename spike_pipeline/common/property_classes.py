# module import
import copy
import os
from functools import partial as pfcn

# pyqt6 module import
import time

import numpy as np
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget,
                             QScrollArea, QSizePolicy, QStatusBar, QMenuBar)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, pyqtBoundSignal, QObject

# spikewrap modules
import spikewrap as sw
import spikeinterface as si

# custom module import
import spike_pipeline.common.common_func as cf
from spike_pipeline.threads.utils import ThreadWorker
from spike_pipeline.info.preprocess import prep_task_map as pp_map

# ----------------------------------------------------------------------------------------------------------------------

"""
    SessionWorkBook:
"""


class SessionWorkBook(QObject):
    # signal functions
    session_change = pyqtSignal()
    sync_channel_change = pyqtSignal()
    bad_channel_change = pyqtSignal(object)
    worker_job_started = pyqtSignal(str)
    worker_job_finished = pyqtSignal(str)

    def __init__(self):
        super(SessionWorkBook, self).__init__()

        # initialisation flag
        self.state = 0
        self.has_init = False

        # main class widgets
        self.session = None
        self.channel_data = None
        self.calculated_data = None
        self.session_props = None

        # other class field
        self.current_run = None
        self.current_ses = None
        self.prep_type = None
        self.n_channels = None

        # resets the initialisation flag
        self.has_init = True
        self.open_session = False

    # ---------------------------------------------------------------------------
    # Getter Functions
    # ---------------------------------------------------------------------------

    def get_channel_info(self):

        probe = self.get_current_recording_probe().get_probe()
        return probe.to_dataframe(complete=True)

    def get_channel_ids(self, i_ch=None):

        probe_rec = self.get_current_recording_probe()

        if i_ch is None:
            return probe_rec.channel_ids

        else:
            return probe_rec.channel_ids[i_ch]

    def get_traces(self, **kwargs):

        probe_rec = self.get_current_recording_probe()
        return probe_rec.get_traces(**kwargs)

    def get_selected_channels(self):

        can_show = np.logical_and(self.channel_data.is_selected, self.channel_data.is_filt)
        return np.where(can_show)[0]

    def get_min_max_values(self, t_lim, i_ch):

        # determines the current run
        i_run = self.session.get_run_index(self.current_run)

        # retrieves the blocks covered by the time range
        t_min_max = self.session.t_min_max[i_run]
        i_blk0 = np.where(t_lim[0] >= t_min_max[:, 0])[0][0]
        i_blk1 = np.where(t_lim[1] <= t_min_max[:, 1])[0][0]
        i_blk_rng = np.arange(int(i_blk0), int(i_blk1 + 1))

        # calculates the overall min/max value over all contiguous blocks
        y_min = self.session.min_max[i_run, 0][0][i_blk_rng, i_ch]
        y_max = self.session.min_max[i_run, 1][0][i_blk_rng, i_ch]

        if len(i_blk_rng) > 1:
            return np.min(y_min, axis=0), np.max(y_max, axis=0)

        else:
            return y_min, y_max

    def get_channel_count(self):

        probe_rec = self.get_current_recording_probe()
        return probe_rec.get_num_channels()

    def get_frame_count(self):

        return self.session_props

    def get_current_recording_probe(self):

        return self.session.get_session_runs(self.current_run, self.current_ses, self.prep_type)

    def get_current_prep_data_names(self):

        return self.session.get_prep_data_names(self.current_run, self.current_ses)

    # ---------------------------------------------------------------------------
    # Setter Functions
    # ---------------------------------------------------------------------------

    def set_all_channel_states(self, is_checked):

        self.channel_data.is_selected[:] = is_checked

    def set_current_run(self, new_run):

        self.current_run = new_run

    def set_prep_type(self, new_type):

        self.prep_type = new_type

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def toggle_channel_flag(self, i_channel, state=1):

        self.channel_data.toggle_channel_flag(i_channel, state)

    def reset_session(self, ses_data):

        # resets the session object
        self.session = SessionObject(ses_data['session_props'], True, self.worker_job_started)
        self.session.channel_calc.connect(self.channel_calc)

        # resets the other class fields
        self.state = ses_data['state']

    def channel_calc(self, ch_type, session=None):

        # flags that the job worker has finished
        self.worker_job_finished.emit(ch_type)

        # runs the signal function (based on data type)
        match ch_type:
            case 'sync':
                self.sync_channel_change.emit()

            case 'bad':
                self.bad_channel_change.emit(session)


    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_session(_self):

        # resets the current run/session names
        _self.current_run = _self.session.get_run_names()[0]
        _self.current_ses = _self.session.get_session_names(0)[0]

        # sets up the channel data object
        _probe_current = _self.get_current_recording_probe()
        _self.channel_data = ChannelData(_probe_current)
        _self.session_props = SessionProps(_probe_current)

        # runs the session change signal function
        if _self.has_init:
            _self.session_change.emit()

    # trace property observer properties
    session = cf.ObservableProperty(update_session)


# ----------------------------------------------------------------------------------------------------------------------


"""
    SessionObject:
"""


class SessionObject(QObject):
    # pyqtsignal functions
    channel_data_setup = pyqtSignal(object)
    channel_calc = pyqtSignal(str, object)

    def __init__(self, s_props, ssf_load=False, sig_fcn=None):
        super(SessionObject, self).__init__()

        # class field initialisations
        self._s = None
        self._s_props = s_props
        self.sig_fcn = sig_fcn

        # bad/sync channels
        self.bad_ch = None
        self.sync_ch = None
        self.ssf_load = ssf_load
        self.data_init = {'bad': False, 'sync': False}

        # creates the session property fields from the input dictionary
        for sp in s_props:
            setattr(self, sp, s_props[sp])

        # loads the session
        self.load_session()

    # ---------------------------------------------------------------------------
    # Session I/O Functions
    # ---------------------------------------------------------------------------

    def load_session(self):

        match self.format_type:
            case 'folder':
                # case is loading from folder format
                self._s = sw.Session(
                    subject_path=self.subject_path,
                    session_name=self.session_name,
                    file_format=self.file_format,
                    run_names=self.run_names,
                    output_path=self.output_path,
                )

            case 'file':
                # case is loading from raw data file

                # FINISH ME!
                pass

        # loads the raw data and channel data
        self._s.load_raw_data()

        # loads the channel data (if not loading session from .ssf file)
        if not self.ssf_load:
            self.load_channel_data()

    def load_channel_data(self):

        # pauses for things to catch up...
        time.sleep(0.1)

        # memory allocation
        n_run = self.get_run_count()
        self.bad_ch = np.empty(n_run, dtype=object)
        self.sync_ch = np.empty(n_run, dtype=object)

        # field initialisation
        self.data_init['bad'] = False
        self.data_init['sync'] = False

        for i_run in range(n_run):
            # retrieves the raw session run object
            ses_run = self.get_session_runs(i_run)

            # sets up the bad channel detection worker
            t_worker_bad = ThreadWorker(self.get_bad_channel, (ses_run, i_run))
            t_worker_bad.work_finished.connect(self.post_get_bad_channel)
            t_worker_bad.start()

            # sets up the sync channel detection worker
            t_worker_sync = ThreadWorker(self.get_sync_channel, (self._s, i_run))
            t_worker_sync.work_finished.connect(self.post_get_sync_channel)
            t_worker_sync.start()

            # updates the signal function
            if self.sig_fcn is not None:
                if isinstance(self.sig_fcn, pyqtSignal):
                    self.sig_fcn.emit('bad')
                    self.sig_fcn.emit('sync')

                else:
                    self.sig_fcn('bad')
                    self.sig_fcn('sync')

        # pauses for things to catch up...
        time.sleep(0.1)

    def recalc_bad_channel_detect(self, p_props):

        # pauses for things to catch up...
        time.sleep(0.1)

        # memory allocation
        t_worker = []
        n_run = self.get_run_count()
        self.bad_ch = np.empty(n_run, dtype=object)

        # field initialisation
        self.data_init['bad'] = False

        for i_run in range(n_run):
            # retrieves the raw session run object
            t0 = time.time()
            ses_run = self.get_session_runs(i_run)

            # sets up the bad channel detection worker
            t_worker_new = ThreadWorker(self.get_bad_channel, (ses_run, i_run, p_props))
            t_worker_new.work_finished.connect(self.post_get_bad_channel)
            t_worker_new.start()

            # appends the worker objects
            t_worker.append(t_worker_new)

            # updates the signal function
            if self.sig_fcn is not None:
                if isinstance(self.sig_fcn, pyqtBoundSignal):
                    self.sig_fcn.emit('bad')

                else:
                    self.sig_fcn('bad')

        return t_worker

    # ---------------------------------------------------------------------------
    # Thread worker functions
    # ---------------------------------------------------------------------------

    @staticmethod
    def get_bad_channel(run_data):

        # field retrieval
        if len(run_data) == 2:
            p_props = {}
            ses_run, i_run = run_data

        else:
            ses_run, i_run, p_props = run_data

        # retrieves the sync channels for each session/run
        b_channel = []
        for probe in ses_run._raw.values():
            b_channel.append(si.preprocessing.detect_bad_channels(probe, **p_props))

        # returns the bad channels
        return b_channel, i_run

    @staticmethod
    def get_sync_channel(run_data):

        # field retrieval
        ses_obj, i_run = run_data

        # returns the sync channels
        return ses_obj.get_sync_channel(i_run).flatten(), i_run

    @staticmethod
    def calc_trace_minmax(run_data):

        # field retrieval
        ses_run, i_run = run_data

        # memory allocation
        y_min, y_max = [], []
        # hist_range = (-500, 500)
        sz_blk, n_bins, t_blk, n_ds = 150000, 100, 10, 10

        for probe in ses_run._raw.values():
            # retrieves the traces for the current probe
            y_sig = probe.get_traces()

            # determines the histogram block size
            n_frm, n_ch = y_sig.shape
            n_frm_blk = np.min([n_frm, int(probe.sampling_frequency * t_blk)])
            n_blk = int(np.ceil(n_frm / n_frm_blk))

            # allocates memory for the current probe
            t_blk = np.zeros((n_blk, 2))
            y_min_tmp, y_max_tmp = np.zeros((n_blk, n_ch)), np.zeros((n_blk, n_ch))
            for i_blk in range(n_blk):
                # retrieves the sub-signal block
                t_blk[i_blk, 0] = i_blk * n_frm_blk
                t_blk[i_blk, 1] = np.min([(i_blk + 1) * n_frm_blk, n_frm])
                i_row_blk = np.arange(int(t_blk[i_blk, 0]), int(t_blk[i_blk, 1]))
                y_sig_blk = y_sig[i_row_blk, :][::n_ds, :]

                # calculates the min/max over the block
                y_min_tmp[i_blk, :] = np.min(y_sig_blk, axis=0)
                y_max_tmp[i_blk, :] = np.max(y_sig_blk, axis=0)

            # appends the min/max values
            y_min.append(y_min_tmp)
            y_max.append(y_max_tmp)

        # returns the min/max values
        return t_blk, y_min, y_max, i_run

    # ---------------------------------------------------------------------------
    # Post thread worker functions
    # ---------------------------------------------------------------------------

    def post_get_bad_channel(self, data):

        ch_data, i_run = data
        self.bad_ch[i_run] = ch_data

        # if all runs have been detected, then run the signal function
        if np.all([x is not None for x in self.bad_ch]):
            self.data_init['bad'] = True
            self.channel_calc.emit('bad', self)

    def post_get_sync_channel(self, data):

        ch_data, i_run = data
        self.sync_ch[i_run] = ch_data

        # if all runs have been detected, then run the signal function
        if np.all([x is not None for x in self.sync_ch]):
            self.data_init['sync'] = True
            self.channel_calc.emit('sync', self)

    def post_calc_trace_minmax(self, data):

        t_blk, y_min, y_max, i_run = data
        self.t_min_max[i_run] = t_blk
        self.min_max[i_run, :] = [y_min, y_max]

        # if all runs have been detected, then run the signal function
        if np.all([x is not None for x in self.t_min_max]):
            self.data_init['minmax'] = True
            self.channel_calc.emit('minmax', self)

    def set_sync_channel(self, sync_ch_data):

        self.sync_ch = sync_ch_data

    def set_bad_channel(self, bad_ch_data):

        self.bad_ch = bad_ch_data

    # ---------------------------------------------------------------------------
    # Session wrapper functions
    # ---------------------------------------------------------------------------

    def get_session_runs(self, i_run, run_type=None, pp_type=None):

        if isinstance(i_run, str):
            i_run = self.get_run_index(i_run)

        if pp_type is not None:
            return self._s._pp_runs[i_run]._preprocessed[run_type][pp_type]

        elif run_type is not None:
            return self._s._raw_runs[i_run]._raw[run_type]

        else:
            return self._s._raw_runs[i_run]

    def get_session_names(self, i_run):

        ses_run = self.get_session_runs(i_run)
        return list(ses_run._raw.keys())

    def get_run_names(self, *_):

        return [x._run_name for x in self._s._raw_runs]

    def get_session_props(self):

        return self._s_props

    def get_prep_data_names(self, i_run, run_type):

        if isinstance(i_run, str):
            i_run = self.get_run_index(i_run)

        return list(self._s._pp_runs[i_run]._preprocessed[run_type].keys())

    def get_run_index(self, run_name):

        return self.get_run_names().index(run_name)

    def get_run_count(self):

        return len(self._s._raw_runs)

    def run_preprocessing(self, configs, per_shank=False, concat_runs=False):

        self._s.preprocess(
            configs=configs,
            per_shank=per_shank,
            concat_runs=concat_runs,
        )

    # ---------------------------------------------------------------------------
    # Protected Properties
    # ---------------------------------------------------------------------------

    @property
    def format_type(self):
        return self._format_type

    @property
    def subject_path(self):
        return self._subject_path

    @property
    def session_name(self):
        return self._session_name

    @property
    def file_format(self):
        return self._file_format

    @property
    def run_names(self):
        return self._run_names

    @property
    def output_path(self):
        return self._output_path

    # ---------------------------------------------------------------------------
    # Protected Property Setter Functions
    # ---------------------------------------------------------------------------

    @format_type.setter
    def format_type(self, new_format):
        self._format_type = new_format

    @subject_path.setter
    def subject_path(self, new_path):
        self._subject_path = new_path

    @session_name.setter
    def session_name(self, new_name):
        self._session_name = new_name

    @file_format.setter
    def file_format(self, new_format):
        self._file_format = new_format

    @run_names.setter
    def run_names(self, new_names):
        self._run_names = new_names

    @output_path.setter
    def output_path(self, new_path):
        self._output_path = new_path


# ----------------------------------------------------------------------------------------------------------------------

"""
    ChannelData: 
"""


class ChannelData:
    def __init__(self, probe_rec):

        # class field initialisations
        self.channel_ids = probe_rec.channel_ids
        self.n_channel = probe_rec.get_num_channels()

        # memory allocation
        self.is_filt = np.ones(self.n_channel, dtype=bool)
        self.is_selected = np.zeros(self.n_channel, dtype=bool)

    def toggle_channel_flag(self, i_channel, state):

        if not isinstance(i_channel, list):
            i_channel = [i_channel]

        for i_ch in i_channel:
            match state:
                case 0:
                    self.is_selected[i_ch] = False

                case 1:
                    self.is_selected[i_ch] ^= True

                case 2:
                    self.is_selected[i_ch] = True

    def set_filter_flag(self, is_filt_new):

        self.is_filt = is_filt_new


# ----------------------------------------------------------------------------------------------------------------------


class SessionProps:
    def __init__(self, probe_rec):
        # retrieves the
        self.n_samples = probe_rec.get_num_frames()
        self.n_channels = probe_rec.get_num_channels()
        self.n_segment = probe_rec.get_num_segments()
        self.t_dur = probe_rec.get_duration()
        self.s_freq = probe_rec.get_sampling_frequency()

    def get_value(self, p_str):
        return getattr(self, p_str)
