import argparse
from hashlib import new
from lib2to3.pgen2.token import OP
import time
from typing import Optional, Tuple, List

import matplotlib.pyplot as plt

import bpy
import bmesh
import mathutils
import numpy as np
from blender_plotting.utils.background import set_pastel_background
from blender_plotting.utils.materials import create_solid_material
from blender_plotting.utils.renderers import cycles_render, eevee_render, workbench_render
from blender_plotting.utils.scenes import create_2d_scene


def parse_args():
    parser = argparse.ArgumentParser(description='Draw a R2 plane.')
    parser.add_argument('--cycles', action='store_true', help='Use Cycles.')
    parser.add_argument('--eevee', action='store_true', help='Use Eevee.')

    args = parser.parse_args()
    return args

DPI = 300 # Dots per inch

SCALE = 4
X_LIM = [-SCALE/2, SCALE/2]
Y_LIM = [-SCALE/2, SCALE/2]

BG_LIGTNESS = 0.01
BG_COLOR = (BG_LIGTNESS, BG_LIGTNESS, BG_LIGTNESS, 1.0)


def add_arrow(vector_origin: np.ndarray,
              vector_end: np.ndarray,
              name: Optional[str] = None,
              color: tuple = (1, 0, 0, 1.0)) -> Tuple[bpy.types.Object, bpy.types.Object]:
    """Add a 3D arrow model to the scene.

    Args:
        vector_origin (np.ndarray): Origin of the arrow.
        vector_end (np.ndarray): End of the arrow.
        name (Optional[str]): Name of the arrow.
        color (tuple): Color of the arrow.

    Returns:
        Tuple[bpy.types.Object, bpy.types.Object]: The arrow body and the arrow head.
    """

    if vector_origin.size == 2:
        vector_origin = np.append(vector_origin, 0)
    if vector_end.size == 2:
        vector_end = np.append(vector_end, 0)


    np_vector = vector_end - vector_origin
    v = mathutils.Vector(np_vector)
    up = mathutils.Vector((0,0,1))  # Z-Axis up convention
    if v!=-up:
        rot = up.rotation_difference(v)
    else:
        rot = mathutils.Quaternion((1,0,0),np.pi)

    # Create the cylinder part
    cyl_length = v.length*0.8
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,
                                        radius=0.01,
                                        depth=cyl_length,
                                        end_fill_type='NGON',
                                        enter_editmode=False)
    cylinder = bpy.context.active_object
    cylinder.location = vector_origin + cyl_length/2 * v.normalized()
    cylinder.rotation_mode = 'QUATERNION'
    cylinder.rotation_quaternion = rot
    if name is not None:
        cylinder.name = name + '_body'

    # Create the cone part
    cone_length = v.length*0.2
    bpy.ops.mesh.primitive_cone_add(
        radius1=0.05,
        radius2=0,
        depth=cone_length,
        enter_editmode=False)
    # bpy.ops.mesh.faces_shade_smooth()
    cone = bpy.context.active_object
    cone.location = vector_origin + (cyl_length + cone_length/2) * v.normalized()
    cone.rotation_mode = 'QUATERNION'
    cone.rotation_quaternion = rot
    if name is not None:
        cone.name = name + '_head'

    # Create the material
    if name is None:
        arrow_mat = create_solid_material(color)
    else:
        arrow_mat = create_solid_material(color, name=name + '_color')

    cylinder.data.materials.append(arrow_mat)
    cone.data.materials.append(arrow_mat)

    return (cylinder, cone)

