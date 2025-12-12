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
    plot_views = ['waveform', 'upset', 'unitmet', 'unithist']

    # widget dimensions
    dx_gap = 15

    def __init__(self, main_obj):
        # initialises the property widget
        super(PostProcProps, self).__init__(main_obj, 'postprocess', None)

        # sets the input arguments
        self.main_obj = main_obj

        # widget layout setup
        self.pp_layout = QVBoxLayout()

        # tab class widget setup
        self.tab_group_pp = cw.create_tab_group(self)

        # other class fields
        self.tabs = []
        self.mm_name = []
        self.is_updating = False

        # initialises the property tabs
        self.init_class_fields()
        self.init_pp_fields()
        self.init_pp_group()
        self.init_pp_tabs()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        # creates the combobox group
        self.soln_combo = cw.QLabelCombo(None, 'Solution Name: ', None, None, font_lbl=cw.font_lbl)

        # creates the combobox
        self.soln_combo.setSizePolicy(QSizePolicy(cf.q_min, cf.q_max))
        self.soln_combo.setContentsMargins(0, 5, 5, 5)
        self.soln_combo.connect(self.combo_soln_name)

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
            self.tabs.append(tab_widget)

            # adds the tab to the tab group
            self.tab_group_pp.addTab(tab_widget, t_lbl)

    def add_soln_file(self, mm_name_new):

        # adds the solver solution file name
        self.mm_name.append(mm_name_new)

        # adds the new field to the combobox
        self.is_updating = True
        self.soln_combo.obj_cbox.addItem(mm_name_new)
        self.is_updating = False

        # updates the other properties
        self.soln_combo.set_enabled(len(self.mm_name) > 1)

    # ---------------------------------------------------------------------------
    # View Specific Functions
    # ---------------------------------------------------------------------------

    def reset_waveform_info(self):

        a = 1

    # ---------------------------------------------------------------------------
    # Special Widget Event Functions
    # ---------------------------------------------------------------------------

    def tab_change_pp(self, h_tab):

        pass

    def combo_soln_name(self, h_combo):

        # resets the post-processing tabs/views
        if not self.is_updating:
            self.main_obj.post_process_change(h_combo.currentIndex())

    # ---------------------------------------------------------------------------
    # Miscellaneous Functions
    # ---------------------------------------------------------------------------

    def set_plot_view(self, p_type, p_view):

        p_tab = self.tabs[self.plot_views.index(p_type)]
        p_tab.set_plot_view(p_view)

    def get_tab_view(self, p_type):

        return self.tabs[self.plot_views.index(p_type)]

    def get_field(self, p_fld):

        return self.main_obj.main_obj.session_obj.get_mem_map_field(p_fld)