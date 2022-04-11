
import glob
from os import getcwd
import math
import cv2
import numpy as np
from model.pointset import *


count = 0


def points_triangulate(points, y_offset):

    cam_degree = 30
    x, y = points
    cam_angle = math.radians(cam_degree)
    calc_x = x / math.tan(cam_angle)
    calc_y = x - y_offset

    return [
        calc_x,
        calc_y,
        y_roi[1]-y * 1.00,
        0.0, 0.0, 0.0
    ]


def points_triangulate_ls(points, y_offset):

    cam_degree = 30
    x, y = points
    cam_angle = math.radians(cam_degree)
    calc_x = x / math.sin(cam_angle)
    calc_y = calc_x * math.tan(cam_angle)
    x_offset = y_offset * math.tan(-60)

    return [
        calc_x,
        -y_offset,
        800-y * 1.00,
        0.0, 0.0, 0.0
    ]


def points_triangulate_new(points, y_offset, z_zero):
    cam_degree = 30
    px, py = points
    cam_angle = math.radians(cam_degree)

    x = px / math.tan(cam_angle) * 1.0
    y = (px - y_offset) * 1.0

    return [
        x,
        y,
        z_zero - py
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


def points_max_cols(img, threshold=(200, 255)):
    """
    Read maximum pixel value in one color channel for each row
    """

    tmin, tmax = threshold
    h, w, c = img.shape
    xy = list()

    for i in range(y_roi[0], y_roi[1], 3):
        mx = 0
        mv = [0, 0, 0]
        for x in range(x_roi[0], x_roi[1], 3):
            try:
                if img[i, x, 2] > mv[2]:
                    mv = img[i, x]
                    mx = x
                """
                avg = sum(img[i, x])/3
                if avg > mv:
                    mv = avg
                    mx = x
                """
            except IndexError as e:
                print(f'x[{x}] y[{i}]')

        #valid = i < m*mx + b
        valid = True
        if mv[2] > tmin and mv[0] > 50 and valid:
            xy.append((mx, i))

    return xy


def get_normal(xyz, i, i_off):
    #print(f'i[{str(i)}] i_off[{str(i_off)}]')
    z0 = xyz[i][2]
    z1 = xyz[i + i_off][2]
    x0 = xyz[i][0]
    x1 = xyz[i + i_off][0]

    if x1 - x0 == 0:
        nx = 0.0
        if z1 - z0 >= 0:
            nz = 0.2
        else:
            nz = -0.2
    else:
        if z1 - z0 == 0:
            nz = 0.0
            nx = 0.2
        else:
            m = (z1 - z0) / (x1 - x0)
            x = math.sqrt(0.04 / (1 + 1 / math.pow(m, 2))) + x0
            nz = -1 / m * (x - x0)
            nx = x - x0

    #if i_off < 0:
    #    nz = 0 - nz
    #    nx = 0 - nx

    return nx, nz


def get_normal_b(xyz, i, i_off, r):
    z0 = xyz[i][2]
    z1 = xyz[i + i_off][2]
    xT = 0
    for a in range(i-r, i+r+1):
        xT += xyz[a][0]
    x0 = xT/5
    xT = 0
    for a in range(i+i_off-r, i+i_off+r+1):
        xT += xyz[a][0]
    x1 = xT/5
    # print(x0, x1)
    if x1 - x0 == 0:
        nx = 0.0
        if z1 - z0 >= 0:
            nz = 0.2
        else:
            nz = -0.2
    else:
        if z1 - z0 == 0:
            nz = 0.0
            nx = 0.2
        else:
            m = (z1 - z0) / (x1 - x0)
            x = math.sqrt(0.04 / (1 + 1 / math.pow(m, 2))) + x0
            nz = -1 / m * (x - x0)
            nx = x - x0

    return nx, nz


def calc_normals(xyz):
    global count
    length = len(xyz)

    i_off = 5
    r = 4
    for i in range(r+1, length-i_off-r, 1):
        nx, nz = get_normal_b(xyz, i, i_off, r)

        xyz[i][3] = nx
        xyz[i][4] = 0.0
        xyz[i][5] = nz
    return xyz


def calc_normals_b(xyz):
    global count
    length = len(xyz)

    i_index = 1
    i_off = 2
    i_avg = 5
    a_range = i_avg*i_off
    for i in range(a_range, length-i_index, i_index):
        nx = 0.0
        nz = 0.0
        for a in range(i-a_range+1, i+1, i_off):
            x, z = get_normal(xyz, i-i_off, i_off)
            nx += x
            nz += z

        xyz[i][3] = nx/(i_avg*1.0)
        xyz[i][4] = 0.0
        xyz[i][5] = nz/(i_avg*1.0)
    return xyz


def get_roi(path):
    xroi = [0, 0]
    yroi = [0, 0]
    img = cv2.imread(path)
    h, w, c = img.shape
    shrink = 6
    h_tmp = int(h / shrink)
    w_tmp = int(w / shrink)
    roi = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_LINEAR_EXACT)
    r = cv2.selectROI("ROI", roi)
    xroi[0] = int(r[0]) * shrink
    xroi[1] = int(r[0] + r[2]) * shrink
    yroi[0] = int(r[1]) * shrink
    yroi[1] = int(r[1] + r[3]) * shrink
    print('ROI')
    print(xroi, yroi)
    cv2.destroyWindow("ROI")
    return [int(xroi[0] / ratio), int(xroi[1] / ratio)], [int(yroi[0] / ratio), int(yroi[1] / ratio)]


