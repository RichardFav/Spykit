# module import
import re
import time
import docker
import numpy as np
import pandas as pd
from copy import deepcopy
from functools import partial as pfcn

# spykit module imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.threads.utils import ThreadWorker

# spike interface module imports
from spikeinterface.sorters import (available_sorters, installed_sorters, get_sorter_params_description,
                                    get_sorter_description, get_default_sorter_params)

# pyqt6 module import
from PyQt6.QtWidgets import (QMainWindow, QWidget, QFrame, QFormLayout, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLineEdit, QCheckBox, QTabWidget, QSizePolicy, QProgressBar)
from PyQt6.QtCore import pyqtSignal, QTimeLine, Qt, QObject

# widget dimensions
x_gap = 5

# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeSortingDialog:  
"""


class SpikeSortingDialog(QMainWindow):
    # pyqtsignal functions
    prop_updated = pyqtSignal()
    close_spike_sorting = pyqtSignal(bool)

    # widget dimensions
    n_prog = 2
    gap_sz = 5
    dlg_width = 450
    dlg_height = 600
    but_height = 20
    p_row = np.array([20, 1, 2, 1])

    # array class fields
    sort_str = ['Start Spike Sorting', 'Cancel Spike Sorting']

    # sorter tab groupings
    sorter_groups = {
        'Local': 'local',
        'Docker Images': 'image',
        'Repositories': 'other',
        'Custom': 'custom',
    }

    # sorter group descriptions
    sorter_group_desc = {
        'local': 'Spikewrap Sorters',
        'image': 'Locally Stored Docker Images',
        'other': 'Available Docker Images',
        'custom': 'Custom Sorters',
    }

    # widget stylesheets
    border_style = "border: 1px solid;"
    no_border_style = "border: 0px; padding-top: 3px;"
    frame_border_style = """
        QFrame#sortFrame {
            border: 1px solid;
        }
    """

    def __init__(self, main_obj=None, ss_config=None):
        super(SpikeSortingDialog, self).__init__(main_obj)

        # sets the input arguments
        self.main_obj = main_obj
        self.ss_config = ss_config

        if main_obj is not None:
            # creates the preprocessing run class object
            self.session = self.main_obj.session_obj.session
            self.prep_opt = [self.session.prep_obj.per_shank, self.session.prep_obj.concat_runs]

            # preprocessing options
            self.per_shank_pp = self.session.prep_obj.per_shank
            self.concat_runs_pp = self.session.prep_obj.concat_runs

        else:
            self.session = None

        # sets the central widget
        self.main_widget = QWidget(self)
        self.ss_obj = SpikeSortPara(self.session)

        # widget layouts
        self.main_layout = QGridLayout()
        self.sort_layout = QVBoxLayout()
        self.progress_layout = QVBoxLayout()
        self.cont_layout = QHBoxLayout()
        self.checkbox_layout = QHBoxLayout()

        # class widgets
        self.sort_frame = QFrame(self)
        self.progress_frame = QFrame(self)
        self.checkbox_frame = QFrame(self)
        self.cont_frame = QFrame(self)
        self.tab_group_sort = QTabWidget(self)

        # other class widget
        self.prog_bar = []
        self.button_cont = []
        self.checkbox_opt = []
        self.solver_tab = {}

        # boolean class fields
        self.has_ss = False
        self.is_running = True
        self.is_updating = False
        self.per_shank = False
        self.concat_runs = False

        # initialisations
        self.s_props = {}
        self.s_prop_flds = {}
        self.g_type = None
        self.s_type = None
        self.t_worker = None

        # initialises the major widget groups
        self.init_class_fields()
        self.init_sorting_frame()
        self.init_checkbox_opt()
        self.init_progress_frame()
        self.init_button_frame()
        self.set_widget_config()

        # REMOVE ME LATER
        self.tab_group_sort.currentWidget().findChild(QTabWidget).setCurrentIndex(1)
        a = 1

    # ---------------------------------------------------------------------------
    # Class Property Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # creates the dialog window
        self.setWindowTitle("Spike Sorting Parameters")
        self.setFixedSize(self.dlg_width, self.dlg_height)
        self.setWindowModality(Qt.WindowModality(1))
        self.setLayout(self.main_layout)

        # sets the main widget properties
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        # resets the frame object names
        for qf in self.findChildren(QFrame):
            qf.setObjectName('sortFrame')

        # sets up the property fields
        for s_type in ['local', 'image', 'other']:
            self.init_sorter_props(s_type)

    def init_button_frame(self):

        # initialisations
        b_str = [self.sort_str[0], 'Close Window']
        cb_fcn = [self.start_spike_sort, self.close_window]

        # sets the control button panel properties
        self.cont_frame.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.cont_frame.setLayout(self.cont_layout)
        self.cont_frame.setStyleSheet(self.frame_border_style)
        self.cont_layout.setContentsMargins(0, 0, 0, 0)
        self.cont_layout.setSpacing(2 * x_gap)

        # creates the control buttons
        for bs, cb in zip(b_str, cb_fcn):
            # creates the button object
            button_new = cw.create_push_button(self, bs, font=cw.font_lbl)
            self.cont_layout.addWidget(button_new)
            self.button_cont.append(button_new)

            # sets the button properties
            button_new.pressed.connect(cb)
            button_new.setFixedHeight(cf.but_height)
            button_new.setStyleSheet(self.border_style)

        # sets the control button properties
        self.button_cont[0].setCheckable(True)

    def init_sorting_frame(self):

        # sets the sorting parameter panel properties
        self.sort_frame.setLayout(self.sort_layout)
        self.sort_frame.setStyleSheet(self.frame_border_style)
        self.sort_layout.setSpacing(0)
        self.sort_layout.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.sort_layout.addWidget(self.tab_group_sort)

        # sets up the sorter tab groups (for each type)
        for i, (gn, gf) in enumerate(self.sorter_groups.items()):
            # creates the sorter group tab
            grp_tab = self.create_sort_group_tab(gf)
            self.tab_group_sort.addTab(grp_tab, gn)
            self.tab_group_sort.setTabEnabled(i, grp_tab.isEnabled())
            self.tab_group_sort.setTabToolTip(i, self.sorter_group_desc[gf])

        # sets the main tab group callback function
        self.tab_group_sort.currentChanged.connect(self.sort_tab_change)

        # resets the tab types
        self.reset_tab_types()

    def init_checkbox_opt(self):

        # initialisations
        c_str = ['Split Recording By Shank', 'Concatenate Experimental Runs']
        cb_fcn = [self.checkbox_split_shank, self.checkbox_concat_expt]

        # sets the frame/layout properties
        self.checkbox_frame.setContentsMargins(x_gap, x_gap, x_gap, x_gap)
        self.checkbox_frame.setLayout(self.checkbox_layout)
        self.checkbox_frame.setStyleSheet(self.frame_border_style)
        self.checkbox_layout.setContentsMargins(2 * x_gap, 0, 2 * x_gap, 0)
        self.checkbox_layout.setSpacing(self.but_height + 2 * self.gap_sz)

        # creates the control buttons
        for cs, cb in zip(c_str, cb_fcn):
            # creates the button object
            checkbox_new = cw.create_check_box(self, cs, False, font=cw.font_lbl)
            self.checkbox_layout.addWidget(checkbox_new)
            self.checkbox_opt.append(checkbox_new)

            # sets the button properties
            checkbox_new.pressed.connect(cb)
            checkbox_new.setFixedHeight(cf.but_height)

        if self.main_obj is not None:
            # sets the by shank checkbox enabled properties
            n_shank = self.main_obj.session_obj.get_shank_count()
            self.checkbox_opt[0].setEnabled((n_shank > 1) and (not self.per_shank_pp))
            self.checkbox_opt[0].setCheckState(cf.chk_state[self.per_shank_pp])

            # sets the concatenation checkbox enabled properties
            n_run = self.session.get_run_count()
            self.checkbox_opt[1].setEnabled((n_run > 1) and (not self.concat_runs_pp))
            self.checkbox_opt[1].setCheckState(cf.chk_state[self.concat_runs_pp])

    def init_progress_frame(self):

        # sets the frame/layout properties
        self.progress_frame.setContentsMargins(0, 0, 0, 0)
        self.progress_frame.setLayout(self.progress_layout)
        self.progress_frame.setStyleSheet(self.frame_border_style)
        self.progress_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_layout.setSpacing(0)

        # creates the progressbar widgets
        for i in range(self.n_prog):
            prog_bar_new = cw.QDialogProgress(font=cw.font_lbl, is_task=bool(i))
            prog_bar_new.set_enabled(False)
            prog_bar_new.setContentsMargins(x_gap, x_gap, x_gap, i * x_gap)

            self.prog_bar.append(prog_bar_new)
            self.progress_layout.addWidget(prog_bar_new)

    def init_sorter_props(self, s_type):

        # retrieves the sorter list
        self.s_prop_flds[s_type] = {}
        s_list = getattr(self.ss_obj, '{0}_s'.format(s_type))

        # -----------------------------------------------------------------------
        # Sorting Properties
        # -----------------------------------------------------------------------

        for sl in s_list:
            # sets an empty sorter name (some sorters don't have descriptions)
            s_name = None
            s_desc = None

            # sets the sorter specific parameter fields
            match sl:
                case 'ironclust':
                    # case is Ironcluster
                    s_name = 'IronClust'
                    s_desc =("Ironclust is a density-based spike sorter designed for high-density probes \n"
                             "(e.g. Neuropixels). It uses features and spike location estimates for clustering, and \n"
                             "it performs a drift correction. For more information see https://doi.org/10.1101/101030")

                case 'simple':
                    # case is simple
                    s_name = 'Simple'
                    s_desc =  ("Implementation of a very simple sorter usefull for teaching.\n\n"
                              " * detect peaks\n"
                              " * project waveforms with SVD or PCA\n"
                              " * apply a well known clustering algos from scikit-learn\n\n"
                              "No template matching. No auto cleaning.\n\n"
                              "Mainly usefull for few channels (1 to 8), teaching and testing.")

                case 'tridesclous2':
                    # case is Tridesclous2
                    s_name = 'Tridesclous2'
                    s_desc = ("Tridesclous2 is a template-matching spike sorter with a real-time engine.\n"
                              "For more information see https://tridesclous.readthedocs.io")

                case 'waveclus_snippets':
                    # case is Wave Clus
                    s_name = 'Wave Clus Snippets'

            if s_desc is None:
                s_desc = get_sorter_description(sl)
                if (s_desc is None) or (len(s_desc) == 0):
                    s_desc = 'No Description'

            # retrieves the sorter description and name fields
            if s_name is None:
                s_name = self.get_sorter_name(s_desc)

            # sets the property fields for the sorter
            self.s_prop_flds[s_type][sl] = {
                'name': s_name,
                'desc': s_desc,
                'tab': None,
                'props': {},
            }

    def set_widget_config(self):

        # main layout properties
        self.main_layout.setHorizontalSpacing(x_gap)
        self.main_layout.setVerticalSpacing(x_gap)
        self.main_layout.setContentsMargins(2 * x_gap, x_gap, 2 * x_gap, 2 * x_gap)
        self.setLayout(self.main_layout)

        # adds the main widgets to the main layout
        self.main_layout.addWidget(self.sort_frame, 0, 0, 1, 1)
        self.main_layout.addWidget(self.checkbox_frame, 1, 0, 1, 1)
        self.main_layout.addWidget(self.progress_frame, 2, 0, 1, 1)
        self.main_layout.addWidget(self.cont_frame, 3, 0, 1, 1)

        # set the grid layout column sizes
        self.main_layout.setRowStretch(0, self.p_row[0])
        self.main_layout.setRowStretch(1, self.p_row[1])
        self.main_layout.setRowStretch(2, self.p_row[2])
        self.main_layout.setRowStretch(3, self.p_row[3])

    # ---------------------------------------------------------------------------
    # Property Field Functions
    # ---------------------------------------------------------------------------

    def create_sorter_tab_group(self, grp_type):

        # retrieves the list of sorters
        s_list = getattr(self.ss_obj, '{0}_s'.format(grp_type))

        #
        return len(s_list)

    def create_sort_group_tab(self, p_str):

        # creates the tab widget
        obj_tab = QWidget()
        obj_tab.setObjectName(p_str)

        # creates the children objects for the current parent object
        tab_layout = QFormLayout(obj_tab)
        tab_layout.setSpacing(0)
        tab_layout.setContentsMargins(1, 1, 0, 0)
        tab_layout.setLabelAlignment(cf.align_type['right'])

        # creates the panel object
        panel_frame = QFrame()
        panel_frame.setFrameStyle(QFrame.Shadow.Plain | QFrame.Shape.Box)
        panel_frame.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        tab_layout.addWidget(panel_frame)

        # sets up the parameter layout
        layout_para = QVBoxLayout()
        layout_para.setSpacing(x_gap)

        # sets up the sort group tab
        s_list = getattr(self.ss_obj, '{0}_s'.format(p_str))
        if len(s_list):
            # field retrieval
            s_prop_tab = self.s_prop_flds[p_str]

            # creates the tab group widget
            obj_tab_group = QTabWidget(self)
            layout_para.addWidget(obj_tab_group)
            layout_para.setContentsMargins(x_gap, x_gap, x_gap, x_gap)

            # creates the solver parameter tabs
            for i, (k, v) in enumerate(s_prop_tab.items()):
                # creates the spike sorter tab object
                obj_tab_para = SpikeSorterTab(self, k)
                obj_tab_group.addTab(obj_tab_para, v['name'])
                obj_tab_group.setTabToolTip(i, v['desc'])

                # stores the tab widget
                s_prop_tab[k]['tab'] = obj_tab_para

            # sets the tabgroup callback function
            obj_tab_group.currentChanged.connect(self.sort_tab_change)

        else:
            obj_tab.setEnabled(False)

        # sets the tab layout
        panel_frame.setLayout(layout_para)
        obj_tab.setLayout(tab_layout)

        # returns the tab object
        return obj_tab

    # ---------------------------------------------------------------------------
    # Widget Event Functions
    # ---------------------------------------------------------------------------

    def checkbox_split_shank(self):

        self.per_shank = self.checkbox_opt[0].checkState() == cf.chk_state[False]

    def checkbox_concat_expt(self):

        self.concat_runs = self.checkbox_opt[1].checkState() == cf.chk_state[False]

    def sort_tab_change(self):

        # resets the tab types
        self.reset_tab_types()

        # retrieves the currently selected tab properties
        s_prop_t = self.s_prop_flds[self.g_type][self.s_type]['tab']
        if not s_prop_t.is_init:
            # initialise the sorter tab (if not initalised)
            s_prop_t.setup_tab_objects()

        # REMOVE ME LATER
        a = 1

    def prop_update(self, p_str, h_obj):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        if isinstance(h_obj, QCheckBox):
            self.check_prop_update(h_obj, p_str)

        elif isinstance(h_obj, QLineEdit):
            self.edit_prop_update(h_obj, p_str)

        # flag that the property has been updated
        self.prop_updated.emit()

    def check_prop_update(self, h_obj, p_str):

        cf.set_multi_dict_value(self.s_props, p_str, h_obj.isChecked())

    def edit_prop_update(self, h_obj, p_str):

        # field retrieval
        str_para = []
        nw_val = h_obj.text()

        if p_str in str_para:
            # case is a string field
            cf.set_multi_dict_value(self.s_props, p_str, nw_val)

        else:
            # determines if the new value is valid
            chk_val = cf.check_edit_num(nw_val, min_val=0)
            if chk_val[1] is None:
                # case is the value is valid
                cf.set_multi_dict_value(self.s_props, p_str, chk_val[0])

            else:
                # otherwise, reset the previous value
                p_val_pr = self.s_props[p_str[0]][p_str[1]]
                if (p_val_pr is None) or isinstance(p_val_pr, str):
                    # case is the parameter is empty
                    h_obj.setText('')

                else:
                    # otherwise, update the numeric string
                    h_obj.setText('%g' % p_val_pr)

    def start_spike_sort(self):

        # if manually updating, then exit
        if self.is_updating:
            return

        # resets the button state
        self.is_running = not self.button_cont[0].isChecked()

        if self.is_running:
            # sets up the configuration dictionary
            sort_config = self.setup_config_dict()

            # retrieves the preprocessing information
            prep_obj = self.main_obj.session_obj.session.prep_obj
            sort_opt = (prep_obj.per_shank, prep_obj.concat_runs)

            # starts running the pre-processing
            self.setup_spike_sorting_worker((sort_config, sort_opt))

        else:
            # case is cancelling the calculations
            self.is_running = False

            # stops the worker
            self.t_worker.force_quit()
            self.t_worker.deleteLater()
            time.sleep(0.01)

            # disables the progressbar fields
            for pb in self.prog_bar:
                pb.set_progbar_state(False)

            # resets the other properties
            self.set_preprocess_props(True)
            self.button_control[0].setText(self.sort_str[0])

    def close_window(self):

        # runs the post window close functions
        self.close_spike_sorting.emit(self.has_ss)

        # closes the window
        self.close()

    # ---------------------------------------------------------------------------
    # Spike Sorting Worker Functions
    # ---------------------------------------------------------------------------

    def setup_spike_sorting_worker(self, sort_obj):

        # creates the threadworker object
        self.t_worker = ThreadWorker(self, self.run_spike_sorting_worker, sort_obj)
        self.t_worker.work_finished.connect(self.spike_sorting_complete)

        # starts the worker object
        self.t_worker.start()

    def run_spike_sorting_worker(self, sort_obj):

        # sorting parameters
        sort_config, sort_opt = sort_obj
        per_shank, concat_runs = sort_opt

        # runs the preprocessing
        self.session.sort_obj.sort(sort_config, per_shank, concat_runs)

    def spike_sorting_complete(self):

        # pauses for a little bit...
        time.sleep(0.25)

        # updates the boolean flags
        self.has_ss = True

    def reset_tab_types(self):

        # tab-group change callback function
        h_tab_sel = self.tab_group_sort.currentWidget()
        self.g_type = h_tab_sel.objectName()

        # retrieves the sub-group type
        h_tab_grp_sub = h_tab_sel.findChild(QTabWidget)
        self.s_type = h_tab_grp_sub.currentWidget().objectName()


    # ---------------------------------------------------------------------------
    # Worker Progress Functions
    # ---------------------------------------------------------------------------

    def worker_progress(self, pr_type, pr_dict):

        # initialisations
        pr_val = None
        m_str = [None, None]

    def setup_overall_progress_msg(self):

        # initialisations
        m_str0 = 'Progress'

    # ---------------------------------------------------------------------------
    # Miscellaneous Methods
    # ---------------------------------------------------------------------------

    def setup_config_dict(self):

        return {'sorting': {self.s_type: self.s_props[self.s_type]}}

    # ---------------------------------------------------------------------------
    # Static Methods
    # ---------------------------------------------------------------------------

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None,
                          p_min=None, p_max=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'ch_fld': ch_fld, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'p_min': p_min, 'p_max': p_max}

    @staticmethod
    def get_sorter_name(s_desc):

        # memory allocation
        s_name_list = []

        # search for the words that comprise the sorter name (capitalised words)
        for s_desc_sp in s_desc.split():
            if s_desc_sp[0].isupper() or s_desc_sp.isnumeric():
                # if capitalised, then add
                s_name_list.append(s_desc_sp)

            else:
                # otherwise, exit the function
                break

        # returns the final sorter name
        return ' '.join(s_name_list)

# ----------------------------------------------------------------------------------------------------------------------

"""
    RunSpikeSorting:  
