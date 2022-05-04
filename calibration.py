import os
import cv2
import numpy as np
import glob
from scan_popup import ScanPopup

steps = 11
nx = 6              # nx: number of grids in x axis
ny = 9              # ny: number of grids in y axis

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((nx*ny, 3), np.float32)
objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)
# Arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.


def det_camera_matrix():
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    path = os.getcwd() + "\\calibration"
    images = glob.glob("%s/calibration_00*" % path.rstrip('/'))
    images.sort()

    for f_name in images:
        img = cv2.imread(f_name)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)

        # If found, add object points, image points (after refining them)
        if ret:
            objpoints.append(objp)

            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)

            # Draw and display the corners
            img = cv2.drawChessboardCorners(img, (nx, ny), corners2, ret)
            cv2.imshow('img', img)
            cv2.waitKey(500)

    cv2.destroyAllWindows()

    img = cv2.imread(images[5])
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    img_path = os.getcwd() + "\\scans\\20220504084303\\right_0091.jpg"
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
    # undistort
    dst = cv2.undistort(img, mtx, dist, None, newcameramtx)

    # crop the image
    x, y, w, h = roi
    dst = dst[y:y + h, x:x + w]
    cv2.imshow('undistorted', dst)
    cv2.imshow('original', img)
    cv2.waitKey()


class Calibration(object):
    def __init__(self, arduino=None, android=None, path="/", callback=None):
        self.arduino = arduino
        self.android = android
        self.path = path
        self._callback = callback
        self.popup = ScanPopup()

    def start(self):
        self.popup = ScanPopup(steps=steps)
        self.popup.open()
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
        self.calibrate()

    def step(self, val):
        self.popup.step(val)

    def calibrate(self):
        self.arduino.send_msg_new(1)
        self.arduino.send_msg_new(3)
        dps = 180.0 / 360.0 / (steps * 1.0 - 1.0)  # degrees / step, 180 degrees / 10 steps
        pps = round(200.0 * 16.0 * dps)  # 200 full steps per rotation (motor), 16 micro-steps
        for i in range(1, steps):
            self.android.take_picture(f'%s/calibration_%04d.jpg' % (self.path, i))
            self.arduino.send_msg_new(6, 1, pps)  # turn platform
            if self.popup is not None:
                self.step(i + 1)

        self.android.move_files()
        if self._callback is not None:
            self._callback()
