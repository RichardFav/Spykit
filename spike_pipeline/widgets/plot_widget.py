import os
import functools
import numpy as np
import pyqtgraph as pg
from copy import deepcopy

# pyqt6 module import
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QFormLayout, QGridLayout, QHBoxLayout,
                             QGroupBox, QColorDialog, QScrollArea, QFrame, QSizePolicy, QLayout, QLayoutItem,
                             QLineEdit, QComboBox, QCheckBox, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon

# custom module import
import spike_pipeline.common.common_widget as cw
import spike_pipeline.common.common_func as cf
from spike_pipeline.common.common_widget import (QCollapseGroup, QLabelEdit, QCheckboxHTML, QLabelCombo,
                                                 QTraceTree, QRegionConfig, QLabelButton, QFileSpec)

# label/header font objects
font_lbl = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold)
font_hdr = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

# file path/filter modes
icon_dir = os.path.join(os.getcwd(), 'resources', 'icons')
icon_path = {'pre_processing': os.path.join(icon_dir, 'pre_processing_icon.png'),
             'general': os.path.join(icon_dir, 'general_icon.png'),
             'reset': os.path.join(icon_dir, 'reset_icon.png'),
             'open': os.path.join(icon_dir, 'open_icon.png'),
             'save': os.path.join(icon_dir, 'save_icon.png'),
             'close': os.path.join(icon_dir, 'close_icon.png'),
             'search': os.path.join(icon_dir, 'search_icon')}

# main trace root string
main_name = "Main Trace"

# widget dimensions
x_gap = 15
grp_width = 250

# object dimensions
dlg_width = 1650
dlg_height = 900

min_width = 800
min_height = 450

# MAIN WIDGET OBJECTS --------------------------------------------------------------------------------------------------


class QPlotWidgetMain(QDialog):
    def __init__(self, x=None, y=None):
        super(QPlotWidgetMain, self).__init__()

        # scalar class fields
        self.n_trace = 0
        self.i_trace = None

        # array class fields
        self.tr_obj = []

        # boolean class fields
        self.was_reset = False

        # field initialisations
        self.x = x
        self.y = y

        # field initialisation
        self.setup_dialog()
        self.init_class_fields()

        # sets up the main layout
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        # plot parameter widget setup
        self.obj_para = QPlotPara(self)
        self.main_layout.addWidget(self.obj_para)

        # plot window widget setup
        self.obj_plot = QPlotWindow(self)
        self.main_layout.addWidget(self.obj_plot)

        # sets the event callback functions
        self.obj_para.axes_reset.connect(self.obj_plot.config_reset)

        # creates the trace objects
        self.dx = np.diff(self.x[:2])
        self.tr_obj = [QTraceObject(self, main_name)]
        self.i_trace = 0

    # CLASS INITIALISATION FUNCTIONS -----------------------------------

    def setup_dialog(self):

        # creates the dialog window
        self.setWindowTitle("Plotting Widget")
        self.setMinimumSize(min_width, min_height)
        self.resize(dlg_width, dlg_height)

    def init_class_fields(self):

        if self.x is None:
            # test signals
            self.x = np.arange(0, 4 * np.pi, 1e-6)
            self.y = 1e-2 * np.sin(1e3 * self.x) + np.sin(self.x) + 1e-3 * np.sin(1e10 * self.x)

    # OBSERVER PARAMETER EVENT FUNCTIONS -------------------------------

    def update_trace(self, p_str):

        # if manually updating parameters, then exit
        if self.obj_para.is_updating:
            return

        else:
            # otherwise, set the update flag
            self.obj_para.is_updating = True

        # updates the signal trace object with the new parameter value
        obj_tr_sel = self.tr_obj[self.i_trace]
        setattr(obj_tr_sel.plot_para, p_str, getattr(self.obj_para.p_props, p_str))

        # updates the trace
        obj_tr_sel.plot_obj.update_trace(p_str)

        # resets the update flag
        self.obj_para.is_updating = False

    def trace_operation(self, p_str):

        # if manually updating parameters, then exit
        if self.obj_para.is_updating:
            return

        # updates the signal trace object with the new parameter value
        obj_tr_sel = self.tr_obj[self.i_trace]
        setattr(obj_tr_sel.plot_para, p_str, getattr(self.obj_para.p_props, p_str))

        match p_str:
            # case is showing the trace highlight
            case 'show_child':
                # field retrieval
                is_show = obj_tr_sel.plot_para.show_child

                # shows/hides the linear region object
                obj_tr_sel.plot_obj.l_reg.show() if is_show else obj_tr_sel.plot_obj.l_reg.hide()
                self.obj_para.update_button_props(obj_tr_sel)

            # case is showing the trace highlight
            case 'show_parent':
                # field retrieval
                is_show = obj_tr_sel.plot_para.show_parent

                # shows/hides the linear region object
                obj_tr_sel.plot_obj.l_reg_p.show() if is_show else obj_tr_sel.plot_obj.l_reg_p.hide()
                self.obj_para.update_button_props(obj_tr_sel)

            # case is creating a new trace
            case 'create_trace':
                # creates and appends the trace object
                n_tr_obj = len(self.tr_obj)
                tr_name = self.get_trace_name(obj_tr_sel)
                obj_tr_new = QTraceObject(self, tr_name, obj_tr_sel)
                self.tr_obj.append(obj_tr_new)

                # resets the selected trace index
                self.i_trace = n_tr_obj
                obj_tr_sel.plot_obj.h_child = obj_tr_new

                # resets the show child checkbox
                obj_tr_sel.plot_para.show_child = False
                obj_tr_sel.plot_obj.l_reg.hide()
                self.obj_para.findChild(QCheckboxHTML, name='show_child').set_check(False)

            # case is clipping the existing trace
            case 'clip_trace':
                # prompts the user if they want to reset all the fields
                u_choice = QMessageBox.question(self, 'Clip Trace?',
                                                "Are you sure you want to clip the trace from the parent trace?",
                                                cf.q_yes_no, QMessageBox.StandardButton.Yes)
                if u_choice == QMessageBox.StandardButton.No:
                    # exit if they cancelled
                    return

                # field retrieval
                obj_tr = self.get_trace_object()
                h_tree_pr = obj_tr.h_tree.parent()

                # determines the tree items row index
                i_row = next((i for i in range(h_tree_pr.rowCount()) if (h_tree_pr.child(i) == obj_tr.h_tree)))

                # swaps the rows
                item_tmp = h_tree_pr.takeRow(i_row)
                self.obj_para.obj_ttree.t_model.appendRow(item_tmp)

                # resets the clipped trace object fields
                obj_tr.plot_obj.l_reg_p.deleteLater()
                obj_tr.h_parent.h_child.pop(obj_tr.h_parent.h_child.index(obj_tr))
                obj_tr.h_parent = None

                # resets the show parent checkbox
                obj_tr.plot_para.show_parent = False
                self.obj_para.findChild(QCheckboxHTML, name='show_parent').set_check(False)

                # resets the button properties
                self.obj_para.update_button_props(obj_tr)

                # re-expands all the tree branches
                self.obj_para.obj_ttree.obj_tview.expandAll()

            # case is delete the existing trace
            case 'delete_trace':
                # field retrieval
                obj_tr_rmv = self.tr_obj[self.i_trace]
                has_child = len(obj_tr_rmv.h_child) > 0

                # prompts the user if they want to delete the trace
                m_str = "Are you sure you want to delete the current trace"
                u_choice = QMessageBox.question(self, 'Delete Trace(s)?',
                                                '{0}{1}?'.format(m_str, ' (and descendents)' if has_child else ''),
                                                cf.q_yes_no, QMessageBox.StandardButton.Yes)
                if u_choice == QMessageBox.StandardButton.No:
                    # exit if they cancelled
                    return

                # deletes the currently selected trace object
                obj_tr_rmv.delete()

                if obj_tr_rmv.h_parent is None:
                    # if a root node, then reset to the root trace
                    ind_m = np.where(self.obj_para.obj_rcfig.c_id > 0)
                    self.i_trace = self.obj_para.obj_rcfig.c_id[ind_m[0], ind_m[1]][0] - 1

                else:
                    # otherwise, determine the matching trace
                    self.i_trace = self.get_trace_object_index(obj_tr_rmv.h_parent)

                # resets the axes limit fields
                self.obj_para.reset_axis_limit_fields(self.tr_obj[self.i_trace])

                # resets the selection highlight
                p_gbox = self.tr_obj[self.i_trace].plot_obj.obj_plot_gbox
                p_gbox.setObjectName('selected')
                p_gbox.setStyleSheet(p_gbox.styleSheet())

                # resets the trace-object properties
                tr_obj_nw = self.tr_obj[self.i_trace]
                self.obj_para.reset_para_props(tr_obj_nw)
                self.obj_para.axes_reset.emit(self.obj_para.obj_rcfig)
                self.obj_para.obj_rcfig.obj_lbl_combo.obj_cbox.setCurrentIndex(self.i_trace)

            # case is deleting the descendent traces
            case 'delete_children':
                # field retrieval
                obj_tr_sel = self.tr_obj[self.i_trace]

                # prompts the user if they want to delete the trace
                m_str = "Are you sure you want to delete the descendent traces?"
                u_choice = QMessageBox.question(self, 'Delete Descendent Traces?', m_str,
                                                cf.q_yes_no, QMessageBox.StandardButton.Yes)
                if u_choice == QMessageBox.StandardButton.No:
                    # exit if they cancelled
                    return

                # deletes all the descendent nodes
                for tr_obj_ch in obj_tr_sel.h_child:
                    tr_obj_ch.delete()

                # disables the pushbutton
                self.obj_para.findChild(QPushButton, p_str).setEnabled(False)

    def update_limits(self, p_str):

        # if manually updating parameters, then exit
        if self.obj_para.is_updating:
            return

        # updates the signal trace object with the new parameter value
        obj_tr_sel = self.tr_obj[self.i_trace]
        setattr(obj_tr_sel.plot_para, p_str, getattr(self.obj_para.p_props, p_str))

    # MISCELLANEOUS FUNCTIONS ------------------------------------------

    def change_selected_plot(self, tr_obj_p):

        # removes the current highlight and resets the selected region index
        self.remove_plot_highlight()
        self.i_trace = next((i for i, h in enumerate(self.tr_obj) if (h == tr_obj_p)))

        # resets the parameter properties
        self.obj_para.reset_para_props(self.tr_obj[self.i_trace])

    def trace_added(self, p_obj, tr_name):

        # increments the trace counter
        self.n_trace += 1

        # updates the region configuration widgets
        self.obj_para.obj_rcfig.add_new_trace(tr_name, self.n_trace)

        # adds the widget and update the configuration ID
        self.obj_plot.main_layout.addWidget(p_obj)
        self.obj_plot.main_layout.updateID(self.obj_para.obj_rcfig.c_id, False)

    def remove_plot_highlight(self):

        g_box = self.tr_obj[self.i_trace].plot_obj.obj_plot_gbox
        g_box.setObjectName(None)
        g_box.setStyleSheet(g_box.styleSheet())

    def get_trace_object(self):

        return self.tr_obj[self.i_trace]

    def get_trace_object_index(self, tr_obj):

        return next((i for i, x in enumerate(self.tr_obj) if (x == tr_obj)))

    @staticmethod
    def get_trace_name(_obj_tr):

        if _obj_tr.i_lvl == 0:
            # case is the parent node is the main trace
            return 'Trace {0}'.format(_obj_tr.n_tr + 1)

        else:
            # case is another node type

            # initialisations
            h_p = _obj_tr.h_parent
            f_id = [_obj_tr.n_tr + 1, _obj_tr.tr_id]

            # retrieves the trace count for each of the upper levels
            while h_p.i_lvl > 0:
                f_id.append(h_p.tr_id)
                h_p = h_p.h_parent

            # returns the final trace name
            return 'Trace {0}'.format('/'.join([str(x) for x in np.flip(f_id)]))


