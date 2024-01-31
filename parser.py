import optparse
import glob
import model.pointset as ps
import math
import numpy as np
import shutil
from os import getcwd, path, makedirs

import visualizer
from calibrate_camera import CameraCalibration
from calibration import AndroidCalibration
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


def vector_normal(p1, p2, p3):
    v1 = [(p1[0]-p2[0]), (p1[1]-p2[1]), (p1[2]-p2[2])]
    v2 = [(p3[0]-p2[0]), (p3[1]-p2[1]), (p3[2]-p2[2])]
    #v1, v2 = vector_angle(v1, v2, offset)
    n = [(v1[1]*v2[2]-v1[2]*v2[1]), -1*(v1[0]*v2[2]-v1[2]*v2[0]), (v1[0]*v2[1]-v1[1]*v2[0])]
    if p2[9]:
        n = [n[0]*-1, n[1]*-1, n[2]*-1]
    v1m = math.sqrt(math.pow(v1[0], 2) + math.pow(v1[1], 2) + math.pow(v1[2], 2))
    v2m = math.sqrt(math.pow(v2[0], 2) + math.pow(v2[1], 2) + math.pow(v2[2], 2))
    vm = v1m * v2m
    if vm == 0:
        return [0.0, 0.0, 0.0]
    else:
        return [n[0]/vm, n[1]/vm, n[2]/vm]


def vector_angle(v1, v2, offset):
    a_dot_b = v1[0] * v2[0] + v1[2] * v2[2]
    a_mag = math.sqrt(math.pow(v1[0], 2) + math.pow(v1[2], 2))
    b_mag = math.sqrt(math.pow(v2[0], 2) + math.pow(v2[2], 2))

    det = v1[0] * v2[2] - v1[2] * v2[0]
    alpha = math.atan2(det, a_dot_b)
    #print(offset, round(alpha, 2))
    """
    theta = 0
    if a_mag and b_mag != 0:
        mag = a_dot_b/(a_mag*b_mag)
        if -1 <= mag <= 1:
            theta = math.acos(a_dot_b/(a_mag*b_mag))

        #print(offset, mag, theta)
    """
    if alpha < 0:
        return v2, v1
    else:
        return v1, v2


def calculate_normal_vector(xyz, xyz2, flip=False):
    length = len(xyz)
    l2 = len(xyz2)
    r = 8
    for i in range(0, length-r, 1):
        if flip:
            p1 = xyz2[i if i < l2 else l2-1]
        else:
            p1 = xyz[i]
        p2 = xyz[i+r]
        if flip:
            p3 = xyz[i]
        else:
            p3 = xyz2[i if i < l2 else l2-1]
        n = vector_normal(p2, p1, p3)

        xyz[i][6] = n[0]
        xyz[i][7] = n[1]
        xyz[i][8] = n[2]
    return xyz


def calculate_normal_new(xyz, a):
    length = len(xyz)
    r = 8
    angle = math.radians(a)
    for i in range(0, length-r, 1):
        p1 = xyz[i]
        p2 = xyz[i+r]
        #r1 = p1[0]/math.cos(angle)
        r1 = math.sqrt(math.pow(p1[0], 2) + math.pow(p1[2], 2))
        #if p1[0] < 0:
        #    r1 *= -1

        #r2 = p2[0]/math.cos(angle)
        r2 = math.sqrt(math.pow(p2[0], 2) + math.pow(p2[2], 2))
        #if p2[0] < 0:
        #    r2 *= -1
        beta = 0
        y_d = p1[1]-p2[1]
        r_d = r1 - r2
        if y_d != 0:
            beta = math.pi/2.0 - math.atan(r_d/y_d)
        rd = abs(math.sin(beta))
        yd = abs(math.cos(beta))
        if r_d == 0 and y_d == 0:
            rd = 0
            yd = 0
        elif r_d == 0:
            yd = 0
            if y_d < 0:
                rd *= -1
        elif y_d == 0:
            rd = 0
            if r_d > 0:
                yd *= -1
        elif r_d > 0:
            y_d *= -1
            if y_d < 0:
                r_d *= -1
        elif r_d < 0:
            if y_d < 0:
                r_d *= -1

        #y1 = p1[1]-p2[1] + math.sin(beta)

        #x_neg = p1[0] < 0
        #z_neg = p1[2] < 0
        calc_x = rd * math.cos(angle)
        #if x_neg:
        #    calc_x *= -1
        calc_z = rd * math.sin(angle)
        #if z_neg:
        #    calc_z *= -1

        xyz[i][6] = calc_x
        xyz[i][7] = yd
        xyz[i][8] = calc_z
    return xyz


