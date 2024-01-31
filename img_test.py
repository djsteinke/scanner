import time
from os import getcwd
import numpy as np

import cv2
from matplotlib import pyplot as plt

scan_dir = '20230828115808'
# frog: 20221220212413

#scan_dir = '20221213094320'
scan_path = getcwd() + "\\scans\\" + scan_dir
image_path = scan_path + "\\images"
xyz_path = scan_path + "\\" + scan_dir + ".xyz"
#xyz_data = np.loadtxt(xyz_path, dtype=float)
# mentioning absolute path of the image

threshold = 55
pic_num = 26
lower = np.array([0, 0, 130])
upper = np.array([175, 150, 255])
right = image_path + "\\left_%04d.jpg" % pic_num
#color = image_path + "\\color_%04d.jpg" % pic_num

#image_orig = cv2.imread(color)
# read/load an image in grayscale mode
image_r = cv2.imread(right, 0)
#image_c = cv2.imread(color, 0)

image_cr = cv2.imread(right)

Rh, Rw = image_r.shape
print(Rh, Rw)
r = 2.0
w = int(float(Rw) / r)
h = int(float(Rh) / r)
print(h, w)


#image_d = cv2.subtract(image_r, image_c)

image_r = cv2.resize(image_r, (w, h), interpolation=cv2.INTER_AREA)
#image_c = cv2.resize(image_c, (w, h), interpolation=cv2.INTER_AREA)

# show the Input image on the newly created image window

#image_d = cv2.resize(image_d, (w, h), interpolation=cv2.INTER_AREA)
#image_d = cv2.resize(image_d, (Rw, Rh), interpolation=cv2.INTER_AREA)
# applying cv2.THRESH_BINARY thresholding techniques
#ret, bin_img = cv2.threshold(image_d, threshold, 255, cv2.THRESH_BINARY)

#image_cr = cv2.subtract(image_cr, image_orig)
#image_orig = cv2.resize(image_orig, (w, h), interpolation=cv2.INTER_AREA)

# show the binary image on the newly created image window

print(time.time())
# extracting the contours from the given binary image
#contour, hierarchy = cv2.findContours(bin_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

print(time.time())
#sought = [255, 255, 255]
#print(np.all(bin_img == sought, axis=0))
        #print(bin_img[y][x])

print(time.time())
#color = (25, 25, 25)
#mask = cv2.inRange(image_d, np.array(color), np.array(color))
#contour = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2][0]


#print("Total Number of Contours found =", len(contour))
#print("contours are: \n", contour)
#print("hierarchy is: \n", hierarchy)
min = []
for i in range(0, h):
    min.append([w, 0])

avg = []
for i in range(0, h):
    avg.append([0, 0])
"""
for c in contour:
    for p in c:
        #print(p[0])
        avg[p[0][1]][0] += p[0][0]
        avg[p[0][1]][1] += 1
        if min[p[0][1]][0] > p[0][0]:
            min[p[0][1]][0] = p[0][0]
            min[p[0][1]][1] += 1
        image_orig[p[0][1], p[0][0], 0] = 0
        image_orig[p[0][1], p[0][0], 1] = 255
        image_orig[p[0][1], p[0][0], 2] = 0

for i in range(0, len(avg)):
    m = min[i]
    if m[1] > 0:
        x_avg = m[0]
        image_orig[i, x_avg, 0] = 0
        image_orig[i, x_avg, 1] = 0
        image_orig[i, x_avg, 2] = 255

    a = avg[i]
    if a[1] > 0:
        x_avg = int(round(a[0]/a[1], 0))
        image_orig[i, x_avg, 0] = 255
        image_orig[i, x_avg, 1] = 0
        image_orig[i, x_avg, 2] = 0
"""


r_img = cv2.inRange(image_cr, lower, upper)

