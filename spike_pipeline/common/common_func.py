# module import
import os
import math
import colorsys
import threading
from typing import TypeVar

# pyqt6 module import
import numpy as np
from PyQt6.QtWidgets import (QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# other initialisations
q_fix = QSizePolicy.Policy.Fixed
q_exp = QSizePolicy.Policy.Expanding
q_expm = QSizePolicy.Policy.MinimumExpanding
q_pref = QSizePolicy.Policy.Preferred
q_max = QSizePolicy.Policy.Maximum
q_min = QSizePolicy.Policy.Minimum

# messagebox flags
q_no = QMessageBox.StandardButton.No
q_yes = QMessageBox.StandardButton.Yes
q_cancel = QMessageBox.StandardButton.Cancel

# combined messagebox flags
q_yes_no = q_yes | q_no
q_yes_no_cancel = q_yes_no | q_cancel

# common parameters
align_type = {
    'center': Qt.AlignmentFlag.AlignCenter,
    'left': Qt.AlignmentFlag.AlignLeft,
    'right': Qt.AlignmentFlag.AlignRight
}

pen_style = {
    'Solid': Qt.PenStyle.SolidLine,
    'Dash': Qt.PenStyle.DashLine,
    'Dot': Qt.PenStyle.DotLine,
    'Dash-Dot': Qt.PenStyle.DashDotLine,
    'Dash-Dot-Dot': Qt.PenStyle.DashDotDotLine
}

chk_state = {
    False: Qt.CheckState.Unchecked,
    True: Qt.CheckState.Checked,
}

ascend_flag = {
    True: Qt.SortOrder.AscendingOrder,
    False: Qt.SortOrder.DescendingOrder,
}

# widget dimensions
but_height = 24
edit_height = 20
combo_height = 22

# other parameters
n_col_max = 20
Cls = TypeVar('Cls')

# ----------------------------------------------------------------------------------------------------------------------


class IteratorThread:

    def __init__(self, n=np.inf):

        self.i = 0
        self.n = n
        self.lock = threading.Lock()

    def __iter__(self):

        return self

    def reset(self):

        self.i = 0

    def reset_n(self, n_new):

        self.n = n_new

    def next(self):

        with self.lock:
            self.i += 1
            if self.i >= self.n:
                return None
            else:
                return self.i


# ----------------------------------------------------------------------------------------------------------------------


class ObservableProperty:
    def __init__(self, callback=None):
        super(ObservableProperty, self).__init__()

        self._value = None
        self._callback = callback

    def __get__(self, instance, owner):
        return self._value

    def __set__(self, instance, new_value):
        if new_value != self._value:
            self._value = new_value
            if self._callback:
                self._callback(instance)


# ----------------------------------------------------------------------------------------------------------------------


class ObservableThreadSafe:
    def __init__(self, initial_value=None, callback=None):
        self._value = initial_value
        self._callback = callback
        self._lock = threading.Lock()

    @property
    def value(self):
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value):
        with self._lock:
            if new_value != self._value:
                self._value = new_value
                if self._callback:
                    self._callback(new_value)

    def set_callback(self, callback):
        self._callback = callback


# ----------------------------------------------------------------------------------------------------------------------


def check_edit_num(nw_str, is_int=False, min_val=-1e100, max_val=1e10, show_err=True):

    # initialisations
    nw_val, e_str = None, None

    if is_int:
        # case is the string must be a float
        try:
            nw_val = int(nw_str)

        except ValueError:
            try:
                # if there was an error, then determine if the string was a float
                nw_val = float(nw_str)
                if nw_val % 1 == 0:
                    # if the float is actually an integer, then return the value
                    nw_val, e_str = int(nw_val), 1
                else:
                    # otherwise,
                    e_str = 'Entered value is not an integer.'

            except ValueError:
                # case is the string was not a valid number
                e_str = 'Entered value is not a valid number.'
    else:
        # case is the string must be a float
        try:
            nw_val = float(nw_str)

        except ValueError:
            # case is the string is not a valid number
            e_str = 'Entered value is not a valid number.'

    # determines if the new value meets the min/max value requirements
    if nw_val is not None:
        if nw_val < min_val:
            e_str = 'Entered value must be greater than or equal to {0}'.format(min_val)
        elif nw_val > max_val:
            e_str = 'Entered value must be less than or equal to {0}'.format(max_val)
        else:
            return nw_val, e_str

    # shows the error message (if required)
    if show_err:
        show_error(e_str, 'Error!')

    # shows the error and returns a None value
    return None, e_str


def show_error(text, title=""):

    # otherwise, create the error message
    err_dlg = QMessageBox()
    err_dlg.setText(text)
    err_dlg.setWindowTitle(title)
    err_dlg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    # shows the final message
    err_dlg.exec()


