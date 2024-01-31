import glob
import os

import cv2
import numpy as np

from AndroidSocket import AndroidSocket
from calibrate_camera import CameraCalibration
from scan_popup import ScanPopup


nx = 11
ny = 14
xy = 14.5  # mm

dz1 = 293.0
#dz1 = 344.0
#dz2 = 304.0

objp = np.zeros((nx * ny, 3), np.float32)
objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


class AndroidScalar(object):
    def __init__(self, path="/"):
        self._path = path  # /calibration/android
        self._popup = ScanPopup(steps=2, button="Next", callback=self.step)
        self._curr_step = 0

    def start(self):
        self._popup.open()
        if not os.path.isdir(self._path):
            os.makedirs(self._path)
        self.step()

    def step(self):
        if 0 < self._curr_step < 3:
            android_socket = AndroidSocket(self._path)
            name = f'scalar_%04d.jpg' % self._curr_step
            android_socket.take_pic(name)
        self._popup.step(self._curr_step)
        self._curr_step += 1

    def calculate_f_o(self):

        camera_calibration = CameraCalibration(wd=self._path, reload=False)
        images = glob.glob('%s/scalar_*.jpg' % self._path.rstrip('/'))
        print(images)

        objpoints = []  # 3d point in real world space
        imgpoints = []  # 2d points in image plane.

        i = 0
        x_a = []
        for img_name in images:
            cv2image = cv2.imread(img_name)
            h, w, _ = cv2image.shape
            if w > h:
                cv2image = cv2.rotate(cv2image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                h, w, _ = cv2image.shape

            cv2image = camera_calibration.undistort_img(cv2image, crop=False)

            gray = cv2.cvtColor(cv2image, cv2.COLOR_BGR2GRAY)

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)

            print(i, "found chessboard", ret)

            # If found, add object points, image points (after refining them)
            if ret:
                objpoints.append(objp)

                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                imgpoints.append(corners2)

                # Draw and display the corners
                img = cv2.drawChessboardCorners(cv2image, (nx, ny), corners2, ret)
                cv2.imshow('img', img)
                cv2.waitKey()

                pX = corners2[(ny - 1) * nx][0][0]
                pdx = 0
                pdy = 0
                pdt = 0
                # print(calibration.corners_ret)
                for y in range(0, ny - 1):
                    for x in range(0, nx - 1):
                        pdt += 1
                        i = y * nx + x
                        pdx += corners2[i + 1][0][0] - corners2[i][0][0]
                        pdy += corners2[i + nx][0][1] - corners2[i][0][1]
                pdx /= pdt
                pdy /= pdt
                x_a.append(pdx)
                i += 1
                print(i, pX, pdx, pdy)
        #f = (dz1 - dz2)/(xy/x_a[0] - xy/x_a[1])
        f = 1520.7
        o = xy/x_a[0] * f - dz1
        #of = xy/x_a[0] * 1581.4 - dz1
        print(round(f, 1), round(o, 1))  # 1559.5 33.1 @ 23deg

"""
p = os.getcwd() + "\\calibration\\android"
print(p)
if os.path.isfile(p + "\\scalar_0002.jpg"):
    print("scalar exists")
else:
    print("incorrect path")
cal = AndroidScalar(path=p)
cal.calculate_f_o()
"""

# c dist 281.2
