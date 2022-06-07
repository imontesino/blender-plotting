import argparse
from typing import Callable, List, Tuple

import bpy
import numpy as np

from blender_plotting.utils.background import set_solid_color_background
from blender_plotting.utils.curves import draw_parametric_curve
from blender_plotting.utils.materials import create_solid_material
from blender_plotting.utils.renderers import (cycles_render, eevee_render,
                                              workbench_render)
from blender_plotting.utils.scenes import create_2d_scene
from blender_plotting.utils.shapes import draw_points


def parse_args():
    parser = argparse.ArgumentParser(description='Draw a R2 plane.')
    parser.add_argument('--cycles', action='store_true', help='Use Cycles.')
    parser.add_argument('--eevee', action='store_true', help='Use Eevee.')

    args = parser.parse_args()
    return args

def lerp(a: np.ndarray, b: np.ndarray, t: np.ndarray)  -> np.ndarray:
    return (1-t)*a+t*b

def bezierN(points,t) -> np.ndarray:
    points = np.asarray(points)
    if len(points) == 1:
        return points[0]
    if len(points)==2:
        return lerp(points[0],points[1],t)
    else:
        return lerp(bezierN(points[:-1],t),bezierN(points[1:],t),t)

def bezier_curve_manim(points: np.ndarray , t: float) -> np.ndarray:
    return bezierN(points,t).tolist()+[0]

L = 4  # Scale factor

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

def set_animation(scene: bpy.types.Scene,
                  fps: int = 24,
                  frame_start: int = 1,
                  frame_end: int = 48,
                  frame_current: int = 1,
                  file_extension: str = 'FFMPEG') -> None:
    scene.render.fps = fps
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    scene.frame_current = frame_current
    scene.render.image_settings.file_format = file_extension
    if file_extension == 'FFMPEG':
        scene.render.ffmpeg.codec = 'H264'

def main():
    args = parse_args()

    FPS = 60
    DURATION = 15
    TOTAL_FRAMES =  FPS * DURATION

    # Plot limits
    x_min = -3
    x_max = 3
    y_min = -3
    y_max = 3


    # Create a new scene
    scene, _ = create_2d_scene([x_min, x_max], [y_min, y_max])

    set_solid_color_background(scene, (1.0, 1.0, 1.0, 1.0))

    # Create the Bezier Control points
    control_points = [[-1,  0, 0],
                      [-1,  1, 0],
                      [ 1,  1, 0],
                      [ 1,  0, 0]]

    # Draw the First level lerps
    for i in range(len(control_points) - 1):
        draw_line([control_points[i], control_points[i + 1]],
                  color=(0.6, 0.6, 1.0, 1.0),
                  thickness=0.01,
                  draw_markers=False,
                  marker_radius=0.05,
                  draw_line=True)

    draw_points(control_points, color=(0.6, 0.6, 1.0, 1.0), radius=0.05)


    f = lambda t: bezierN(control_points, t)

    print(f"f(0) = {f(0)}")
    print(f"f(1) = {f(1)}")


    # # Draw the function
    draw_parametric_curve(f, resolution=100)

    # Render the scene
    imf_filename = 'draw_bezier_r2'
    folder = 'renders/'
    if args.cycles:
        cycles_render(scene, folder+'cycles/'+imf_filename, animation=False)
    elif args.eevee:
        eevee_render(scene, folder+'eevee/'+imf_filename, animation=False)
    else:
        workbench_render(scene, folder+'workbench/'+imf_filename, animation=False)

    # Close blender
    bpy.ops.wm.quit_blender()



if __name__ == '__main__':
    main()