def get_parent_widget(h_obj, w_type):

    # retrieves the parent object
    h_obj_p = h_obj.parent()

    while True:
        if isinstance(h_obj_p, w_type):
            # if there is a match, then exit
            return h_obj_p

        elif h_obj_p is None:
            # if the root object, then exit
            return None

        else:
            # otherwise, retrieve the next parent object
            h_obj_p = h_obj_p.parent()


def get_root_widget(h_obj):

    # keep searching until there are no more parent widgets
    while True:
        # retrieves the parent object
        h_obj_p = h_obj.parent()
        if h_obj_p is None:
            # if there are no more parents, then exit
            return h_obj

        else:
            # otherwise, reset the widget field
            h_obj = h_obj_p


def get_greek_chr(x):

    return '<a>&{0};<\a>'.format(x)


def set_multi_dict_value(d, k, v):

    if len(k) == 1:
        # case is a leaf level
        d[k[0]] = v

    else:
        # case is a branch level
        set_multi_dict_value(d[k[0]], k[1:], v)


def get_multi_dict_value(d, k):

    # case is the leaf level
    if not k:
        return d

    return get_multi_dict_value(d.get(k[0], {}), k[1:])


def set_text_colour(text, col='black'):

    return '<span style="color:{0}">{1}</span>'.format(col, text)


def set_text_background_colour(text, col='black'):

    return '<span style="background-color: {0}">{1}</span>'.format(col, text)


def arr_chr(is_chk):

    return '\u2B9F' if is_chk else '\u2B9E'


def get_colour_value(col_id, alpha=255, n_col_new=None):

    match col_id:
        case col_id if col_id in ['red', 'r']:
            # case is red
            return QColor(255, 0, 0, alpha)

        case col_id if col_id in ['green', 'g']:
            # case is green
            return QColor(0, 255, 0, alpha)

        case col_id if col_id in ['blue', 'b']:
            # case is blue
            return QColor(0, 0, 255, alpha)

        case col_id if col_id in ['yellow', 'y']:
            # case is green
            return QColor(255, 255, 0, alpha)

        case col_id if col_id in ['magenta', 'm']:
            # case is magenta
            return QColor(255, 0, 255, alpha)

        case col_id if col_id in ['cyan', 'c']:
            # case is cyan
            return QColor(0, 255, 255, alpha)

        case col_id if col_id in ['white', 'w']:
            # case is white
            return QColor(255, 255, 255, alpha)

        case col_id if col_id in ['black', 'k']:
            # case is black
            return QColor(0, 0, 0, alpha)

        case col_id if col_id in ['dark-gray', 'dg']:
            # case is dark-gray
            return QColor(50, 50, 50, alpha)

        case col_id if col_id in ['light-gray', 'lg']:
            # case is light-gray
            return QColor(200, 200, 200, alpha)

        case _:
            # case is a number
            n_col = n_col_max if n_col_new is None else n_col_new
            p_hsv = (col_id * 1.0 / n_col, 0.5, 0.5)
            p_rgb = [int(255 * x) for x in list(colorsys.hsv_to_rgb(*p_hsv))]
            return QColor(p_rgb[0], p_rgb[1], p_rgb[2], alpha)


def lcm(a, b):

    return (a * b) // math.gcd(a, b)


def get_path_matches(f_path, f_str, is_file=False):

    # initialisations
    f_list = []

    for root, dirs, files in os.walk(f_path):
        if is_file:
            # case is a file search
            for f in files:
                if f == f_str:
                    f_list.append(os.path.join(root, f))

        else:
            # case is a directory search
            for d in dirs:
                if d == f_str:
                    f_list.append(os.path.join(root, d))

    return f_list


def get_folder_dir(f_path):

    return [x for x in os.listdir(f_path) if os.path.isdir(os.path.join(f_path, x))]


def setup_image_file_name(fig_dir, fig_name):

    if not os.path.exists(fig_dir):
        os.mkdir(fig_dir)

    return os.path.join(fig_dir, fig_name)


def get_dict_key_from_value(d, val):

    return next((k for k, v in d.items() if (v == val)))


def normalise_trace(y):

    y_min, y_max = np.min(y), np.max(y)

    if y_max == y_min:
        return np.zeros(len(y))

    else:
        return (y - y_min) / (y_max - y_min)


def list_add(y, dy):
    return list(np.asarray(y) + dy)


def list_mult(y, dy):
    return list(np.asarray(y) * dy)


def resize_limits(y, yscl):
    y = np.asarray(y)
    dy = np.diff(y)[0]
    return list(y + np.array([-1, 1]) * (yscl / 2) * dy)


def remove_baseline(y):

    return y - np.min(y)
