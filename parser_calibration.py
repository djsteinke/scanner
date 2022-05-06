import math
import cv2
from parser_roi import get_roi_by_img
import parser_util
import json
import os


grid_size = 13.0    # mm of grid squares
nx = 6              # nx: number of grids in x axis
ny = 9              # ny: number of grids in y axis
c_offset_x_top = (1540.0 - 3120.0/2.0)  # 900
c_offset_x = (1520.0 - 3120.0/2.0)   # 3300
c_offset_y = 3645

c_offset_top = [-20, 900]
c_offset_bottom = [-40, 3300]

yf = 62.245
yr = -57.625


def get_p2p_dist(p):
    avg_r = []
    avg_c = []
    for y in range(0, ny):
        for x in range(0, nx-1):
            x0 = p[y*nx+x, 0, 0]
            y0 = p[y*nx+x, 0, 1]
            x1 = p[y*nx+x+1, 0, 0]
            y1 = p[y*nx+x+1, 0, 1]
            d = math.sqrt(math.pow((x1-x0), 2) + math.pow((y1-y0), 2))
            # print('y x d', y, x, d)
            avg_r.append(d)
    for x in range(0, nx):
        for y in range(0, ny-1):
            x0 = p[x+y*nx, 0, 0]
            y0 = p[x+y*nx, 0, 1]
            x1 = p[x+y*nx+nx, 0, 0]
            y1 = p[x+y*nx+nx, 0, 1]
            d = math.sqrt(math.pow((x1-x0), 2) + math.pow((y1-y0), 2))
            # print('x y d', x, y, d)
            avg_c.append(d)
    print('length', len(avg_r), len(avg_c))
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


def get_slope(p):
    m = (p[1][1] - p[0][1]) * 1.0 / ((p[1][0] - p[0][0]) * 1.0)
    b = p[0][1] - (m * p[0][0])
    return m, b


