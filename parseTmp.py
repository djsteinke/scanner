import glob
from os import getcwd
import math
import cv2
from model.pointset import *
from json import load
import visualize_point_cloud
from parser_roi import get_roi_by_path
from parser_util import points_max_cols

count = 0


def points_triangulate(points, y_offset, color=None):

    cam_degree = 30
    px, py = points

    bgr = [0, 0, 0]
    if color is not None:
        bgr = color[round(py), round(px)]

    pz = y_roi[1]-py
    calc_z = pz/scaler
    px /= scaler
    py /= scaler
    cam_angle = math.radians(cam_degree)
    calc_x = px / math.tan(cam_angle)
    calc_y = px - y_offset


    return [
        calc_x,
        calc_y,
        calc_z,
        bgr[2], bgr[1], bgr[0],
        0.0, 0.0, 0.0
    ]


def points_triangulate_cir(points, a, color=None):
    cam_degree = 30
    px, py = points
    cam_angle = math.radians(cam_degree)
    angle = math.radians(a)
    #angle = (a/360.0)*(2.0*math.pi)

    bgr = [0, 0, 0]
    if color is not None:
        bgr = color[round(py), round(px)]

    radius = px / math.sin(cam_angle)
    pz = y_roi[1]-py

    calc_z = pz/scaler
    calc_x = radius * math.sin(angle) / scaler
    calc_y = radius * math.cos(angle) / scaler
    return [
        calc_x,
        calc_y,
        calc_z,
        (bgr[2]*1.0)/255.0, (bgr[1]*1.0)/255.0, (bgr[0]*1.0)/255.0,
        0.0, 0.0, 0.0
    ]


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


def points_process_images(images, color=None):
    global x_roi, y_roi
    turns = 1
    per_turn = 2
    x_offset_pic = turns * per_turn
    points = []
    x_roi, y_roi = get_roi_by_path(images[0], ratio)
    x_offset_pic = x_offset_pic * scaler / ratio
    x_offset = 0.0
    #images = images[1:]
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
            tmin = 60
        h, w, _ = img.shape
        if ratio > 1:
            h_tmp = int(h/ratio)
            w_tmp = int(w/ratio)
            img = cv2.resize(img, (w_tmp, h_tmp), interpolation=cv2.INTER_AREA)
            h, w, _ = img.shape

        xy = points_max_cols(img, threshold=(tmin, 255), c=True)
        # xy = points_max_cols(img)
        xy = remove_noise(xy, w)

        if details['type'] == "circular":
            x_offset = pic_num * float(details['dps'])
            cent = 285*6
            # xyz = [points_triangulate_cir((x - (w / 2), y), x_offset, color=c) for x, y in xy]
            xyz = [points_triangulate_cir((cent-x, y), x_offset, color=c) for x, y in xy]
            xyz = calc_normals(xyz, x_offset)
        else:
            xyz = [points_triangulate((x - (w / 2), y), x_offset, color=c) for x, y in xy]
            # x_offset -= x_offset_pic
            xyz = calc_normals(xyz, 0)
            x_offset = - pic_num * float(details['dps'])
        # xyz = [[x, y, z, xn, yn, zn] for x, y, z, xn, yn, zn in xyz if x >= 0]
        xyz = [[x, y, z, r, g, b, xn, yn, zn] for x, y, z, r, g, b, xn, yn, zn in xyz]
        points.extend(xyz)

        preview = False
        if preview:
            visualize_point_cloud.vis_points(points)

    return points


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


def parse_images(images, color=None):

    points = points_process_images(images, color=color)

    return points


def main():
    global details
    color = []
    left = []
    scan_folder = "20220424102807"
    path = getcwd() + "\\scans\\" + scan_folder
    filename = f'{path}\\{scan_folder}.xyz'

    details_path = f'{getcwd()}\\scans\\' + scan_folder + '\\details.json'
    f = open(details_path, 'r')
    details = load(f)
    print(details)

    # print "Scanning %s for files" % path

    right = glob.glob("%s/right*" % path.rstrip('/'))
    right.sort()

    if details['left']:
        left = glob.glob("%s/left*" % path.rstrip('/'))
        left.sort()

    if details['color']:
        color = glob.glob("%s/color*" % path.rstrip('/'))
        color.sort()

    print(f'RIGHT[{len(right)}] LEFT[{len(left)}] COLOR[{len(color)}]')
    if len(color) == 0:
        color = None
    steps = details['steps']

    print("I: processing %d steps" % steps)

    right = parse_images(right, color=color)

    if details['left']:
        left = parse_images(left, color=color)

    print("I: Writing pointcloud to %s" % filename)
    output_asc_pointset(filename, right, 'xyzcn')

    # Visualize point cloud
    visualize_point_cloud.main(filename)
    #subprocess.run(['python', '-f', f'{scan_folder}.xyz', '-p', path], shell=True)


