import cv2
from os import getcwd
from parser_calibration import get_p2p_dist


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

fr = cv2.imread(scan_path + "linear_calibration_F0.jpg")
#cn = cv2.imread(scan_path + "linear_calibration_C0.jpg")
rr = cv2.imread(scan_path + "linear_calibration_B0.jpg")

fr_s = get_scalar(fr)
#cn_s = get_scalar(cn)
rr_s = get_scalar(rr)

#print(fr_s - cn_s)
#print(cn_s - rr_s)


"""
13.62 @ 62.25
9.45 @ -57.75
"""