import math
from os import getcwd

import cv2

from parser import points_triangulate
from parser_roi import get_roi_by_path
from parser_util import points_max_cols

threshold = 8
scan_dir = '20221220085549'
scan_path = getcwd() + "\\scans\\" + scan_dir

# mentioning absolute path of the image

pic_num = 0
right = scan_path + "\\right_%04d.jpg" % pic_num
left = scan_path + "\\left_%04d.jpg" % pic_num
color = scan_path + "\\color_%04d.jpg" % pic_num

image_orig = cv2.imread(color)
image_r = cv2.imread(right, 0)
image_c = cv2.imread(color, 0)
image_l = cv2.imread(left, 0)

Rh, Rw = image_r.shape
print(Rh, Rw)
r = 3.0
w = int(float(Rw) / r)
h = int(float(Rh) / r)
print(h, w)

image_dr = cv2.subtract(image_r, image_c)
image_dl = cv2.subtract(image_l, image_c)

image_r = cv2.resize(image_r, (w, h), interpolation=cv2.INTER_AREA)
image_c = cv2.resize(image_c, (w, h), interpolation=cv2.INTER_AREA)
image_l = cv2.resize(image_r, (w, h), interpolation=cv2.INTER_AREA)
image_orig = cv2.resize(image_orig, (w, h), interpolation=cv2.INTER_AREA)
image_dr = cv2.resize(image_dr, (w, h), interpolation=cv2.INTER_AREA)
image_dl = cv2.resize(image_dl, (w, h), interpolation=cv2.INTER_AREA)

ret_r, img_r = cv2.threshold(image_dr, threshold, 255, cv2.THRESH_BINARY)
ret_l, img_l = cv2.threshold(image_dl, threshold, 255, cv2.THRESH_BINARY)

#cv2.imshow('right', img_r)
#cv2.waitKey()

roi_x, roi_y = get_roi_by_path(right, r)

xy_r = points_max_cols(image_dr, roi=[roi_x, roi_y], threshold=(threshold, 255))

r_angle = 26.0
cz = 302.88
cx = 533.0/r
cy = 962.0/r
cf = 1548.95/r
r_end = int((34.2 - r_angle)/0.1)

best_angle = [0, 100]
for i in range(0, r_end, 1):
    tmp_angle = r_angle + i*0.1
    xyz = []
    for px, py in xy_r:
        calc_x = 0.0
        if float(px) != cx:
            calc_x = cz / (cf / (float(px) - cx) + 1.0 / math.tan(math.radians(tmp_angle)))
        calc_z = -calc_x / math.tan(math.radians(tmp_angle))
        calc_y = (cz+calc_z)*(cy-float(py))/cf
        xyz.append(calc_y)
    s = 0
    for y in xyz:
        s += y
    m = float(s)/float(len(xyz))
    ms = 0
    for y in xyz:
        ms += math.pow((y-m), 2)
    v = float(ms)/float(len(xyz))
    diff = math.sqrt(v)
    """
    mm = [0.0, 0.0]
    for y in xyz:
        if mm[0] == 0.0 or y < mm[0]:
            mm[0] = y
        if mm[1] == 0.0 or y > mm[1]:
            mm[1] = y
    """
    #diff = abs(round(xyz[0] - xyz[len(xyz)-1], 1))
    #diff = mm[1] - mm[0]
    if diff < best_angle[1]:
        best_angle = [tmp_angle, diff]
print("right: ", best_angle)


best_angle = [0, 100]
xy_r = points_max_cols(image_dl, roi=[roi_x, roi_y], threshold=(threshold, 255))
for i in range(0, r_end, 1):
    tmp_angle = r_angle + i*0.1
    xyz = []
    for px, py in xy_r:
        calc_x = 0.0
        if float(px) != cx:
            calc_x = cz / (cf / (float(px) - cx) - 1.0 / math.tan(math.radians(tmp_angle)))
        calc_z = calc_x / math.tan(math.radians(tmp_angle))
        calc_y = (cz+calc_z)*(cy-float(py))/cf
        xyz.append(calc_y)
    """
    mm = [0.0, 0.0]
    for y in xyz:
        if mm[0] == 0.0 or y < mm[0]:
            mm[0] = y
        if mm[1] == 0.0 or y > mm[1]:
            mm[1] = y
    """
    s = 0
    for y in xyz:
        s += y
    m = float(s)/float(len(xyz))
    ms = 0
    for y in xyz:
        ms += math.pow((y-m), 2)
    v = float(ms)/float(len(xyz))
    diff = math.sqrt(v)
    #diff = abs(round(xyz[0] - xyz[len(xyz)-1], 1))
    # diff = mm[1] - mm[0]
    if diff < best_angle[1]:
        best_angle = [tmp_angle, diff]
print("left: ", best_angle)


"""
[74.12, 74.19, 1548.95, 537.63, 960.74, 302.88]
                calc_x = cz / (cf / (cx - float(px)) + 1.0 / math.tan(math.radians(cam_degree)))
"""