def tmp_pic():
    global x_roi, y_roi, details, ratio
    scan_folder = "20220424102807"
    path = getcwd() + "\\scans\\" + scan_folder + '\\'
    im_n = 0
    pic = f"{path}right_%04d.jpg" % im_n
    color = f"{path}color_%04d.jpg" % im_n

    details_path = f'{getcwd()}\\scans\\' + scan_folder + '\\details.json'
    f = open(details_path, 'r')
    details = load(f)
    print(details)

    img = cv2.imread(pic)
    col = cv2.imread(color)
    sub = cv2.subtract(img, col)
    h, w, c = img.shape
    img = cv2.resize(img, (w // 6, h // 6), interpolation=cv2.INTER_AREA)
    sub = cv2.resize(sub, (w // 6, h // 6), interpolation=cv2.INTER_AREA)
    h, w, c = sub.shape

    ratio = 6
    x_roi, y_roi = get_roi_by_path(pic)

    f_xy = list()
    xy = points_max_cols(sub, threshold=(60, 255), c=True)

    new = np.zeros((h, w, 3), np.uint8)
    new_f = np.zeros((h, w, 3), np.uint8)
    #img[:, :, 2] = np.zeros([img.shape[0], img.shape[1]])

    print(x_roi, y_roi)

    r = float(w) * 0.02

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
            img[b, a, 0] = 255
    for a in range(0, h, 50):
        r = 5
        if a % 100 == 0:
            r = 2
        for b in range(0, w, r):
            new[a, b, 0] = 255
            new_f[a, b, 0] = 255
            img[a, b, 0] = 255
    cv2.imshow("orig", img)
    cv2.imshow("minus", sub)
    cv2.imshow("noise", new_f)
    cv2.imshow("new", new)
    cv2.waitKey()


nx = 6              # nx: number of grids in x axis
ny = 9              # ny: number of grids in y axis


def get_p2p_dist(p):
    # print(p[0], p[1])
    # print(f'x[%0.2f] y[%0.2f]' % (p[0, 0, 0], p[0, 0, 1]))
    avg_r = []
    avg_c = []
    for y in range(0, ny):
        for x in range(0, nx):
            x0 = p[y*x+x, 0, 0]
            y0 = p[y*x+x, 0, 1]
            x1 = p[y*x+x+1, 0, 0]
            y1 = p[y*x+x+1, 0, 1]
            d = math.sqrt(math.pow((x1-x0), 2) + math.pow((y1-y0), 2))
            avg_r.append(d)
    for x in range(0, nx):
        for y in range(0, ny):
            x0 = p[y*x+x, 0, 0]
            y0 = p[y*x+x, 0, 1]
            x1 = p[y*x+x+1, 0, 0]
            y1 = p[y*x+x+1, 0, 1]
            d = math.sqrt(math.pow((x1-x0), 2) + math.pow((y1-y0), 2))
            avg_c.append(d)

    avg_x = sum(avg_r)/len(avg_r)
    avg_y = sum(avg_c)/len(avg_c)
    print('avg_x[%0.2f], avg_y[%0.2f]' % (avg_x, avg_y))
    return avg_x, avg_y


def linear_calibration_process():
    scan_folder = "calibration"
    path = getcwd() + "\\" + scan_folder + '\\'
    pic = f"{path}linear_calibration_0000.jpg"
    pic = f"{path}calibration_0008.jpg"

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


def process_calibration_pics(ratio):
    scan_folder = "calibration"
    path = getcwd() + "\\" + scan_folder + '\\'
    pic = f"{path}linear_calibration_0000.jpg"

    img = cv2.imread(pic)
    x_r, y_r = get_roi_by_path(pic, ratio)
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
    scaler = 258.87/20.0
    ratio = 1
    main()
    #linear_calibration_process()
    #process_calibration_pics()
    #tmp_pic()
