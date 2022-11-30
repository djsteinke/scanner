import optparse
import glob
import model.pointset as ps
import math
import numpy as np
import shutil
from os import getcwd, path, makedirs
from parser_calibration import Calibration
from parser_linear_calibration import LinearCalibration
from json import load
from parser_util import *


def get_normal(xyz, i, i_off, r, a=0):
    angle = math.radians(a)
    c = math.cos(angle)
    if c == 0:
        c = 1
    s = math.sin(angle)

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
    if details['type'] != 'circular':
        a = 0

    length = len(xyz)
    i_off = 5
    r = 4
    for i in range(r+1, length-i_off-r, 1):
        nx, ny, nz = get_normal(xyz, i, i_off, r, a)

        xyz[i][6] = nx
        xyz[i][7] = ny
        xyz[i][8] = nz
    return xyz


def calculate_normal_new(xyz, a):
    length = len(xyz)
    r = 5
    angle = math.radians(a)
    for i in range(0, length-r, 1):
        p1 = xyz[i]
        p2 = xyz[i+r]
        r1 = math.sqrt(math.pow(p1[0], 2) + math.pow(p1[2], 2))
        r2 = math.sqrt(math.pow(p2[0], 2) + math.pow(p2[2], 2))
        beta = 0.0
        if p1[1]-p2[1] > 0:
            beta = math.pi/2.0 - math.atan((r1-r2)/(p1[1]-p2[1]))
        r1 += math.cos(beta)
        y1 = p1[1]-p2[1] + math.sin(beta)

        x_neg = p1[0] < 0
        z_neg = p1[2] < 0
        calc_x = r1 * math.cos(angle)
        if x_neg:
            calc_x *= -1
        calc_z = r1 * math.sin(angle)
        if z_neg:
            calc_z *= -1

        xyz[i][6] = calc_x/100.0
        xyz[i][7] = y1/100.0
        xyz[i][8] = calc_z/100.0
    return xyz


def points_triangulate(points, offset, color=None, right=True):
    if right:
        cam_degree = 26
    else:
        cam_degree = 26
    px, py = points

    bgr = [255, 0, 0]
    if color is not None and right:
        bgr = color[round(py), round(px)]

    if details['type'] == 'circular':
        #calc_x, calc_y, calc_z = calibration.get_scaled_xyz(px, py, right, offset)
        calc_x = 0.0
        if float(px) != 632.0:
            calc_x = 374.0/(1701.0/(float(px)-632.0) + 1.0/math.tan(math.radians(cam_degree)))
        calc_z = -calc_x/math.tan(math.radians(cam_degree))
        calc_y = (374.0+calc_z)*(1048.0-float(py))/1701.0

        angle = math.radians(offset)
        radius = math.sqrt(math.pow(calc_z, 2) + math.pow(calc_x, 2))
        x_neg = calc_x < 0
        z_neg = calc_z < 0
        calc_x = radius * math.cos(angle)
        if x_neg:
            calc_x *= -1
        calc_z = radius * math.sin(angle)
        if z_neg:
            calc_z *= -1
        # print(round(calc_x, 2), round(calc_y, 2), round(calc_z, 2), px, py)
    else:
        """
        h, w, _ = color.shape
        cx = int(w/2)
        cy = int(h/2)
        cam_angle = math.radians(26.0)
        scalar = calibration.get_scalar_by_x(px)
        calc_x = ((px-cx) / math.tan(cam_angle)) / scalar
        calc_y = ((px-cx) / scalar) - offset
        calc_z = (cy-py) / scalar
        """
        calc_x, calc_y, calc_z = calibration.get_scaled_xyz(px, py, offset)
        # pz = roi_y[1]-py
        # calc_y = (px - offset) / calibration.scalar
        # calc_z = pz / calibration.scalar

        """
        if -150 > calc_x > 150 or -150 > calc_y > 150:
            calc_x = 0.0
            calc_y = 0.0
            calc_z = 0.0
        """
    return [
        calc_x,
        calc_y,
        calc_z,
        bgr[2], bgr[1], bgr[0],
        0.0, 0.0, 0.0
    ]


def points_process_images(images, color=None, right=True):
    points = []
    #images = images[1:]
    s = details['steps']
    for i, path in enumerate(images):
        if right:
            pic_num = path.split('right_')
        else:
            pic_num = path.split('left_')
        pic_num = int(pic_num[1].split('.')[0])
        side = "RIGHT" if right else "LEFT"
        print("%s: %03d/%03d" % (side, pic_num+1, s))
        img = cv2.imread(path)
        tmin = 200
        c = None
        if color is not None:
            c = cv2.imread(color[i])
            img = cv2.subtract(img, c)
            tmin = 30
        h, w, _ = img.shape
        if ratio > 1:
            h_tmp = int(h/ratio)
            w_tmp = int(w/ratio)
            img = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
            h, w, _ = img.shape

        step = None
        if calibration is not None:
            step = [calibration.scalar, float(details['dps']), ratio]
        xy = points_max_cols(img, threshold=(tmin, 255), c=True, roi=[roi_x, roi_y], step=step)
        xy = remove_noise(xy, w)

        offset = pic_num * float(details['dps'])
        xyz = [points_triangulate((x, y), offset, color=c, right=right) for x, y in xy]
        xyz = calculate_normal_new(xyz, offset)
        #xyz = calc_normals(xyz, offset)
        xyz = [[x, y, z, r, g, b, xn, yn, zn] for x, y, z, r, g, b, xn, yn, zn in xyz]
        points.extend(xyz)

        preview = False
        if preview:
            visualize_point_cloud.vis_points(points)

    return points


