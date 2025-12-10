# module import
import os
import copy
import time
import glob
import numpy as np
import pandas as pd
from pathlib import Path
from functools import partial as pfcn

# pyqt6 module imports
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget,
                             QScrollArea, QSizePolicy, QStatusBar, QMenuBar)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, pyqtBoundSignal, QObject

# spikeinterface/spikewrap module import
import spikewrap as sw
import spikeinterface as si
from spikeinterface.sorters import available_sorters
from spikeinterface.core import order_channels_by_depth

# spykit module imports
import spykit.common.common_func as cf
from spykit.threads.utils import ThreadWorker
from spykit.common.postprocess import PostMemMap
from spykit.info.preprocess import pp_flds, RunPreProcessing
from spykit.info.preprocess import prep_task_map as pp_map
from spykit.widgets.spike_sorting import RunSpikeSorting, SpikeSortInfo

# ----------------------------------------------------------------------------------------------------------------------

"""
    SessionWorkBook:
"""


class SessionWorkBook(QObject):
    # signal functions
    session_change = pyqtSignal()
    sync_channel_change = pyqtSignal()
    bad_channel_change = pyqtSignal(object)
    keep_channel_reset = pyqtSignal()
    worker_job_started = pyqtSignal(str)
    worker_job_finished = pyqtSignal(str)
    prep_progress_update = pyqtSignal(str, float)
    added_post_process = pyqtSignal(str)

    # array class fields
    c_hdr = ['', 'Keep?', 'Status', 'Channel ID', 'Contact ID', 'Channel Index', 'X-Coord', 'Y-Coord', 'Shank ID']

    def __init__(self):
        super(SessionWorkBook, self).__init__()

        # initialisation flag
        self.state = 0
        self.has_init = False

        # main class widgets
        self.session = None
        self.channel_data = None
        self.post_data = None
        self.session_props = None

        # other class field
        self.current_run = None
        self.current_ses = None
        self.current_shank = None
        self.prep_type = None
        self.n_channels = None

        # resets the initialisation flag
        self.has_init = True
        self.open_session = False

    # ---------------------------------------------------------------------------
    # Getter Functions
    # ---------------------------------------------------------------------------

    def get_avail_channel(self, is_raw=False, use_last_rec=False):

        if use_last_rec:
            if len(self.session._s._pp_runs):
                pp = self.session._s._pp_runs[0]._preprocessed
                rec_runs = list(pp.values())[0]
                probe_rec = rec_runs[list(rec_runs.keys())[-1]]

            else:
                probe_rec = self.get_raw_recording_probe()

        elif is_raw or (not self.session.has_prep()):
            probe_rec = self.get_raw_recording_probe()

        else:
            probe_rec = self.get_current_recording_probe()

        return probe_rec.get_channel_ids()

        # if (len(self.session._s._pp_runs) == 0) or is_raw:
        #     # case is no preprocessing has taken place
        #     rec_runs = self.session._s._raw_runs[0]._raw
        #     rec_run = rec_runs[list(rec_runs.keys())[0]]
        #
        # else:
        #     # case is preprocessing has taken place
        #     pp = self.session._s._pp_runs[0]._preprocessed
        #     rec_runs = list(pp.values())[0]
        #     rec_run = rec_runs[list(rec_runs.keys())[-1]]
        #
        # return rec_run.get_channel_ids()

    def get_info_data_frame(self, probe=None):

        # array fields
        c_list = ['keep', 'status', 'channel_ids', 'contact_ids',  'device_channel_indices', 'x', 'y', 'shank_ids']

        # retrieves the necessary channel information data
        ch_info = self.get_channel_info(probe)
        ch_keep = self.get_keep_channels()
        p_dframe = ch_info[ch_info.columns.intersection(c_list)][c_list[2:]]

        # inserts the "status" column
        n_row, n_col = p_dframe.shape
        p_dframe.insert(0, 'status', np.array(['***'] * n_row))
        p_dframe.insert(0, 'keep', ch_keep)

        # appends the "show" channel column
        is_show = np.zeros(p_dframe.shape[0], dtype=bool)
        p_dframe.insert(0, "Show", is_show, True)

        return p_dframe

    def get_channel_info(self, probe=None):

        if probe is None:
            probe = self.get_current_recording_probe().get_probe()

        return probe.to_dataframe(complete=True)

    def get_keep_channels(self):

        return self.channel_data.is_keep

    def get_removed_channels(self):

        return self.channel_data.is_removed

    def get_channel_ids(self, i_ch=None, is_sorted=None):

        # field retrieval
        ch_id = self.channel_data.channel_ids
        if i_ch is None:
            i_ch = np.array(range(len(ch_id)))

        # sorts the channel indices by depth
        if is_sorted:
            i_ch = i_ch[np.argsort(self.channel_data.i_sort_rev[i_ch])]

        return ch_id[i_ch], i_ch

    def get_traces(self, probe_rec=None, **kwargs):

        if probe_rec is None:
            probe_rec = self.get_current_recording_probe()

        return probe_rec.get_traces(**kwargs)

    def get_selected_channels(self):

        if self.channel_data is None:
            return []

        else:
            can_show = np.logical_and(self.channel_data.is_selected, self.channel_data.is_filt)
            return np.where(can_show)[0]

    def get_current_run_index(self):

        return self.session.get_run_index(self.current_run)

    def get_min_max_values(self, t_lim, i_ch):

        # determines the current run
        i_run = self.get_current_run_index()

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

    def get_preprocessing_steps(self):

        # memory allocation
        pp_steps = []
        if self.has_pp_runs():
            # retrieves the
            pp_runs = self.get_pp_runs()
            pp_steps = [v[0] for v in pp_runs[0]._pp_steps.values()]

        return pp_steps

    def get_channel_count(self):

        probe_rec = self.get_current_recording_probe()
        return probe_rec.get_num_channels()

    def get_shank_id(self, i_channel):

        probe = self.get_raw_recording_probe().get_probe()
        shank_id = self.get_channel_info(probe)['shank_ids'][i_channel]

        if len(shank_id):
            return int(shank_id)

        else:
            return 1

    def get_frame_count(self):

        return self.session_props.n_samples

    def get_current_recording_probe(self):

        return self.session.get_session_runs(self.current_run, self.current_ses, self.prep_type, self.current_shank)

    def get_run_durations(self):

        # memory allocation
        n_run = self.session.get_run_count()
        t_dur = np.zeros(n_run, dtype=float)

        # retrieves the durations of each raw run
        for i_run in range(n_run):
            probe = self.session.get_session_runs(i_run, i_run, pp_type='raw')
            t_dur[i_run] = probe.get_duration()

        return t_dur

    def get_raw_recording_probe(self, i_run=None, ses_name=None):

        if i_run is None:
            i_run = self.current_run

        if ses_name is None:
            ses_name = self.current_ses

        return self.session.get_session_runs(i_run, ses_name, None)

    def get_current_prep_data_names(self, i_run=None, ses_name=None):

        if i_run is None:
            i_run = self.current_run

        if ses_name is None:
            ses_name = self.current_ses

        return self.session.get_prep_data_names(i_run, ses_name)

    def get_channel_location(self, i_channel, probe=None):

        if probe is None:
            probe = self.get_current_recording_probe()

        return probe.get_channel_locations()[i_channel]

    def get_channel_status(self, i_channel):

        i_run = self.session.get_run_index(self.current_run)

        if (self.session.bad_ch is None) or (self.session.bad_ch[i_run] is None):
            return 'na'

        else:
            ch_id = self.channel_data.channel_ids[i_channel]
            return self.session.bad_ch[i_run][ch_id]

    def get_bad_channels(self, s_type='all', i_bad_filt=None, is_feas=None):

        # field retrieval
        bad_ch = self.session.bad_ch[0]
        ch_status = np.array(list(bad_ch.values()))

        # memory allocation
        if i_bad_filt is None:
            i_bad_filt = np.zeros(len(ch_status), dtype=bool)

        if is_feas is None:
            is_feas = np.ones(len(ch_status), dtype=bool)

        # ensures the type strings are set correctly
        if s_type == 'all':
            s_type = ['dead', 'noise', 'out']

        elif isinstance(s_type, str):
            s_type = [s_type]

        # determines if the bad channel indices (which are being kept)
        for i, st in enumerate(s_type):
            i_bad_filt = np.logical_or(i_bad_filt, ch_status == st)

        # returns the final bad channel IDs
        # i_bad_ch = np.logical_and(i_bad_filt, self.channel_data.is_keep)
        i_bad_ch = np.where(np.logical_and(i_bad_filt, is_feas))[0]
        ch_id, _ = self.get_channel_ids(i_bad_ch)
        return ch_id, i_bad_ch

    def get_shank_index(self):

        if self.is_per_shank():
            return 1

        else:
            return None

    def get_shank_count(self):

        return self.session.get_session_runs(0,'grouped').get_probe().get_shank_count()

    def get_shank_ids(self):

        ch_info = self.get_channel_info()
        return ch_info['shank_ids']

    def get_shank_names(self, per_shank=None):

        if per_shank is None:
            per_shank = self.is_per_shank()

        if per_shank:
            # if there is more than one shank, then separate out the names
            n_shanks = self.get_shank_count()
            shank_list = ['Shank #{0}'.format(s_id + 1) for s_id in range(n_shanks)]

        else:
            # initialisations
            shank_list = ['All Shanks']

        # returns the shank name list
        return shank_list

    def get_pp_runs(self):

        if self.session is None:
            return None

        else:
            return self.session._s._pp_runs

    def get_sorting_folder_paths(self, f_type=''):

        # field retrieval
        is_concat_run = self.is_concat_run()
        n_shank = self.get_shank_count if self.is_per_shank() else 1
        n_run = 1 if is_concat_run else self.session.get_run_count()

        # determines path of sorting output directory exists
        s_props = self.session.get_session_props()
        s_path_split = s_props['subject_path'].split('/')
        base_dir = Path('/'.join(s_path_split[:-2]))

        # retrieves the run names
        if is_concat_run:
            # case is a concatenated run
            run_names = ['concat_run']

        elif (s_props['run_names'] == 'all'):
            # case is using all runs
            run_names = self.session.get_run_names()

        else:
            # case is using specific runs
            run_names= s_props['run_names']

        # other session properties
        sub_name = s_path_split[-1]
        ses_name = s_props['session_name']
        base_path = os.path.join("derivatives", sub_name, ses_name, "ephys")

        # sets folder suffix path
        match f_type.lower():
            case 'bombcell':
                # case is bombcell
                suf_path = os.path.join('sorter_output', 'BombCell')
            case _:
                # default case
                suf_path = None

        # determines if all runs/shanks have
        f_path = np.empty((n_run, n_shank), dtype=object)
        for i_run, r_name in enumerate(run_names):
            # appends the run name to the path
            f_path_nw = os.path.join(str(base_dir), base_path, r_name, 'sorting')

            # case specific folder path update
            if self.is_per_shank():
                # case is a multi-shank session
                for i_shank in range(n_shank):
                    # if there is a match, then exit the inner loop
                    f_path[i_run, i_shank] = os.path.join(f_path_nw, f'shank_{i_shank}')
                    if suf_path is not None:
                        f_path[i_run, i_shank] = os.path.join(f_path[i_run, i_shank], suf_path)

            else:
                # case is a grouped/single shank session
                f_path[i_run, 0] = f_path_nw
                if suf_path is not None:
                    f_path[i_run, 0] = os.path.join(f_path[i_run, 0], suf_path)

        # return the overall search match results
        return f_path

    def get_mem_map_field(self, p_fld):

        i_run = self.get_current_run_index()
        i_shank = 0 if (self.current_shank is None) else self.current_shank
        return self.post_data.get_mem_map_field(i_run, i_shank, p_fld)

    def get_metric_table(self):

        q_hdr = self.get_mem_map_field('q_hdr')[0]
        q_met = self.get_mem_map_field('q_met')
        return pd.DataFrame(q_met, columns=q_hdr)

    def get_session_base_path(self):

        # splits the subject path
        s_props = self.session.get_session_props()
        s_path_split = s_props['subject_path'].split('/')

        # returns the base session path
        return Path('/'.join(s_path_split[:-2]))

    def get_mem_map_files(self, is_flat=True):

        # field retrieval
        bc_dir = self.get_sorting_folder_paths('bombcell')

        # finds all the bombcell memory mapping files
        if is_flat:
            mmap_files = []
            for bc in bc_dir.flatten():
                if os.path.exists(bc):
                    # case is the bombcell directory exists
                    mmap_files_new = glob.glob(os.path.join(bc, '*.dat'))
                    if len(mmap_files_new):
                        # appends the found memory mapped files
                        mmap_files += mmap_files_new

        else:
            # memory allocation
            n_run_pp, n_shank_pp = bc_dir.shape

            for i_run in range(n_run_pp):
                for i_shank in range(n_shank_pp):
                    # search bombcell folder for .dat files
                    mmap_files_new = glob.glob(os.path.join(bc_dir[i_run, i_shank], '*.dat'))
                    if (i_run == 0) and (i_shank == 0):
                        n_file_pp = len(mmap_files_new)
                        if n_file_pp:
                            # memory allocation
                            mmap_files = np.empty((n_run_pp, n_shank_pp, n_file_pp), dtype=object)
                        else:
                            # if no match, then exit
                            return None

                    if len(mmap_files_new) == n_file_pp:
                        for i_file in range(n_file_pp):
                            mmap_files[i_run, i_shank, i_file] = mmap_files_new[i_file]
                    else:
                        return None

        # returns the memory map file
        return mmap_files

    # ---------------------------------------------------------------------------
    # Setter Functions
    # ---------------------------------------------------------------------------

    def set_all_channel_states(self, is_checked):

        self.channel_data.is_selected[self.channel_data.is_keep] = is_checked

    def set_channel_indices(self, ch_id):

        self.channel_data.is_selected[:] = False
        self.channel_data.is_selected[ch_id] = True

    def set_current_run(self, new_run):

        self.current_run = new_run

    def set_current_shank(self, new_shank):

        self.current_shank = new_shank

    def set_prep_type(self, new_type):

        self.prep_type = new_type

    def set_sorting_props(self, new_sort_props):

        self.session.sort_obj.s_props = new_sort_props

    # ---------------------------------------------------------------------------
    # Boolean Inspection Functions
    # ---------------------------------------------------------------------------

    def has_pp_runs(self):

        pp_runs = self.get_pp_runs()
        if pp_runs is None:
            return 0

        else:
            return len(self.get_pp_runs()) > 0

    def is_channel_removed(self):

        ch_run = self.get_avail_channel(use_last_rec=True)
        ch_full = self.channel_data.channel_ids
        ch_intersect = np.intersect1d(ch_full, ch_run, return_indices=True)

        is_rmv = np.ones(len(ch_full), dtype=bool)
        is_rmv[ch_intersect[1]] = False

        return is_rmv

    def is_session_sorted(self):

        f_path = self.get_sorting_folder_paths()
        return np.all([os.path.exists(x) for x in f_path.flatten()])

    # ---------------------------------------------------------------------------
    # Session wrapper functions
    # ---------------------------------------------------------------------------

    def reset_channel_data(self, ch_data):

        # resets the bad/sync channels
        self.session.bad_ch = ch_data['bad']
        self.session.sync_ch = ch_data['sync']

        # resets the channel keep field
        self.channel_data.is_keep = ch_data['keep']
        self.channel_data.is_removed = ch_data['removed']
        self.keep_channel_reset.emit()

    def reset_current_session(self, is_pp=False):

        if is_pp:
            # case is using preprocessing fields
            s_keys = list(self.session._s._pp_runs[0]._preprocessed.keys())

            # resets the current session name based on the shank index
            if self.current_shank is None:
                self.current_ses = s_keys[0]
            else:
                self.current_ses = s_keys[self.current_shank]

        else:
            # case is using raw data fields
            s_keys = list(self.session._s._raw_runs[0]._raw.keys())
            self.current_ses = s_keys[0]

    def is_concat_run(self):

        return (not self.is_raw_run()) and self.session.prep_obj.concat_runs

    def is_per_shank(self):

        if self.session is None:
            return False

        else:
            return (not self.is_raw_run()) and self.session.prep_obj.per_shank

    def is_raw_run(self):

        return self.prep_type == '0-raw'

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def added_post_proc(self, mm_name):

        self.added_post_process.emit(mm_name)

    def setup_mmap_files(self, mm_name):

        # sets up the memory mapped file names
        pp_file = f"{mm_name}.dat"
        mm_file = self.get_sorting_folder_paths('bombcell')
        bc_mod = np.nditer(mm_file, flags=['refs_ok'], op_flags=['readwrite'])

        # sets up the memory mapped file names
        with bc_mod:
            for x in bc_mod:
                x[...] = os.path.join(str(x), pp_file)

        return mm_file

    def toggle_channel_flag(self, i_channel, state=1, is_keep=False):

        if is_keep:
            self.channel_data.toggle_keep_flag(i_channel, state)

        else:
            self.channel_data.toggle_select_flag(i_channel, state)

    def reset_session(self, ses_data):

        # resets the session object
        self.session = SessionObject(ses_data['session_props'], True, self.worker_job_started)
        self.session.channel_calc.connect(self.channel_calc)
        self.session.prep_prop_update.connect(self.prep_prop_update)

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

    def prep_prop_update(self, m_str, pr_val):

        self.prep_progress_update.emit(m_str, pr_val)

    def silence_sync(self, i_run, ind_s, ind_f):

        self.session.sync_ch[i_run][ind_s:ind_f] = 0

    def clear_preprocessing(self):

        self.prep_type = None
        self.reset_current_session()
        self.session._s._pp_runs = []

    def clear_postprocessing(self):

        if self.post_data is not None:
            self.post_data.clear_post_process()

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_session(_self):

        # resets the preprocessing type/postpressing data fields
        _self.prep_type = None
        has_session = _self.session is not None

        # resets the current run/session names
        if has_session:
            # case is there is a new session set (clearing session)
            _self.current_run = _self.session.get_run_names()[0]
            _self.current_ses = _self.session.get_session_names(0)[0]

            # sets up the channel data object
            _probe_current = _self.get_current_recording_probe()
            _self.channel_data = ChannelData(_probe_current)
            _self.session_props = SessionProps(_probe_current)
            _self.post_data = PostProcessData()
            _self.session.load_sorting_para(_self)

            # connects the signal functions
            _self.post_data.added_pp.connect(_self.added_post_proc)

        else:
            # case is there is no session set (clearing session)
            _self.current_run = None
            _self.current_shank = None
            _self.current_ses = None
            _self.channel_data = None
            _self.session_props = None
            _self.post_data = None

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
    prep_prop_update = pyqtSignal(str, float)

    # parameters
    dy_min = 1.5

    def __init__(self, s_props, ssf_load=False, sig_fcn=None):
        super(SessionObject, self).__init__()

        # class field initialisations
        self._s = None
        self._s_props = s_props
        self.sig_fcn = sig_fcn

        # bad/sync channels
        self.bad_ch = None
        self.sync_ch = None
        self.prep_obj = None
        self.sort_obj = None
        self.bcell_obj = None
        self.t_worker = None
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
        self.prep_obj = RunPreProcessing(self._s)
        self.sort_obj = RunSpikeSorting(self._s)
        # self.prep_obj.update_prog.connect(self.update_prog)

        # loads the channel data (if not loading session from .ssf file)
        if not self.ssf_load:
            self.load_channel_data()

    def load_channel_data(self):

        # pauses for things to catch up...
        time.sleep(0.1)

        # memory allocation
        self.t_worker = []
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
            t_worker_bad = ThreadWorker(None, self.get_bad_channel, (ses_run, i_run))
            t_worker_bad.work_finished.connect(self.post_get_bad_channel)
            t_worker_bad.desc = 'bad'
            t_worker_bad.start()

            # sets up the sync channel detection worker
            t_worker_sync = ThreadWorker(None, self.get_sync_channel, (self._s, i_run))
            t_worker_sync.work_finished.connect(self.post_get_sync_channel)
            t_worker_sync.desc = 'sync'
            t_worker_sync.start()

            # appends the worker objects
            self.t_worker.append(t_worker_bad)
            self.t_worker.append(t_worker_sync)

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

    def load_sorting_para(self, ses_obj):

        # updates the signal function
        if (ses_obj.session.sig_fcn is not None) and (not ses_obj.session.ssf_load):
            # sets up the bad channel detection worker
            t_worker_sort = ThreadWorker(None, self.get_sorter_info, (ses_obj))
            t_worker_sort.work_finished.connect(self.post_get_sorter_info)
            t_worker_sort.desc = 'sorterpara'
            t_worker_sort.start()

            # updates the signal function
            self.sig_fcn('sorterpara')

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
            ses_run = self.get_session_runs(i_run)

            # sets up the bad channel detection worker
            t_worker_new = ThreadWorker(None, self.get_bad_channel, (ses_run, i_run, p_props))
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

    def update_prog(self, m_str, pr_val):

        self.prep_prop_update.emit(m_str, pr_val)

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

    @staticmethod
    def get_sorter_info(run_data):

        # initialisations
        ss_info = SpikeSortInfo(run_data)
        return ss_info.setup_all_sort_para()

    # ---------------------------------------------------------------------------
    # Post thread worker functions
    # ---------------------------------------------------------------------------

    def post_get_bad_channel(self, data):

        # sets the channel data
        ch_data, i_run = data
        ch_id = self._s._raw_runs[0]._raw['grouped'].get_channel_ids()
        self.bad_ch[i_run] = dict(zip(ch_id, ch_data[0][1]))

        # if all runs have been detected, then run the signal function
        if np.all([x is not None for x in self.bad_ch]):
            self.data_init['bad'] = True

        self.channel_calc.emit('bad', self)

    def post_get_sync_channel(self, data):

        # sets the signal data
        ch_data, i_run = data

        y_min, y_max = np.min(ch_data), np.max(ch_data)
        if y_max - y_min <= self.dy_min:
            # if the signal amplitude is below tolerance, then set all zeros
            ch_data[:] = 0

        else:
            # resets the signal values as being on/off
            ch_data = 100 * (ch_data > (y_min + y_max) / 2).astype(int)

        # if all runs have been detected, then run the signal function
        self.sync_ch[i_run] = ch_data
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

    def post_get_sorter_info(self, data):

        # updates the sorter parameter fields
        self.sort_obj.s_props = data

        self.channel_calc.emit('sorterpara', self)

    # ---------------------------------------------------------------------------
    # Preprocessing Functions
    # ---------------------------------------------------------------------------

    def run_preprocessing(self, configs, per_shank=False, concat_runs=False):

        self.prep_obj.preprocess(configs, per_shank, concat_runs)

    # ---------------------------------------------------------------------------
    # Session wrapper functions
    # ---------------------------------------------------------------------------

    def get_session_runs(self, i_run, run_type=None, pp_type=None, i_shank=None):

        if isinstance(i_run, str):
            i_run = self.get_run_index(i_run)

        if (pp_type is None) or (pp_type.endswith('raw')):
            if run_type is None:
                # case is the run type is not specified
                run = self._s._raw_runs[i_run]
                if i_shank is None:
                    return run
                else:
                    run_shank = run._get_split_by_shank()
                    return run_shank['shank_{0}'.format(i_shank)]

            else:
                return self._s._raw_runs[i_run]._raw['grouped']

        elif self.prep_obj.concat_runs:
            return self._s._pp_runs[0]._preprocessed[run_type][pp_type]

        else:
            return self._s._pp_runs[i_run]._preprocessed[run_type][pp_type]

    def get_session_names(self, i_run):

        ses_run = self.get_session_runs(i_run)
        return list(ses_run._raw.keys())

    def get_run_names(self, *_):

        return [x._run_name for x in self._s._raw_runs]

    def get_session_props(self):

        return self._s_props

    def get_prep_data_names(self, i_run, run_type):

        if len(self._s._pp_runs):
            if isinstance(i_run, str):
                i_run = self.get_run_index(i_run)

            return list(self._s._pp_runs[i_run]._preprocessed[run_type].keys())

        else:
            return []

    def get_run_index(self, run_name):

        return self.get_run_names().index(run_name)

    def get_run_count(self):

        return len(self._s._raw_runs)

    def has_prep(self):

        return len(self._s._pp_runs) > 0

    def force_close_workers(self):

        if self.t_worker is not None:
            for tw in self.t_worker:
                if tw.is_running:
                    tw.force_quit()
                    self.channel_calc.emit(tw.desc, self)

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
        self.is_keep = np.ones(self.n_channel, dtype=bool)
        self.is_removed = np.zeros(self.n_channel, dtype=bool)

        # determines the channel depth ordering
        self.i_sort, self.i_sort_rev = order_channels_by_depth(probe_rec)

    def clear_select_flag(self):

        self.is_selected[:] = False

    def toggle_select_flag(self, i_channel, state):

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

    def toggle_keep_flag(self, i_channel, state):

        if not isinstance(i_channel, list):
            i_channel = [i_channel]

        for i_ch in i_channel:
            match state:
                case 0:
                    self.is_keep[i_ch] = False

                case 1:
                    self.is_keep[i_ch] ^= True

                case 2:
                    self.is_keep[i_ch] = True

    def set_filter_flag(self, is_filt_new):

        self.is_filt = is_filt_new


