# module import
import numpy as np
from functools import partial as pfcn

# spike pipeline imports
import spykit.props.prop_type as pt
import spykit.common.common_func as cf
import spykit.common.common_widget as cw
from spykit.props.utils import PropWidget, PropPara

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
    TraceProps:
"""


class TraceProps(PropWidget):
    # field properties
    type = 'trace'
    trace_views = ['traceview', 'tracespike']

    # widget dimensions
    dx_gap = 15
    info_width = 210

    def __init__(self, main_obj):
        # initialises the property widget
        super(TraceProps, self).__init__(main_obj, 'trace', None)

        # sets the input arguments
        self.main_obj = main_obj

        # widget layout setup
        self.tr_layout = QVBoxLayout()

        # tab class widget setup
        self.tab_group_tr = cw.create_tab_group(self)

        # other class fields
        self.tabs = []
        self.is_updating = False

        # initialises the property tabs
        self.init_class_fields()
        self.init_trace_fields()
        self.init_trace_group()
        self.init_trace_tabs()

    # ---------------------------------------------------------------------------
    # Class Widget Setup Functions
    # ---------------------------------------------------------------------------

    def init_class_fields(self):

        pass

    def init_trace_fields(self):

        # sets the main widget properties
        self.setFixedWidth(self.main_obj.info_width - self.dx_gap)
        self.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))

        # sets the outer groupbox layout
        self.outer_box.setLayout(self.tr_layout)

    def init_trace_group(self):

        # sets the property tab group properties
        self.tr_layout.setSpacing(0)
        self.tr_layout.setContentsMargins(x_gap_h, x_gap_h, x_gap_h, x_gap_h)
        self.tr_layout.addWidget(self.tab_group_tr)

        # sets up the slot function
        cb_fcn = pfcn(self.tab_change_trace)
        self.tab_group_tr.currentChanged.connect(cb_fcn)
        self.tab_group_tr.setContentsMargins(0, 0, 0, 0)
        self.tab_group_tr.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_min))

    def init_trace_tabs(self):

        # creates the post-processing plot views
        for i_pf, pf in enumerate(self.trace_views):
            # creates the tab widget (based on type)
            t_lbl = pt.prop_names[pf]
            tab_constructor = pt.prop_types[pf]
            tab_widget = tab_constructor(self)
            self.tabs.append(tab_widget)

            # adds the tab to the tab group
            self.tab_group_tr.addTab(tab_widget, t_lbl)

        # sets the other tab properties
        self.set_tab_visible('tracespike', False)

    # ---------------------------------------------------------------------------
    # Special Widget Event Functions
    # ---------------------------------------------------------------------------

    def tab_change_trace(self, h_tab):

        pass

    # ---------------------------------------------------------------------------
    # Class Setter Functions
    # ---------------------------------------------------------------------------

    def set_trace_view(self, p_view):

        # creates the post-processing plot views
        for pf in self.trace_views:
            p_tab = self.tabs[self.trace_views.index(pf)]
            p_tab.set_trace_view(p_view)

    def set_tab_visible(self, t_type, state):

        i_tab = self.trace_views.index(t_type)
        self.tab_group_tr.setTabVisible(i_tab, state)

    # ---------------------------------------------------------------------------
    # Class Getter Functions
    # ---------------------------------------------------------------------------

    def get_tab_view(self, p_type):

        return self.tabs[self.trace_views.index(p_type)]

    def get_field(self, p_fld):

        return self.main_obj.main_obj.session_obj.get_mem_map_field(p_fld)
