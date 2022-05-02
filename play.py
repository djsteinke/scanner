import cv2
from os import getcwd
from parser_calibration import get_p2p_dist, Calibration


grid_size = 15.0
nx = 6
ny = 9


def get_scalar(img):
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
    if ret:
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        scalar_x, scalar_y = get_p2p_dist(corners2)
        scalar_x /= grid_size
        scalar_y /= grid_size
        _scalar = (scalar_x + scalar_y) / 2.0
        print('scalar', _scalar)
        return _scalar


scan_path = getcwd() + "\\calibration\\"

ratio = 6

f2 = cv2.imread(scan_path + "calibration_F2.jpg")
f1 = cv2.imread(scan_path + "calibration_F1.jpg")
f0 = cv2.imread(scan_path + "calibration_F0.jpg")
c2 = cv2.imread(scan_path + "calibration_C2.jpg")
c1 = cv2.imread(scan_path + "calibration_C1.jpg")
c0 = cv2.imread(scan_path + "calibration_C0.jpg")
h, w, _ = f2.shape

h_tmp = int(h / ratio)
w_tmp = int(w / ratio)
f2 = cv2.subtract(c2, c0)
f2 = cv2.resize(f2, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
h, w, _ = f2.shape

"""  # draw line
for r in f_xy:
    new_f[r[1], r[0], 2] = 255
for r in xy:
    new[r[1], r[0], 2] = 255
    img[r[1], r[0], 2] = 255
"""

for a in range(0, w, 50):
    r = 5
    if a % 100 == 0:
        r = 2
    for b in range(0, h, r):
        f2[b, a, 0] = 255
for a in range(0, h, 50):
    r = 5
    if a % 100 == 0:
        r = 2
    for b in range(0, w, r):
        f2[a, b, 0] = 255

#cv2.imshow('Front', f2)
#cv2.waitKey()

calibration = Calibration(getcwd() + "\\calibration")
"""
13.65 @ 62.25
9.83 @ -57.75
"""