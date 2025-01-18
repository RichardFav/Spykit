# custom module import
import spike_pipeline.common.common_func as cf

# pyqt6 module import
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QGroupBox, QTabWidget,
                             QFormLayout, QLabel, QCheckBox, QLineEdit, QComboBox, QSizePolicy, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

########################################################################################################################
########################################################################################################################


class QFileSpec(QGroupBox):
    def __init__(self, parent=None, grp_hdr=None, file_path=None, name=None, f_mode=None):
        super(QFileSpec, self).__init__(parent)

        # initialisations
        self.f_mode = f_mode
        font_hdr = create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)
        font_but = create_font_obj(size=10, is_bold=True, font_weight=QFont.Weight.Bold)

        # sets the groupbox properties
        self.setTitle(grp_hdr)
        self.setFont(font_hdr)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # creates the editbox widget
        self.h_edit = create_line_edit(None, file_path, align='left', name=name)
        self.layout.addWidget(self.h_edit)
        self.h_edit.setReadOnly(True)
        self.h_edit.setObjectName(name)

        # creates the button widget
        self.h_but = create_push_button(None, '...', font_but)
        self.layout.addWidget(self.h_but)
        self.h_but.setFixedWidth(25)

########################################################################################################################
########################################################################################################################


class QCheckboxHTML(QWidget):
    def __init__(self, parent=None, text=None, state=False, font=None, name=None):
        super(QCheckboxHTML, self).__init__(parent)

        # creates the layout widget
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # creates the checkbox object
        self.h_chk = create_check_box(None, '', state, name=name)
        self.h_chk.adjustSize()
        self.h_chk.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))

        # creates the label object
        self.h_lbl = create_text_label(None, text, font, align='left')
        self.h_lbl.setStyleSheet('padding-bottom: 2px;')
        self.h_lbl.adjustSize()

        # adds the widgets to the layout
        self.layout.addWidget(self.h_chk)
        self.layout.addWidget(self.h_lbl)

    def set_label_text(self, t_lbl):
        """

        :param t_lbl:
        :return:
        """

        self.h_lbl.setText(t_lbl)

    def set_slot_func(self, cb_fcn):
        """

        :param cb_fcn:
        :return:
        """

        self.h_chk.stateChanged.connect(cb_fcn)
        self.h_lbl.mousePressEvent = cb_fcn

########################################################################################################################
########################################################################################################################


class FileDialogModal(QFileDialog):
    def __init__(self, parent=None, caption=None, f_filter=None,
                 f_directory=None, is_save=False, dir_only=False, is_multi=False):
        # creates the object
        super(FileDialogModal, self).__init__(parent=parent, caption=caption, filter=f_filter, directory=f_directory)

        # sets the file dialog parameters
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # sets the file dialog to open if
        if is_save:
            self.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

        # sets the file mode to directory (if directory only)
        if dir_only:
            self.setFileMode(QFileDialog.FileMode.Directory)

        # sets the multi-select flag to true (if required)
        if is_multi:
            self.setFileMode(QFileDialog.FileMode.ExistingFiles)


########################################################################################################################
########################################################################################################################

# object dimensions
d_hght = 5
w_space = 10
txt_hght = 16.5

expand_style = """
    text-align:left;
    background-color: rgba(26, 83, 200, 255);
    color: rgba(255, 255, 255, 255);
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
"""

close_style = """
    text-align:left;
    background-color: rgba(26, 83, 200, 255);
    color: rgba(255, 255, 255, 255);
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
"""


# lambda function declarations
def arr_chr(is_chk):
    """

    :param is_chk:
    :return:
    """

    return '\u2B9F' if is_chk else '\u2B9E'


class QCollapseGroup(QWidget):
    def __init__(self, parent=None, grp_name=None, grp_info=None, is_first=False, root=None):
        super(QCollapseGroup, self).__init__(parent)

        # initialisations
        self.root = root
        self.is_expanded = True
        self.panel_hdr = grp_name

        # label/header font objects
        self.font_txt = create_font_obj()
        self.font_hdr = create_font_obj(size=9, is_bold=True, font_weight=QFont.Weight.Bold)

        # creates the panel objects
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(w_space, is_first * w_space, w_space, w_space)

        # creates the expansion button
        self.expand_button = create_push_button(None, '', font=self.font_hdr)
        self.main_layout.addWidget(self.expand_button, 0, Qt.AlignmentFlag.AlignTop)

        # creates the groupbox object
        self.group_panel = QGroupBox()
        self.main_layout.addWidget(self.group_panel)

        # creates the children objects for the current parent object
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # adds the sub-groups to the
        for ch_grp in grp_info:
            self.add_group_row(ch_grp, grp_info[ch_grp])

        # sets the final layout
        self.group_panel.setLayout(self.form_layout)
        self.setLayout(self.main_layout)
        self.set_styling()

        # retrieves the original height
        self.orig_hght = self.group_panel.maximumHeight()
        self.update_button_text()

        # resets the collapse panel size policy
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, cf.q_fix))

    # ------------------------------ #
    # --- WIDGET SETUP FUNCTIONS --- #
    # ------------------------------ #

    def add_group_row(self, p_str, p_info):
        """

        :param p_str:
        :param p_info:
        :return:
        """

        # creates the text labels
        h_gap = create_text_label(None, '', name=p_str)
        h_txt = create_text_label(None, p_info['name'], align='left', name=p_str)

        h_txt.adjustSize()
        h_txt.setSizePolicy(QSizePolicy(cf.q_fix, cf.q_fix))

        # sets the gap object properties
        h_gap.setFixedWidth(5)
        h_gap.setStyleSheet("background-color: rgba(240, 240, 255, 255) ;")

        # sets the text label properties
        h_txt.setStyleSheet("""
            QLabel {
                color: rgba(26, 83, 200, 255) ;
            }
            QLabel:hover {
                color: rgba(255, 0, 0, 255) ;
            }""")

        # adds the object to the layout
        self.form_layout.addRow(h_gap, h_txt)
        self.orig_hght = self.height()

        # appends the group
        h_root = cf.get_parent_widget(self, type(self.root))
        h_root.search_dlg.append_grp_obj(h_txt, p_str, p_info['name'])

    # ------------------------------- #
    # --- MISCELLANEOUS FUNCTIONS --- #
    # ------------------------------- #

    def update_button_text(self):
        """

        :return:
        """

        self.expand_button.setText(' {0} {1}'.format(arr_chr(self.is_expanded), self.panel_hdr))
        self.group_panel.setMaximumHeight(self.is_expanded * self.orig_hght)

    def set_styling(self):
        """

        :return:
        """

        self.group_panel.setStyleSheet("background-color: rgba(240, 240, 255, 255) ;")
        self.expand_button.setStyleSheet(expand_style)

