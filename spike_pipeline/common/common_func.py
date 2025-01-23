# module import
import threading

# pyqt6 module import
from PyQt6.QtWidgets import (QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt

# other initialisations
q_fix = QSizePolicy.Policy.Fixed
q_exp = QSizePolicy.Policy.Expanding

q_yes = QMessageBox.StandardButton.Yes
q_yes_no = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

# common parameters
align_type = {'centre': Qt.AlignmentFlag.AlignCenter,
              'left': Qt.AlignmentFlag.AlignLeft,
              'right': Qt.AlignmentFlag.AlignRight}

from PyQt6.QtGui import QColor

# widget dimensions
but_height = 24
edit_height = 20
combo_height = 22

########################################################################################################################


class ObservableProperty:
    def __init__(self, callback=None):
        self._value = None
        self._callback = callback

    def __get__(self, instance, owner):
        return self._value

    def __set__(self, instance, new_value):
        if (new_value != self._value) and (self._value is not None):
            self._value = new_value
            if self._callback:
                self._callback(instance)


########################################################################################################################


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


########################################################################################################################


def check_edit_num(nw_str, is_int=False, min_val=-1e100, max_val=1e10, show_err=True):
    """

    :param nw_str:
    :param is_int:
    :param min_val:
    :param max_val:
    :param show_err:
    :return:
    """

    # initialisations
    nw_val, e_str = None, None

    if is_int:
        # case is the string must be a float
        try:
            nw_val = int(nw_str)

        except:
            try:
                # if there was an error, then determine if the string was a float
                nw_val = float(nw_str)
                if nw_val % 1 == 0:
                    # if the float is actually an integer, then return the value
                    nw_val, e_str = int(nw_val), 1
                else:
                    # otherwise,
                    e_str = 'Entered value is not an integer.'
            except:
                # case is the string was not a valid number
                e_str = 'Entered value is not a valid number.'
    else:
        # case is the string must be a float
        try:
            nw_val = float(nw_str)
        except:
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


def show_error(text, title):
    """

    :param text:
    :param title:
    :return:
    """

    # otherwise, create the error message
    err_dlg = QMessageBox()
    err_dlg.setText(text)
    err_dlg.setWindowTitle(title)
    err_dlg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    # shows the final message
    err_dlg.exec()


def get_parent_widget(h_obj, w_type):
    """

    :return:
    """

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
    """

    :param h_obj:
    :return:
    """

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
    """

    :param x:
    :return:
    """

    return '<a>&{0};<\a>'.format(x)


def set_multi_dict_value(d, k, v):
    """

    :param d:
    :param k:
    :param v:
    :return:
    """

    if len(k) == 1:
        # case is a leaf level
        d[k[0]] = v

    else:
        # case is a branch level
        set_multi_dict_value(d[k[0]], k[1:], v)


def get_multi_dict_value(d, k):
    """

    :param d:
    :param k:
    :return:
    """

    # case is the leaf level
    if not k:
        return d

    return get_multi_dict_value(d.get(k[0], {}), k[1:])


def set_text_colour(text, col='black'):
    """

    :param text:
    :param col:
    :return:
    """

    return '<span style="color:{0}">{1}</span>'.format(col, text)


def set_text_background_colour(text, col='black'):
    """

    :param text:
    :param col:
    :return:
    """

    return '<span style="background-color: {0}">{1}</span>'.format(col, text)


# lambda function declarations
def arr_chr(is_chk):
    """

    :param is_chk:
    :return:
    """

    return '\u2B9F' if is_chk else '\u2B9E'


def get_colour_value(col_id, alpha=255):

    match col_id:
        case col_id if col_id in ['red', 'r', 0]:
            # case is red
            return QColor(255, 0, 0, 255)

        case col_id if col_id in ['green', 'g', 1]:
            # case is green
            return QColor(0, 255, 0)

        case col_id if col_id in ['blue', 'b', 2]:
            # case is blue
            return QColor(0, 0, 255)

        case col_id if col_id in ['yellow', 'y', 3]:
            # case is green
            return QColor(255, 255, 0)

        case col_id if col_id in ['magenta', 'm', 4]:
            # case is magenta
            return QColor(255, 0, 255)

        case col_id if col_id in ['cyan', 'c', 5]:
            # case is cyan
            return QColor(0, 255, 255)

        case col_id if col_id in ['white', 'w']:
            # case is white
            return QColor(255, 255, 255)

        case col_id if col_id in ['black', 'k']:
            # case is black
            return QColor(0, 0, 0)

        case col_id if col_id in ['dark-gray', 'dg']:
            # case is dark-gray
            return QColor(50, 50, 50)

        case col_id if col_id in ['light-gray', 'lg']:
            # case is light-gray
            return QColor(200, 200, 200)