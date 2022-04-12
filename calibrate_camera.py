import codecs
import math

import pickle

import numpy as np
import cv2
import glob
import json
from tkinter import Tk, Label
from PIL import ImageTk, Image
from os import path
#import matplotlib.pyplot as plt

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

nx = 11      # nx: number of grids in x axis
ny = 6     # ny: number of grids in y axis

objp = np.zeros((nx * ny, 3), np.float32)
objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)

images = glob.glob('*.jpg')

cap = cv2.VideoCapture(0, cv2.CAP_ANY)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

out = True

printed = False


def get_p2p_dist(p):
    print(p[0], p[1])
    print(f'x[%0.2f] y[%0.2f]' % (p[0, 0, 0], p[0, 0, 1]))
    avg_x = []
    avg_y = []
    for y in range(0, ny):
        for x in range(0, nx-1):
            x0 = p[y*x+x, 0, 0]
            y0 = p[y*x+x, 0, 1]
            x1 = p[y*x+x+1, 0, 0]
            y1 = p[y*x+x+1, 0, 1]
            d = math.sqrt(math.pow((x1-x0), 2) + math.pow((y1-y0), 2))
            #print(x0, y0, x1, y1, d)
            avg_x.append(d)
    for x in range(0, nx):
        for y in range(0, ny-1):
            x0 = p[y*x+x, 0, 0]
            y0 = p[y*x+x, 0, 1]
            x1 = p[y*x+x+1, 0, 0]
            y1 = p[y*x+x+1, 0, 1]
            d = math.sqrt(math.pow((x1-x0), 2) + math.pow((y1-y0), 2))
            #print(x0, y0, x1, y1, d)
            avg_y.append(d)

    avgX = sum(avg_x)/len(avg_x)
    avgY = sum(avg_y)/len(avg_y)
    print('avg_x[%0.2f], avg_y[%0.2f]' % (avgX, avgY))


def video_stream():
    global out, printed
    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d points in real world space
    imgpoints = []  # 2d points in image plane.

    res, fr = cap.read()

    dimensions = fr.shape  # height, width, number of channels in image

    gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
    color_img = fr
    if ret:
        #print("Corners found.")
        objpoints.append(objp)
        imgpoints.append(corners)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        # Draw and display the corners
        if not printed:
            print(corners2)
            get_p2p_dist(corners2)
            printed = True
        color_img = cv2.drawChessboardCorners(fr, (nx, ny), corners2, ret)

    if ret and out:
        # img = cv2.imread('left12.jpg')
        h, w = gray.shape[:2]
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))

        dst = cv2.undistort(gray, mtx, dist, None, newcameramtx)
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        cv2.imwrite('calibresult.png', dst)
        dist_pickle = {"mtx": mtx, "dist": dist}
        """
        print('mtx: ' + mtx)
        print('dist: ' + dist)
        destination = path.join('/', 'calibration_pickle.p')
        destnation = path.join(basepath,'calibration_pickle.p')
        pickle.dump( dist_pickle, open( destnation, "wb" ) )
        print("calibration data is written into: {}".format(destination))
        out = False
        """
    # return mtx, dist
    color_img = Image.fromarray(color_img)
    color_img = ImageTk.PhotoImage(color_img)
    lmain.imgtk = color_img
    lmain.configure(image=color_img)
    lmain.after(1, video_stream)


def undistort_image(imagepath, calib_file, visulization_flag):
    """ undistort the image and visualization

    :param imagepath: image path
    :param calib_file: includes calibration matrix and distortion coefficients
    :param visulization_flag: flag to plot the image
    :return: none
    """
    mtx, dist = load_calibration(calib_file)

    img = cv2.imread(imagepath)

    # undistort the image
    img_undist = cv2.undistort(img, mtx, dist, None, mtx)
    img_undistRGB = cv2.cvtColor(img_undist, cv2.COLOR_BGR2RGB)

    """
    if visulization_flag:
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        f, (ax1, ax2) = plt.subplots(1, 2)
        ax1.imshow(imgRGB)
        ax1.set_title('Original Image', fontsize=30)
        ax1.axis('off')
        ax2.imshow(img_undistRGB)
        ax2.set_title('Undistorted Image', fontsize=30)
        ax2.axis('off')
        plt.show()
    """

    return img_undistRGB


def load_calibration(calib_file):
    """
    :param calib_file:
    :return: mtx and dist
    """
    with open(calib_file, 'rb') as file:
        # print('load calibration data')
        data = pickle.load(file)
        mtx = data['mtx']       # calibration matrix
        dist = data['dist']     # distortion coefficients

    return mtx, dist


if __name__ == '__main__':
    root = Tk()
    root.title("Scanner")

    lmain = Label(root)
    lmain.pack()

    video_stream()
    root.mainloop()

    cap.release()
    cv2.destroyAllWindows()