# MAIN WIDGET OBJECTS --------------------------------------------------------------------------------------------------


class QPlotPara(QWidget):
    # signal functions
    axes_reset = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        super(QPlotPara, self).__init__(parent)

        # field initialisations
        self.n_para = 0
        self.n_trace = 0
        self.p_info = {}

        # widget initialisation
        self.obj_axlim = None
        self.obj_rcfig = None
        self.obj_ttree = None

        # boolean class fields
        self.is_updating = False

        # field initialisation
        self.h_root = cf.get_parent_widget(self, QPlotWidgetMain)

        # sets up the properties class object
        self.p_props = QParaClass(main_name)
        self.p_props.update_props.connect(self.h_root.update_trace)
        self.p_props.trace_operation.connect(self.h_root.trace_operation)
        self.p_props.update_limits.connect(self.h_root.update_limits)

        # widget setup
        self.main_layout = QFormLayout()
        self.h_scroll = QScrollArea(self)
        self.h_widget_scroll = QWidget()
        self.scroll_layout = QFormLayout()

        # label/header font objects
        self.font_lbl = cw.create_font_obj(is_bold=True, font_weight=QFont.Weight.Bold)
        self.font_hdr = cw.create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

        # initialises the class fields
        self.init_class_fields()

        # sets up the objects for each parameter group
        for i, p in enumerate(self.p_info):
            self.setup_para_group(p, i)

        # sets the object style sheets
        self.update_button_props()
        self.set_styles()

    # CLASS INITIALISATION FUNCTIONS ------------------------------------------

    def init_class_fields(self):

        # initialises the parameter information fields
        self.setup_para_info_fields()

        # sets the main widget properties
        self.setFixedWidth(grp_width + x_gap)
        self.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_exp))
        self.setLayout(self.main_layout)

        # sets the widget layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.h_scroll)

        # SCROLL AREA WIDGET SETUP --------------------------------------------

        # sets the scroll area properties
        self.h_scroll.setWidgetResizable(True)
        self.h_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.h_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.h_scroll.setStyleSheet("background-color: rgba(120, 152, 229, 255) ;")
        self.h_scroll.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        self.h_scroll.setWidget(self.h_widget_scroll)

        # sets the scroll widget layout widget
        self.h_widget_scroll.setLayout(self.scroll_layout)

        # sets the scroll widget layout properties
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

    # PARAMETER WIDGET SETUP --------------------------------------------------

    def setup_para_info_fields(self):

        # TRACE STRUCTURE OBJECTS ---------------------------------------------

        # sets up the subgroup fields
        p_tmp = {
            'obj_tree': self.create_para_field('Trace Structure', 'tree', None),
        }

        # updates the class field
        self.p_info['trace_tree'] = {'name': 'Trace Explorer', 'type': 'v_panel', 'ch_fld': p_tmp}

        # REGION CONFIGURATION OBJECTS ----------------------------------------

        # sets up the subgroup fields
        p_tmp = {
            'r_config': self.create_para_field('Region Configuration', 'rconfig', None),
        }

        # updates the class field
        self.p_info['reg_config'] = {'name': 'Region Configuration', 'type': 'v_panel', 'ch_fld': p_tmp}

        # TRACE PROPERTIES OBJECTS --------------------------------------------

        # group initialisations
        style_list = ['Solid', 'Dash', 'Dot', 'Dash-Dot', 'Dash-Dot-Dot']
        grid_list = ['No Grid', 'X-Direction Only', 'Y-Direction Only', 'Both Directions']

        # sets up the subgroup fields
        p_tmp = {
            'name': self.create_para_field('Name', 'edit', self.p_props.name),
            'p_width': self.create_para_field('Line Width', 'edit', self.p_props.p_width),
            'p_style': self.create_para_field('Line Style', 'combobox', self.p_props.p_style, p_list=style_list),
            'p_col': self.create_para_field('Trace Colour', 'colorpick', self.p_props.p_col),
            'g_style': self.create_para_field('Grid Style', 'combobox', self.p_props.g_style, p_list=grid_list),
        }

        # updates the class field
        self.p_info['tr_prop'] = {'name': 'Current Trace Properties', 'type': 'g_panel', 'ch_fld': p_tmp}

        # TRACE OPERATIONS OBJECTS --------------------------------------------

        # sets up the subgroup fields
        p_tmp = {
            'show_child': self.create_para_field('Show Sub-Trace Region', 'checkbox', False),
            'show_parent': self.create_para_field('Show Parent Region', 'checkbox', False),
            'create_trace': self.create_para_field('Create New Sub-Trace', 'pushbutton', None),
            'clip_trace': self.create_para_field('Clip Highlighted Region', 'pushbutton', None),
            'delete_trace': self.create_para_field('Delete Current Trace', 'pushbutton', None),
            'delete_children': self.create_para_field('Delete Descendent Traces', 'pushbutton', None),
        }

        # updates the class field
        self.p_info['tr_op'] = {'name': 'Trace Operations', 'type': 'v_panel', 'ch_fld': p_tmp}

        # TRACE PROPERTIES OBJECTS --------------------------------------------

        # sets up the subgroup fields
        p_tmp = {
            'ax_lim': self.create_para_field('Axis Limits', 'axeslimits', None)
        }

        # updates the class field
        self.p_info['tr_limits'] = {'name': 'Current Trace Limits', 'type': 'v_panel', 'ch_fld': p_tmp}

    def setup_para_group(self, p, i_grp):

        # retrieves the group properties
        grp_type = self.p_info[p]['type']
        grp_name = self.p_info[p]['name']
        grp_info = self.p_info[p]['ch_fld']

        # creates the collapsible group object
        f_layout = QGridLayout() if grp_type == 'g_panel' else QFormLayout()
        obj_panel_c = QCollapseGroup(self.h_scroll, grp_name, is_first=i_grp == 0, f_layout=f_layout)
        self.scroll_layout.addRow(obj_panel_c)
        obj_panel_c.setFixedWidth(grp_width)

        # sets the button click event function
        cb_fcn_c = functools.partial(self.expand, obj_panel_c)
        obj_panel_c.connect(cb_fcn_c)

        # sets the collapsible panel object properties
        obj_panel_c.setObjectName(p)
        obj_panel_c.expand_button.setFixedHeight(cf.but_height + 1)
        # h_panel_c.expand_button.setIcon(QIcon(icon_path[p]))
        # h_panel_c.expand_button.setIconSize(QSize(cf.but_height, cf.but_height))

        if isinstance(f_layout, QGridLayout):
            for i in range(3):
                f_layout.setColumnStretch(i, 1)

        # creates the parameter objects
        self.n_para = 0
        for ps_ch in grp_info:
            self.create_para_object(obj_panel_c.form_layout, ps_ch, grp_info[ps_ch], [p, ps_ch])
            self.n_para += 1

    def create_para_object(self, layout, p_name, ps, p_str_l):

        # base callback function
        cb_fcn = self.setup_widget_callback()

        match ps['type']:
            # REGULAR WIDGETS -------------------------------------------------

            # case is a text label
            case 'text':
                # creates the label widget combo
                lbl_str = '%g' % (ps['value'])
                obj_lbl = cw.create_text_label(None, '{0}: '.format(ps['name']), font=self.font_lbl)
                obj_txt = cw.create_text_label(None, lbl_str, name=p_name, align='left', font=self.font_lbl)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_txt, self.n_para, 1, 1, 2)

                else:
                    # case is another layout type
                    layout.addRow(obj_lbl, obj_lbl)

            # case is an editbox
            case 'edit':
                # sets the editbox string
                lbl_str = '{0}: '.format(ps['name'])
                if isinstance(ps['value'], str):
                    # parameter is a string
                    edit_str = ps['value']

                else:
                    # parameter is a number
                    edit_str = '%g' % (ps['value'])

                # creates the label/editbox widget combo
                obj_lbledit = QLabelEdit(None, lbl_str, edit_str, name=p_name, font_lbl=self.font_lbl)

                # sets the widget callback function
                obj_lbledit.connect(cb_fcn)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lbledit.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_lbledit.obj_edit, self.n_para, 1, 1, 2)

                else:
                    # case is another layout type
                    layout.addRow(obj_lbledit)

            # case is a combobox
            case 'combobox':
                # creates the label/combobox widget combo
                lbl_str = '{0}: '.format(ps['name'])
                obj_lblcombo = QLabelCombo(None, lbl_str, ps['p_list'], ps['value'], name=p_name,
                                           font_lbl=self.font_lbl)

                # sets the widget callback function
                obj_lblcombo.connect(cb_fcn)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lblcombo.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_lblcombo.obj_cbox, self.n_para, 1, 1, 2)

                else:
                    # case is another layout type
                    layout.addRow(obj_lblcombo)

            # case is a checkbox
            case 'checkbox':
                # creates the checkbox widget
                obj_checkbox = QCheckboxHTML(
                    None, ps['name'], ps['value'], font=self.font_lbl, name=p_name)

                # sets up the checkbox callback function
                cb_fcn_chk = self.setup_widget_callback(obj_checkbox.h_chk)
                obj_checkbox.connect(cb_fcn_chk)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_checkbox, self.n_para, 0, 1, 3)

                else:
                    # case is another layout type
                    layout.addRow(obj_checkbox)

            # case is a pushbutton
            case 'pushbutton':
                # creates the button widget
                obj_button = cw.create_push_button(None, ps['name'], self.font_lbl, name=p_name)

                # sets the callback function
                cb_fcn_but = self.setup_widget_callback(obj_button)
                obj_button.clicked.connect(cb_fcn_but)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_button, self.n_para, 0, 1, 4)

                else:
                    # case is another layout type
                    layout.addRow(obj_button)

            # SPECIAL WIDGETS -------------------------------------------------

            # case is a tree widget
            case 'tree':
                # creates the trace tree widget
                self.obj_ttree = QTraceTree(self, font=self.font_lbl)

                # sets the layout properties
                layout.setSpacing(0)
                layout.addWidget(self.obj_ttree)

            # case is a region configuration widget
            case 'rconfig':
                # creates the region configuration widget
                self.obj_rcfig = QRegionConfig(self, font=self.font_lbl)

                # sets the layout properties
                layout.setSpacing(0)
                layout.addWidget(self.obj_rcfig)

                # connects the config widget slot functions
                self.obj_rcfig.config_reset.connect(self.config_reset)

            # case is a colorpick object
            case 'colorpick':
                # creates the label/editbox widget combo
                lbl_str = '{0}: '.format(ps['name'])
                obj_lblbutton = QLabelButton(None, lbl_str, "", name=p_name, font_lbl=self.font_lbl)
                obj_lblbutton.obj_but.setStyleSheet(
                    "border: 2px solid;"
                    "background-color: {0}".format(ps['value'].name())
                )

                # connects the event function
                obj_lblbutton.connect(self.button_color_pick)

                if isinstance(layout, QGridLayout):
                    # case is adding to a QGridlayout
                    layout.addWidget(obj_lblbutton.obj_lbl, self.n_para, 0, 1, 1)
                    layout.addWidget(obj_lblbutton.obj_but, self.n_para, 1, 1, 2)

                else:
                    # case is another layout type
                    layout.addRow(obj_lblbutton)

            # case is the axes limit widget
            case 'axeslimits':
                # creates the file selection widget
                self.obj_axlim = cw.QAxesLimits(None, font=self.font_lbl, p_props=self.p_props)
                layout.addRow(self.obj_axlim)

            # case is a file selection widget
            case 'filespec':
                # creates the file selection widget
                obj_fspec = QFileSpec(None, ps['name'], ps['value'], name=p_name, f_mode=ps['p_misc'])
                layout.addRow(obj_fspec)

                # sets up the slot function
                cb_fcn = functools.partial(self.button_file_spec, p_str_l)
                obj_fspec.connect(cb_fcn)

    def reset_para_props(self, tr_obj):

        # updates the parameter field
        self.is_updating = True

        # resets the trace property panel properties
        h_group_pr = self.findChildren(QCollapseGroup, name='tr_prop')[0]
        self.reset_widget_values(h_group_pr, self.p_info['tr_prop'], tr_obj.plot_para)

        # updates the name editbox properties (can't alter main trace string)
        h_edit_name = h_group_pr.findChild(QLineEdit, name='name')
        h_edit_name.setEnabled(h_edit_name.text() != main_name)

        # resets the operation panel properties
        h_group_op = self.findChildren(QCollapseGroup, name='tr_op')[0]
        self.reset_widget_values(h_group_op, self.p_info['tr_op'], tr_obj.plot_para)
        self.h_root.obj_para.update_button_props(tr_obj)
        self.h_root.obj_para.reset_axis_limit_fields(tr_obj)

        # sets the axes limit values
        for p in self.h_root.obj_para.obj_axlim.p_str:
            setattr(self.p_props, p, getattr(tr_obj.plot_para, p))

        # updates the parameter field
        self.is_updating = False

    def reset_widget_values(self, h_group, p_info_grp, _p_props):

        for i, p_fld in enumerate(p_info_grp['ch_fld'].keys()):
            p_val = getattr(_p_props, p_fld)
            setattr(self.p_props, p_fld, p_val)
            h_widget_p = h_group.findChildren(QWidget, name=p_fld)[0]

            if isinstance(h_widget_p, QLineEdit):
                # case is a lineedit widget
                if isinstance(p_val, str):
                    # case is a string
                    h_widget_p.setText(p_val)

                else:
                    # case is a number
                    h_widget_p.setText('%g' % p_val)

            elif isinstance(h_widget_p, QComboBox):
                # case is a combobox
                h_widget_p.setCurrentText(p_val)

            elif isinstance(h_widget_p, QCheckBox):
                # case is a checkbox
                h_widget_p.setChecked(p_val)

            elif isinstance(h_widget_p, QCheckboxHTML):
                # case is a checkbox
                h_widget_p.h_chk.setChecked(p_val)

            else:
                # case is another widget type
                match h_widget_p.objectName():
                    case 'p_col':
                        # case is the colour picker
                        h_widget_p.setStyleSheet(
                            "border: 2px solid;"
                            "background-color: {0}".format(p_val.name())
                        )

    def reset_axis_limit_fields(self, tr_obj):

        # flag that manual updating is taking place
        is_updating0 = deepcopy(self.is_updating)
        self.is_updating = True

        # updates the x/y-axis limits
        i_frm = tr_obj.plot_obj.i_frm

        # calculates the axis limits
        if tr_obj.i_lvl == 0:
            x_lim = tr_obj.plot_obj.x_lim
            y_lim = tr_obj.plot_obj.y_lim

        else:
            y_frm = tr_obj.plot_obj.y[range(i_frm[0], i_frm[1])]
            x_lim = tr_obj.plot_obj.x[i_frm]
            y_lim = [np.min(y_frm), np.max(y_frm)]

        # resets the editbox values
        self.obj_axlim.h_edit[0].setText('%g' % x_lim[0])
        self.obj_axlim.h_edit[1].setText('%g' % x_lim[1])
        self.obj_axlim.h_edit[2].setText('%g' % y_lim[0])
        self.obj_axlim.h_edit[3].setText('%g' % y_lim[1])

        # updates the parameter fields
        tr_obj.plot_para.x_min = x_lim[0]
        tr_obj.plot_para.x_max = x_lim[1]
        tr_obj.plot_para.y_min = y_lim[0]
        tr_obj.plot_para.y_max = y_lim[1]

        # resets the duration label string
        self.obj_axlim.obj_lbl_dur.obj_txt.setText('%g' % np.diff(x_lim))

        # updates the editbox enabled properties
        [x.setEnabled(tr_obj.i_lvl > 0) for x in self.obj_axlim.h_edit]

        # resets the update flag
        self.is_updating = is_updating0

    # COLLAPSIBLE PANEL EVENT FUNCTIONS ---------------------------------------

    def expand(self, h_panel_c):

        if self.h_root.was_reset:
            # hack fix - top panel group wants to collapse when editbox value is reset?
            self.h_root.was_reset = False

        else:
            # field retrieval
            h_panel_c.is_expanded = h_panel_c.is_expanded ^ True
            h_panel_c.update_button_text()

            f_style = cw.expand_style if h_panel_c.is_expanded else cw.close_style
            h_panel_c.expand_button.setStyleSheet(f_style)

    #  PROPERTY WIDGET EVENT FUNCTIONS ----------------------------------------

    def widget_para_update(self, h_widget, *_):

        # case is a widget type is not provided
        if isinstance(h_widget, QLineEdit):
            self.edit_para_update(h_widget)

        elif isinstance(h_widget, QComboBox):
            self.combobox_para_update(h_widget)

        elif isinstance(h_widget, QCheckBox):
            self.checkbox_para_update(h_widget)

        elif isinstance(h_widget, QPushButton):
            self.pushbutton_para_update(h_widget)

    def edit_para_update(self, h_edit):
 
        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        nw_val = h_edit.text()
        p_str = h_edit.objectName()
        num_para = ['p_width']

        if p_str in num_para:
            # case is a numerical parameters

            # updates the reset flag
            self.h_root.was_reset = True

            # sets the parameter limiting properties
            p_min, p_max, is_int = -1e6, 1e6, True
            match p_str:
                case 'p_width':
                    # case is the line pen width
                    p_min, p_max = 1, 5

            # determines if the new value is valid
            chk_val = cf.check_edit_num(nw_val, min_val=p_min, max_val=p_max, is_int=is_int)
            if chk_val[1] is None:
                # case is the value is valid
                setattr(self.p_props, p_str, chk_val[0])

            else:
                # otherwise, reset the previous value
                h_edit.setText('%g' % getattr(self.p_props, p_str))

        else:
            # case is the value is valid
            setattr(self.p_props, p_str, nw_val)

    def combobox_para_update(self, h_cbox):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        p_str = h_cbox.objectName()
        nw_val = h_cbox.currentText()

        # updates the parameter field
        setattr(self.p_props, p_str, nw_val)

    def checkbox_para_update(self, h_chk):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        p_str = h_chk.objectName()
        nw_val = h_chk.isChecked()

        # updates the parameter field
        setattr(self.p_props, p_str, nw_val)

        # parameter specific updates
        match p_str:
            case 'show_child':
                # case is show highlight
                self.update_button_props(self.h_root.tr_obj[self.h_root.i_trace])

    def pushbutton_para_update(self, h_button):

        # if manually updating elsewhere, then exit
        if self.is_updating:
            return

        # field retrieval
        p_str = h_button.objectName()
        nw_val = (getattr(self.p_props, p_str) + 1) % 2

        # updates the parameter field
        setattr(self.p_props, p_str, nw_val)

    # WIDGET EVENT FUNCTIONS --------------------------------------------------

    def config_reset(self):

        self.axes_reset.emit(self.obj_rcfig)

    def button_file_spec(self, p_str_l, h_fspec):

        a = 1

    def button_color_pick(self, h_button):

        # runs the colour picker dialog
        p_str = h_button.objectName()
        p_col = QColorDialog.getColor()

        if p_col.isValid():
            # if successful, then update the parameter fields
            h_button.setStyleSheet(
                "border: 2px solid;"
                "background-color: {0}".format(p_col.name())
            )

            # updates the parameter field
            setattr(self.p_props, p_str, p_col)

    # MISCELLANEOUS FUNCTIONS -------------------------------------------------

    def update_button_props(self, tr_obj=None):

        # initialisations
        can_clip, is_child, has_child = False, False, False

        # determines if the trace object is a sub-trace/non-root node
        if tr_obj is not None:
            has_child = len(tr_obj.h_child) > 0
            is_child = tr_obj.h_parent is not None
            if is_child:
                can_clip = tr_obj.h_parent is not None

        # retrieves the operation panel widget
        h_panel_c = self.findChild(QCollapseGroup, 'tr_op')

        # updates the button properties
        h_panel_c.findChild(QPushButton, name='create_trace').setEnabled(self.p_props.show_child)
        h_panel_c.findChild(QPushButton, name='delete_trace').setEnabled(is_child)
        h_panel_c.findChild(QPushButton, name='delete_children').setEnabled(has_child)
        h_panel_c.findChild(QPushButton, name='clip_trace').setEnabled(can_clip)
        h_panel_c.findChild(QCheckboxHTML, name='show_parent').setEnabled(is_child)

    def setup_widget_callback(self, h_widget=None):

        if h_widget is None:
            return self.widget_para_update

        else:
            return functools.partial(self.widget_para_update, h_widget)

    def set_styles(self):

        # sets the style sheets
        self.h_scroll.setStyleSheet("background-color: rgba(120, 152, 229, 255) ;")

    @staticmethod
    def create_para_field(name, obj_type, value, p_fld=None, p_list=None, p_misc=None, ch_fld=None):

        return {'name': name, 'type': obj_type, 'value': value, 'p_fld': p_fld,
                'p_list': p_list, 'p_misc': p_misc, 'ch_fld': ch_fld}