def points_process_images(images, threshold_min=200, threshold_max=255):
    """
    extract 3d pixels and colors from either left or right set of images
    """
    global x_roi, y_roi
    turns = 1
    per_turn = 2
    x_offset_pic = turns * per_turn
    points = []
    x_roi, y_roi = get_roi(images[0])
    x_offset_pic = x_offset_pic * scaler / ratio
    x_offset = 0.0
    #images = images[40:41]
    for i, path in enumerate(images):
        print("II: %03d/%03d processing %s" % (i, len(images), path))
        img = cv2.imread(path)
        h, w, c = img.shape
        h_tmp = int(h/ratio)
        w_tmp = int(w/ratio)
        img = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_LINEAR_EXACT)
        h, w, c = img.shape

        xy = points_max_cols(img)
        xyz = [points_triangulate((x - (w / 2), y), x_offset) for x, y in xy]
        xyz = calc_normals(xyz)
        xyz = [[x, y, z, xn, yn, zn] for x, y, z, xn, yn, zn in xyz if x >= 0]
        points.extend(xyz)

        x_offset -= x_offset_pic

    return points


def remove_noise(points):
    tmp = 1


def parse_images(images_right):

    points_right = points_process_images(images_right)

    return points_right


def main():

    right = []
    scan_folder = "20220410105543"
    path = getcwd() + "\\scans\\" + scan_folder
    filename = f'{path}\\{scan_folder}.xyz'

    # print "Scanning %s for files" % path

    right = glob.glob("%s/right*" % path.rstrip('/'))
    right.sort()

    steps = len(right)

    print("I: processing %d steps" % steps)

    right = parse_images(right)

    #right = remove_noise(right)
    #xyz = calc_normals(xyz)

    print("I: Writing pointcloud to %s" % filename)

    # TODO write XYZ file
    output_asc_pointset(filename, right, 'xyzn')


def tmp_pic():
    scan_folder = "20220407103614"
    path = getcwd() + "\\scans\\" + scan_folder + '\\'
    pic = f"{path}right_{scan_folder}_0098.jpg"

    img = cv2.imread(pic)
    h, w, c = img.shape
    img = cv2.resize(img, (w//4, h//4), interpolation=cv2.INTER_LINEAR_EXACT)

    h, w, c = img.shape

    #img[:, :, 0] = np.zeros([img.shape[0], img.shape[1]])

    xy = points_max_cols(img, threshold=(200, 255))

    new = np.zeros((h, w, 3), np.uint8)
    img[:, :, 2] = np.zeros([img.shape[0], img.shape[1]])

    for r in xy:
        new[r[1], r[0], 2] = 255
        img[r[1], r[0], 2] = 255
    #for b in range(0, 325):
    #    new[b, mid, 0] = 255
    for a in range(0, w, 50):
        r = 5
        if a % 100 == 0:
            r = 2
        for b in range(0, h, r):
            new[b, a, 0] = 255
            img[b, a, 0] = 255
    for a in range(0, h, 50):
        r = 5
        if a % 100 == 0:
            r = 2
        for b in range(0, w, r):
            new[a, b, 0] = 255
            img[a, b, 0] = 255
    #new = cv2.resize(new, (w//4, h//4), interpolation=cv2.INTER_LINEAR_EXACT)
    cv2.imshow("new", img)
    cv2.waitKey()
    cv2.imshow("new", new)
    cv2.waitKey()
    #cv2.imwrite(path+"small.jpg", img)


def process_calibration_pics():
    scan_folder = "20220407103614"
    path = getcwd() + "\\scans\\" + scan_folder + '\\'
    pic = f"{path}calib_one.jpg"

    img = cv2.imread(pic)
    x_r, y_r = get_roi(pic)
    diff = []
    avg = []
    rows = []
    vals = []
    found = False
    for y in range(y_r[0], y_r[1]):
        for x in range(x_r[0], y_r[1]):
            if sum(img[y, x]) < 400:
                vals.append(x)
                found = True
                # print(x)
            else:
                if found:
                    rows.append(vals)
                    found = False
                    vals = []
        for v in rows:
            a = float(sum(v)) / len(v)
            #print(f'a[{str(a)}]')
            avg.append(a)
        rows = []
        for i in range(1, len(avg)):
            d = avg[i] - avg[i - 1]
            #print(f'd[{str(d)}]')
            diff.append(d)
        avg = []

    av = float(sum(diff)) / len(diff)
    print('%0.2f' % av)


if __name__ == "__main__":
    x_roi = [0, 0]
    y_roi = [0, 0]
    scaler = 10.1 #(px/mm)
    ratio = 1
    main()
    #process_calibration_pics()
    #tmp_pic()
