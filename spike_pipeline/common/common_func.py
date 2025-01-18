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

# widget dimensions
edit_height = 20
combo_height = 22

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