"""
xy = []
for x in range(0, w):
    for y in range(0, h):
        if bin_img[y][x] > 0:
            xy.append([x, y])
            image_orig[y, x, 0] = 0
            image_orig[y, x, 1] = 0
            image_orig[y, x, 2] = 255

start = time.time()
#print(time.time())
it = np.nditer(r_img)
i = 0
f = 0
for x in it:
    if x > 0:
        f += 1
        #print(i % w, int(i/h))
    i += 1
print(time.time() - start, f)

f = 0
start = time.time()
for y in range(0, Rh, 3):
    found = False
    for x in range(0, Rw):
        if r_img[y][x] > 0:
            f += 1
            found = True
        else:
            if found:
                break
print(time.time() - start, f)

start = time.time()
points = []
for y in range(0, Rh, 3):
    found = False
    max_r = -1
    max_rx = -1
    r_min = 60
    while r_min >= 5:
        for x in range(Rw-1, 0, -1):
            b, g, r = image_cr[y][x]
            if r > r_min and b < r*0.8 and g < r*0.7:
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

    #print(max_rx, y)
    if max_rx > 0:
        points.append([max_rx, y])

points_noise = []
points_ignore = []
for i in range(3, len(points)-3):
    x_tot_b = 0
    x_tot_a = 0
    cnt_b = 0
    cnt_a = 0
    for b in range(1, 4):
        if i-b not in points_ignore:
            x_tot_b += points[i-b][0]
            cnt_b += 1
        x_tot_a += points[i+b][0]
        cnt_a += 1
    if cnt_b == 0 or cnt_a == 0 or abs(x_tot_b/cnt_b - points[i][0]) < 30 or abs(x_tot_a/cnt_a - points[i][0]) < 30:
        points_noise.append(points[i])
    else:
        points_ignore.append(i)


print(time.time() - start, f)
new = np.zeros((Rh, Rw, 3), np.uint8)
for xy in points_noise:
    new[xy[1]][xy[0]] = 255
"""
thr3 = cv2.adaptiveThreshold(image_r, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 2)
ret, thr2 = cv2.threshold(image_r, 60, 255, cv2.THRESH_BINARY)
image_cr = cv2.resize(image_cr, (w, h), interpolation=cv2.INTER_AREA)
r_img = cv2.resize(r_img, (w, h), interpolation=cv2.INTER_AREA)
#new = cv2.resize(new, (w, h), interpolation=cv2.INTER_AREA)

image_cr = cv2.cvtColor(image_cr, cv2.COLOR_BGR2RGB)
imgs = [image_cr, image_r]
names = ["color", "gray"]
for i in range(20, 161, 20):
    ret, thr = cv2.threshold(image_r, i, 255, cv2.THRESH_BINARY)
    imgs.append(thr)
    names.append(str(i))

for i in range(10):
    plt.subplot(2, 5, i+1), plt.imshow(imgs[i], 'gray')
    plt.title(names[i])
    plt.xticks([]), plt.yticks([])
plt.show()

#ax = plt.axes(projection="3d")
#ax = fig.gca(projection="3d")

x_a = []
y_a = []
z_a = []
#for i in range(0, len(xyz_data), 30):
#    x, y, z, _, _, _, _, _, _ = xyz_data[i]
#    x_a.append(x)
#    y_a.append(y)
#    z_a.append(z)
#ax.plot3D(x_a, y_a, z_a, 'rd')
fig = plt.figure()
ax = fig.add_subplot(projection='3d')
ax.set_xlim3d([-200, 200])
ax.set_ylim3d([-200, 200])
ax.set_zlim3d([-200, 200])
#ax.plot_wireframe(x_a, y_a, z_a, rstride=10, cstride=10)
ax.scatter(x_a, y_a, z_a)
"""
plt.show()

cv2.imshow('range_orig', image_cr)
cv2.imshow('image_r', image_r)
cv2.imshow('thr3', thr3)
cv2.imshow('thr2', thr2)
#cv2.imshow('range', r_img)
#cv2.imshow('new', new)
#cv2.imshow('orig', image_orig)
#cv2.imshow('Input', image_d)
#cv2.imshow('Intermediate', bin_img)
cv2.waitKey()


"""