import pickle
import numpy as np
import cv2
import glob
from os import getcwd, path


pickle_file = 'calibration_pickle.p'

"""
grid_size = 15.0    # mm of grid squares
nx = 13              # nx: number of grids in x axis
ny = 17              # ny: number of grids in y axis
"""

# 7, 9, 25
# 11, 14, 14.5

grid_size = 25    # mm of grid squares
nx = 7              # nx: number of grids in x axis
ny = 9              # ny: number of grids in y axis
#nx = 11              # nx: number of grids in x axis
#ny = 14              # ny: number of grids in y axis

objp = np.zeros((nx * ny, 3), np.float32)
objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

out = True

printed = False


class CameraCalibration(object):
    def __init__(self, wd=None, reload=False):
        self._mtx = None
        self.dist = None
        self.wd = wd
        if wd is not None:
            self._mtx, self.dist = self.load_calibration(reload)

    def undistort_img(self, img, crop=True):
        if self.wd is not None:
            h, w = img.shape[:2]
            if h < w:
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                h, w = img.shape[:2]
            newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self._mtx, self.dist, (w, h), 1, (w, h))
            img_undist = cv2.undistort(img, self._mtx, self.dist, None, newcameramtx)

            if crop:
                x, y, w, h = roi
                img_undist = img_undist[y:y + h, x:x + w]
            #img_color = cv2.cvtColor(img_undist, cv2.COLOR_GRAY2RGB)
            return img_undist
        else:
            return img

    def undistort_file(self, imagepath):
        img = cv2.imread(imagepath)
        # undistort the image
        img_undist = cv2.undistort(img, self._mtx, self.dist, None, self._mtx)
        img_undistRGB = cv2.cvtColor(img_undist, cv2.COLOR_BGR2RGB)
        return img_undistRGB

    def determine_calibration(self):
        objpoints = []  # 3d point in real world space
        imgpoints = []  # 2d points in image plane.

        p = self.wd

        images = glob.glob('%s/calibration_*.jpg' % p.rstrip('/'))
        print(images)

        gray_pic = None
        for fname in images:
            img = cv2.imread(fname)
            #img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if gray_pic is None:
                gray_pic = gray

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)

            print(fname, "found chessboard", ret)

            # If found, add object points, image points (after refining them)
            if ret:
                objpoints.append(objp)

                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                imgpoints.append(corners2)

                # Draw and display the corners
                img = cv2.drawChessboardCorners(img, (nx, ny), corners2, ret)
                cv2.imshow('img', img)
                cv2.waitKey()

        cv2.destroyAllWindows()
        if gray_pic is None:
            self.wd = None
            return None, None

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray_pic.shape[::-1], None, None)
        print(cv2.calibrationMatrixValues(mtx, gray_pic.shape[::-1], 4.896, 3.864))
        return mtx, dist

    def load_calibration(self, reload):
        source = self.wd + "\\" + pickle_file

        if path.isfile(source) and not reload:
            with open(source, 'rb') as file:
                # print('load calibration data')
                data = pickle.load(file)
                mtx = data['mtx']       # calibration matrix
                dist = data['dist']     # distortion coefficients
                print(mtx)
        else:
            mtx, dist = self.determine_calibration()
            if mtx is not None or dist is not None:
                save_calibration(mtx, dist, self.wd)

        return mtx, dist

    @property
    def mtx(self):
        if self._mtx is None:
            return [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        else:
            return self._mtx


def save_calibration(mtx, dist, wd):
    data = {'mtx': mtx, 'dist': dist}
    if wd is None:
        destination = getcwd() + "\\calibration\\" + pickle_file
    else:
        destination = wd + "\\" + pickle_file
    pickle.dump(data, open(destination, "wb"))


p = "C:\\Users\\djste\\PyCharmProjects\\scanner\\calibration\\android"
print(p)
if path.isfile(p + "\\calibration_0001.jpg"):
    print("cal exists")
cal = CameraCalibration(wd=p, reload=True)
print(cal.mtx)
