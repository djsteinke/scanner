
import glob
from os import getcwd
import math
import cv2
import numpy as np
from model.pointset import *


def points_triangulate(points, y_offset, l_dist):

    cam_degree = 30
    x, y = points
    cam_angle = math.radians(cam_degree)
    calc_x = x / math.sin(cam_angle)
    calc_y = calc_x * math.tan(cam_angle)
    x_offset = y_offset * math.tan(-60)

    return [
        calc_x + x_offset,
        calc_y + y_offset,
        y * 1.00
    ]


def points_triangulate_old(points, y_offset, l_dist):
    cam_degree = 30
    x, y = points
    cam_angle = math.radians(cam_degree)
    angle = math.radians(0)

    radius = x / math.sin(cam_angle)

    return [
        radius * math.cos(angle),
        radius * math.sin(angle) + y_offset,
        y * 1.00
    ]


def points_max_cols(img, threshold=(200, 255), xR=None, yR=None):
    """
    Read maximum pixel value in one color channel for each row
    """

    tmin, tmax = threshold
    h, w, c = img.shape
    xy = list()

    if xR is None:
        xR = (0, w)
    if yR is None:
        yR = (0, h)

    hStart = int(h/2)

    for i in range(yR[0], yR[1]):
        mx = 0
        mv = 0
        for x in range(xR[0], xR[1]):
            try:
                if img[i, x, 2] > mv:
                    mv = img[i, x, 2]
                    mx = x
            except IndexError as e:
                print(f'x[{x}] y[{i}]')
        valid = i < 0.5*mx +565
        if mv > tmin and valid:
            xy.append((mx, i))

    return xy


def points_process_images(images, threshold_min=200, threshold_max=255):
    """
    extract 3d pixels and colors from either left or right set of images
    """
    turns = 1.8
    x_offset_turn = 1.0/18.0*turns/0.75*45
    #x_offset_turn = 10
    l_distance = 165
    points = []

    x_offset = 0.0
    for i, path in enumerate(images):
        print("II: %03d/%03d processing %s" % (i, len(images), path))
        img = cv2.imread(path)
        h, w, c = img.shape

        img = cv2.resize(img, (w // 4, h // 4), interpolation=cv2.INTER_LINEAR_EXACT)
        h, w, c = img.shape

        xR = (300, 500)
        yR = (550, 800)

        xy = points_max_cols(img, xR=xR, yR=yR)

        xyz = [points_triangulate((x - (w / 2), y), x_offset, l_distance) for x, y in xy]

        xyz = [[x, y, z, 0.25, 0.25, 0.9] for x, y, z in xyz]

        points.extend(xyz)

        x_offset -= x_offset_turn

    return points


def parse_images(images_right):

    points_right = points_process_images(images_right)

    return points_right


def main():

    right = []
    scan_folder = "20220406145334"
    path = getcwd() + "\\scan\\" + scan_folder
    filename = f'{path}\\{scan_folder}.xyzrgb'

    # print "Scanning %s for files" % path

    right = glob.glob("%s/right*" % path.rstrip('/'))
    right.sort()

    steps = len(right)

    print("I: processing %d steps" % steps)

    right = parse_images(right)

    print("I: Writing pointcloud to %s" % filename)

    # TODO write XYZ file
    output_asc_pointset(filename, right)


def tmp_pic():
    scan_folder = "20220406145334"
    pic = f"right_{scan_folder}_0013.jpg"
    path = getcwd() + "\\scan\\" + scan_folder + '\\' + pic

    img = cv2.imread(path)
    h, w, c = img.shape
    img = cv2.resize(img, (w//4, h//4), interpolation=cv2.INTER_LINEAR_EXACT)

    h, w, c = img.shape

    xR = (300, 500)
    yR = (550, 800)

    xy = points_max_cols(img, xR=xR, yR=yR)
    print(xy)


    new = np.zeros((h, w, 3), np.uint8)

    mid = int(w/2)

    #400x765

    for r in xy:
        new[r[1], r[0], 2] = 255
    #for b in range(0, 325):
    #    new[b, mid, 0] = 255
    for a in range(0, w, 50):
        for b in range(0, h, 5):
            new[b, a, 0] = 255
    for a in range(0, h, 50):
        for b in range(0, w, 5):
            new[a, b, 0] = 255
    #new = cv2.resize(new, (w//4, h//4), interpolation=cv2.INTER_LINEAR_EXACT)
    cv2.imshow("new", new)
    cv2.waitKey()


if __name__ == "__main__":
    main()
    #tmp_pic()
