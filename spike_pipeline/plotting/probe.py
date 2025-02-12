# module import
import numpy as np
import pyqtgraph as pg

import spike_pipeline.common.common_func as cf

# pyqt6 module import
from PyQt6.QtCore import QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPolygonF, QPicture, QPainter


class ProbePlot(pg.GraphicsObject):
    # parameters
    dp = 0.1

    # plot pen widgets
    pen = pg.mkPen(width=2, color='b')
    pen_h = pg.mkPen(width=2, color='g')

    # pyqtsignal functions
    update_roi = pyqtSignal(object)

    def __init__(self, parent, probe):
        super(ProbePlot, self).__init__()

        self.setParent(parent)

        # field initialisation
        self.roi = None
        self.width = None
        self.height = None
        self.x_lim = None
        self.y_lim = None
        self.x_lim_full = None
        self.y_lim_full = None

        # field retrieval
        self.n_dim = probe.ndim
        self.n_contact = probe.get_contact_count()
        self.si_units = probe.si_units

        # contact property fields
        self.c_id = probe.contact_ids
        self.c_index = probe.device_channel_indices
        self.c_pos = probe.contact_positions
        self.c_vert = self.setup_contact_coords(probe.get_contact_vertices())

        # probe properties
        self.p_title = probe.get_title()
        self.p_vert = self.vert_to_pointf(probe.probe_planar_contour)
        self.p_ax = probe.contact_plane_axes

        # sets up the axes limits
        self.get_axes_limits(probe)

        # plot widgets
        self.picture = QPicture()

        # creates the probe plot
        self.create_probe_plot()

    # INITIALISATION FUNCTIONS ---------------------------------------------

    def setup_contact_coords(self, vert0):

        # sets up the contact polygon objects
        return [self.vert_to_pointf(v) for v in vert0]

    def create_probe_plot(self):

        # polygon setup
        p_poly = QPolygonF(self.p_vert)
        c_poly = [QPolygonF(x) for x in self.c_vert]

        p_col_probe = cf.get_colour_value('r', 128)
        c_col_probe = cf.get_colour_value('y', 128)

        # painter object setup
        p = QPainter(self.picture)

        # probe shape plot
        p.setPen(pg.mkPen(p_col_probe))
        p.setBrush(pg.mkBrush(p_col_probe))
        p.drawPolygon(p_poly)

        # probe contact plots
        p.setPen(pg.mkPen(c_col_probe))
        p.setBrush(pg.mkBrush(c_col_probe))
        for c_p in c_poly:
            p.drawPolygon(c_p)

        # ends the drawing
        p.end()

    def create_inset_roi(self, x_lim_s, y_lim_s):

        p_0 = [x_lim_s[0], y_lim_s[0]]
        p_sz = [np.diff(x_lim_s), np.diff(y_lim_s)]
        p_lim = QRectF(self.x_lim_full[0], self.y_lim_full[0], self.width, self.height)

        self.roi = pg.ROI(p_0, p_sz, pen=self.pen, hoverPen=self.pen_h,
                          handlePen=self.pen, handleHoverPen=self.pen_h, maxBounds=p_lim)
        self.roi.addTranslateHandle([0, 0])
        self.roi.addScaleHandle([1, 1], [0, 0])
        self.roi.addScaleHandle([0, 1], [1, 0])
        self.roi.addScaleHandle([1, 0], [0, 1])
        self.roi.sigRegionChanged.connect(self.roi_moved)

        self.parent().addItem(self.roi)

    # ROI MOVEMENT FUNCTIONS -----------------------------------------------

    def roi_moved(self, h_roi):

        #
        x0, y0, p_sz = h_roi.x(), h_roi.y(), h_roi.size()
        self.update_roi.emit([x0, y0, p_sz])

    # MISCELLANEOUS FUNCTIONS ----------------------------------------------

    def reset_axes_limits(self, is_full=True):

        if is_full:
            _x_lim, _y_lim = self.x_lim_full, self.y_lim_full

        else:
            _x_lim, _y_lim = self.x_lim, self.y_lim

        # updates the figure limits
        vb = self.getViewBox()
        vb.setXRange(_x_lim[0], _x_lim[1])
        vb.setYRange(_y_lim[0], _y_lim[1])
        vb.setLimits(xMin=_x_lim[0], xMax=_x_lim[1], yMin=_y_lim[0], yMax=_y_lim[1])

    def get_axes_limits(self, probe):

        # calculates the contact vertex range
        c_vert_tot = np.vstack(probe.get_contact_vertices())
        c_min_ex, c_max_ex = self.calc_expanded_limits(c_vert_tot, np.array([0.1, 0.1]))

        # calculates the probe shape vertefx range
        p_min0 = np.vstack((np.min(probe.probe_planar_contour, axis=0), c_min_ex))
        p_max0 = np.vstack((np.max(probe.probe_planar_contour, axis=0), c_max_ex))
        p_lim_tot = np.vstack((p_min0, p_max0))
        p_min_ex, p_max_ex = self.calc_expanded_limits(p_lim_tot, np.array([0.1, 0.0]))

        # sets the contact x/y axes limits
        self.x_lim = [c_min_ex[0], c_max_ex[0]]
        self.y_lim = [c_min_ex[1], c_max_ex[1]]
        self.x_lim_full = [p_min_ex[0], p_max_ex[0]]
        self.y_lim_full = [p_min_ex[1], p_max_ex[1]]

        # calculates the full width/height dimensions
        self.width = self.x_lim_full[1] - self.x_lim_full[0]
        self.height = self.y_lim_full[1] - self.y_lim_full[0]

    # FUNCTION OVERRIDES  ---------------------------------------------------

    def paint(self, p, *args):

        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        ## boundingRect _must_ indicate the entire area that will be drawn on
        ## or else we will get artifacts and possibly crashing.
        ## (in this case, QPicture does all the work of computing the bouning rect for us)
        return QRectF(self.picture.boundingRect())

    @staticmethod
    def calc_expanded_limits(y, dy):

        y_min = np.min(y, axis=0)
        y_rng = np.max(y, axis=0) - y_min

        return y_min - np.multiply(dy, y_rng), y_min + np.multiply(1 + dy, y_rng)

    @staticmethod
    def vert_to_pointf(v):

        return [QPointF(x[0], x[1]) for x in v]