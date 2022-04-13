import numpy as np
from os import getcwd
import open3d as o3d
import math
import optparse


def temp():
    points = []
    for i in range(0, 360, 3):
        man_rad = ((i*1.0)/360.0)*(2*math.pi)
        r = 30.0
        x = r*math.cos(man_rad)
        y = r*math.sin(man_rad)
        z = 1.0
        points.append([x, y, z])
    print(points[1])
    a = np.array(points)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(a)
    print(pcd)
    o3d.visualization.draw_geometries([pcd], width=1280, height=720)


def main():
    global path
    pcd = None
    if path == "/":
        input_path = getcwd()
        dataname = "20220407103614"
        pcd = o3d.io.read_point_cloud(input_path + '\\scans\\' + dataname + '\\' + dataname + ".xyz", format='xyzn')
    else:
        xyz = open(path + '\\' + file, mode="r")
        points = []
        for line in xyz:
            x, y, z, r, g, b = line.split()
            points.append([x, y, z, r, g, b])
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points)
    if pcd is None:
        print("PCD not created. Exiting")
        exit()

    # surface reconstruction using Poisson reconstruction
    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd=pcd, depth=9)

    # paint uniform color to better visualize, not mandatory
    mesh.paint_uniform_color(np.array([0.7, 0.7, 0.7]))
    o3d.visualization.draw_geometries([pcd, mesh], width=1280, height=720)


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-p", "--path", action="store", type="string", default="/", dest="path",
                      help="path to dir to visualize binary")
    parser.add_option("-f", "--file", action="store", type="string", default="value.xyz", dest="file",
                      help="filename to visualize")
    args, _ = parser.parse_args()

    path = args.path
    file = args.file
    main()
    #temp()
