import math
import cv2
from parser_roi import get_roi_by_img
import parser_util


grid_size = 15.0    # mm of grid squares
nx = 6              # nx: number of grids in x axis
ny = 9              # ny: number of grids in y axis
c_offset_x = -15.0
c_offset_y = 3654


def get_p2p_dist(p):
    avg_r = []
    avg_c = []
    for y in range(0, ny):
        for x in range(0, nx):
            x0 = p[y*x+x, 0, 0]
            y0 = p[y*x+x, 0, 1]
            x1 = p[y*x+x+1, 0, 0]
            y1 = p[y*x+x+1, 0, 1]
            d = math.sqrt(math.pow((x1-x0), 2) + math.pow((y1-y0), 2))
            avg_r.append(d)
    for x in range(0, nx):
        for y in range(0, ny):
            x0 = p[y*x+x, 0, 0]
            y0 = p[y*x+x, 0, 1]
            x1 = p[y*x+x+1, 0, 0]
            y1 = p[y*x+x+1, 0, 1]
            d = math.sqrt(math.pow((x1-x0), 2) + math.pow((y1-y0), 2))
            avg_c.append(d)

    avg_x = sum(avg_r)/len(avg_r)
    avg_y = sum(avg_c)/len(avg_c)
    print('avg_x[%0.2f], avg_y[%0.2f]' % (avg_x, avg_y))
    return avg_x, avg_y


def get_scalar(img):
    print('get_scalar()')
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
    if ret:
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        scalar_x, scalar_y = get_p2p_dist(corners2)
        scalar_x /= grid_size
        scalar_y /= grid_size
        _scalar = (scalar_x + scalar_y)/2.0
        print('scalar', _scalar)
        return _scalar, scalar_x, scalar_y
    else:
        print('ERROR: Pattern not found.')
        return 0.0, 0.0, 0.0


class Calibration(object):
    def __init__(self, scan_dir):
        self._scalar = [0.0, 0.0]       # Front, Back
        self.scalar_x = [0.0, 0.0]
        self.scalar_y = [0.0, 0.0]
        self.b0 = cv2.imread(f'{scan_dir}\\calibration_b0.jpg')
        self.b1 = cv2.imread(f'{scan_dir}\\calibration_b1.jpg')
        self.b2 = cv2.imread(f'{scan_dir}\\calibration_b2.jpg')
        self.f0 = cv2.imread(f'{scan_dir}\\calibration_f0.jpg')
        self.f1 = cv2.imread(f'{scan_dir}\\calibration_f1.jpg')
        self.f2 = cv2.imread(f'{scan_dir}\\calibration_f2.jpg')
        self.ll_c = []
        self.rl_c = []
        self.get_scalar()
        self.get_c_tmp()

    def get_scalar(self):
        print('get_scalar()')
        s, x, y = get_scalar(self.b0)
        self._scalar[0] = s
        self.scalar_x[0] = x
        self.scalar_y[0] = y
        s, x, y = get_scalar(self.f0)
        self._scalar[1] = s
        self.scalar_x[1] = x
        self.scalar_y[1] = y

    def get_c_tmp(self):
        print('get_c_tmp()')
        rx, ry = get_roi_by_img(self.line, 1)
        roi = [rx, ry]
        xy = parser_util.points_min_cols(self.line, c=True, roi=roi)
        xy_l = len(xy) - 1
        print(xy)
        p = [[xy[0][0], xy[0][1]], [xy[xy_l][0], xy[xy_l][1]]]
        if p[1][0] - p[0][0] == 0:
            m = 1
        else:
            m = (p[1][1] - p[0][1]) * 1.0 / ((p[1][0] - p[0][0]) * 1.0)
        b = p[0][1] - (m * p[0][0])
        self.rl_c.append(m)
        self.rl_c.append(b)
        self.ll_c.append(m)
        self.ll_c.append(b)

    def get_c(self):
        print('get_c()')
        roi = []
        if self.rl is not None:
            # get x for y top, get x for y bot
            rx, ry = get_roi_by_img(self.rl, 1)
            roi = [rx, ry]
            img = cv2.subtract(self.rl, self.line)
            xy = parser_util.points_max_cols(img, c=True, roi=roi)
            xy_l = len(xy) - 1
            p = [[xy[0][0], xy[0][1]], [xy[xy_l][0], xy[xy_l][1]]]
            m = (p[1][1] - p[0][1]) * 1.0 / ((p[1][0] - p[0][0]) * 1.0)
            b = p[0][1] - (m * p[0][0])
            self.rl_c.append(m)
            self.rl_c.append(b)

        if self.ll is not None:
            # use RL ROI, get x for y top, get x for y bot
            if len(roi) == 0:
                rx, ry = get_roi_by_img(self.ll, 1)
                roi = [rx, ry]
            img = cv2.subtract(self.ll, self.line)
            xy = parser_util.points_max_cols(img, c=True, roi=roi)
            xy_l = len(xy) - 1
            p = [[xy[0][0], xy[0][1]], [xy[xy_l][0], xy[xy_l][1]]]
            m = (p[1][1] - p[0][1]) * 1.0 / ((p[1][0] - p[0][0]) * 1.0)
            b = p[0][1] - (m * p[0][0])
            self.ll_c.append(m)
            self.ll_c.append(b)

    def get_center_x(self, right, y):
        if right:
            return (y - self.rl_c[1]) / self.rl_c[0]
        else:
            return (y - self.ll_c[1]) / self.ll_c[0]

    @property
    def scalar(self):
        return self._scalar


"""
13.62 @ 62.25
9.45 @ -57.75
"""