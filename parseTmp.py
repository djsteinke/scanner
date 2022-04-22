import subprocess
import glob
from os import getcwd
import math
import cv2
import numpy as np
from model.pointset import *
from json import load


count = 0


def points_triangulate(points, y_offset, color=None):

    cam_degree = 30
    px, py = points

    pz = y_roi[1]-py
    calc_z = pz/scaler
    px /= scaler
    py /= scaler
    cam_angle = math.radians(cam_degree)
    calc_x = px / math.tan(cam_angle)
    calc_y = px - y_offset

    bgr = [0, 0, 0]
    if color is not None:
        bgr = color[round(py), round(px)]

    return [
        calc_x,
        calc_y,
        calc_z,
        bgr[2], bgr[1], bgr[0],
        0.0, 0.0, 0.0
    ]


def points_triangulate_ls(points, y_offset, color=None):

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


def points_triangulate_cir(points, a, color=None):
    cam_degree = 30
    px, py = points
    cam_angle = math.radians(cam_degree)
    angle = math.radians(a)
    #angle = (a/360.0)*(2.0*math.pi)

    radius = px / math.sin(cam_angle)

    bgr = [0, 0, 0]
    if color is not None:
        bgr = color[round(py), round(px)]

    return [
        radius * math.cos(angle),
        radius * math.sin(angle),
        y_roi[1] - py * 1.00,
        (bgr[2]*1.0)/255.0, (bgr[1]*1.0)/255.0, (bgr[0]*1.0)/255.0,
        0.0, 0.0, 0.0
    ]


def red_val(in_val, t_min):
    r = int(in_val[2])
    g = int(in_val[1])
    b = int(in_val[0])
    v = 1.2
    """
    if r > t_min and r > g*v and r > b*v:
        return r - (g+b)
    else:
        return 0
    """
    if r >= t_min:
        ret = r - (g+b)
        if ret > 0:
            return ret
        else:
            return 0
    else:
        return 0


def points_max_cols(img, threshold=(220, 255)):
    """
    Read maximum pixel value in one color channel for each row
    """

    t_min, _ = threshold
    xy = list()

    for i in range(y_roi[0], y_roi[1], int(scaler)):
        mx = 0
        mv = 0
        for x in range(x_roi[0], x_roi[1], 1):
            v = red_val(img[i, x], 60)
            if v > mv:
                mv = v
                mx = x

        # valid = i < m*mx + b
        # valid = True
        if mv > 0:
            xy.append((mx, i))
        # if mv[2] > tmin and valid:
        #     xy.append((mx, i))

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


def get_normal_b(xyz, i, i_off, r, a=0):
    angle = math.radians(a)
    c = math.cos(angle)
    if c == 0:
        c = 1
    s = math.sin(angle)

    """
        radius * math.cos(angle),
        radius * math.sin(angle),
        y_roi[1] - py * 1.00,
    """

    z0 = xyz[i][2]
    z1 = xyz[i + i_off][2]
    xT = 0
    for a in range(i-r, i+r+1):
        xT += xyz[a][0]
    x0 = xT/5/c
    xT = 0
    for a in range(i+i_off-r, i+i_off+r+1):
        xT += xyz[a][0]
    x1 = xT/5/c

    if x1 - x0 == 0:
        nx = 0.0
        if z1 - z0 >= 0:
            nz = 0.2
        else:
            nz = -0.2
    else:
        if z1 - z0 == 0:
            nz = 0.0
            if x1 - x0 >= 0:
                nx = 0.2
            else:
                nx = -0.2
        else:
            m = (z1 - z0) / (x1 - x0)
            x = math.sqrt(0.04 / (1 + 1 / math.pow(m, 2))) + x0
            nz = -1 / m * (x - x0)
            nx = x - x0

    nx = nx * c
    ny = nx * s
    return nx, ny, nz


def calc_normals(xyz, a):
    global count
    length = len(xyz)

    i_off = 5
    r = 4
    for i in range(r+1, length-i_off-r, 1):
        nx, ny, nz = get_normal_b(xyz, i, i_off, r, a)

        xyz[i][6] = nx
        xyz[i][7] = ny
        xyz[i][8] = nz
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


def points_process_images(images, color=None):
    global x_roi, y_roi
    turns = 1
    per_turn = 2
    x_offset_pic = turns * per_turn
    points = []
    x_roi, y_roi = get_roi(images[0])
    x_offset_pic = x_offset_pic * scaler / ratio
    x_offset = 0.0
    # images = images[40:41]
    s = details['steps']
    for i, path in enumerate(images):
        pic_num = path.split('right_')
        pic_num = int(pic_num[1].split('.')[0])
        print("II: %03d/%03d processing %s" % (pic_num+1, s, path))
        img = cv2.imread(path)
        tmin = 200
        c = None
        if color is not None:
            c = cv2.imread(color[i])
            img = cv2.subtract(img, c)
            tmin = 75
        h, w, _ = img.shape
        if ratio > 1:
            h_tmp = int(h/ratio)
            w_tmp = int(w/ratio)
            img = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
            h, w, _ = img.shape

        xy = points_max_cols(img, threshold=(tmin, 255))
        # xy = points_max_cols(img)
        xy = remove_noise(xy, w)

        if details['type'] == "circular":
            xyz = [points_triangulate_cir((x - (w / 2), y), x_offset, color=c) for x, y in xy]
            xyz = calc_normals(xyz, x_offset)
            x_offset -= - pic_num * float(details['dps'])
        else:
            xyz = [points_triangulate((x - (w / 2), y), x_offset, color=c) for x, y in xy]
            # x_offset -= x_offset_pic
            x_offset = - pic_num * float(details['dps'])
        # xyz = [[x, y, z, xn, yn, zn] for x, y, z, xn, yn, zn in xyz if x >= 0]
        xyz = [[x, y, z, r, g, b, xn, yn, zn] for x, y, z, r, g, b, xn, yn, zn in xyz]
        points.extend(xyz)

    return points


