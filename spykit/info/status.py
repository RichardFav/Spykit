#
from copy import deepcopy

# custom module imports
import spykit.common.common_widget as cw
import spykit.common.common_func as cf
from spykit.info.utils import InfoWidgetPara
from spykit.threads.utils import ThreadWorker

# pyqt imports
from PyQt6.QtWidgets import (QSpinBox, QFrame, QTabWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QListWidget, QGridLayout, QSpacerItem, QDialog)
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtCore import QSize, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# preprocessing task map dictionary
status_task_map = {
    'Common Parameters': 'common',
    'Coherence + PSD Method Parameters': 'coh_psd',
    'Std Dev/Map Method Parameters': 'std_map',
}


# ----------------------------------------------------------------------------------------------------------------------

"""
    StatusInfoTab:
"""


class StatusInfoTab(InfoWidgetPara):
    # pyqtSignal functions
    start_recalc = pyqtSignal(object)
    cancel_recalc = pyqtSignal()

    # array class fields
    tree_hdr = ['Property', 'Value']
    b_str = ['Recalculate Channel Status', 'Cancel Channel Status Calculations']
    pp_flds = {
        'common': 'Common Parameters',
        'coh_psd': 'Coherence + PSD Method Parameters',
        'std_map': 'Std Dev/Map Method Parameters',
    }

    def __init__(self, t_str, main_obj):
        super(StatusInfoTab, self).__init__(t_str, main_obj, layout=QFormLayout)

        # class widgets
        self.toggle_calc = cw.create_push_button(None, self.b_str[0], cw.font_lbl)

        # initialises the major widget groups
        self.setup_prop_fields()
        self.init_filter_edit()
        self.init_property_frame()
        self.init_toggle_button()

        # copies the original properties
        self.t_worker = None
        self.p_props0 = deepcopy(self.p_props)

        # # special property fields
        # self.spin_neighbor_count = self.findChild(QSpinBox, name='n_neighbors')
        # self.spin_neighbor_count.setSingleStep(2)

        #
        self.prop_updated.connect(self.status_prop_updated)

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def setup_prop_fields(self):

        # list arrays
        dir_list = ["x", "y", "z"]
        loc_list = ["top", "bottom", "both"]
        met_list = ["coherence+psd", "std", "mad", "neighborhood_r2"]

        # sets up the parameter fields
        pp_str = [
            # common parameters
            {
                'method': self.create_para_field('Detection Method', 'combobox', met_list[0], p_list=met_list),
                'noisy_channel_threshold': self.create_para_field('Noisy Channel Threshold', 'edit', 1.0),
                'chunk_duration_s': self.create_para_field('Chunk Duration (s)', 'edit', 0.3),
                'num_random_chunks': self.create_para_field('Random Chunk Count', 'edit', 100),
                'welch_window_ms': self.create_para_field('Welch Window Size', 'edit', 10.0),
                'highpass_filter_cutoff': self.create_para_field('Highpass Filter Cutoff', 'edit', 300.0),
                'neighborhood_r2_threshold': self.create_para_field('Neighbourhood Threshold', 'edit', 0.9),
                'neighborhood_r2_radius_um': self.create_para_field('Neighbourhood Radius', 'edit', 30.),
            },

            # coherence+psd method parameters
            {
                'psd_hf_threshold': self.create_para_field('PSD Threshold', 'edit', 0.02),
                'dead_channel_threshold': self.create_para_field('Dead Channel Threshold', 'edit', -0.5),
                'outside_channel_threshold': self.create_para_field('Outside Channel Threshold', 'edit', -0.75),
                'outside_channels_location': self.create_para_field('Outside Channel Location', 'combobox',
                                                                    loc_list[0], p_list=loc_list),
                'n_neighbors': self.create_para_field('Channel Neighbours', 'edit', 11),
                'nyquist_threshold': self.create_para_field('Nyquist Threshold', 'edit', 0.8),
                'direction': self.create_para_field('Depth Direction', 'combobox', dir_list[1], p_list=dir_list),
            },

            # std dev/map method parameters
            {
                'std_mad_threshold': self.create_para_field('Multiplier Threshold', 'edit', 5.),
            },
        ]

        # sets up the property fields for each section
        for pp_k, pp_s in zip(self.pp_flds.keys(), pp_str):
            # sets up the parent fields
            self.p_props[pp_k] = {}
            self.p_prop_flds[pp_k] = {
                'name': self.pp_flds[pp_k],
                'props': pp_s,
            }

            # sets the children properties
            for k, p in pp_s.items():
                self.p_props[pp_k][k] = p['value']

    def init_toggle_button(self):

        self.toggle_calc.setEnabled(False)
        self.toggle_calc.setCheckable(True)
        self.toggle_calc.setFixedHeight(cf.but_height + self.x_gap)
        self.toggle_calc.clicked.connect(self.toggle_click)

        self.tab_layout.addWidget(self.toggle_calc)

    # ---------------------------------------------------------------------------
    # Property Field Functions
    # ---------------------------------------------------------------------------

    def toggle_click(self):

        # updates the button string
        is_checked = self.toggle_calc.isChecked()
        self.toggle_calc.setText(self.b_str[is_checked])

        if is_checked:
            # starts the calculation thread worker
            self.start_recalc.emit(self.p_props)

        else:
            # cancels the calculation thread worker
            self.cancel_recalc.emit()

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def status_prop_updated(self):

        self.toggle_calc.setEnabled(self.p_props0 != self.p_props)