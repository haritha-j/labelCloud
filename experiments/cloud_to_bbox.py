import open3d as o3d
import numpy as np
from os import listdir
from os.path import isfile, join
import os
import json
import math

def rot2eul(R):
    beta = -np.arcsin(R[2,0])
    alpha = np.arctan2(R[2,1]/np.cos(beta),R[2,2]/np.cos(beta))
    gamma = np.arctan2(R[1,0]/np.cos(beta),R[0,0]/np.cos(beta))
    return np.array((alpha, beta, gamma))


if __name__ == "__main__":

    path = os.path.join(os.path.dirname(os.getcwd()), 'pointclouds/pipes')
    files = [f for f in listdir(path) if isfile(join(path, f))]
    #print(files)
    bboxes = []
    
    for file in files:
        try:
            f = os.path.join(path, file)
            
            pointset = []
            with open(f, 'r') as fp:
                points = fp.readlines()
                for point in points:
                    point_list = point.strip().split(" ")[:3]
                    pointset.append([float(x) for x in point_list])
            pointset = np.array(pointset)

            pcl = o3d.geometry.PointCloud()
            pcl.points = o3d.utility.Vector3dVector(pointset)
            oriented_bounding_box = pcl.get_oriented_bounding_box()
            
            r = [math.degrees(x) for x in rot2eul(oriented_bounding_box.R)]
            c = oriented_bounding_box.center
            e = oriented_bounding_box.extent
            
            bbox = {
                'name': 'pipe',
                'centroid': {
                    'x': c[0],
                    'y': c[1],
                    'z': c[2]
                },
                'dimensions': {
                    'length': e[0],
                    'width': e[1],
                    'height': e[2]
                },
                'rotations': {
                    'x': r[0],
                    'y': r[1],
                    'z': r[2]
                }
            }
            bboxes.append(bbox)
        except:
            print(file)

    with open('data.json', 'w') as f:
        json.dump({'objects':bboxes}, f)

