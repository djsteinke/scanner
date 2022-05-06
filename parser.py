import optparse
import glob
import model.pointset as ps
import math
import numpy as np
from os import getcwd
from parser_calibration import Calibration
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


def points_triangulate(points, offset, color=None, right=True):
    if right:
        cam_degree = 30
    else:
        cam_degree = 15
    px, py = points

    bgr = [255, 0, 0]
    if color is not None and right:
        bgr = color[round(py), round(px)]

    if details['type'] == 'circular':
        calc_x, calc_y, calc_z = calibration.get_scaled_xyz(px, py, right, offset)
    else:
        pz = roi_y[1]-py
        cam_angle = math.radians(cam_degree)
        calc_x = (px / math.tan(cam_angle)) / calibration.scalar
        calc_y = (px - offset) / calibration.scalar
        calc_z = pz / calibration.scalar

    return [
        calc_x,
        calc_y,
        calc_z,
        (bgr[2]*1.0)/255.0, (bgr[1]*1.0)/255.0, (bgr[0]*1.0)/255.0,
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

        step = [calibration.scalar[0], float(details['dps']), ratio]
        xy = points_max_cols(img, threshold=(tmin, 255), c=True, roi=[roi_x, roi_y], step=step)
        xy = remove_noise(xy, w)

        offset = pic_num * float(details['dps'])
        xyz = [points_triangulate((x, y), offset, color=c, right=right) for x, y in xy]
        xyz = calc_normals(xyz, offset)
        xyz = [[x, y, z, r, g, b, xn, yn, zn] for x, y, z, r, g, b, xn, yn, zn in xyz]
        points.extend(xyz)

        preview = False
        if preview:
            visualize_point_cloud.vis_points(points)

    return points


def single():
    global calibration, roi_x, roi_y
    print("single()")
    pic_num = 25
    right = scan_path + "\\right_%04d.jpg" % pic_num
    color = scan_path + "\\color_%04d.jpg" % pic_num
    r_pic = cv2.imread(right)
    c_pic = cv2.imread(color)
    d_pic = cv2.subtract(r_pic, c_pic)

    roi_x = [1134, 2460]
    roi_y = [666, 3408]
    #roi_x, roi_y = get_roi_by_path(right, ratio)
    tmin = 60
    step = [calibration.scalar[0], float(details['dps']), ratio]
    xy = points_max_cols(d_pic, threshold=(tmin, 255), c=True, roi=[roi_x, roi_y], step=step)
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
    h_tmp = int(h / 6)
    w_tmp = int(w / 6)
    new = np.zeros((h_tmp, w_tmp, 3), np.uint8)
    print('xy length', len(xy))
    r_pic = cv2.resize(r_pic, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
    d_pic = cv2.resize(d_pic, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
    for x, y in xy:
        x = int(x/6)
        y = int(y/6)
        new[y, x, 2] = 255
        d_pic[y, x, 0] = 255
        r_pic[y, x, 1] = 255
    #new = cv2.resize(new, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)

    #cv2.imshow('orig', r_pic)
    #cv2.imshow('diff', d_pic)
    #cv2.imshow('points', new)
    #cv2.waitKey()


def main():
    global calibration, roi_x, roi_y
    print("main()")
    right = []
    left = []
    color = []
    points = []

    if details['rl']:
        right = glob.glob("%s/right*" % scan_path.rstrip('/'))
        right.sort()

    if details['ll']:
        left = glob.glob("%s/left*" % scan_path.rstrip('/'))
        left.sort()

    if details['rl']:
        roi_x, roi_y = get_roi_by_path(right[0], ratio)
    else:
        roi_x, roi_y = get_roi_by_path(left[0], ratio)

    if details['color']:
        color = glob.glob("%s/color*" % scan_path.rstrip('/'))
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

    scan_dir = '20220505145503'
    scan_path = getcwd() + "\\scans\\" + scan_dir

    details_path = f'{scan_path}\\details.json'
    f = open(details_path, 'r')
    details = load(f)
    print(details)

    calibration_path = getcwd() + "\\calibration"
    calibration = Calibration(calibration_path)
    ratio = 1

    roi_x = []
    roi_y = []

    if t is None:
        main()
    elif t == 'single':
        single()
