import math
import cv2
import numpy as np
from scipy import interpolate


def points_triangulate_old(points, y_offset, l_dist):

    cam_degree = 30
    x, y = points
    cam_angle = math.radians(cam_degree)
    r = x / math.tan(cam_angle)

    return [
        r,
        y_offset,
        y * 1.00
    ]


def points_triangulate(points, y_offset, l_dist):
    cam_degree = 30
    x, y = points
    cam_angle = math.radians(cam_degree)

    radius = x / math.sin(cam_angle)

    return [
        radius * math.cos(cam_angle),
        radius * math.sin(cam_angle) + y_offset,
        y * 1.00
    ]


def points_max_cols(img, threshold=(200, 255)):
    """
    Read maximum pixel value in one color channel for each row
    """

    tmin, tmax = threshold
    h, w, c = img.shape
    xy = list()

    hStart = int(h/2)

    for i in range(hStart, h):
        mx = 0
        mv = 0
        for x in range(0, w):
            if img[i, x, 2] > mv:
                mv = img[i, x, 2]
                mx = x

        if mv > tmin:
            xy.append((mx, i))

    return xy


def points_process_images(images, threshold_min=200, threshold_max=255):
    """
    extract 3d pixels and colors from either left or right set of images
    """
    turns = 1.8
    x_offset_turn = 1.0/18.0*turns*25.4
    l_distance = 165
    points = []

    x_offset = 0.0
    for i, path in enumerate(images):
        print("II: %03d/%03d processing %s" % (i, len(images), path))
        img = cv2.imread(path)
        h, w, c = img.shape
        img = cv2.resize(img, (w // 4, h // 4), interpolation=cv2.INTER_LINEAR_EXACT)

        xy = points_max_cols(img, threshold=(threshold_min, threshold_max))

        xyz = [points_triangulate((x - (w / 2), y), x_offset, l_distance) for x, y in xy]

        xyz = [[x, y, z, 1.0, 1.0, 1.0] for x, y, z in xyz]

        points.extend(xyz)

        x_offset += x_offset_turn
        if i > 2:
            return points

    return points


def parse_images(images_right):

    points_right = points_process_images(images_right)

    return points_right