def add_line(start: np.ndarray,
             end: np.ndarray,
             thickness: float = 0.1,
             name: Optional[str] = None,
             color: tuple = (1, 0, 0, 1.0),
             material: Optional[bpy.types.Material] = None,
             subdivisions: int = 20) -> bpy.types.Object:
    """Add a line to the scene.

    Args:
        origin (np.ndarray): Origin of the line.
        end (np.ndarray): End of the line.
        thickness (float): Thickness of the line.
        name (Optional[str]): Name of the line.
        color (tuple): Color of the line.

    Returns:
        bpy.types.Object: The line.
    """

    start = np.asarray(start)
    end = np.asarray(end)

    if start.size == 2:
        start = np.append(start, 0)
    if end.size == 2:
        end = np.append(end, 0)

    # create a plane object
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False)  # Volume prevents merging issues
    line = bpy.context.active_object

    me = line.data
    # New bmesh
    bm = bmesh.new()
    # load the mesh
    bm.from_mesh(me)

    # subdivide

    bmesh.ops.subdivide_edges(bm,
                              edges=bm.edges,
                              cuts=subdivisions,
                              use_grid_fill=True,
                              )

    # Write back to the mesh

    bm.to_mesh(me)
    me.update()

    # strech the object to the desired size
    line_length = np.linalg.norm(end - start)
    line.scale = (line_length, thickness, 0.001)

    # rotate the object to the desired orientation
    up = mathutils.Vector((1,0,0))
    rot = up.rotation_difference(end - start)
    line.rotation_mode = 'QUATERNION'
    line.rotation_quaternion = rot


    # move the object to the desired location
    line.location = (start + end) / 2

    # fix this orientation as the default
    mb = line.matrix_basis
    if hasattr(line.data, "transform"):
        line.data.transform(mb)
    for c in line.children:
        c.matrix_local = mb @ c.matrix_local
    line.matrix_basis.identity()

    # create the material
    if material is None:
        if name is None:
            line_mat = create_solid_material(color)
        else:
            line_mat = create_solid_material(color, name=name + '_color')
    else:
        line_mat = material

    line.data.materials.append(line_mat)

    return line

def merge_meshes(meshes: List[bpy.types.Object]) -> bpy.types.Object:
    """Merge a list of meshes into one.

    Args:
        meshes (List[bpy.types.Object]): List of meshes to merge.

    Returns:
        bpy.types.Object: The merged mesh.
    """

    # get objecs names
    meshes_names = [obj.name for obj in meshes]

    # Deselect all meshes
    bpy.ops.object.select_all(action='DESELECT')

    for o in bpy.data.objects:
        # Check for given object names
        if o.name in meshes_names:
            o.select_set(True)

    # Select all meshes
    bpy.ops.object.join()
    merged_mesh = bpy.context.active_object

    return merged_mesh

