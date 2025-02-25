# module import
import os
import functools

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QFormLayout, QWidget,
                             QScrollArea, QSizePolicy, QStatusBar, QMenuBar)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QObject

# spikewrap modules
import spikewrap as sw

# custom module import
import spike_pipeline.common.common_func as cf

# WORKBOOK OBJECT ------------------------------------------------------------------------------------------------------


class SessionWorkBook(QObject):
    # signal functions
    session_change = pyqtSignal()

    def __init__(self):
        super(SessionWorkBook, self).__init__()

        # initialisations
        self.has_init = False

        # class field initialisations
        self.session = None

        # initialisations
        self.has_init = True

    # ---------------------------------------------------------------------------
    # Protected Properties
    # ---------------------------------------------------------------------------

    @staticmethod
    def update_session(_self):

        if _self.has_init:
            _self.session_change.emit()

    # trace property observer properties
    session = cf.ObservableProperty(update_session)


# SESSION OBJECT -------------------------------------------------------------------------------------------------------


class SessionObject:
    def __init__(
        self,
        subject_path,
        session_name,
        file_format,
        run_names,
        output_path=None
    ):

        # class field initialisations
        self._s = None
        self._subject_path = subject_path
        self._session_name = session_name
        self._file_format = file_format
        self._run_names = run_names
        self._output_path = output_path

        # loads the session object
        self.load_session()
        self.load_raw_data()

    # ---------------------------------------------------------------------------
    # Session I/O Functions
    # ---------------------------------------------------------------------------

    def load_session(self):

        # creates the spikewrap session object
        self._s = sw.Session(
            subject_path=self._subject_path,
            session_name=self._session_name,
            file_format=self._file_format,
            run_names=self._run_names,
            output_path=self._output_path,
        )

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

    # ---------------------------------------------------------------------------
    # Protected Properties
    # ---------------------------------------------------------------------------

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
