import threading

import numpy as np
import open3d as o3d


class Viewer3D(object):

    def __init__(self, title, points):
        self.vis = o3d.visualization.O3DVisualizer()
        #self.vis.create_window("scan")
        #cloud = o3d.io.read_point_cloud(out_fn)  # out_fn is file name
        #vis.add_geometry(cloud)
        self.in_points = []
        self.running = False

        points = []
        normals = []
        colors = []
        for x, y, z, r, g, b, nx, ny, nz in self.in_points:
            r = str(round(float(r) / 255.0, 2))
            g = str(round(float(g) / 255.0, 2))
            b = str(round(float(b) / 255.0, 2))
            # print(x, y, z, r, g, b)
            points.append([x, y, z])
            normals.append([nx, ny, nz])
            colors.append([r, g, b])
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.normals = o3d.utility.Vector3dVector(normals)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        self.vis.add_geometry(self.vis, "points", [pcd])
        self.vis.show()

    def update_point_clouds(self):
        points = []
        normals = []
        colors = []
        for x, y, z, r, g, b, nx, ny, nz in self.in_points:
            r = str(round(float(r) / 255.0, 2))
            g = str(round(float(g) / 255.0, 2))
            b = str(round(float(b) / 255.0, 2))
            # print(x, y, z, r, g, b)
            points.append([x, y, z])
            normals.append([nx, ny, nz])
            colors.append([r, g, b])
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.normals = o3d.utility.Vector3dVector(normals)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        print("update")
        self.vis.add_geometry(pcd)
        #self.vis.update_geometry(pcd)
        #self.vis.update_renderer()
        #self.vis.poll_events()
        #threading.Timer(0.1, self.vis.run).start()
        # update your point cloud data here: convert depth to point cloud / filter / etc.
        #pass