# ----------------------------------------------------------------------------------------------------------------------


class QPlotWindow(QWidget):
    update_id = pyqtSignal()

    def __init__(self, parent=None):
        super(QPlotWindow, self).__init__(parent)

        # field allocation
        self.grid_id = []
        self.h_tree = None
        self.n_row, self.n_col = 1, 1

        # widget setup
        sz_layout = QSize(dlg_width - (grp_width + x_gap), dlg_height)
        self.main_layout = QPlotLayout(self, sz_hint=sz_layout)
        self.bg_widget = QWidget()

        # initialises the class fields
        self.init_class_fields()

    # CLASS INITIALISATION FUNCTIONS -----------------------------------

    def init_class_fields(self):

        # sets the configuration options
        pg.setConfigOptions(antialias=True)

        # sets the main widget properties
        self.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        self.setLayout(self.main_layout)

        # sets the widget layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.bg_widget)

        # creates the background widget
        self.bg_widget.setStyleSheet("background-color: black;")

    # CLASS INITIALISATION FUNCTIONS -----------------------------------

    def config_reset(self, obj_rcfig):

        # hides all the current plot items
        for items in self.main_layout.items[1:]:
            items.widget().hide()

        # field retrieval
        self.main_layout.updateID(obj_rcfig.c_id)


