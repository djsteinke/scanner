import math
import cv2
from parser_roi import get_roi_by_img
import parser_util
import json
import os
from calibrate_camera import CameraCalibration


grid_size = 13.0    # mm of grid squares
nx = 6              # nx: number of grids in x axis
ny = 6              # ny: number of grids in y axis

yf = 48.4
yr = -51.4

scale_x_slope = [0.0, 0.0]  # M(b, f) B(b, f)
scale_y_slope = [0.0, 0.0]  # M(b, f) B(b, f)
alpha_slope = [0.0, 0.0]  # M(b, f) B(b, f)


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


class LinearCalibration(object):
    def __init__(self, path):
        self._scalar = [0.0, 0.0]       # Front, Back
        self.scalar_x = [0.0, 0.0]
        self.scalar_y = [0.0, 0.0]
        self.b0 = None
        self.b1 = None
        self.f0 = None
        self.f1 = None
        self.c0 = None
        self.c1 = None
        self.la = [0.0, 0.0]
        self.lc = 0
        self.lx = [0, 0]
        self.ll_c = []
        self.rl_c = []
        #self.camera_calibration = CameraCalibration(path)
        self.path = path
        self.height = 0.0
        self.width = 0.0
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
            #self.b0 = self.camera_calibration.undistort_img(cv2.imread(f'{self.path}\\calibration_B0.jpg'))
            self.b0 = cv2.imread(f'{self.path}\\calibration_B0.jpg')
        else:
            #self.b0 = self.camera_calibration.undistort_img(cv2.imread(f'{self.path}\\calibration_B0.jpg'))
            #self.b1 = self.camera_calibration.undistort_img(cv2.imread(f'{self.path}\\calibration_B1.jpg'))
            #self.f0 = self.camera_calibration.undistort_img(cv2.imread(f'{self.path}\\calibration_F0.jpg'))
            #self.f1 = self.camera_calibration.undistort_img(cv2.imread(f'{self.path}\\calibration_F1.jpg'))
            self.b0 = cv2.imread(f'{self.path}\\calibration_B0.jpg')
            self.b1 = cv2.imread(f'{self.path}\\calibration_B1.jpg')
            self.f0 = cv2.imread(f'{self.path}\\calibration_F0.jpg')
            self.f1 = cv2.imread(f'{self.path}\\calibration_F1.jpg')
            self.get_scalar()
            self.get_c()
        self.height, self.width, _ = self.b0.shape
        print(self.height, self.width)
        self.set_slope()

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
        # print('f2', xy[xy_l][0], xy[xy_l][1])
        img = cv2.subtract(self.f1, self.f0)
        xy = parser_util.points_max_cols(img, c=True, roi=roi)
        xy_l = len(xy) - 1
        f1x = xy[xy_l][0]
        # print('f1', xy[xy_l][0], xy[xy_l][1])

        # get back r/l
        rx, ry = get_roi_by_img(self.b0, 1)
        roi = [rx, ry]
        # print('b2', xy[xy_l][0], xy[xy_l][1])
        img = cv2.subtract(self.b1, self.b0)
        xy = parser_util.points_max_cols(img, c=True, roi=roi)
        xy_l = len(xy) - 1
        b1x = xy[xy_l][0]
        # print('b1', xy[xy_l][0], xy[xy_l][1])
        self.lx = [b1x, f1x]

        h, w, _ = img.shape

        c = w/2
        if self.lc == 0:
            self.lc = c
        rad = math.atan((b1x - self.lc)*1.0/self._scalar[0]/yr)
        deg = math.degrees(rad)
        self.la[0] = deg
        print('b1', deg)
        rad = math.atan((f1x - self.lc)*1.0/self._scalar[1]/yf)
        deg = math.degrees(rad)
        self.la[1] = deg
        print('f1', deg)
        cal = {'scalar': self._scalar, 'sx': self.scalar_x, 'sy': self.scalar_y, 'la': self.la, 'lc': self.lc, 'lx': self.lx}
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

    def set_slope(self):
        global scale_x_slope, scale_y_slope, alpha_slope
        p = [[self.lx[0], self.scalar_x[0]], [self.lx[1], self.scalar_x[1]]]
        m, b = get_slope(p)
        scale_x_slope[0] = m
        scale_x_slope[1] = b
        p = [[self.lx[0], self.scalar_y[0]], [self.lx[1], self.scalar_y[1]]]
        m, b = get_slope(p)
        scale_y_slope[0] = m
        scale_y_slope[1] = b
        p = [[self.lx[0], self.la[0]], [self.lx[1], self.la[1]]]
        m, b = get_slope(p)
        alpha_slope[0] = m
        alpha_slope[1] = b

    def get_scaled_xyz(self, px, py, offset=0):
        # get scale at x
        # get alpha at x
        # use scale to get x
        # use x and alpha for corrected xy
        px = px * 1.0
        py = py * 1.0
        scale_x = scale_x_slope[0] * px + scale_x_slope[1]
        scale_y = scale_y_slope[0] * px + scale_y_slope[1]
        # alpha = alpha_slope[0] * px + alpha_slope[1]
        alpha = 25.5
        cam_angle = math.radians(alpha)

        cx = self.width/2.0
        cy = self.height/2.0
        r_cam = 235.0
        y = (px - cx) / scale_x
        x = y / math.tan(cam_angle)
        z = (cy - py) / scale_y

        beta = math.atan(y/(r_cam - x))
        y_cam = - offset + r_cam * math.sin(beta)
        x_cam = x - r_cam*(1.0 - math.cos(beta))

        delta = math.atan(z / (r_cam - x))
        z_cam = r_cam * math.sin(delta)

        # r_cam_old = 450.0
        # beta_old = math.atan(y/(r_cam_old - x))
        # y_cam_old = - offset + r_cam_old * math.sin(beta_old)
        # x_cam_old = x - r_cam_old*(1.0 - math.cos(beta_old))
        # delta_old = math.atan(z / (r_cam_old - x))
        # z_cam_old = r_cam_old * math.sin(delta_old)
        print(round(x_cam, 2), round(x, 2), round(y_cam, 2), round(y - offset, 2), round(z_cam, 2), round(z, 2))

        return x_cam, y_cam, z_cam

    def get_scalar_by_x(self, x):
        return scale_x_slope[0] * x + scale_x_slope[1]

    @property
    def scalar(self):
        return self._scalar[0]


"""
13.62 @ 62.25
9.45 @ -57.75
"""