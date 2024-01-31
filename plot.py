from os import getcwd, read
from time import sleep

import matplotlib.pyplot as plt
import numpy
from numpy import array


class Plot(object):
    def __init__(self, point_cloud):
        self.pc = point_cloud

    def show(self):
        plt.ion()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        # x, y, z = [], [], []
        x = array([[0, 0, 0]])
        ax.set_zlim(-150, 150)
        up_cnt = int(len(pc)/100)
        up = 0
        plt.xlim(-150, 150)
        plt.ylim(-150, 150)
        sc = ax.scatter(x[:, 0], x[:, 1], x[:, 2], s=0.1, marker='o', c="green")
        fig.show()
        lp = 0
        y = []
        for a, b, c, _, _, _, _, _, _ in self.pc:
            y.append([a, c, b])
            up += 1
            if up >= up_cnt:
                lp += 1
                print(lp)
                up = 0
                z = array(y)
                rot = ((lp*3) + 180) % 360 - 180
                ax.view_init(elev=30, azim=rot, roll=0)
                sc._offsets3d = (z[:, 0], z[:, 1], z[:, 2])
                plt.draw()
                #fig.canvas.draw()
                #fig.canvas.flush_events()
                #x, y, z = [], [], []
                plt.pause(0.1)
                #y = []
        plt.waitforbuttonpress()


scan_dir = '20221230134211'
scan_path = getcwd() + "\\scans\\" + scan_dir
details_path = f'{scan_path}\\{scan_dir}.xyz'
pc = numpy.loadtxt(details_path, float)
print(len(pc))

plot = Plot(pc)
plot.show()