# TRACE OBJECT CLASSES -------------------------------------------------------------------------------------------------


class QTraceObject(object):
    def __init__(self, parent, tr_name, h_parent=None):
        super(QTraceObject, self).__init__()

        # scalar class fields
        self.n_tr = 0
        self.tr_id = 1

        # array class fields
        self.h_child = []

        # boolean class fields
        self.has_child = False

        # field initialisation
        self.parent = parent
        self.h_parent = h_parent
        x_0, y_0 = self.parent.x, self.parent.y

        # boolean fields
        self.is_root = h_parent is None
        self.i_lvl = 0 if self.is_root else (self.h_parent.i_lvl + 1)

        # creates the plot parameter class object
        self.plot_para = QParaTrace(tr_name)
        self.plot_para.show_parent = not self.is_root

        # appends the new tree-item
        self.h_tree = self.parent.obj_para.obj_ttree.add_tree_item(tr_name, h_parent)

        # creates the new plot object
        if self.is_root:
            # case is the root trace

            # creates the root plot widget
            self.plot_obj = QPlotWidget(
                self, x=x_0, y=y_0, hdr=tr_name, p_props=self.plot_para)

        else:
            # case are the sub-traces

            # creates the sub-trace plot widget
            self.plot_obj = QPlotWidget(
                self, x=x_0, y=y_0, hdr=tr_name, p_props=self.plot_para, h_parent=h_parent)
            self.plot_obj.region_moved.connect(self.region_moved)

            # enables the parent line region object
            self.plot_obj.l_reg_p.show()

            # updates the parent trace object fields
            self.h_parent.n_tr += 1
            self.h_parent.h_child.append(self)
            self.tr_id = deepcopy(self.h_parent.n_tr)

        # adds to the trace explorer
        self.parent.obj_para.reset_para_props(self)
        self.parent.trace_added(self.plot_obj, tr_name)

    # EVENT FUNCTIONS --------------------------------------------------

    def region_moved(self):

        self.parent.obj_para.reset_axis_limit_fields(self)

    # MISCELLANEOUS FUNCTIONS ------------------------------------------

    def delete(self):

        # deletes any children objects
        for tr_obj_ch in self.h_child:
            tr_obj_ch.delete()

        # field initialisations
        self.parent.obj_para.is_updating = True
        i_trace0 = self.parent.get_trace_object_index(self)

        # resets the parent trace object fields
        if self.h_parent is not None:
            self.h_parent.plot_obj.h_child = None
            self.h_parent.plot_obj.h_plot.removeItem(self.plot_obj.l_reg_p)
            self.h_parent.h_child.pop(self.h_parent.h_child.index(self))

        # sets the parent widget fields
        self.parent.obj_para.obj_ttree.delete_tree_item(self.h_tree)

        # removes the region configuration items
        self.parent.obj_para.obj_rcfig.delete_existing_trace(self, i_trace0)
        self.parent.tr_obj.pop(i_trace0)

        # removes the plot widget from the main canvas
        self.parent.obj_plot.main_layout.itemAt(i_trace0 + 1).widget().setHidden(True)
        self.parent.obj_plot.main_layout.removeAt(i_trace0 + 1)

        # resets the parameter update flag
        self.parent.obj_para.is_updating = False
        self.parent.n_trace -= 1