def remove_noise(xy, w):
    f_xy = list()
    r = float(w) * 0.03
    for v in range(2, len(xy) - 2):
        x0, _ = xy[v - 2]
        x1, _ = xy[v - 1]
        x2, _ = xy[v]
        x3, _ = xy[v + 1]
        x4, _ = xy[v + 2]
        if abs(float(x0 + x1 + x3 + x4) / 4.0 - x2) < r:
            f_xy.append(xy[v])
    return f_xy


def parse_images(images, color=None):

    points = points_process_images(images, color=color)

    return points


def main():
    global details
    color = []
    scan_folder = "20220422123148"
    path = getcwd() + "\\scans\\" + scan_folder
    filename = f'{path}\\{scan_folder}.xyz'

    details_path = f'{getcwd()}\\scans\\details.json'
    f = open(details_path, 'r')
    details = load(f)
    print(details)

    # print "Scanning %s for files" % path

    right = glob.glob("%s/right*" % path.rstrip('/'))
    right.sort()

    if details['color']:
        color = glob.glob("%s/color*" % path.rstrip('/'))
        color.sort()

    print(f'RIGHT[{len(right)}] COLOR[{len(color)}]')
    if len(color) == 0:
        color = None
    steps = details['steps']

    print("I: processing %d steps" % steps)

    right = parse_images(right, color=color)

    #right = remove_noise(right)
    #xyz = calc_normals(xyz)

    print("I: Writing pointcloud to %s" % filename)

    output_asc_pointset(filename, right, 'xyzcn')

    #subprocess.run(['python', '-f', f'{scan_folder}.xyz', '-p', path], shell=True)


def tmp_pic():
    global x_roi, y_roi
    scan_folder = "20220406081736"
    path = getcwd() + "\\scans\\" + scan_folder + '\\'
    pic = f"{path}color_0041.jpg"
    color = f"{path}right_0042.jpg"

    img = cv2.imread(pic)
    col = cv2.imread(color)
    img = cv2.subtract(img, col)
    h, w, c = img.shape

    img = cv2.resize(img, (w//6, h//6), interpolation=cv2.INTER_AREA)
    h, w, c = img.shape

    cv2.imshow("minus", img)

    x_roi = (250, 450)
    y_roi = (0, h)

    f_xy = list()
    xy = points_max_cols(img, threshold=(100, 255))

    new = np.zeros((h, w, 3), np.uint8)
    new_f = np.zeros((h, w, 3), np.uint8)
    #img[:, :, 2] = np.zeros([img.shape[0], img.shape[1]])

    print(w)

    r = float(w) * 0.01

    for i in range(2, len(xy)-2):
        x0, _ = xy[i-2]
        x1, _ = xy[i-1]
        x2, _ = xy[i]
        x3, _ = xy[i+1]
        x4, _ = xy[i+2]
        if abs(float(x0 + x1 + x3 + x4)/4.0 - x2) < r:
            f_xy.append(xy[i])

    for r in f_xy:
        new_f[r[1], r[0], 2] = 255
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
            new_f[b, a, 0] = 255
    for a in range(0, h, 50):
        r = 5
        if a % 100 == 0:
            r = 2
        for b in range(0, w, r):
            new[a, b, 0] = 255
            new_f[a, b, 0] = 255
    cv2.imshow("img", new_f)
    cv2.imshow("new", new)
    cv2.waitKey()


def get_p2p_dist(p):
    # print(p[0], p[1])
    # print(f'x[%0.2f] y[%0.2f]' % (p[0, 0, 0], p[0, 0, 1]))
    avg_x = []
    avg_y = []
    for y in range(0, ny):
        for x in range(0, nx):
            x0 = p[y*x+x, 0, 0]
            y0 = p[y*x+x, 0, 1]
            x1 = p[y*x+x+1, 0, 0]
            y1 = p[y*x+x+1, 0, 1]
            d = math.sqrt(math.pow((x1-x0), 2) + math.pow((y1-y0), 2))
            #print(x0, y0, x1, y1, d)
            avg_x.append(d)
    for x in range(0, nx):
        for y in range(0, ny):
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


nx = 6  # nx: number of grids in x axis
ny = 9  # ny: number of grids in y axis


def linear_calibration_process():
    scan_folder = "calibration"
    path = getcwd() + "\\" + scan_folder + '\\'
    pic = f"{path}linear_calibration_0000.jpg"

    img = cv2.imread(pic)


    objp = np.zeros((nx * ny, 3), np.float32)
    objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    objpoints = []  # 3d points in real world space
    imgpoints = []  # 2d points in image plane.

    dimensions = img.shape  # height, width, number of channels in image

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
    color_img = img
    if ret:
        #print("Corners found.")
        objpoints.append(objp)
        imgpoints.append(corners)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        # Draw and display the corners
        #print(corners2)
        get_p2p_dist(corners2)


def process_calibration_pics():
    scan_folder = "calibration"
    path = getcwd() + "\\" + scan_folder + '\\'
    pic = f"{path}linear_calibration_0000.jpg"

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
    details = {}
    x_roi = [0, 0]
    y_roi = [0, 0]
    #scaler = 10.1 #(px/mm)
    scaler = 346.26/20.0
    ratio = 1
    #main()
    linear_calibration_process()
    #process_calibration_pics()
    #tmp_pic()