class Calibration(object):
    def __init__(self, path):
        self._scalar = [0.0, 0.0]       # Front, Back
        self.scalar_x = [0.0, 0.0]
        self.scalar_y = [0.0, 0.0]
        self.b0 = None
        self.b1 = None
        self.b2 = None
        self.f0 = None
        self.f1 = None
        self.f2 = None
        self.c0 = None
        self.c1 = None
        self.c2 = None
        self.la = [[0.0, 0.0], [0.0, 0.0]]
        self.lc = [0, 0]
        self.lx = [[0, 0], [0, 0]]
        self.ll_c = []
        self.rl_c = []
        self.path = path
        self.load()

    def load(self):
        file = self.path + "\\calibration.json"
        if os.path.isfile(file):
            f = open(file, 'r')
            cal = json.load(f)
            self._scalar = cal['scalar']
            self.scalar_x = cal['sx']
            self.scalar_y = cal['sy']
            self.la = cal['la']
            self.lc = cal['lc']
            self.lx = cal['lx']
        else:
            self.b0 = cv2.imread(f'{self.path}\\calibration_B0.jpg')
            self.b1 = cv2.imread(f'{self.path}\\calibration_B1.jpg')
            self.b2 = cv2.imread(f'{self.path}\\calibration_B2.jpg')
            self.f0 = cv2.imread(f'{self.path}\\calibration_F0.jpg')
            self.f1 = cv2.imread(f'{self.path}\\calibration_F1.jpg')
            self.f2 = cv2.imread(f'{self.path}\\calibration_F2.jpg')
            self.c0 = cv2.imread(f'{self.path}\\calibration_C0.jpg')
            self.c1 = cv2.imread(f'{self.path}\\calibration_C1.jpg')
            self.c2 = cv2.imread(f'{self.path}\\calibration_C2.jpg')
            self.get_scalar()
            self.get_c()

    def get_scalar(self):
        s, x, y = get_scalar(self.b0)
        self._scalar[0] = s
        self.scalar_x[0] = x
        self.scalar_y[0] = y
        s, x, y = get_scalar(self.f0)
        self._scalar[1] = s
        self.scalar_x[1] = x
        self.scalar_y[1] = y

    def get_c(self):
        # print('get_c()')
        # get front r/l
        rx, ry = get_roi_by_img(self.f0, 1)
        roi = [rx, ry]
        img = cv2.subtract(self.f2, self.f0)
        xy = parser_util.points_max_cols(img, c=True, roi=roi)
        xy_l = len(xy) - 1
        f2x = xy[xy_l][0]
        # print('f2', xy[xy_l][0], xy[xy_l][1])
        img = cv2.subtract(self.f1, self.f0)
        xy = parser_util.points_max_cols(img, c=True, roi=roi)
        xy_l = len(xy) - 1
        f1x = xy[xy_l][0]
        # print('f1', xy[xy_l][0], xy[xy_l][1])

        # get back r/l
        rx, ry = get_roi_by_img(self.b0, 1)
        roi = [rx, ry]
        img = cv2.subtract(self.b2, self.b0)
        xy = parser_util.points_max_cols(img, c=True, roi=roi)
        xy_l = len(xy) - 1
        b2x = xy[xy_l][0]
        # print('b2', xy[xy_l][0], xy[xy_l][1])
        img = cv2.subtract(self.b1, self.b0)
        xy = parser_util.points_max_cols(img, c=True, roi=roi)
        xy_l = len(xy) - 1
        b1x = xy[xy_l][0]
        # print('b1', xy[xy_l][0], xy[xy_l][1])
        self.lx = [[b1x, b2x], [f1x, f2x]]

        # get center r/l
        rx, ry = get_roi_by_img(self.c0, 1)
        roi = [rx, ry]
        img = cv2.subtract(self.c2, self.c0)
        xy = parser_util.points_max_cols(img, c=True, roi=roi)
        xy_l = len(xy) - 1
        c2x = xy[xy_l][0]
        # print('b2', xy[xy_l][0], xy[xy_l][1])
        img = cv2.subtract(self.c1, self.c0)
        xy = parser_util.points_max_cols(img, c=True, roi=roi)
        xy_l = len(xy) - 1
        c1x = xy[xy_l][0]
        self.lc = [c1x, c2x]
        print(self.lc)

        h, w, _ = img.shape

        c = w/2 + c_offset_x
        rad = math.atan((b1x - self.lc[0])/self.scalar[0]/yr)
        deg = math.degrees(rad)
        self.la[0][0] = deg
        print('b1', deg)
        rad = math.atan((b2x - self.lc[1])*1.0/self.scalar[0]/yr)
        deg = math.degrees(rad)
        self.la[0][1] = deg
        print('b2', deg)
        rad = math.atan((f1x - self.lc[0])*1.0/self.scalar[1]/yf)
        deg = math.degrees(rad)
        self.la[1][0] = deg
        print('f1', deg)
        rad = math.atan((f2x - self.lc[1])*1.0/self.scalar[1]/yf)
        deg = math.degrees(rad)
        self.la[1][1] = deg
        print('f2', deg)
        cal = {'scalar': self.scalar, 'sx': self.scalar_x, 'sy': self.scalar_y, 'la': self.la, 'lc': self.lc, 'lx': self.lx}
        print(cal)
        d_path = self.path + "\\calibration.json"
        f = open(d_path, 'w')
        f.write(json.dumps(cal))
        f.close()

    def get_center_x(self, right, y):
        if right:
            return (y - self.rl_c[1]) / self.rl_c[0]
        else:
            return (y - self.ll_c[1]) / self.ll_c[0]

    def get_scaled_xyz(self, px, py, right, offset=0):
        # get scale at x
        # get alpha at x
        # use scale to get x
        # use x and alpha for corrected xy
        px = px * 1.0
        py = py * 1.0
        orig_x = px
        l = 1 if right else 0
        p = [[self.lx[0][l], self.scalar_x[0]], [self.lx[1][l], self.scalar_x[1]]]
        m, b = get_slope(p)
        scale_x = m*px + b
        p = [[self.lx[0][l], self.scalar_y[0]], [self.lx[1][l], self.scalar_y[1]]]
        m, b = get_slope(p)
        scale_y = m*px + b
        p = [[self.lx[0][l], self.la[0][l]], [self.lx[1][l], self.la[1][l]]]
        m, b = get_slope(p)
        alpha = m*px + b
        if l == 0:
            p = [[self.lx[0][1], self.la[0][1]], [self.lx[1][1], self.la[1][1]]]
            m, b = get_slope(p)
            alpha_r = m * px + b
            offset += (alpha_r - alpha)
        cam_angle = math.radians(alpha)

        cy = 4160.0/2.0
        pz = cy - py
        calc_z = pz / scale_y
        r_cam = 463.0

        #pz = py - c_offset_bottom[1]
        m, b = get_slope([c_offset_top, c_offset_bottom])
        c_offset = (py - b) / m
        px -= self.lc[l]
        px -= c_offset
        angle = math.radians(offset)
        zx = px / math.tan(cam_angle) / scale_x
        radius = px / math.sin(cam_angle)
        calc_x = zx
        """
        alpha_p = math.atan(px / (r_cam - zx))
        calc_x = r_cam * math.sin(alpha_p)
        calc_y = r_cam - (r_cam * math.cos(alpha_p))
        """
        #calc_x = radius * math.sin(angle) / scale_x
        #calc_y = radius * math.cos(angle) / scale_x
        x = r_cam - zx
        a_x = math.atan((px/scale_x)/x)
        calc_y = r_cam * math.cos(a_x) - (r_cam - calc_x)
        calc_x *= math.sin(angle)
        calc_y *= math.cos(angle)
        a = math.atan(calc_z/x)
        calc_z = r_cam * math.sin(a)
        #calc_z = pz / scale_y

        return calc_x, calc_y, calc_z

    @property
    def scalar(self):
        return self._scalar


"""
13.62 @ 62.25
9.45 @ -57.75
"""