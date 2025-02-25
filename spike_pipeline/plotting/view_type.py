# module import
import os

# PyQt6 module imports
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# spikewrap/spikeinterface module imports
import spike_pipeline.common.common_widget as cw
from spike_pipeline.plotting.trace import TracePlot
from spike_pipeline.plotting.probe import ProbePlot

# list of all plot types
plot_types = {
    'trace': TracePlot,         # trace plot type
    'probe': ProbePlot,         # probe plot type
}

# list of plot title names
plot_names = {
    'trace': 'Trace View',
    'probe': 'Probe View',
}

# alignment flags
align_flag = {
    'top': Qt.AlignmentFlag.AlignTop,
    'bottom': Qt.AlignmentFlag.AlignBottom,
    'left': Qt.AlignmentFlag.AlignLeft,
    'right': Qt.AlignmentFlag.AlignRight,
    'center': Qt.AlignmentFlag.AlignCenter,
}

# label/header font objects
font_lbl = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold)
font_hdr = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)
font_panel = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

# file path/filter modes
f_mode_ssf = "Spike Pipeline Session File (*.ssf)"

# parameter/resource folder paths
data_dir = "C:\\Work\\Other Projects\\EPhys Project\\Data"
icon_dir = os.path.join(os.getcwd(), 'resources', 'icons')
para_dir = os.path.join(os.getcwd(), 'resources', 'parameters').replace('\\', '/')

# icon paths
icon_path = {
    'open': os.path.join(icon_dir, 'open_icon.png'),
    'restart': os.path.join(icon_dir, 'restart_icon.png'),
    'close': os.path.join(icon_dir, 'close_icon.png'),
    'reset': os.path.join(icon_dir, 'reset_icon.png'),
    'save': os.path.join(icon_dir, 'save_icon.png'),
}