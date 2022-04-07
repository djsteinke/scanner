
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
        calc_x,
        -y_offset,
        800-y * 1.00,
        1,
        0,
        0,
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


def points_max_cols(img, threshold=(220, 255), xR=None, yR=None):
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

    forward = False

    density = 3

    p1 = (530, 852)
    p2 = (386, 762)
    p1 = (p1[0]*4/ratio, p1[1]*4/ratio)
    p2 = (p2[0]*4/ratio, p2[1]*4/ratio)
    m = (p2[1] - p1[1])/(p2[0] - p1[0])
    b = p1[1] - m*p1[0]

    for i in range(yR[0], yR[1], 3):
        mx = 0
        mv = [0, 0, 0]
        for x in range(xR[0], xR[1], 3):
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

        valid = i < m*mx + b
        #valid = True
        if mv[2] > tmin and mv[0] > 140 and valid:
            xy.append((mx, i))

    return xy

count = 0
def calc_normals(xyz):
    global count
    length = len(xyz)

    for i in range(0, length-1):
        z0 = xyz[i][2]
        z1 = xyz[i+1][2]
        x0 = xyz[i][0]
        x1 = xyz[i+1][0]

        if x1-x0 == 0:
            m = 1
        else:
            m = (z1-z0)/(x1-x0)

        if count < 100:
            print(m)
        count += 1
        x = math.sqrt(1/(1+1/math.pow(m, 2))) + x0
        z = -1/m*(x-x0) + z0
        xyz[i][3] = x - x0
        xyz[i][4] = 0
        xyz[i][5] = z - z0
    return xyz


def points_process_images(images, threshold_min=200, threshold_max=255):
    """
    extract 3d pixels and colors from either left or right set of images
    """
    turns = 1.8
    per_turn = 1.0/18.0*25.4
    x_offset_pic = turns * per_turn
    #x_offset_turn = 10
    l_distance = 165
    points = []
    ratio = 2
    xR = (350, 575)
    yR = (450, 850)
    xR = (1400, 2300)
    yR = (1800, 3400)

    xR = (int(xR[0]/ratio), int(xR[1]/ratio))
    yR = (int(yR[0]/ratio), int(yR[1]/ratio))
    x_offset_pic = x_offset_pic * scaler / ratio
    x_offset = 0.0
    for i, path in enumerate(images):
        print("II: %03d/%03d processing %s" % (i, len(images), path))
        img = cv2.imread(path)
        h, w, c = img.shape
        h_tmp = int(h/ratio)
        w_tmp = int(w/ratio)
        img = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_LINEAR_EXACT)
        h, w, c = img.shape

        xy = points_max_cols(img, xR=xR, yR=yR)
        xyz = [points_triangulate((x - (w / 2), y), x_offset, l_distance) for x, y in xy]
        #xyz = calc_normals(xyz)
        xyz = [[x, y, z, 0.2, 0, 0.05] for x, y, z, xn, xy, xz in xyz if x >= 0]
        points.extend(xyz)
        #xyz = [[0, y, z, -1, xy, xz] for x, y, z, xn, xy, xz in xyz if x >= 0]
        #points.extend(xyz)

        x_offset -= x_offset_pic

    return points


def remove_noise(points):
    tmp = 1


def parse_images(images_right):

    points_right = points_process_images(images_right)

    return points_right


def main():

    right = []
    scan_folder = "20220407103614"
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

    xR = None
    yR = None
    xR = (350, 575)
    yR = (450, 850)

    print(sum(img[700, 300]))

    #img[:, :, 0] = np.zeros([img.shape[0], img.shape[1]])

    xy = points_max_cols(img, xR=xR, yR=yR, threshold=(200, 255))

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
    h, w, c = img.shape
    yR = (1800, h)
    calib = np.zeros((500, 500, 3), np.uint8)
    for a in range(2000, 2500):
        y = a-2000
        for b in range(2000, 2500):
            x = b-2000
            calib[y, x] = img[a, b]

    found = False
    h, w, c = calib.shape
    rows = []
    vals = []
    for x in range(0, w):
        if sum(calib[100, x]) < 400:
            vals.append(x)
            found = True
            print(x)
        else:
            if found:
                rows.append(vals)
                found = False
                vals = []
    print(rows)
    avg = []
    for v in rows:
        a = float(sum(v))/len(v)
        avg.append(a)

    for i in range(1, len(avg)):
        dif = avg[i] - avg[i-1]
        print(dif)

    cv2.imshow('orig', calib)
    cv2.waitKey()


if __name__ == "__main__":
    scaler = 10.1 #(px/mm)
    ratio = 2
    main()
    #process_calibration_pics()
    #tmp_pic()