# ----------------------------------------------------------------------------------------------------------------------


class QPlotWidget(QWidget):
    # signal functions
    region_moved = pyqtSignal()

    # mouse event function fields
    mp_event_release = None
    mp_event_click = None

    # dimensions
    x_gap_plt = 2
    but_height_plt = 16

    # widget stylesheets
    plot_gbox_style = """
        QGroupBox {
            color: white;
            border: 2px solid white;
            border-radius: 5px;
        }
        QGroupBox::title
        {
            padding: 0px 5px;
            background-color: transparent;
        }
        QGroupBox[objectName='selected'] {
            color: white;
            border: 2px solid red;
            border-radius: 5px;
        }                                    
    """

    def __init__(self, parent_tr=None, x=None, y=None, hdr=None, p_props=None, h_parent=None):
        super(QPlotWidget, self).__init__()

        # array initialisation
        self.i_frm = []
        self.i_frm_ch = []
        self.x_lim = []
        self.x_lim0 = []
        self.y_lim = []

        # widget initialisations
        self.l_reg = None
        self.l_reg_p = None
        self.h_child = None
        self.h_plot_line = None

        # boolean class fields
        self.region_clicked = False
        self.is_updating = False

        # field setup
        self.x = x
        self.y = y
        self.hdr = hdr
        self.p_props = p_props
        self.parent_tr = parent_tr
        self.setParent(parent_tr.parent)

        # widget fields
        self.h_parent = h_parent
        self.pen = self.setup_plot_pen()

        # boolean class fields
        self.is_root = h_parent is None

        # other field initialisations
        self.h_root = cf.get_parent_widget(self, QPlotWidgetMain)

        # sets the panel properties
        self.main_layout = QHBoxLayout()
        self.obj_plot_gbox = QGroupBox(hdr, self)
        self.plot_layout = QVBoxLayout()

        # plot-widget setup
        self.h_plot = pg.PlotWidget()
        self.h_plot_item = self.h_plot.getPlotItem()
        self.h_plot_item.setMouseEnabled(y=False)

        # sets the parent index range (for non-root widgets)
        if not self.is_root:
            self.i_frm = self.h_parent.plot_obj.i_frm_ch

        # sets up the plot widgets
        self.setup_plot_widget()
        self.setup_plot_buttons()
        self.setup_plot_region()

    # CLASS WIDGET SETUP -----------------------------------------------

    def setup_plot_widget(self):

        if not self.is_root:
            self.h_root.remove_plot_highlight()

        # sets the main widget properties
        self.setSizePolicy(QSizePolicy(cf.q_pref, cf.q_exp))
        self.setLayout(self.main_layout)

        # sets the main layout properties
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.obj_plot_gbox)

        # sets the groupbox properties
        self.obj_plot_gbox.setObjectName('selected')
        self.obj_plot_gbox.setFont(font_hdr)
        self.obj_plot_gbox.setCheckable(False)
        self.obj_plot_gbox.setSizePolicy(QSizePolicy(cf.q_exp, cf.q_exp))
        self.obj_plot_gbox.setLayout(self.plot_layout)
        self.obj_plot_gbox.setStyleSheet(self.plot_gbox_style)

        # sets up the
        self.obj_plot_gbox.mousePressEvent = self.click_plot_region

    def setup_plot_buttons(self):

        # initialisations
        f_name = ['reset', 'open', 'save', 'close']
        tt_str = 'Finish Me!'

        # sets up the
        gb_layout = QHBoxLayout()
        gb_layout.setContentsMargins(0, 0, self.x_gap_plt, 0)

        # creates the checkbox object
        obj_grp = QWidget()
        obj_grp.setLayout(gb_layout)
        obj_grp.setStyleSheet("""
            background-color: transparent;
        """)

        # adds the widgets
        obj_gap = QWidget()
        gb_layout.addWidget(obj_gap)
        obj_gap.setStyleSheet("""
            background-color: transparent;
        """)

        # frame layout
        frm_layout = QHBoxLayout()
        frm_layout.setSpacing(self.x_gap_plt)
        frm_layout.setContentsMargins(self.x_gap_plt, self.x_gap_plt, self.x_gap_plt, self.x_gap_plt)

        # frame widget
        obj_frm = QFrame()
        obj_frm.setLayout(frm_layout)
        obj_frm.setFixedHeight(self.but_height_plt + 3 * self.x_gap_plt)
        obj_frm.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))
        obj_frm.setStyleSheet("""
            border: 1px solid white;
        """)

        # creates the push button objects
        for fp in f_name:
            obj_but = cw.create_push_button(None, "")
            obj_but.setIcon(QIcon(icon_path[fp]))
            obj_but.setIconSize(QSize(self.but_height_plt - 1, self.but_height_plt - 1))
            obj_but.setFixedSize(self.but_height_plt, self.but_height_plt)
            obj_but.setCursor(Qt.CursorShape.PointingHandCursor)
            obj_but.setToolTip(tt_str)
            obj_but.setObjectName(fp)

            obj_but.setStyleSheet("""
                QToolTip {
                    color: white;                 
                }
            """)

            # sets the callback function
            obj_but.clicked.connect(self.button_plot_click)

            # adds the widgets
            frm_layout.addWidget(obj_but)

        # adds the plot widget
        gb_layout.addWidget(obj_frm)
        self.plot_layout.addWidget(obj_grp)

    def setup_plot_region(self):

        # creates the plot object
        x_plt, y_plt = self.get_plot_values()

        # resets the axis limits (vertical limits are fixed)
        self.h_plot_line = self.h_plot.plot(x_plt, y_plt, pen=self.pen)

        # sets up the plot item
        self.h_plot_item.setDownsampling(auto=True)
        self.h_plot_item.setDefaultPadding(0.0)
        self.h_plot_item.showGrid(x=True, y=True, alpha=0.5)
        self.plot_layout.addWidget(self.h_plot)

        # updates the axis limits
        v_box = self.h_plot.getViewBox()
        p_rng = v_box.viewRange()
        self.x_lim, self.y_lim = x_plt[::len(x_plt) - 1], p_rng[1]

        # fixes the x-limits (for the root trace)
        y_min, y_max = self.y_lim[0], self.y_lim[1]
        x_min, x_max = self.x_lim[0], self.x_lim[1]

        if self.is_root:
            # case is the root plot
            self.i_frm = [0, (x_plt.size - 1)]

        # initialises the children index array
        self.i_frm_ch = deepcopy(self.i_frm)

        # resets the axis limits
        v_box.setXRange(x_min, x_max)
        v_box.setYRange(y_min, y_max)
        v_box.setLimits(xMin=p_rng[0][0], xMax=p_rng[0][1], yMin=y_min, yMax=y_max)

        # adds the plot widget
        self.setup_linear_region_items()
        if not self.is_root:
            self.setup_linear_region_items(True)

    def setup_linear_region_items(self, link_parent=False):

        # sets up the linear region item
        # p_obj = self.h_parent.plot_obj if link_parent else self
        l_pen = pg.mkPen(width=3, color='y' if link_parent else 'm')
        l_pen_h = pg.mkPen(width=3, color='g')
        l_reg_new = pg.LinearRegionItem(
            self.x_lim, bounds=self.x_lim, span=[0, 1], pen=l_pen, hoverPen=l_pen_h, swapMode='block')

        # sets the linear region item properties
        l_reg_new.setZValue(int(link_parent)-10)
        l_reg_new.hide()

        # sets the linear region callback function
        if link_parent:
            # case is the linear region is being added to the parent axes
            self.l_reg_p = l_reg_new
            self.x_lim0 = deepcopy(self.x_lim)

            # sets the linear region properties
            self.l_reg_p.setBrush(pg.mkBrush(255, 0, 0, 100))
            self.l_reg_p.setHoverBrush(pg.mkBrush(255, 0, 0, 120))

            # sets the linear region callback function
            self.h_parent.plot_obj.h_plot.addItem(l_reg_new)
            self.l_reg_p.sigRegionChanged.connect(self.region_parent_moving)
            self.l_reg_p.sigRegionChangeFinished.connect(self.region_parent_moved)

            # sets up the mouse press event
            self.mp_event_click = self.l_reg_p.mousePressEvent
            self.l_reg_p.mousePressEvent = self.region_mouse_click

            # sets up the mouse press event
            self.mp_event_release = self.l_reg_p.mouseReleaseEvent
            self.l_reg_p.mouseReleaseEvent = self.region_mouse_release

        else:
            # case is the linear region is being added to the current axes
            self.l_reg = l_reg_new
            self.l_reg.sigRegionChangeFinished.connect(self.region_current_move)
            self.h_plot.addItem(self.l_reg)

    def setup_plot_pen(self):

        pen_style = cf.pen_style[self.p_props.p_style]
        return pg.mkPen(color=self.p_props.p_col, width=self.p_props.p_width, style=pen_style)

    # REGION MOVEMENT FUNCTIONS ----------------------------------------

    def region_current_move(self):

        x_lim = self.l_reg.getRegion()
        self.i_frm_ch = np.int64(np.ceil(np.array(x_lim) / self.h_root.dx))

    def region_parent_moved(self):

        # recalculates the region frame indices
        x_lim = self.l_reg_p.getRegion()
        self.i_frm = np.int64(np.ceil(np.array(x_lim) / self.h_root.dx))

        # resets the plot data
        self.reset_plot_data()
        self.reset_current_region()

        # resets the click flag and evoke a region movement event
        self.region_moved.emit()

    def region_parent_moving(self):

        if self.is_updating:
            return

        # determines if the current trace has any children objects
        tr_obj = self.h_root.get_trace_object()
        if len(tr_obj.h_child):
            # if so, determine if the limits don't violate the internal limits

            # retrieves the current location of the linear region
            x_lim_p, update_reqd = list(self.l_reg_p.getRegion()), False

            # determines if the left side exceeds the lower limit
            x_lower = np.min([x.plot_para.x_min for x in tr_obj.h_child])
            if x_lim_p[0] > x_lower:
                x_lim_p[0], update_reqd = x_lower, True

            x_upper = np.max([x.plot_para.x_max for x in tr_obj.h_child])
            if x_lim_p[1] < x_upper:
                x_lim_p[1], update_reqd = x_upper, True

            if update_reqd:
                self.is_updating = True
                self.l_reg_p.setRegion(x_lim_p)
                self.is_updating = False

    # WIDGET EVENT FUNCTIONS -------------------------------------------

    def click_plot_region(self, *_):

        if self.region_clicked:
            self.region_clicked = False
            return

        if self.h_root.get_trace_object() != self.parent_tr:
            # if the selected trace index doesn't match the plot widget, then update
            self.h_root.change_selected_plot(self.parent_tr)

            # resets the s
            self.obj_plot_gbox.setObjectName('selected')
            self.obj_plot_gbox.setStyleSheet(self.obj_plot_gbox.styleSheet())

    def region_mouse_click(self, evnt):

        self.h_parent.plot_obj.region_clicked = True

        if self.h_root.get_trace_object() != self.parent_tr:
            # if the selected trace index doesn't match the plot widget, then update
            self.h_root.change_selected_plot(self.parent_tr)

            # resets the s
            self.obj_plot_gbox.setObjectName('selected')
            self.obj_plot_gbox.setStyleSheet(self.obj_plot_gbox.styleSheet())

        # runs the mouse-clicked event
        self.mp_event_click(evnt)

    def region_mouse_release(self, evnt):

        # runs the mouse-clicked event
        self.mp_event_release(evnt)

    def button_plot_click(self):

        cf.show_error('Finish Me!')

    def update_trace(self, p_str):

        match p_str:
            # case is the trace name
            case 'name':

                # field retrieval
                tr_name = self.p_props.name
                self.h_root.was_reset = True

                # resets the plot trace object title
                tr_name0 = self.obj_plot_gbox.title()
                self.obj_plot_gbox.setTitle(tr_name)

                # resets the explorer tree string
                h_ttree = self.h_root.obj_para.obj_ttree
                if self.is_root:
                    h_ttree.t_model.item(0).setText(tr_name)

                else:
                    self.h_root.tr_obj[self.h_root.i_trace].h_tree.setText(tr_name)

                # updates the combo box text
                h_cbox_tr = self.h_root.obj_para.obj_rcfig.obj_lbl_combo.obj_cbox
                for i in range(h_cbox_tr.count()):
                    if h_cbox_tr.itemText(i) == tr_name0:
                        h_cbox_tr.setItemText(i, tr_name)
                        break

                # updates the trace name editbox
                h_group_c = self.h_root.obj_para.findChildren(QCollapseGroup, name='tr_prop')[0]
                h_edit_c = h_group_c.findChildren(QLineEdit, name='name')[0]
                h_edit_c.setText(tr_name)

            case p_str if p_str in ['p_width', 'p_col', 'p_style']:

                # case is the line pen-width
                pen = pg.mkPen(color=self.p_props.p_col, width=self.p_props.p_width)
                self.h_plot_item.dataItems[0].setPen(pen)

            case 'g_style':

                # sets the x/y-grid flag values
                x_on = ('X-Dir' in self.p_props.g_style) or (self.p_props.g_style == 'Both Directions')
                y_on = ('Y-Dir' in self.p_props.g_style) or (self.p_props.g_style == 'Both Directions')

                # resets the grid values
                self.h_plot_item.showGrid(x=y_on, y=x_on, alpha=0.5)

    # MISCELLANEOUS FUNCTIONS ------------------------------------------

    def reset_plot_data(self):

        # updates the plot values
        x_plt, y_plt = self.get_plot_values()

        # # updates the plot line
        # self.h_plot_line = self.h_plot.plot(x_plt, y_plt, pen=self.pen, clear=True)

        # resets the axis limit fields
        self.x_lim, self.y_lim = x_plt[::len(x_plt) - 1], [np.min(y_plt), np.max(y_plt)]

        # resets the axis limits
        v_box = self.h_plot.getViewBox()
        v_box.setLimits(xMin=self.x_lim[0], xMax=self.x_lim[1], yMin=self.y_lim[0], yMax=self.y_lim[1])
        v_box.setXRange(self.x_lim[0], self.x_lim[1])
        v_box.setYRange(self.y_lim[0], self.y_lim[1])

    def reset_current_region(self):

        # initialisations
        is_change = False

        # recalculates the region frame indices
        x_lim = list(self.l_reg.getRegion())
        x_lim_p = list(self.l_reg_p.getRegion())

        # lower region limit check
        if x_lim_p[0] > x_lim[0]:
            x_lim[0], is_change = x_lim_p[0], True
            if x_lim_p[0] > x_lim[1]:
                x_lim[1] = x_lim_p[0]

        # upper region limit check
        if x_lim_p[1] < x_lim[1]:
            x_lim[1] = x_lim_p[1]
            is_change = True
            if x_lim_p[1] < x_lim[0]:
                x_lim[0] = x_lim_p[1]

        # if there is a change, then update the linear region
        if is_change:
            self.l_reg.setRegion(tuple(x_lim))

    def get_plot_values(self):

        if self.is_root:
            # case is the root trace
            return self.h_root.x, self.h_root.y

        else:
            # case is a sub-trace

            # retrieves the global index range
            xi_frm = range(self.i_frm[0], self.i_frm[1])

            # returns the final plot coordinates
            return self.x[xi_frm], self.y[xi_frm]

    def delete(self):

        # removes the plot widget from the plot canvas
        self.h_root.obj_plot.main_layout.removeItem(self)

        # deletes the class widget
        del self