########################################################################################################################
########################################################################################################################


def create_text_label(parent, text, font=None, align='right', name=None):
    """

    :param parent: parent object
    :param text:
    :param font:
    :param align: alignment flag (left, centre or right)
    :param name: object name
    :return:
    """

    # sets the label font properties
    if font is None:
        font = create_font_obj()

    # creates the label object
    h_lbl = QLabel(parent)

    # sets the label properties
    h_lbl.setText(text)
    h_lbl.setFont(font)
    h_lbl.setAlignment(cf.align_type[align])

    # sets the object name string
    if name is not None:
        h_lbl.setObjectName(name)

    # returns the label object
    return h_lbl


def create_line_edit(parent, text, font=None, align='centre', name=None):
    """

    :param parent:
    :param text:
    :param font:
    :param align:
    :param name:
    :return:
    """

    # sets the label font properties
    if font is None:
        font = create_font_obj()

    # sets the text string (if None)
    if text is None:
        text = " "

    elif isinstance(text, int):
        text = str(text)

    # creates the line edit object
    h_ledit = QLineEdit(parent)

    # sets the label properties
    h_ledit.setFont(font)
    h_ledit.setText(text)
    h_ledit.setAlignment(cf.align_type[align])

    # sets the object name string
    if name is not None:
        h_ledit.setObjectName(name)

    # returns the object
    return h_ledit


def create_push_button(parent, text, font=None):
    """

    :param parent:
    :param text:
    :param font:
    :return:
    """

    # creates a default font object (if not provided)
    if font is None:
        font = create_font_obj()

    # creates the button object
    h_button = QPushButton(parent)

    # sets the button properties
    h_button.setFont(font)
    h_button.setText(text)

    # returns the button object
    return h_button


def create_combo_box(parent, text=None, font=None, name=None):
    """

    :param parent:
    :param text:
    :param font:
    :param name:
    :return:
    """

    # creates a default font object (if not provided)
    if font is None:
        font = create_font_obj()

    # creates the listbox object
    h_combo = QComboBox(parent)

    # sets the combobox object properties
    h_combo.setFont(font)

    # sets the combobox text (if provided)
    if text is not None:
        for t in text:
            h_combo.addItem(t)

    # sets the object name string
    if name is not None:
        h_combo.setObjectName(name)

    # returns the object
    return h_combo


def create_check_box(parent, text, state, font=None, name=None):
    """

    :param parent:
    :param text:
    :param state:
    :param font:
    :param name:
    :return:
    """

    # sets the label font properties
    if font is None:
        font = create_font_obj()

    # creates the listbox object
    h_chk = QCheckBox(parent)

    # sets the object properties
    h_chk.setText(text)
    h_chk.setFont(font)
    h_chk.setChecked(state)

    # sets the object name string
    if name is not None:
        h_chk.setObjectName(name)

    # returns the object
    return h_chk


def create_tab_group(parent, font=None, name=None):
    """

    :param parent:
    :param font:
    :param name:
    :return:
    """

    # creates a default font object (if not provided)
    if font is None:
        font = create_font_obj()

    # creates the tab object
    h_tab_grp = QTabWidget(parent)

    # sets the listbox object properties
    h_tab_grp.setFont(font)

    # sets the object name string
    if name is not None:
        h_tab_grp.setObjectName(name)

    # returns the tab object
    return h_tab_grp


def create_font_obj(size=9, is_bold=False, font_weight=QFont.Weight.Normal):
    """

    :param size:
    :param is_bold:
    :param font_weight:
    :return:
    """

    # creates the font object
    font = QFont()

    # sets the font properties
    font.setPointSize(size)
    font.setBold(is_bold)
    font.setWeight(font_weight)

    # returns the font object
    return font