"""


class RunSpikeSorting(QObject):

    def __init__(self, s):
        super(RunSpikeSorting, self).__init__()

        # session object
        self.s = s

        # boolean class fields
        self.per_shank = False
        self.concat_runs = False

    def sort(self, ss_config, per_shank, concat_runs):

        # sets the input arguments
        self.per_shank = per_shank
        self.concat_runs = concat_runs
        self.ss_config = ss_config

        # REMOVE ME LATER
        ss_config = {'sorting': {'kilosort4': {'batch_size': 5000}}}

        # runs the spike sorting solver
        self.s.sort(
            ss_config,
            run_sorter_method="local",
            per_shank=self.per_shanke,
            concat_runs=self.concat_runs,
        )

        # initialises the progressbar
        self.update_prep_prog(0)


# ----------------------------------------------------------------------------------------------------------------------

"""
    SpikeSorterTab:  
"""


class SpikeSorterTab(QTabWidget):

    def __init__(self, main_dlg, s_name):
        super(SpikeSorterTab, self).__init__(main_dlg)

        # sets the input arguments
        self.s_name = s_name
        self.main_dlg = main_dlg

        # sets the main widget names
        self.setObjectName(s_name)

        # other class fields
        self.s_props = None
        self.is_init = False

    def setup_tab_objects(self):

        # retrieves the sorter properties
        self.s_props = self.main_dlg.ss_obj.setup_sorter_para(self.s_name)

        a = 1

        # updates the initialisation flag
        self.is_init = True

# ----------------------------------------------------------------------------------------------------------------------

"""
    RunSpikeSorting:  