def points_triangulate(points, offset, color=None, right=True):
    left_offset = 0
    if right:
        cam_degree = 30.8  # 29.75
    else:
        cam_degree = -29.2   # 31
        left_offset = 60.0
    px, py = points

    bgr = [147, 201, 3]
    if color is not None:
        bgr = color[round(py), round(px)]
    #cz = camera_config.config[5]
    cz = 302.88
    cx = 534.0  #533.0/ratio    #534
    cy = 962.0  #962.0/ratio
    #cf = camera_config.config[2]/ratio
    cf = 1548.95
    flip = False
    #if details['type'] == 'circular':
    if True:
        #calc_x, calc_y, calc_z = calibration.get_scaled_xyz(px, py, right, offset)
        calc_x = 0.0
        if float(px) != cx:
            # webcam f 1701.0 / cx 632 / cy 1048 / z 374.0
            # calc f 1559.50 / z 314.9
            # cv2 f 1581.4 / 305.5 382.5
            #
            if right:
                calc_x = cz/(cf/(float(px)-cx) + 1.0/math.tan(math.radians(cam_degree)))
                flip = calc_x < 0.0
            else:
                calc_x = cz / (cf / (cx - float(px)) - 1.0 / math.tan(math.radians(cam_degree)))
                flip = calc_x > 0.0
        if right:
            calc_z = -calc_x / math.tan(math.radians(cam_degree))
        else:
            calc_z = calc_x / math.tan(math.radians(cam_degree))
        calc_y = (cz+calc_z)*(cy - float(py))/cf
        # 348 + 33.1

        if not right:
            offset += left_offset
        angle = math.radians(offset)
        """
        radius = math.sqrt(math.pow(calc_z, 2) + math.pow(calc_x, 2))
        x_neg = calc_x < 0
        z_neg = calc_z < 0
        calc_x = radius * math.cos(angle)
        if x_neg:
            calc_x *= -1
        calc_z = radius * math.sin(angle)
        if z_neg:
            calc_z *= -1
        """
        orig_x = calc_x
        orig_z = calc_z
        calc_x = orig_x*math.cos(angle) - orig_z*math.sin(angle)
        calc_z = orig_x*math.sin(angle) + orig_z*math.cos(angle)
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
        0.0, 0.0, 0.0, flip
    ]


last_xyz = []
first_xyz = []


