# module import
import os
import functools

# pyqt6 module import
import numpy as np
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget,
                             QScrollArea, QSizePolicy, QStatusBar, QMenuBar)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QObject

# spikewrap modules
import spikewrap as sw

# custom module import
import spike_pipeline.common.common_func as cf

# ----------------------------------------------------------------------------------------------------------------------

"""
    SessionWorkBook:
"""


class SessionWorkBook(QObject):
    # signal functions
    session_change = pyqtSignal()

    def __init__(self):
        super(SessionWorkBook, self).__init__()

        # initialisation flag
        self.state = 0
        self.has_init = False

        # main class widgets
        self.session = None
        self.channel_data = None
        self.calculated_data = None

        # other class field
        self.current_run = None
        self.current_ses = None
        self.n_channels = None

        # resets the initialisation flag
        self.has_init = True

    # ---------------------------------------------------------------------------
    # Getter Functions
    # ---------------------------------------------------------------------------

    def get_current_probe(self):

        return self.session.get_session_runs(self.current_run, self.current_ses)

    def get_session_save_data(self):

        # sets up the session save data dictionary
        save_data = {
            'state': self.state,
            'session_props': self.session.get_session_props(),
            'channel_data': self.channel_data,
            'calculated_data': self.calculated_data,
        }

        # returns the data struct
        return save_data

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def toggle_channel_flag(self, i_channel):

        self.channel_data.toggle_channel_flag(i_channel)

    def reset_session(self, ses_data):

        # resets the session object
        self.session = SessionObject(ses_data['session_props'])

        # resets the other class fields
        self.state = ses_data['state']
        self.channel_data = ses_data['channel_data']
        self.calculated_data = ses_data['calculated_data']

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_session(_self):

        # resets the current run/session names
        _self.current_run = _self.session.get_run_names()[0]
        _self.current_ses = _self.session.get_session_names(0)[0]

        # sets up the channel data object
        _self.channel_data = ChannelData(_self.get_current_probe())

        # runs the session change signal function
        if _self.has_init:
            _self.session_change.emit()

    # trace property observer properties
    session = cf.ObservableProperty(update_session)


# ----------------------------------------------------------------------------------------------------------------------

"""
    SessionObject:
"""


class SessionObject:
    def __init__(self, s_props):

        # class field initialisations
        self._s = None
        self._s_props = s_props

        # creates the session property fields from the input dictionary
        for sp in s_props:
            setattr(self, sp, s_props[sp])

        # loads the session object
        self.load_session()
        self.load_raw_data()

    # ---------------------------------------------------------------------------
    # Session I/O Functions
    # ---------------------------------------------------------------------------

    def load_session(self):

        match self.format_type:
            case 'folder':
                # case is loading from folder format

                # creates the spikewrap session object
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

    def load_raw_data(self):

        self._s.load_raw_data()

    # ---------------------------------------------------------------------------
    # Session wrapper functions
    # ---------------------------------------------------------------------------

    def get_session_runs(self, i_run, r_name=None):

        if isinstance(i_run, str):
            run_names = self.get_run_names()
            i_run = run_names.index(i_run)

        if r_name is not None:
            return self._s._runs[i_run]._raw[r_name]

        else:
            return self._s._runs[i_run]

    def get_session_names(self, i_run):

        ses_run = self.get_session_runs(i_run)
        return list(ses_run._raw.keys())

    def get_run_names(self, *_):

        return [x._run_name for x in self._s._runs]

    def get_session_props(self):

        return self._s_props

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
    def __init__(self, probe):

        # class field initialisations
        self.n_channel = probe.get_num_channels()

        # memory allocation
        self.is_selected = np.zeros(self.n_channel, dtype=bool)

    def toggle_channel_flag(self, i_channel):

        self.is_selected[i_channel] ^= True


# ----------------------------------------------------------------------------------------------------------------------

"""
    CalculatedData: 
"""


class CalculatedData:
    def __init__(self):

        # FINISH ME!
        a = 1