"""


class SpikeSortPara(QObject):
    # common sorter fields

    # other static class fields
    ig_para = ['shift', 'scale', 'bad_channels', 'datashift', 'fs', 'x_centers']
    l_pattern = rf"(?<={re.escape('spikeinterface/')}).*?(?={re.escape('-')})"

    def __init__(self, s=None):
        super(SpikeSortPara, self).__init__()

        # sets the session object
        self.s = s

        # memory allocation
        self.all_s = available_sorters()
        self.local_s = installed_sorters()
        self.image_s = []
        self.other_s = []
        self.custom_s = []

        # spike sorting parameters
        self.ss_para = {}
        self.ss_info = {}

        # loads the sorting parameters
        self.load_sort_para()

        # # REMOVE ME LATER
        # for s in self.all_s:
        #     # if s == 'kilosort4':
        #     #     continue
        #
        #     print('Sorter: {0}'.format(s))
        #     self.setup_sorter_para(s)

    def load_sort_para(self):

        # sets up the property fields
        self.get_sorter_info()

        # reads the spike sorting parameter csv file
        df = pd.read_csv(cw.ssort_para, header=0)
        for row in df.itertuples():
            self.ss_info[row.Parameter] = {
                'label': row.Label,
                'type': row.Type,
                'min': row.Min,
                'max': row.Max,
                'class': row.Class,
            }

    def get_sorter_info(self):

        try:
            # retrieves the docker client
            client = docker.from_env(timeout=5)
            image_list = client.images.list()

        except:
            # if there was a timeout error, then exit
            return

        # sets the other sorters
        self.other_s = list(set(self.all_s) - set(self.local_s))
        self.other_s.sort()

        # removes any local sorters from the other sorters list
        for l_sort in self.local_s:
            if l_sort in self.other_s:
                i_match = self.other_s.index(l_sort)
                self.other_s.pop(i_match)

        # removes any docker images from the other sorters list
        for img_l in image_list:
            # retrieves the sorter name from the repo tag
            r_tag = img_l.attrs['RepoTags'][0]
            s_name = re.search(self.l_pattern, r_tag)[0]

            # if the sorter is in the other sorters list, then remove it and add to the image sorter list
            if s_name in self.other_s:
                self.image_s.append(s_name)
                i_match = self.other_s.index(s_name)
                self.other_s.pop(i_match)

    def setup_sorter_para(self, s_name):

        # initialisations
        p_info = get_default_sorter_params(s_name)
        p_desc = get_sorter_params_description(s_name)

        # determines the common info/description fields
        p_fld_common = list(set(p_info.keys()).intersection(set(p_desc.keys())))
        match s_name:
            # appends parameter fields (based on sorter type)
            case 'tridesclous2':
                # case is the tridesclous2 sorter
                p_fld_common += ['apply_motion_correction', 'motion_correction']

        # stores the parameter field for the sorter
        return self.setup_sorter_para_fields(s_name, p_fld_common, p_info, p_desc)

    def setup_sorter_para_fields(self, s_name, p_fld, p_value, p_desc=None, d_name=None, i_lvl=0):

        # initialisations
        p_dict = {}

        # sets up the fields for all common parameters in the sorter
        for pf in p_fld:
            # skip any parameters that are being ignored
            if pf in self.ig_para:
                continue

            # sets up the base parameter field
            p_desc_f = self.get_description_field(p_desc, pf)
            p_dict[pf] = self.setup_para_field(self.ss_info[pf], p_value[pf], p_desc_f, i_lvl)

            # sets parameter specific fields
            p_type = p_dict[pf]['type']
            match p_type:
                case p_type if p_type in ['edit_float', 'edit_int', 'group_edit_float', 'group_edit_int']:
                    # case is a numerical float
                    p_dict[pf] = self.setup_para_limits(pf, p_dict[pf])

                case 'combobox':
                    # case is a combobox (enumeration)
                    p_dict[pf]['list'] = self.setup_para_list(pf, s_name, d_name)

                case 'dict':
                    # case is a dictionary field
                    p_dict[pf]['child'] = self.setup_para_dictionary(pf, p_dict[pf], s_name)

        # returns the dictionary
        return p_dict

    def setup_para_limits(self, p_fld, p_dict):

        # sets the lower parameter limit
        p_lim_lo = 0 if p_dict['isint'] else 0.

        # sets the lower/upper limits
        p_dict['min'] = self.get_limit_value(p_dict['min'], p_lim_lo)
        p_dict['max'] = self.get_limit_value(p_dict['max'], np.inf)

        return p_dict

    def setup_para_dictionary(self, p_fld, p_dict, s_name, d_name=None):

        # memory allocation
        p_fld_ch = p_dict['value']
        i_lvl_ch = p_dict['lvl'] + 1
        return self.setup_sorter_para_fields(s_name, list(p_fld_ch.keys()), p_fld_ch, d_name=p_fld, i_lvl=i_lvl_ch)

    def setup_para_list(self, p_fld, s_name, d_name=None):

        match p_fld:
            case 'amplitude_mode':
                # case is amplitude mode (spykingcircus2)
                return ['extremum', 'at_index', 'peak_to_peak']

            case 'clusterer':
                # case is the clusterer
                return ['hdbscan']

            case 'cluster_selection_method':
                # case is the cluster selection methods (simple/tridesclous2)
                return ['leaf', 'eom']

            case 'common_ref_type':
                # case is the common reference type (ironclust)
                return ['none', 'mean', 'median', 'trimmean']

            case 'common_reference':
                # case is the common reference calculation type (herdingspikes)
                return ['average', 'median']

            case 'detect_sign':
                # case is the peak detection sign
                match s_name:
                    case s_name if s_name in ['combinato', 'hdsort', 'mountainsort4', 'tridesclous']:
                        # case is the older sorter types
                        return ['neg', 'pos']

                    case _:
                        # case is the newer sorter types
                        return ['neg', 'pos', 'both']

            case 'dtype':
                # case is the data type (fixed)
                return ['int16']

            case 'feature_type':
                # case is the feature type
                match s_name:
                    case 'ironclust':
                        # case is the ironclust sorter
                        return ['gpca', 'pca', 'vpp', 'vmin', 'vminmax', 'cov', 'energy', 'xcov']

                    case s_name if s_name in ['waveclus', 'waveclus_snippets']:
                        # case is the waveclus/waveclus_snippets sorters:
                        return ['wav', 'pca']

            case p_fld if p_fld in ['filter_type', 'filter_detect_type']:
                # case is the filter/filter detect types (ironclust)
                return ["none", "bandpass", "wiener", "fftdiff", "ndiff"]

            case 'ftype':
                # case is the filtering function type (spykingcircus2)
                return ['bessel']                       # QUESTION: Any more filtering functions?!

            case 'loop_mode':
                # case is the loop mode (hdsort)
                return ['loop', 'local_parfor', 'grid']

            case 'method':
                # case is the method selection
                match d_name:
                    case d_name if d_name in ['clustering', 'matching']:
                        # case is clustering/matching dictionary
                        match s_name:
                            case s_name if s_name in ['spykingcircus2', 'tridesclous2']:
                                # case is the spykingcircus2 sorter
                                return ['naive', 'tridesclous', 'circus', 'circus-omp-svd', 'wobble']

                            case 'simple':
                                # case is the simple sorter
                                return ['hdbscan']              # QUESTION: Any more filtering functions?!

                    case 'detection':
                        # case is the detection dictionary
                        return ['by_channel', 'locally_exclusive', 'locally_exclusive_cl',
                                'by_channel_torch', 'locally_exclusive_torch', 'matched_filtering']

                    case 'selection':
                        # case is the selection dictionary (spykingcircus2/tridesclous2)
                        return ['uniform', 'uniform_locations', 'smart_sampling_amplitudes',
                                'smart_sampling_locations', 'smart_sampling_locations_and_time']

                    case 'sparsity':
                        # case is the sparsity dictionary (spykingcircus2)
                        return ['radius', 'best_channels', 'closest_channels', 'snr', 'amplitude', 'energy']

            case 'mode':
                # case is the mode selection
                match d_name:
                    case 'cache_preprocessing':
                        # case is cache preprocessing (spykingcircus2/tridesclous2)
                        return ['memory', 'folder', 'zarr']

                    case 'whitening':
                        # case is whitening (spykingcircus2)
                        return ['local', 'global']

            case 'peak_sign':
                # case is the peak sign (simple/spykingcircus2/tridesclous2)
                return ['neg', 'pos', 'both']

            case 'preprocessing_function':
                # case is the preprocessing function (pykilosort)
                return ['kilosort2', 'destriping']

            case 'preset':
                # case is the motion correction presets (spykingcircus2/tridesclous2)
                return ['dredge', 'dredge_fast', 'nonrigid_accurate',
                        'nonrigid_fast_and_accurate', 'rigid_fast', 'kilosort_like']

            case 'scheme':
                # case is the sorting scheme
                return ['1', '2', '3']

            case 'scheme2_training_recording_sampling_mode':
                # case is the scheme 2 training sampling mode (mountainsort5)
                return ['initial', 'uniform']

            case 'torch_device':
                # case is the torch device (kilosort4)
                return ['auto', 'cuda', 'cpu']

            case 'version':
                # case is the ironclust version (ironclust)
                return ['1', '2']

    def setup_para_field(self, ss_info, value, desc, lvl=0):

        # sets the integer flag
        isint = ss_info['type'] in ['group_edit_int', 'edit_int']

        return {
            # common parameter fields
            'label': ss_info['label'],
            'value': value,
            'type': ss_info['type'],
            'class': ss_info['class'],
            'desc': desc,
            'lvl': lvl,

            # numerical fields
            'isint': isint,
            'min': self.convert_string(ss_info['min'], isint),
            'max': self.convert_string(ss_info['max'], isint),

            # combobox fields
            'list': [],

            # children parameter fields (dictionaries)
            'child': {},
        }

    def get_para_label(self, p_fld, s_type):

        pass

    def get_para_type(self, p_fld, s_type):

        pass

    @staticmethod
    def get_limit_value(p_val, p_val_def):

        if np.isnan(p_val) or np.isinf(p_val):
            # case is the parameter value is not set, so use the default value
            return p_val_def

        else:
            # otherwise, return the limit value
            return p_val

    @staticmethod
    def convert_string(p_val_str, isint):

        if isint:
            # case is an integer string
            try:
                return int(p_val_str)
            except:
                return np.nan

        else:
            # case is a float string
            try:
                return float(p_val_str)
            except:
                return np.nan

    @staticmethod
    def get_description_field(p_desc, pf):

        match pf:
            case 'apply_motion_correction':
                return 'Apply Motion Correction?'

            case 'motion_correction':
                return 'Motion Correction Parameters'

            case _:
                return '' if (p_desc is None) else p_desc[pf]