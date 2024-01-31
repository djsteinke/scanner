from os import getcwd

import visualize_point_cloud
from parser_roi import *
import numpy as np


def remove_noise(xy, w):
    f_xy = list()
    r = float(w) * 0.02
    for v in range(2, len(xy) - 2):
        x0, _ = xy[v - 2]
        x1, _ = xy[v - 1]
        x2, _ = xy[v]
        x3, _ = xy[v + 1]
        x4, _ = xy[v + 2]
        if abs(float(x0 + x1 + x3 + x4) / 4.0 - x2) < r:
            f_xy.append(xy[v])
    return f_xy


def points_min_cols(img, threshold=(0, 60), c=False, roi=None, step=None):
    """
    Read maximum pixel value in one color channel for each row
    """
    if roi is None:
        x_roi, y_roi = get_roi_by_img(img, 1)
    else:
        x_roi = roi[0]
        y_roi = roi[1]

    t_min, t_max = threshold
    xy = list()

    y_step = 5
    if step is not None:
        y_step = int(step[0] * float(step[1]) / (step[2]*1.0))  # scalar, dps, ratio

    for i in range(y_roi[0], y_roi[1], y_step):
        mx = 0
        mv = 0
        for x in range(x_roi[0], x_roi[1], 1):
            if c:
                avg = sum(img[i, x])
                if mv < avg and avg >= t_min and img[i, x, 2] < t_max:
                    mv = avg
                    mx = x
            else:
                v = red_val(img[i, x], 150)
                if v > mv:
                    mv = v
                    mx = x

        if mv > 0:
            xy.append((mx, i))
    return xy


def points_max_cols_a(img, roi):
    Rh, Rw, _ = img.shape
    x_roi, y_roi = roi
    points = []
    for y in range(y_roi[0], y_roi[1], 3):
        found = False
        max_r = -1
        max_rx = -1
        r_min = 200
        while r_min >= r_min:
            for x in range(x_roi[1]-1, x_roi[0]-1, -1):
                if 137 > x > 476 and 150 > y > 263:
                    b, g, r = img[y][x]
                    if r > r_min and b < r * 0.8 and g < r * 0.7:
                        if r > max_r:
                            max_r = r
                            max_rx = x
                        found = True
                    else:
                        if found:
                            break
            if max_rx < 0:
                r_min -= 5
            else:
                break
        if max_rx > 0:
            # print(max_rx, y)
            points.append([max_rx, y])

    """
    points_noise = []
    points_ignore = []
    for i in range(3, len(points) - 3):
        x_tot_b = 0
        x_tot_a = 0
        cnt_b = 0
        cnt_a = 0
        for b in range(1, 4):
            if i - b not in points_ignore:
                x_tot_b += points[i - b][0]
                cnt_b += 1
            x_tot_a += points[i + b][0]
            cnt_a += 1
        if abs(x_tot_b / cnt_b - points[i][0]) < 30 or abs(x_tot_a / cnt_a - points[i][0]) < 30:
            points_noise.append(points[i])
        else:
            points_ignore.append(i)
    """
    return points


def points_max_cols(img, threshold=(60, 255), c=False, roi=None, right=True):

    lower = np.array([30, 20, 60])
    upper = np.array([175, 125, 255])
    if c:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        t_min, t_max = threshold
        ret, bin_img = cv2.threshold(gray, t_min, t_max, cv2.THRESH_BINARY)
        # contour, hierarchy = cv2.findContours(bin_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        h, w = bin_img.shape
    else:
        bin_img = cv2.inRange(img, lower, upper)
        h, w, _ = img.shape

    if roi is None:
        x_roi, y_roi = get_roi_by_img(img, 1)
    else:
        x_roi = roi[0]
        y_roi = roi[1]

    s = 1
    if right:
        s = -1
        x_roi = [x_roi[1]-1, x_roi[0]-1]

    xy = list()

    avg = []
    for i in range(0, h):
        avg.append([0, 0])

    for y in range(y_roi[0], y_roi[1], 4):
        found = False
        for x in range(x_roi[0], x_roi[1], s):
            if bin_img[y][x] > 0:
                avg[y][0] += x
                avg[y][1] += 1
                found = True
            else:
                if found:
                    break

    for i in range(0, len(avg)):
        a = avg[i]
        if a[1] > 0:
            x_avg = int(round(a[0]/a[1], 0))
            xy.append((x_avg, i))

    return xy


def points_max_cols_old(img, threshold=(60, 255), c=False, roi=None, step=None):
    """
    Read maximum pixel value in one color channel for each row
    """

    if roi is None:
        x_roi, y_roi = get_roi_by_img(img, 1)
    else:
        x_roi = roi[0]
        y_roi = roi[1]

    t_min, t_max = threshold
    xy = list()

    y_step = 2
    if step is not None:
        y_step = int(step[0] * float(step[1]) / (step[2]*1.0))  # scalar, dps, ratio

    for i in range(y_roi[0], y_roi[1], y_step):
        mx = 0
        mv = 0
        min_x = (i - 1080.8)/0.84
        min_x = 0
        for x in range(x_roi[0], x_roi[1], 1):
            # if 1096 < i <= 1098 and 600 < x < 608:
            #     print(img[i, x])
            if x >= min_x:
                if c:
                    avg = sum(img[i, x])
                    if avg > mv and avg >= t_min and img[i, x, 2] < t_max:
                        mv = avg
                        mx = x
                else:
                    v = red_val(img[i, x], t_min)
                    if v > mv:
                        mv = v
                        mx = x

        if mv > 0:
            xy.append((mx, i))

    return xy


def red_val(in_val, t_min):
    r = int(in_val[2])
    g = int(in_val[1])
    b = int(in_val[0])
    v = 1.3

    if (r > t_min and r > g*v and r > b*v) or (b > 150 and (r + g) < 50):
        return r
        # return r - (g+b)/2.0/v
    else:
        return 0


def subtract_w_color(l_img, c_img):
    img = cv2.subtract(l_img, c_img)
    h, w, _ = img.shape
    r = float(h)/640.0
    w = int(float(w) / r)
    h = int(float(h) / r)
    img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    l_img = cv2.resize(l_img, (w, h), interpolation=cv2.INTER_AREA)
    c_img = cv2.resize(c_img, (w, h), interpolation=cv2.INTER_AREA)
    cv2.imshow("subtract", img)
    cv2.imshow("l_img", l_img)
    cv2.imshow("c_img", c_img)
    cv2.waitKey()

#p = getcwd() + "\\scans\\20221202084104"
#l_img = cv2.imread(p + "\\right_0064.jpg")
#c_img = cv2.imread(p + "\\color_0064.jpg")
#subtract_w_color(l_img, c_img)
