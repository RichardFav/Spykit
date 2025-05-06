import os
import re

import numpy as np
import pandas as pd
from pathlib import Path, PosixPath
from copy import deepcopy
from bigtree import list_to_tree, dataframe_to_tree

import spike_pipeline.common.common_func as cf


class DirectoryCheck(object):
    col_name = ["path", "err"]

    def __init__(self, f_path, f_format):
        super(DirectoryCheck, self).__init__()

        # input fields
        self.f_path = Path(f_path)
        self.f_format = f_format

        # field initialisation
        self.f_pd = None
        self.t_list = None
        self.sub_dict = None
        self.f_type = None
        self.reg_str = None

        # boolean class fields
        self.dir_match = False

    def init_class_fields(self):

        # field initialisations
        self.t_list = []
        self.sub_dict = {}
        self.f_pd = [[], []]

        # initialisations
        _f_type = ['rawdata', 'sub', 'ses', 'ephys']
        _reg_str = [r'rawdata', r'sub-[0-9]{3}', r'ses-[0-9]{3}', r'ephys']

        match self.f_format:
            case 'spikeglx':
                # case is spikeglx recording
                _f_type = _f_type + ['rundir']
                _reg_str = _reg_str + [r'run-[0-9]{3}_g0_imec0']

            case 'openephys':
                # case is openephys recording
                _f_type = _f_type + ['recordnode', 'experiment', 'recording']
                _reg_str = _reg_str + [r'Recording Node [0-9]{3}|RecordNode[0-9]{3}', r'experiment[0-9]', r'recording[0-9]']

        # sets the field type/regular expression strings
        self.f_type, self.reg_str = _f_type, _reg_str

    # FOLDER STRUCTURE CHECK FUNCTIONS ---------------------------------

    def det_all_feas_folders(self):

        # initialises the class fields
        self.init_class_fields()

        # determines the feasible directories
        feas_dir = cf.get_path_matches(self.f_path, self.f_type[0])
        match len(feas_dir):
            case 0:
                # case is there are no feasible directories
                return

            case 1:
                # case is there is a single match
                common_dir = feas_dir[0]

            case _:
                # case is there are multiple matches
                common_dir = os.path.commonpath(feas_dir)

        #
        path_len = len(str(self.f_path))
        if len(common_dir) > path_len:
            self.f_path = self.f_path / common_dir[path_len + 1:]

        # searches each of the feasible directories
        for f in feas_dir:
            f_list_new = ['*'] + f[len(common_dir)+1:].split(os.sep)
            self.check_folder_level(Path(f), f_list_new, 1)

        # converts the tree list to the final dataframe
        self.dir_match = len(self.t_list) > 0
        if self.dir_match:
            # sets up the data frame
            f_pd0 = pd.DataFrame(self.t_list, columns=self.col_name)

            # splits the dataframe into feasible/infeasible directories
            is_feas = np.array([(len(x) == 0) for x in f_pd0['err']])
            self.f_pd = [f_pd0[is_feas], f_pd0[np.logical_not(is_feas)]]

            # determines the unique feasible subjects
            if np.any(is_feas):
                self.det_feas_subject_paths()

    def det_feas_subject_paths(self):

        # initialisations
        r_sub = re.compile(r'sub-[0-9]{3}')
        r_ses = re.compile(r'ses-[0-9]{3}')
        f_dir = np.array(self.f_pd[0]['path'])

        # from all feasible paths, determine the unique paths preceding the subject paths
        dir_sub_pref = [r_sub.split(x)[0] for x in f_dir]
        dir_sub = [r_sub.findall(x)[0] for x in f_dir]

        # determines the unique
        dir_sub_uniq, ind_sub = np.unique(dir_sub_pref, return_inverse=True)
        for i_sub, d_sub_pr in enumerate(dir_sub_uniq):
            # for each subject, determine the unique sessions
            sub_match = np.where(ind_sub == i_sub)[0]
            dir_ses = [r_ses.findall(x)[0] for x in f_dir[sub_match]]
            dir_ses_uniq, ind_ses = np.unique(dir_ses, return_inverse=True)

            # for each session, sets the
            d_sub = '/' + d_sub_pr + dir_sub[sub_match[0]]
            self.sub_dict[d_sub] = {}
            for i_ses, d_ses in enumerate(dir_ses_uniq):
                ses_match = np.where(ind_ses == i_ses)[0]
                self.sub_dict[d_sub][d_ses] = sub_match[ses_match]

    def check_folder_structure(self):
        """check that the folder structure adheres to file format, f_format"""

        # runs the folder check
        self.check_folder_level(self.f_path, [], 0)
        self.f_pd = pd.DataFrame(self.t_list, columns=self.col_name)

    def check_folder_level(self, f_path_prev, t_list_prev, i_lvl):

        # sets up the regexp object
        r = re.compile(self.reg_str[i_lvl])
        f_path_dir = cf.get_folder_dir(f_path_prev)

        if len(f_path_dir) == 0:
            # if there are no files in the directory, then add this to the list
            err_str_new = self.get_structure_error_string(i_lvl - 1, True)
            self.t_list.append(['/'.join(t_list_prev), err_str_new])
            return

        # searches the sub-directories for matches
        for i, fs in enumerate(f_path_dir):
            # sets the new tree list
            t_list_new = deepcopy(t_list_prev) + [fs]

            if r.match(fs) is not None:
                # case is a match has been found
                if (i_lvl + 1) == len(self.reg_str):
                    # case is the final level has been reached
                    self.t_list.append(['/'.join(t_list_new), ""])

                else:
                    # case is there are lower levels to search
                    f_path_new = f_path_prev / fs
                    self.check_folder_level(f_path_new, t_list_new, i_lvl + 1)

            else:
                # otherwise, append the directory to the list
                err_str_new = self.get_structure_error_string(i_lvl, False)
                self.t_list.append(['/'.join(t_list_new), err_str_new])

    # MISCELLANEOUS FUNCTIONS ------------------------------------------

    def set_path(self, f_path_new):

        self.f_path = f_path_new

    def set_format(self, f_format_new):

        self.f_format = f_format_new

    def get_structure_error_string(self, i_lvl, is_empty=False):

        # initialisations
        err_str = None

        match self.f_type[i_lvl]:
            # COMMON DIRECTORY SEARCH ------------------------------

            case 'rawdata':
                if is_empty:
                    err_str = 'Empty "rawdata" folder'

                else:
                    err_str = 'Mislabelled "rawdata" folder'

            case 'sub':
                if is_empty:
                    err_str = 'Empty "subject" folder'

                else:
                    err_str = 'Incorrect "subject" folder format'

            case 'ses':
                if is_empty:
                    err_str = 'Empty "session" folder'

                else:
                    err_str = 'Incorrect "session" folder format'

            case 'ephys':
                if is_empty:
                    err_str = 'Empty "ephys" folder'

                else:
                    err_str = 'Mislabelled "ephys" folder'

            # SPIKEGLX DIRECTORY SEARCH ----------------------------

            case 'rundir':
                if is_empty:
                    err_str = 'Empty "run" folder ({0})'.format(self.f_format)

                else:
                    err_str = 'Incorrect "run" folder format ({0})'.format(self.f_format)

            case 'runfile':
                if is_empty:
                    err_str = 'Missing "*.bin/.meta" file(s)'

                else:
                    err_str = 'Incorrect "*.bin/.meta" file(s) format'

            # OPENEPHYS DIRECTORY SEARCH ---------------------------

            case 'recordnode':
                if is_empty:
                    err_str = 'Empty "Recording Node" folder ({0})'.format(self.f_format)

                else:
                    err_str = 'Incorrect "Recording Node" folder format ({0})'.format(self.f_format)

            case 'experiment':
                if is_empty:
                    err_str = 'Empty "experiment" folder ({0})'.format(self.f_format)

                else:
                    err_str = 'Incorrect "experiment" folder format ({0})'.format(self.f_format)

            case 'recording':
                if is_empty:
                    err_str = 'Missing "recording" folder ({0})'.format(self.f_format)

                else:
                    err_str = 'Incorrect "recording" folder format ({0})'.format(self.f_format)

        # returns the error string
        return err_str


def get_data_folder_structure(f_type):

    # initialisations
    dir_structure = None

    match f_type:
        case 'spikeglx':
            dir_structure = (
                "└── rawdata/",
                "    └── sub-001/",
                "        └── ses-001/",
                "            └── ephys/",
                "                ├── run-001_g0_imec0/",
                "                │   ├── run-001_g0_t0.imec0.ap.bin",
                "                │   └── run-001_g0_t0.imec0.ap.meta",
                "                └── run-002_g0_imec0/",
                "                    ├── run-002_g0_t0.imec0.ap.bin",
                "                    └── run-002_g0_t0.imec0.ap.meta",
            )

        case 'openephys':
            dir_structure = (
                "└── rawdata/",
                "    └── sub-001/",
                "        └── ses-001/",
                "            └── ephys/",
                "                └── Recording Node 304/",
                "                    └── experiment1/",
                "                        ├── recording1/",
                "                        │   └── ...",
                "                        └── recording2/",
                "                            └── ...",
            )

    # returns the directory struct string
    return '\n'.join(dir_structure)
