import argparse
from typing import Callable, Tuple, List

import bpy
import numpy as np

from blender_plotting.utils.background import set_pastel_background
from blender_plotting.utils.materials import create_solid_material
from blender_plotting.utils.renderers import cycles_render, eevee_render, workbench_render
from blender_plotting.utils.scenes import create_2d_scene
from blender_plotting.utils.shapes import add_arrow

def parse_args():
    parser = argparse.ArgumentParser(description='Draw a R2 plane.')
    parser.add_argument('--cycles', action='store_true', help='Use Cycles.')
    parser.add_argument('--eevee', action='store_true', help='Use Eevee.')

    args = parser.parse_args()
    return args

def draw_xy_axes(axes_length: float = 1.0,
                 origin: Tuple[float, float, float] = (0, 0, 0)):

    origin = np.array([0, 0, 0])

    vector = np.array([1, 0, 0]) * axes_length
    x_axis = add_arrow(origin, vector,
                    name = 'x_axis',
                    color = (1, 0, 0, 1.0))

    vector = np.array([0, 1, 0]) * axes_length
    y_axis = add_arrow(origin, vector,
                    name = 'y_axis',
                    color = (0, 1, 0, 1.0))


    return x_axis, y_axis

def draw_function(f: Callable[[float], float],
                  x_min: float = -1,
                  x_max: float = 1,
                  control_points: int = 10,
                  thickness: float = 0.01) -> bpy.types.Object:
    """Creates a curve following the function f.

    Args:
        f (Callable[[float], float]): Function to draw.
        x_min (float): Minimum x value.
        x_max (float): Maximum x value.

    Returns:
        bpy.types.Object: The curve.
    """

    coords_list = [[x, f(x), 0] for x in np.linspace(x_min, x_max, control_points)]

    curve_data = bpy.data.curves.new('crv', 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.use_fill_caps = True
    curve_data.bevel_mode = 'ROUND'     # Gives it a circle shape without needing another object as a profile.
    curve_data.bevel_depth = thickness

    spline = curve_data.splines.new(type='POLY')
    spline.points.add(len(coords_list) - 1)
    for p, new_co in zip(spline.points, coords_list):
        p.co = (new_co + [1.0])  # (add nurbs
    curve = bpy.data.objects.new('object_name', curve_data)
    bpy.data.scenes[0].collection.objects.link(curve)


    return curve

def draw_points(points: List[Tuple[float, float, float]],
                color: Tuple[float, float, float, float] = (1, 0, 0, 1.0),
                radius: float = 0.05):
    """Draws a list of points.

    Args:
        points (List[Tuple[float, float, float]]): List of points.
        color (Tuple[float, float, float, float]): Color of the points.
        radius (float): Radius of the points.

    Returns:
        List[bpy.types.Object]: List of points.
    """

    points_objs = []

    for point in points:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=point)
        points_objs.append(bpy.context.object)
        bpy.context.object.data.materials.append(create_solid_material(color))

    return points_objs

def draw_line(points: List[Tuple[float, float, float]],
              color: Tuple[float, float, float, float] = (1, 0, 0, 1.0),
              thickness: float = 0.01,
              draw_markers: bool = False,
              marker_radius: float = 0.05,
              draw_line: bool = True):
    """Draws a line along a list of points.

    Args:
        points (List[Tuple[float, float, float]]): List of points.
        color (Tuple[float, float, float, float]): Color of the line.
            Defaults to (1, 0, 0, 1.0).
        thickness (float): Thickness of the line. Defaults to 0.01.
        draw_markers (bool): Whether to draw markers at the points.
            Defaults to False.
        marker_radius (float): Radius of the markers. Defaults to 0.05.
        draw_line (bool): Whether to draw the line. Defaults to True.

    Returns:
        bpy.types.Object: The line.
    """

    if draw_line:
        curve_data = bpy.data.curves.new('crv', 'CURVE')
        curve_data.dimensions = '3D'
        curve_data.use_fill_caps = True
        curve_data.bevel_mode = 'ROUND'     # Gives it a circle shape without needing another object as a profile.
        curve_data.bevel_depth = thickness

        spline = curve_data.splines.new(type='POLY')
        spline.points.add(len(points) - 1)
        for p, new_co in zip(spline.points, points):
            p.co = (new_co + [1.0])
        curve = bpy.data.objects.new('object_name', curve_data)
        curve.data.materials.append(create_solid_material(color))
        bpy.data.scenes[0].collection.objects.link(curve)

    if draw_markers:
        for point in points:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=marker_radius, location=point)
            bpy.context.object.data.materials.append(create_solid_material(color))


def main():
    args = parse_args()

    # Create a new scene
    scene, camera = create_2d_scene([-3,3], [-3,3])

    # Set the background to a pastel color
    set_pastel_background(scene, )

    # Draw the axes
    x_axis, y_axis = draw_xy_axes()

    f = lambda x: 1.5 * np.sin(10*x) /9



    # Draw the function
    curve = draw_function(f, -3, 3, control_points=200)

    # Draw the points
    points = draw_points([(x, f(x), 0) for x in np.linspace(-3, 3, 5)], (0, 1, 0, 1.0))


    print(points[0].material_slots[0].material)
    mat_nodes = points[0].material_slots[0].material.node_tree.nodes
    print(mat_nodes)

    for node in mat_nodes:
        if node.name == "Image Texture":
            print(node.image)


    # Render the scene
    imf_filename = 'draw_function.png'
    if args.cycles:
        cycles_render(scene, imf_filename)
    elif args.eevee:
        eevee_render(scene, imf_filename)
    else:
        workbench_render(scene, imf_filename)

    # Close blender
    bpy.ops.wm.quit_blender()


if __name__ == '__main__':
    main()