# ----------------------------------------------------------------------------------------------------------------------

"""
    SessionProps: 
"""


class SessionProps:
    def __init__(self, probe_rec):
        # retrieves the
        self.n_samples = probe_rec.get_num_frames()
        self.n_channels = probe_rec.get_num_channels()
        self.n_segment = probe_rec.get_num_segments()
        self.t_dur = np.round(probe_rec.get_duration(), cf.n_dp)
        self.s_freq = probe_rec.get_sampling_frequency()

    def get_value(self, p_str):
        return getattr(self, p_str)


# ----------------------------------------------------------------------------------------------------------------------

"""
    PostProcessData: class to store the post-processing memory map files/objects
"""

class PostProcessData(QObject):
    # pyqtsignal functions
    added_pp = pyqtSignal(str)

    def __init__(self):
        # initialises the property widget
        super(PostProcessData, self).__init__()

        # field initialisation
        self.mmap = []
        self.mmap_file = []
        self.mmap_name = []
        self.is_saved = []
        self.i_mmap = 0

    def read_post_process(self, mm_file):

        # creates the memory map object
        pmm_obj = PostMemMap()
        n_run_pp, n_shank_pp, n_file_pp = mm_file.shape

        # reads the stored memory maps
        for i_file in range(n_file_pp):
            # memory allocation
            mmap_tmp = np.empty((n_run_pp, n_shank_pp), dtype=object)

            # reads the memory mapped files (for each run/shank)
            for i_run in range(n_run_pp):
                for i_shank in range(n_shank_pp):
                    pmm_obj.set_mmap_file(mm_file[i_run, i_shank, i_file])
                    mmap_tmp[i_run, i_shank] = pmm_obj.read_mem_map()

            # appends the memory map to the class fields
            self.add_post_process(mm_file[:, :, i_file], mmap_tmp, True)

    def add_post_process(self, mmap_file_new, mmap_new, is_save=False):

        # appends the new mmap file and other properties
        self.mmap.append(mmap_new)
        self.mmap_file.append(mmap_file_new)
        self.mmap_name.append(os.path.split(mmap_file_new[0, 0])[1])

        # sets saved flag
        self.is_saved.append(is_save)

        # flag that a new process has been added
        if not is_save:
            self.added_pp.emit(self.mmap_name[-1])

    def remove_post_process(self, i_mmap_rmv):

        # appends the new mmap file
        self.mmap.pop(i_mmap_rmv)
        self.mmap_file.pop(i_mmap_rmv)
        self.mmap_name.pop(i_mmap_rmv)
        self.is_saved.pop(i_mmap_rmv)

        # decrements the memory index
        if i_mmap_rmv > self.i_mmap:
            self.i_mmap -= 1

    def clear_post_process(self):

        # clears and deletes the temporary memory mapped files
        for i_map in range(len(self.mmap)):
            # field retrieval
            if i_map == 0:
                n_run, n_shank = self.mmap[i_map].shape

            for i_run in range(n_run):
                for i_shank in range(n_shank):
                    # clears the memory maps
                    self.mmap[i_map][i_run, i_shank].flush()
                    self.mmap[i_map][i_run, i_shank] = None
                    time.sleep(0.1)

                    # deletes the temporary file
                    if not self.is_saved[i_map]:
                        try:
                            os.remove(self.mmap_file[i_map][i_run, i_shank])
                        except:
                            pass

    def rename_post_process(self, mmap_file_new):

        # field retrieval
        n_run, n_shank = mmap_file_new.shape

        # renames the temporary file names
        for i_run in range(n_run):
            for i_shank in range(n_shank):
                # field retrieval
                dt = self.mmap[self.i_mmap][i_run, i_shank].dtype

                # flushes and deletes the memory map
                self.mmap[self.i_mmap][i_run, i_shank].flush()
                self.mmap[self.i_mmap][i_run, i_shank] = None
                time.sleep(0.25)

                # recreates the memory mapped file
                os.rename(self.mmap_file[self.i_mmap][i_run, i_shank], mmap_file_new[i_run, i_shank])
                self.mmap[self.i_mmap][i_run, i_shank] = np.memmap(mmap_file_new[i_run, i_shank], dtype=dt, mode='r', shape=(1,))

        # resets the other fields
        self.is_saved[self.i_mmap] = True
        self.mmap_file[self.i_mmap] = mmap_file_new
        self.mmap_name[self.i_mmap] = os.path.split(mmap_file_new[0, 0])[1]

    def set_mmap_index(self, i_mmap_new):

        self.i_mmap = i_mmap_new

    def get_mem_map_field(self, i_run, i_shank, p_fld):

        return self.mmap[self.i_mmap][i_run, i_shank][p_fld][0]