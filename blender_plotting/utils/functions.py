from typing import Callable, Iterable, Tuple, Union

import bpy
import numpy as np

from .color_scale import ColorScale
from .curves import draw_polyline
from .shapes import draw_arrow

def draw_real_function(f: Callable[[float], float],
                       x_min: float = -1,
                       x_max: float = 1,
                       resolution: int = 10,
                       thickness: float = 0.01,
                       color: Iterable[float] = (1, 0, 0, 1.0)) -> bpy.types.Object:
    """Creates a curve following the function f(x) -> y.

    Args:
        f (Callable[[float], float]): Function to draw.
        x_min (float): Minimum x value.
        x_max (float): Maximum x value.
        resolution (int): Number of segments in the rendered curve.
        thickness (float): Thickness of the curve.
        color (Iterable[float,float,float,float]): Color of the curve.

    Returns:
        bpy.types.Object: The curve.
    """
    coords_list = [[x, f(x), 0] for x in np.linspace(x_min, x_max, resolution)]

    return draw_polyline(coords_list,
                         color=color,
                         thickness=thickness,
                         draw_markers=False,
                         draw_line=True)[0] # curve

def draw_vector_field(f: Callable[[float, float], Tuple[float, float]],
                      x_min: float = -1,
                      x_max: float = 1,
                      y_min: float = -1,
                      y_max: float = 1,
                      resolution: int = 1,
                      vector_length: float = 0.1,
                      vector_thickness: float = 2,
                      min_vector_magnitude: float = 0.01,
                      max_vector_magnitude: float = 1.0,
                      colors: Union[str, Iterable] = 'viridis') -> bpy.types.Object:
    """Draws a vector field.

    Args:
        f (Callable[[float, float], Tuple[float, float]]): Vector field.
        x_min (float): Minimum x value.
        x_max (float): Maximum x value.
        y_min (float): Minimum y value.
        y_max (float): Maximum y value.
        resolution (int): number of vectors per unit.


    Returns:
        bpy.types.Object: The curve.
    """
    color_scale = ColorScale(min_value=min_vector_magnitude,
                             max_value=max_vector_magnitude,
                             colors=colors)
    x_res = np.int(np.floor((x_max - x_min) * resolution))
    y_res = np.int(np.floor((y_max - y_min) * resolution))
    x_coords = np.linspace(x_min, x_max, x_res)
    y_coords = np.linspace(y_min, y_max, y_res)

    coords_list = [[x, y] for x in x_coords for y in y_coords]

    for origin in coords_list:
        origin = np.asarray(origin)
        vector = f(origin[0], origin[1])
        length = np.linalg.norm(vector)
        if length > min_vector_magnitude:
            color=[0,0,0,1]
            color[0], color[1], color[2]  = color_scale.get_color(length, ret_type='rgb')
            draw_arrow(origin, origin+vector*vector_length/length,
                      thickness=vector_thickness,
                      color=color)

