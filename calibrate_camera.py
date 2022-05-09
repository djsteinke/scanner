import pickle
import numpy as np
import cv2
import glob
from os import getcwd, path


pickle_file = 'calibration_pickle.p'

grid_size = 15.0    # mm of grid squares
nx = 13              # nx: number of grids in x axis
ny = 17              # ny: number of grids in y axis

objp = np.zeros((nx * ny, 3), np.float32)
objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

out = True

printed = False


class CameraCalibration(object):
    def __init__(self):
        self.mtx = None
        self.dist = None
        load_calibration()

    def undistor_img(self, img):
        img_undist = cv2.undistort(img, self.mtx, self.dist, None, mtx)
        img_undistRGB = cv2.cvtColor(img_undist, cv2.COLOR_BGR2RGB)
        return img_undistRGB

    def undistort_file(self, imagepath):
        img = cv2.imread(imagepath)
        # undistort the image
        img_undist = cv2.undistort(img, self.mtx, self.dist, None, self.mtx)
        img_undistRGB = cv2.cvtColor(img_undist, cv2.COLOR_BGR2RGB)

        """ 
        # new camera matrix, crop
        img = cv2.imread('left12.jpg')
        h, w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
        # undistort
        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        """

        return img_undistRGB


def determine_calibration():
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.

    p = getcwd() + "\\calibration"
    images = glob.glob('%s/calibration_*[0].jpg' % p.rstrip('/'))
    print(images)

    pic_shape = []
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        pic_shape = gray.shape[::-1]

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

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, pic_shape, None, None)
    return mtx, dist


def load_calibration():
    source = getcwd() + "\\calibration" + pickle_file
    if path.isfile(source):
        with open(source, 'rb') as file:
            # print('load calibration data')
            data = pickle.load(file)
            mtx = data['mtx']       # calibration matrix
            dist = data['dist']     # distortion coefficients
    else:
        mtx, dist = determine_calibration()
        save_calibration(mtx, dist)

    return mtx, dist


def save_calibration(mtx, dist):
    data = {'mtx': mtx, 'dist': dist}

    destination = getcwd() + "\\calibration" + pickle_file
    pickle.dump(data, open(destination, "wb"))
