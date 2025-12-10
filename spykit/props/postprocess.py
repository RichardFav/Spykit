# module import
import os
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara
import spykit.props.prop_type as pt

# pyqt imports
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal

# ----------------------------------------------------------------------------------------------------------------------

# widget dimensions
x_gap = 5
x_gap2 = 2 * x_gap
x_gap_h = 2

# ----------------------------------------------------------------------------------------------------------------------

"""
    PostProcProps:
"""


class PostProcProps(PropWidget):
    # field properties
    type = 'postprocess'
    plot_views = ['unitmet', 'unithist', 'waveform', 'upset']

    # widget dimensions
    dx_gap = 15

    def __init__(self, main_obj):
        # initialises the property widget
        super(PostProcProps, self).__init__(main_obj, 'postprocess', None)

        # sets the input arguments
        self.main_obj = main_obj

        # widget layout setup
        self.tabs = []
        self.pp_layout = QVBoxLayout()

        # tab class widget setup
        self.tab_group_pp = cw.create_tab_group(self)

        # initialises the property tabs
        self.init_class_fields()
        self.init_pp_fields()
        self.init_pp_group()
        self.init_pp_tabs()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # retrieves the memory mapped file names
        m_files = self.main_obj.session_obj.get_mem_map_files(False)
        self.m_name = [os.path.split(m_files[0, 0, x])[1] for x in range(m_files.shape[2])]

        # creates the combobox
        self.soln_combo = cw.QLabelCombo(
            None, 'Solution Name: ', self.m_name, self.m_name[0], font_lbl=cw.font_lbl)
        self.soln_combo.connect(self.combo_soln_name)
        self.soln_combo.setEnabled(len(self.m_name) > 1)
        self.soln_combo.setSizePolicy(QSizePolicy(cf.q_min, cf.q_max))
        self.soln_combo.setContentsMargins(0, 5, 5, 5)

    def init_pp_fields(self):

        # sets the main widget properties
        self.setFixedWidth(self.main_obj.info_width - self.dx_gap)
        self.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))

        # sets the outer groupbox layout
        self.outer_box.setLayout(self.pp_layout)

    def init_pp_group(self):

        # sets the property tab group properties
        self.pp_layout.setSpacing(0)
        self.pp_layout.setContentsMargins(x_gap_h, x_gap_h, x_gap_h, x_gap_h)
        self.pp_layout.addWidget(self.soln_combo)
        self.pp_layout.addWidget(self.tab_group_pp)

        # sets up the slot function
        cb_fcn = pfcn(self.tab_change_pp)
        self.tab_group_pp.currentChanged.connect(cb_fcn)
        self.tab_group_pp.setContentsMargins(0, 0, 0, 0)
        self.tab_group_pp.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_min))

    def init_pp_tabs(self):

        # creates the post-processing plot views
        for pf in self.plot_views:
            # creates the tab widget (based on type)
            t_lbl = pt.prop_names[pf]
            tab_constructor = pt.prop_types[pf]
            tab_widget = tab_constructor(self)

            # adds the tab to the tab group
            self.tab_group_pp.addTab(tab_widget, t_lbl)

    # ---------------------------------------------------------------------------
    # Special Widget Event Functions
    # ---------------------------------------------------------------------------

    def tab_change_pp(self):

        pass

    def combo_soln_name(self):

        pass