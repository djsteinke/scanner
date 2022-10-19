import cv2
from os import getcwd
from parser_linear_calibration import get_p2p_dist
import numpy as np
from skimage.metrics import structural_similarity


scan_path = getcwd() + "\\linear_calibration\\"


f1 = cv2.imread(scan_path + "calibration_F1.jpg")
f0 = cv2.imread(scan_path + "calibration_F0.jpg")
b1 = cv2.imread(scan_path + "calibration_B1.jpg")
b0 = cv2.imread(scan_path + "calibration_B0.jpg")


# Convert images to grayscale
f1_g = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
f0_g = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
b1_g = cv2.cvtColor(b1, cv2.COLOR_BGR2GRAY)
b0_g = cv2.cvtColor(b0, cv2.COLOR_BGR2GRAY)

grid_size = 13.0    # mm of grid squares
nx = 6              # nx: number of grids in x axis
ny = 9              # ny: number of grids in y axis

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
gray = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
print(corners)
if ret:
    corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
    scalar_x, scalar_y = get_p2p_dist(corners2)
    scalar_x /= grid_size
    scalar_y /= grid_size
    _scalar = (scalar_x + scalar_y) / 2.0
    print('scalar', _scalar)