# ----------------------------------------------------------------------------------------------------------------------


class QParaTrace(QWidget):
    def __init__(self, tr_name):
        super(QParaTrace, self).__init__()

        # initialisations
        self.has_init = False

        # trace property fields
        self.name = tr_name
        self.p_width = 1
        self.p_style = 'Solid'
        self.p_col = QColor(255, 255, 255)
        self.g_style = 'Both Directions'

        # trace operation fields
        self.show_child = False
        self.show_parent = False
        self.create_trace = 0
        self.clip_trace = 0
        self.delete_trace = 0
        self.delete_children = 0

        # x/y-axes limit fields
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None

        # flag reset
        self.has_init = True


# ----------------------------------------------------------------------------------------------------------------------


class QPlotLayout(QLayout):
    def __init__(self, parent=None, g_id=None, sz_hint=None):
        super(QPlotLayout, self).__init__(parent)

        # field initialisation
        self.g_id = g_id
        self._items = []
        self._sz_hint = sz_hint

    def addItem(self, item: QLayoutItem):
        """Adds an item (widget) to the layout."""
        self._items.append(item)

    def count(self):
        """Returns the number of items in the layout."""
        return len(self._items)

    def sizeHint(self, *args):
        """Returns the number of items in the layout."""
        if self._sz_hint is None:
            return self.parent().size()
        else:
            return self._sz_hint

    def itemAt(self, index: int) -> QLayoutItem:
        """Returns the item at a given index."""
        if index < len(self._items):
            return self._items[index]
        return None

    def setGeometry(self, rect: QRect):
        """Arranges the widgets in a grid-like fashion."""
        d = self.spacing()
        x, y = rect.x() + d, rect.y() + d
        width, height = rect.width() - 2 * d, rect.height() - 2 * d

        # updates the background widget
        rect.adjust(d, d, -2 * d, -2 * d)
        self._items[0].setGeometry(rect)

        # row/column index retrieval
        if self.g_id is None:
            # if there is no grid ID values given, then exit
            return

        else:
            n_rows, n_cols = self.g_id.shape[0], self.g_id.shape[1]

        # Calculate the width and height for each cell in the grid
        c_wid = width // n_cols
        c_hght = height // n_rows

        for i, gid in enumerate(np.unique(self.g_id[self.g_id > 0])):
            widget = self._items[gid].widget()

            if widget:
                # calculates the row/column indices and spans
                id_plt = np.where(self.g_id == gid)
                i_row, i_col = min(id_plt[0]), min(id_plt[1])
                n_row, n_col = len(np.unique(id_plt[0])), len(np.unique(id_plt[1]))

                # Set the geometry of the widget based on the grid's row and column
                widget.show()
                widget.setGeometry(x + i_col * c_wid, y + i_row * c_hght, c_wid * n_col, c_hght * n_row)

        super().setGeometry(rect)

    def invalidate(self):
        """Invalidates the layout, forcing it to recalculate its geometry."""
        super().invalidate()

    def removeAt(self, index: int):
        """Removes an item at a given index."""
        if index < len(self._items):
            del self._items[index]

    def updateID(self, _g_id, force_update=True):
        """Updates the grid ID flags"""
        self.g_id = _g_id

        if force_update:
            self.invalidate()

    @property
    def items(self):
        return self._items