def draw_grid(x_lim: Tuple[float, float],
              y_lim: Tuple[float, float],
              main_subdivision: float = 1,
              minor_subdivision: float = 0.5) -> bpy.types.Object:
    """Draw a grid on the scene.

    Args:
        x_lim (Tuple[float, float]): X-axis limits.
        y_lim (Tuple[float, float]): Y-axis limits.
        main_subdivision (float): Main subdivision.
        minor_subdivision (float): Minor subdivision.

    Returns:
        bpy.types.Object: The grid.
    """
    MAIN_THICKNESS = 0.02
    MINOR_THICKNESS = 0.01
    MAJOR_COLOR = (0.5, 0.5, 0.5, 1.0)
    MINOR_COLOR = (0.5, 0.5, 0.5, 0.5)

    x_lim = np.asarray(x_lim)
    y_lim = np.asarray(y_lim)

    # Prevent coplanar mesh weirdness in cycles
    random_z = lambda z: z + (1-2*np.random.rand()) * 0.0001

    # Create the minor grid
    minor_grid_lines = []

    # create materials
    minor_grid_mat = create_solid_material(MINOR_COLOR)
    major_grid_mat = create_solid_material(MAJOR_COLOR)

    x_minor_n_subdivisions = int(np.ceil((x_lim[1] - x_lim[0]) / minor_subdivision))
    for x in np.linspace(x_lim[0], x_lim[1], x_minor_n_subdivisions + 1):
        # if not in major grid
        if x % main_subdivision != 0:
            line = add_line((x, y_lim[0], random_z(-0.001)),
                            (x, y_lim[1], random_z(-0.001)),
                            name=f'grid_x_minor{x}',
                            thickness=MINOR_THICKNESS,
                            material=minor_grid_mat)
            minor_grid_lines.append(line)

    y_minor_n_subdivisions = int(np.ceil((y_lim[1] - y_lim[0]) / minor_subdivision))
    for y in np.linspace(y_lim[0], y_lim[1], y_minor_n_subdivisions + 1):
        # if not in major grid
        if y % main_subdivision != 0:
            line = add_line((x_lim[0], y, random_z(-0.001)),
                            (x_lim[1], y, random_z(-0.001)),
                            name=f'grid_y_minor{y}',
                            thickness=MINOR_THICKNESS,
                            material=minor_grid_mat)
            minor_grid_lines.append(line)

    # Create the grid
    major_grid_lines = []

    x_major_n_subdivisions = int(np.ceil((x_lim[1] - x_lim[0]) / main_subdivision))
    for x in np.linspace(x_lim[0], x_lim[1], x_major_n_subdivisions + 1):
        line = add_line((x, y_lim[0], random_z(0)),
                        (x, y_lim[1], random_z(0)),
                        name='grid_x',
                        thickness=MAIN_THICKNESS,
                        material=major_grid_mat)
        major_grid_lines.append(line)

    y_major_n_subdivisions = int(np.ceil((y_lim[1] - y_lim[0]) / main_subdivision))
    for y in np.linspace(y_lim[0], y_lim[1], y_major_n_subdivisions + 1):
        line = add_line((x_lim[0], y, random_z(0)),
                        (x_lim[1], y, random_z(0)),
                        name='grid_y',
                        thickness=MAIN_THICKNESS,
                        material=major_grid_mat)
        major_grid_lines.append(line)

    # Merge the grids
    return major_grid_lines , minor_grid_lines

def main():

    # parse the CLI arguments
    args = parse_args()

    CYCLES = args.cycles
    EEVEE = args.eevee

    # Create the scene
    scene, camera = create_2d_scene(X_LIM, Y_LIM)

    origin = np.array([0, 0, 0])

    t_start = time.time()
    vector = np.array([1, 0, 0])
    x_axis = add_arrow(origin, vector,
                    name = 'x_axis',
                    color = (1, 0, 0, 1.0))

    vector = np.array([0, 1, 0])
    y_axis = add_arrow(origin, vector,
                    name = 'y_axis',
                    color = (0, 1, 0, 1.0))
    print(f'Time to create axes: {time.time() - t_start}')

    set_pastel_background(scene, BG_COLOR)

    resolution_x = int(DPI * (X_LIM[1] - X_LIM[0]) / 2)
    resolution_y = int(DPI * (Y_LIM[1] - Y_LIM[0]) / 2)


    # Create the grid
    t_start = time.time()
    grids = draw_grid(X_LIM, Y_LIM, main_subdivision=1, minor_subdivision=0.1)
    print(f'Time to draw grid: {time.time() - t_start}')

    # get grid vertices
    t_start = time.time()
    for grid in grids:
        for line in grid:
            me = line.data
            mat = line.matrix_world
            me.transform(mat)

            for vert in me.vertices:
                new_location = vert.co
                new_location[1] = new_location[0] * np.sign(new_location[1])
                vert.co = new_location

            line.matrix_world = mathutils.Matrix()

    print(f'Time to apply transofmation: {time.time() - t_start}')




    if CYCLES:
        cycles_render(scene, "renders/cycles/arrow.png", use_gpu=True, resolution_x=1080, resolution_y=1080)
    elif EEVEE:
        eevee_render(scene, "renders/eevee/arrow.png", resolution_x=resolution_x, resolution_y=resolution_y)
    else:
        workbench_render(scene, "renders/workbench/arrow.png", resolution_x=resolution_x, resolution_y=resolution_y)

    # IMPOTANT: Close blender when done
    bpy.ops.wm.quit_blender()


if __name__ == '__main__':
    main()
