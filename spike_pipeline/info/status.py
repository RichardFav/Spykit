# custom module imports
import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.common_func as cf
from spike_pipeline.info.utils import InfoWidgetPara

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QFrame, QTabWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QListWidget, QGridLayout, QSpacerItem, QDialog)
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtCore import QSize

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
    # array class fields
    tree_hdr = ['Property', 'Value']
    pp_flds = {
        'common': 'Common Parameters',
        'coh_psd': 'Coherence + PSD Method Parameters',
        'std_map': 'Std Dev/Map Method Parameters',
    }

    def __init__(self, t_str):
        super(StatusInfoTab, self).__init__(t_str, layout=QFormLayout)

        # initialises the major widget groups
        self.setup_prop_fields()
        self.init_filter_edit()
        self.init_property_frame()

    def setup_prop_fields(self):

        # list arrays
        dir_list = ["x", "y", "z"]
        loc_list = ["top", "bottom", "both"]
        met_list = ["coherence + psd", "std", "mad", "neighborhood_r2"]

        # sets up the parameter fields
        pp_str = [
            # common parameters
            {
                'methods': self.create_para_field('Detection Method', 'combobox', met_list[0], p_list=met_list),
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
                'direction': self.create_para_field('Depth Direction', 'combobox', dir_list[0], p_list=dir_list),
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