# COMMON CLASSES -------------------------------------------------------------------------------------------------------


class QParaClass(QParaTrace):
    # signal functions
    update_props = pyqtSignal(str)
    trace_operation = pyqtSignal(str)
    update_limits = pyqtSignal(str)

    def __init__(self, tr_name):
        super(QParaClass, self).__init__(tr_name)

    @staticmethod
    def para_change(p_str, _self):

        if _self.has_init:
            _self.update_props.emit(p_str)

    @staticmethod
    def prop_update(p_str, _self):

        if _self.has_init:
            _self.trace_operation.emit(p_str)

    @staticmethod
    def limit_change(p_str, _self):

        if _self.has_init:
            _self.update_limits.emit(p_str)

    # trace property observer properties
    name = cf.ObservableProperty(functools.partial(para_change, 'name'))
    p_width = cf.ObservableProperty(functools.partial(para_change, 'p_width'))
    p_style = cf.ObservableProperty(functools.partial(para_change, 'p_style'))
    p_col = cf.ObservableProperty(functools.partial(para_change, 'p_col'))
    g_style = cf.ObservableProperty(functools.partial(para_change, 'g_style'))

    # trace operation observer properties
    show_child = cf.ObservableProperty(functools.partial(prop_update, 'show_child'))
    show_parent = cf.ObservableProperty(functools.partial(prop_update, 'show_parent'))
    create_trace = cf.ObservableProperty(functools.partial(prop_update, 'create_trace'))
    clip_trace = cf.ObservableProperty(functools.partial(prop_update, 'clip_trace'))
    delete_trace = cf.ObservableProperty(functools.partial(prop_update, 'delete_trace'))
    delete_children = cf.ObservableProperty(functools.partial(prop_update, 'delete_children'))

    # trace property observer properties
    x_min = cf.ObservableProperty(functools.partial(limit_change, 'x_min'))
    x_max = cf.ObservableProperty(functools.partial(limit_change, 'x_max'))
    y_min = cf.ObservableProperty(functools.partial(limit_change, 'y_min'))
    y_max = cf.ObservableProperty(functools.partial(limit_change, 'y_max'))