def points_process_images(images, color=None, right=True):
    global last_xyz, first_xyz
    points = []
    #images = images[1:]
    s = details['steps']
    xyz_all = []
    for i, i_path in enumerate(images):
        if i <= s:
            if right:
                pic_num = i_path.split('right_')
            else:
                pic_num = i_path.split('left_')
            pic_num = int(pic_num[1].split('.')[0])
            side = "RIGHT" if right else "LEFT"
            img = cv2.imread(i_path, 0)
            img_c = cv2.imread(i_path)
            tmin = 15
            c = None
            max_cols_c = True
            if color is not None and i < len(color):
                #max_cols_c = False
                c = cv2.imread(color[i])
                c_gray = cv2.imread(color[i], 0)
                img = cv2.subtract(img, c_gray)
            if False:
                #max_cols_c = False
                tmin = 80
            h, w = img.shape
            if ratio > 1:
                h_tmp = int(h/ratio)
                w_tmp = int(w/ratio)
                img = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
                c = cv2.resize(c, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
                h, w = img.shape

            step = None
            if calibration is not None:
                step = [calibration.scalar, float(details['dps']), ratio]
            #xy = points_max_cols_a(img_c, roi=[roi_x, roi_y])
            xy = points_max_cols(img_c, threshold=(60, 255), c=max_cols_c, roi=[roi_x, roi_y], right=right)
            #xy = remove_noise(xy, w)

            offset = pic_num * float(details['dps'])

            print("%s: %03d/%03d" % (side, pic_num+1, s), round(offset, 1))
            xyz = []
            for x, y in xy:
                p = points_triangulate((x, y), offset, color=c, right=right)
                r = math.sqrt(math.pow(p[0], 2) + math.pow(p[2], 2))
                # Remove points larger than the scan table
                if r < 120:
                    xyz.append(p)
            #xyz = [points_triangulate((x, y), offset, color=c, right=right) for x, y in xy]

            xyz_all.append([i, offset, xyz])
            """
            if i == 0:
                first_xyz = xyz
            if i > 0 and len(last_xyz) > 0:
                xyz = calculate_normal_vector(xyz, last_xyz, offset)
            last_xyz = xyz
            #xyz = calc_normals(xyz, offset)
            if i > 0:
                xyz = [[x, y, z, r, g, b, xn, yn, zn] for x, y, z, r, g, b, xn, yn, zn, flip in xyz]
                points.extend(xyz)
    
            preview = False
            if preview:
                visualize_point_cloud.vis_points(points)
        if len(last_xyz) > 0 and len(first_xyz) > 0:
            xyz = calculate_normal_vector(first_xyz, last_xyz, 0)
            xyz = [[x, y, z, r, g, b, xn, yn, zn] for x, y, z, r, g, b, xn, yn, zn, flip in xyz]
            points.extend(xyz)
            """

    for i in range(0, len(xyz_all)):
        if i == 0:
            xyz = calculate_normal_vector(xyz_all[i][2], xyz_all[i+1][2], right)
        else:
            xyz = calculate_normal_vector(xyz_all[i][2], xyz_all[i-1][2], right)
        xyz = [[x, y, z, r, g, b, xn, yn, zn] for x, y, z, r, g, b, xn, yn, zn, flip in xyz]
        points.extend(xyz)
    return points


def single():
    global calibration, roi_x, roi_y
    print("single()")
    pic_num = 3
    right = image_path + "\\right_%04d.jpg" % pic_num
    color = image_path + "\\color_%04d.jpg" % pic_num
    r_pic = cv2.imread(right)
    c_pic = None
    c_pic = cv2.imread(color)
    d_pic = cv2.subtract(r_pic, c_pic)
    #d_pic = r_pic

    h, w, _ = r_pic.shape
    r = h / 640.0
    h_tmp = int(h / r)
    w_tmp = int(w / r)
    r_pic = cv2.resize(r_pic, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
    d_pic = cv2.resize(d_pic, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)

    roi_x = [1134, 2460]
    roi_y = [666, 3408]
    roi_x, roi_y = get_roi_by_path(right, ratio)
    tmin = 35
    step = None
    if calibration is not None:
        step = [calibration.scalar, float(details['dps']), ratio]
    xy = points_max_cols_a(d_pic)
    #xy = points_max_cols(d_pic, threshold=(tmin, 255), c=True, roi=[roi_x, roi_y], step=step)
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


    new = np.zeros((h_tmp, w_tmp, 3), np.uint8)
    #cv2.imshow("diff", d_pic)
    #cv2.waitKey()
    for x, y in xy:
        #x = int(x/r)
        #y = int(y/r)
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
        points = points_process_images(right, color=color, right=True)

    if details['ll']:
        left = points_process_images(left, color=color, right=False)
        #visualize_point_cloud.vis_points(left)
        points.extend(left)

    # draw x, z axis
    """
    xyz = [[x, 0, 0, 255, 0, 0, 0, 0, 0] for x in range(0, 100, 5)]
    points.extend(xyz)
    xyz = [[0, 0, z, 0, 255, 0, 0, 0, 0] for z in range(0, 100, 10)]
    points.extend(xyz)
    """

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
    #t = "single"

    scan_dir = '20230828115808'
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
        #calibration = Calibration(cal_path)
        android_cal = getcwd() + "\\calibration\\android"
        camera_config = CameraCalibration(wd=android_cal, reload=True)
        print(camera_config.config)
        calibration = None
    ratio = 1.0

    roi_x = []
    roi_y = []

    if t is None:
        main()
    elif t == 'single':
        single()