def single():
    global calibration, roi_x, roi_y
    print("single()")
    pic_num = 102
    right = image_path + "\\right_%04d.jpg" % pic_num
    color = image_path + "\\color_%04d.jpg" % pic_num
    r_pic = cv2.imread(right)
    c_pic = cv2.imread(color)
    d_pic = cv2.subtract(r_pic, c_pic)
    #d_pic = r_pic

    roi_x = [1134, 2460]
    roi_y = [666, 3408]
    roi_x, roi_y = get_roi_by_path(right, ratio)
    tmin = 40
    step = None
    if calibration is not None:
        step = [calibration.scalar, float(details['dps']), ratio]
    xy = points_max_cols(d_pic, threshold=(tmin, 255), c=True, roi=[roi_x, roi_y], step=step)
    print(xy)
    a_xy = ['%d %d' % (x, y) for x, y in xy]
    str_xy = str.join('\n', a_xy)
    # print(str_xy)

    offset = pic_num * float(details['dps'])
    xyz = [points_triangulate((x, y), offset, color=c_pic, right=True) for x, y in xy]
    a_xyz = ['%d %d' % (x, y) for x, y, z, a, b, c, d, e, f in xyz]
    str_xyz = str.join('\n', a_xyz)
    #print(str_xyz)

    points = []
    xyz = [[x, y, z, r, g, b, xn, yn, zn] for x, y, z, r, g, b, xn, yn, zn in xyz]
    points.extend(xyz)
    visualize_point_cloud.vis_points(points)

    h, w, _ = r_pic.shape
    r = h / 640.0
    h_tmp = int(h / r)
    w_tmp = int(w / r)
    new = np.zeros((h_tmp, w_tmp, 3), np.uint8)
    print('xy length', len(xy))
    r_pic = cv2.resize(r_pic, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
    d_pic = cv2.resize(d_pic, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
    for x, y in xy:
        x = int(x/r)
        y = int(y/r)
        new[y, x, 2] = 255
        d_pic[y, x, 0] = 255
        r_pic[y, x, 1] = 255
    #new = cv2.resize(new, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)

    cv2.imshow('orig', r_pic)
    cv2.imshow('diff', d_pic)
    cv2.imshow('points', new)
    cv2.waitKey()


def main():
    global calibration, roi_x, roi_y
    print("main()")
    right = []
    left = []
    color = []
    points = []

    if details['rl']:
        right = glob.glob("%s/right*" % image_path.rstrip('/'))
        right.sort()

    if details['ll']:
        left = glob.glob("%s/left*" % image_path.rstrip('/'))
        left.sort()

    if details['rl']:
        roi_x, roi_y = get_roi_by_path(right[0], ratio)
    else:
        roi_x, roi_y = get_roi_by_path(left[0], ratio)

    if details['color']:
        color = glob.glob("%s/color*" % image_path.rstrip('/'))
        color.sort()

    print(f'RIGHT[{len(right)}] LEFT[{len(left)}] COLOR[{len(color)}]')
    if len(color) == 0:
        color = None

    print("I: processing %d steps" % details['steps'])

    if details['rl']:
        points = points_process_images(right, color=color)

    if details['ll']:
        left = points_process_images(left, color=color, right=False)
        for p in left:
            points.append(p)

    filename = f'{scan_path}\\{scan_dir}.xyz'
    print("I: Writing pointcloud to %s" % filename)
    ps.output_asc_pointset(filename, points, 'xyzcn')

    visualize_point_cloud.vis_points(points)


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-t", "--type", action="store", type="string", default=None, dest="type",
                      help="")
    args, _ = parser.parse_args()
    t = args.type
    # t = "single"

    scan_dir = '20221129160247'
    scan_path = getcwd() + "\\scans\\" + scan_dir
    image_path = scan_path + "\\images"
    if not path.isdir(image_path):
        image_path = scan_path

    details_path = f'{scan_path}\\details.json'
    f = open(details_path, 'r')
    details = load(f)
    print(details)

    cal_path = scan_path + "\\calibration"
    if not path.isdir(cal_path):
        if details['type'] == 'linear':
            source_path = getcwd() + "\\calibration\\linear"
        else:
            source_path = getcwd() + "\\calibration\\circular"
        shutil.copytree(source_path, cal_path)

    if details['type'] == 'linear':
        calibration = LinearCalibration(cal_path)
    else:
        # calibration = Calibration(cal_path)
        calibration = None
    ratio = 1

    roi_x = []
    roi_y = []

    if t is None:
        main()
    elif t == 'single':
        single()
