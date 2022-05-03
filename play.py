import cv2
from os import getcwd
from parser_calibration import get_p2p_dist, Calibration
import numpy as np


grid_size = 15.0
nx = 6
ny = 9

f_corners = ((1130.8029, 2210.4624), (1957.5778, 2213.00540), (1123.7435, 3218.1375), (1958.0111, 3217.0122))
b_corners = ((1239.5405, 2158.0088), (1826.0752, 2165.559), (1228.4081, 2869.7708), (1819.037,  2874.9055))


def get_mb(pts):
    m = (pts[1][1] - pts[0][1]) * 1.0 / ((pts[1][0] - pts[0][0]) * 1.0)
    b = pts[0][1] - (m * pts[0][0])
    return m, b


def get_scalar(s_img, front=False):
    global f_corners, b_corners
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    gray = cv2.cvtColor(s_img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
    #print(corners)
    if ret:
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        if front:
            f_corners = corners2
        else:
            b_corners = corners2
        #print(corners2)
        scalar_x, scalar_y = get_p2p_dist(corners2)
        scalar_x /= grid_size
        scalar_y /= grid_size
        _scalar = (scalar_x + scalar_y) / 2.0
        print('scalar', _scalar, scalar_x, scalar_y)
        return _scalar


scan_path = getcwd() + "\\calibration\\"

ratio = 6

f2 = cv2.imread(scan_path + "calibration_F2.jpg")
f1 = cv2.imread(scan_path + "calibration_F1.jpg")
f0 = cv2.imread(scan_path + "calibration_F0.jpg")
c2 = cv2.imread(scan_path + "calibration_C2.jpg")
c1 = cv2.imread(scan_path + "calibration_C1.jpg")
c0 = cv2.imread(scan_path + "calibration_C0.jpg")
b0 = cv2.imread(scan_path + "calibration_B0.jpg")
h, w, _ = f2.shape

print('----- FRONT -----')
#get_scalar(f0, True)
#print(f_corners[0], f_corners[5], f_corners[nx*nx], f_corners[nx*nx + (nx-1)])
print('----- BACK -----')
#get_scalar(b0)
#print(b_corners[0], b_corners[5], b_corners[nx*nx], b_corners[nx*nx + (nx-1)])

# line from f->b for each corner, find
new = np.zeros((h, w, 3), np.uint8)
new = b0

m1, b1 = get_mb(((int(f_corners[0][0]), int(f_corners[0][1])), (int(b_corners[0][0]), int(b_corners[0][1]))))
m2, b2 = get_mb(((int(f_corners[1][0]), int(f_corners[1][1])), (int(b_corners[1][0]), int(b_corners[1][1]))))
xc = (b1 - b2) / (m2 - m1)
yc = int(m1*xc + b1)
print('x y', xc, yc)
cv2.line(new, (int(f_corners[0][0]), int(f_corners[0][1])), (int(xc), yc), color=[0, 0, 255], thickness=3)
cv2.line(new, (int(f_corners[1][0]), int(f_corners[1][1])), (int(xc), yc), color=[0, 0, 255], thickness=3)

m3, b3 = get_mb(((int(f_corners[2][0]), int(f_corners[2][1])), (int(b_corners[2][0]), int(b_corners[2][1]))))
m4, b4 = get_mb(((int(f_corners[3][0]), int(f_corners[3][1])), (int(b_corners[3][0]), int(b_corners[3][1]))))
xc = (b3 - b4) / (m4 - m3)
yc = int(m3*xc + b3)
print('x y', xc, yc)

cv2.line(new, (int(f_corners[2][0]), int(f_corners[2][1])), (int(xc), yc), color=[255, 0, 0], thickness=3)
cv2.line(new, (int(f_corners[3][0]), int(f_corners[3][1])), (int(xc), yc), color=[255, 0, 0], thickness=3)

h_tmp = int(h / ratio)
w_tmp = int(w / ratio)
#f2 = cv2.subtract(c2, c0)
new = cv2.resize(new, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
cv2.imshow('lines', new)
img = cv2.resize(f0, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
h, w, _ = img.shape

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
        img[b, a, 0] = 255
for a in range(0, h, 50):
    r = 5
    if a % 100 == 0:
        r = 2
    for b in range(0, w, r):
        img[a, b, 0] = 255

#cv2.imshow('Front', img)
cv2.waitKey()

# calibration = Calibration(getcwd() + "\\calibration")

"""
13.65 @ 62.25
9.83 @ -57.75
"""