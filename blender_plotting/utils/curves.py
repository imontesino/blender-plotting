from typing import Callable, List, Tuple

import bpy
import numpy as np

from .materials import create_solid_material

def draw_polyline(points: List[Tuple[float, float, float]],
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
        Tupel[bpy.types.Object, bpy.types.Object]: The line and markers.
    """
    bpy_curve = None
    bpy_points = None

    if draw_line:
        curve_data = bpy.data.curves.new('crv', 'CURVE')
        curve_data.dimensions = '3D'
        curve_data.use_fill_caps = True
        curve_data.bevel_mode = 'ROUND'     # Gives it a circle shape without needing another object as a profile.
        curve_data.bevel_depth = thickness

        spline = curve_data.splines.new(type='POLY')
        spline.points.add(len(points) - 1)
        for p, new_co in zip(spline.points, points):
            p.co = (list(new_co) + [1.0])
        bpy_curve = bpy.data.objects.new('object_name', curve_data)
        bpy_curve.data.materials.append(create_solid_material(color))
        bpy.data.scenes[0].collection.objects.link(bpy_curve)

    if draw_markers:
        bpy_points = []
        for point in points:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=marker_radius, location=point)
            point = bpy.context.active_object
            point.data.materials.append(create_solid_material(color))
            bpy_points.append(point)

    return bpy_curve, bpy_points

def draw_function(f: Callable[[float], float],
                  x_min: float = -1,
                  x_max: float = 1,
                  resolution: int = 10,
                  thickness: float = 0.01,
                  color: Tuple[float, float, float, float] = (1, 0, 0, 1.0)) -> bpy.types.Object:
    """Creates a curve following the function f.

    Args:
        f (Callable[[float], float]): Function to draw.
        x_min (float): Minimum x value.
        x_max (float): Maximum x value.

    Returns:
        bpy.types.Object: The curve.
    """

    coords_list = [[x, f(x), 0] for x in np.linspace(x_min, x_max, resolution)]

    return draw_polyline(coords_list,
                         color=color,
                         thickness=thickness,
                         draw_markers=False,
                         draw_line=True)[0] # curve

def draw_parametric_curve(f: Callable[[float], np.ndarray],
                          t_min: float = 0.,
                          t_max: float = 1.,
                          resolution: int = 10,
                          color: Tuple[float, float, float, float] = (1, 0, 0, 1.0),
                          thickness: float = 0.01):
    """Draws a parametric curve.

    Args:
        f (Callable[[float], np.ndarray]): Parametric curve.
        t_min (float): Minimum t value.
        t_max (float): Maximum t value.
        resolution (int): Resolution of the curve. Defaults to 10.

    Returns:
        bpy.types.Object: The curve.
    """

    points_list = [list(f(t)) for t in np.linspace(t_min, t_max, resolution)]

    return draw_polyline(points_list,
                         color=color,
                         thickness=thickness,
                         draw_markers=False,
                         draw_line=True)[0] # curve
