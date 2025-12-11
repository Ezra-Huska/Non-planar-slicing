from stl import mesh
import numpy as np
import time
import math

#-----------------------------------------------------------------------------------------
# Transformation Settings
#-----------------------------------------------------------------------------------------

FILE_NAME = 'EN_testhook_hb.stl'                              # Filename with extension
FOLDER_NAME_UNTRANSFORMED = 'stl/'
FOLDER_NAME_TRANSFORMED = 'stl_transformed/'    # Make sure this folder exists                               # Transformation angle
REFINEMENT_ITERATIONS = 0                      # refinement iterations of the stl. 2-3 is a good start for regular stls. If its already uniformaly fine, use 0 or 1. High number cause huge models and long script runtimes
#for cube 5=0.5s,6=3s,7=8s
change=0
TRANSFORMATION_CODE = "0020016"
if TRANSFORMATION_CODE!="":
    LAYER_TYPE=int(TRANSFORMATION_CODE[0])
    MIDDLE_LAYER_DIRECTION=int(TRANSFORMATION_CODE[1])
    LAYER_PART_RADIUS=int(TRANSFORMATION_CODE[2:5])
    CONE_ANGLE=int(TRANSFORMATION_CODE[5:7])
else:
    CONE_ANGLE = 35#16                                      # transformation angle
    LAYER_PART_RADIUS=3
    LAYER_TYPE = 0#0=triangle, 1=circle
    MIDDLE_LAYER_DIRECTION = 0 #0=outward 1=inward

def refinement_four_triangles(triangle):
    #Compute a refinement of a triangle. On every side, the midpoint is added. The three corner points and three midpoints result in four smaller triangles.
    point1 = triangle[0]
    point2 = triangle[1]
    point3 = triangle[2]
    midpoint12 = (point1 + point2) / 2
    midpoint23 = (point2 + point3) / 2
    midpoint31 = (point3 + point1) / 2
    triangle1 = np.array([point1, midpoint12, midpoint31])
    triangle2 = np.array([point2, midpoint23, midpoint12])
    triangle3 = np.array([point3, midpoint31, midpoint23])
    triangle4 = np.array([midpoint12, midpoint23, midpoint31])
    return np.array([triangle1, triangle2, triangle3, triangle4])


def refinement_triangulation(triangle_array):
    #Compute a refinement of a triangulation using the refinement_four_triangles function.
    #The number of iteration defines, how often the triangulation has to be refined; n iterations lead to
    #4^n times many triangles.
    refined_array = triangle_array
    for i in range(0, REFINEMENT_ITERATIONS):
        n_triangles = refined_array.shape[0]*4
        refined_array = np.array(list(map(refinement_four_triangles, refined_array)))
        refined_array = np.reshape(refined_array, (n_triangles, 3, 3))
    return refined_array

def transform(points):
    # Transfoms the points on the triagle bassed on their position to the center
    if LAYER_TYPE==0:
        transformation_method = (lambda x, y, z: np.array([(np.sqrt(x**2+z**2)*np.cos(np.radians(np.degrees(np.arctan(z/x))+CONE_ANGLE))), y, (np.sqrt(x**2+z**2)*np.sin(np.radians(np.degrees(np.arctan(z/x))+CONE_ANGLE)))]))
        points_transformed = list(map(transformation_method, points[:, 0], points[:, 1], points[:, 2]))# makes it work in list form
        return np.array(points_transformed)
    else:
        transformation_method = (lambda x, y, z: np.array([x, y, z + dist_center_transform(x,y,z)]))
        points_transformed = list(map(transformation_method, points[:, 0], points[:, 1], points[:, 2]))# makes it work in list form
        return np.array(points_transformed)
def dist_center_transform(x,y,z):
    x,y=x-change,y-change
    dist = np.sqrt(x**2 + y**2)
    val= (dist%LAYER_PART_RADIUS)
    num = (np.floor(dist/LAYER_PART_RADIUS)%2)*LAYER_PART_RADIUS
    if LAYER_TYPE==0:
        if MIDDLE_LAYER_DIRECTION==0:
            c=LAYER_PART_RADIUS
        else:
            c=0
        if num==c:
            val = LAYER_PART_RADIUS-val
        z_new = round(val*np.tan(np.radians(CONE_ANGLE)),1)
        if z+z_new<0.5 and z+z_new>0.0:
            return 0
        return z_new
    elif LAYER_TYPE==1:
        if MIDDLE_LAYER_DIRECTION==1:
            c=LAYER_PART_RADIUS
        else:
            c=0
        if num==c:
            val = LAYER_PART_RADIUS-val
        if MIDDLE_LAYER_DIRECTION==1:
            return np.sqrt(LAYER_PART_RADIUS**2 - val**2)
        return np.sqrt(LAYER_PART_RADIUS**2 + val**2)
    else:
        raise ValueError(f'{LAYER_TYPE} is not a admissible type for the transformation')


#round(val*np.tan(np.radians(CONE_ANGLE)),1)
def main(path):
    # takes the triangles from stl reifines them, transforms them, then makes a file with the data
    my_mesh = mesh.Mesh.from_file(path)
    vectors = my_mesh.vectors
    vectors_refined = refinement_triangulation(vectors)
    vectors_refined = np.reshape(vectors_refined, (-1, 3))
    vectors_transformed = transform(vectors_refined)
    vectors_transformed = np.reshape(vectors_transformed, (-1, 3, 3))
    my_mesh_transformed = np.zeros(vectors_transformed.shape[0], dtype=mesh.Mesh.dtype)
    my_mesh_transformed['vectors'] = vectors_transformed
    my_mesh_transformed = mesh.Mesh(my_mesh_transformed)
    return my_mesh_transformed

start = time.time()
transformed_STL = main(path=FOLDER_NAME_UNTRANSFORMED + FILE_NAME)
transformed_STL.save(FOLDER_NAME_TRANSFORMED + FILE_NAME.replace(".stl","") + '.stl')
end = time.time()
print('Transformation time:', end - start)
if CONE_ANGLE<10:
    cn="0"+str(CONE_ANGLE)
else:
    cn=str(CONE_ANGLE)

if LAYER_PART_RADIUS<10:
    lpr="00"+str(LAYER_PART_RADIUS)
elif LAYER_PART_RADIUS<100:
    lpr="0"+str(LAYER_PART_RADIUS)
else:
    lpr=str(LAYER_PART_RADIUS)
print("code: "+str(LAYER_TYPE)+str(MIDDLE_LAYER_DIRECTION)+lpr+cn)
