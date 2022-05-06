import visualize_point_cloud
from parser_roi import *


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


def points_max_cols(img, threshold=(60, 255), c=False, roi=None, step=None):
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
                if avg > mv and avg >= t_min and img[i, x, 2] < t_max:
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


def red_val(in_val, t_min):
    r = int(in_val[2])
    g = int(in_val[1])
    b = int(in_val[0])
    v = 1.3

    if r > t_min and r > g*v and r > b*v:
        return r - (g+b)/2.0/v
    else:
        return 0
