import numpy as np
from os import getcwd
import open3d as o3d
import math


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
    input_path = getcwd()
    dataname = "20220410105543"
    #dataname = "20220406081736"
    path = input_path + '\\scans\\' + dataname + '\\' + dataname + ".xyzrgb"
    pathXYZ = input_path + '\\scans\\' + dataname + '\\' + "xyz.xyz"
    xyz = open(input_path + '\\scans\\' + dataname + '\\' + dataname + ".xyz", mode="r")
    points = []
    for line in xyz:
        x, y, z, r, g, b = line.split()
        points.append([x, y, z, r, g, b])
    print(points[1])
    a = np.array(points)
    pcd = o3d.io.read_point_cloud(input_path + '\\scans\\' + dataname + '\\' + dataname + ".xyz", format='xyzn')
    #pcd = o3d.geometry.PointCloud()
    #pcd.points = o3d.utility.Vector3dVector(a)
    print(pcd)
    #pcd.points = o3d.utility.Vector3dVector(points)
    #pcd.colors = o3d.utility.Vector3dVector(colors/65535)
    #pcd.normals = o3d.utility.Vector3dVector(normals)
    downpcd = pcd.voxel_down_sample(voxel_size=0.05)
    #pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    o3d.visualization.draw_geometries([pcd], width=1280, height=720)

    return
    poisson_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd=pcd, depth=8, width=0, scale=1.1,
                                                                             linear_fit=False)[0]
    bbox = pcd.get_axis_aligned_bounding_box()
    p_mesh_crop = poisson_mesh.crop(bbox)
    #o3d.io.write_triangle_mesh(output_path+"bpa_mesh.ply", dec_mesh)
    #o3d.io.write_triangle_mesh(output_path+"p_mesh_c.ply", p_mesh_crop)
    mesh_lod = p_mesh_crop.simplify_quadric_decimation(10000)
    o3d.visualization.draw_geometries([mesh_lod], width=1280, height=720)


if __name__ == "__main__":
    #main()
    temp()
