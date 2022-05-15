import argparse
import subprocess
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
            line = draw_line((x, y_lim[0], random_z(-0.001)),
                             color=MINOR_COLOR)
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
    args = parse_args()

    FPS = 60
    DURATION = 10
    TOTAL_FRAMES =  FPS * DURATION

    # Plot limits
    x_min = -3
    x_max = 3
    y_min = -3
    y_max = 3


    # Create a new scene
    scene, camera = create_2d_scene([x_min, x_max], [y_min, y_max])

    # Create the axes
    x_axis, y_axis = draw_xy_axes(axes_length=1.0)

    # Create the function
    f = lambda x: (x/3)**2

    # Draw the function
    curve = draw_function(f, x_min, x_max, control_points=100)

    # draw sphere
    sphere = draw_points([(x_min, f(x_min), 0)], color=(1, 1, 0, 1.0), radius=0.05)[0]

    # Keyframes
    set_animation(scene,
                  fps=FPS,
                  frame_start=1,
                  frame_end=TOTAL_FRAMES,
                  frame_current=1,
                  file_extension='AVI_JPEG')


    x_length = x_max - x_min
    for i in range(1, TOTAL_FRAMES+1):
        t = (i-1) / TOTAL_FRAMES
        if t < 0.5:
            x = x_min + t ** 2 * x_length / 2
        if t >= 0.5:
            x = x_min + (1 - (t-0.5) ** 2) * x_length / 2
        sphere.location = (x_min + t * x_length, f(x_min + t * x_length), 0)
        print(f" frame {i}: t = {t}, location = {sphere.location}")
        sphere.keyframe_insert(data_path='location', frame=i)



    # Render the scene
    imf_filename = 'animate_transform'
    if args.cycles:
        cycles_render(scene, imf_filename, animation=True)
    elif args.eevee:
        eevee_render(scene, imf_filename, animation=True)
    else:
        workbench_render(scene, imf_filename, animation=True)

    # avi to mp4
    bashCommand = f"ffmpeg -i {scene.render.filepath} -vcodec libx264 -crf 25 -pix_fmt yuv420p -y {imf_filename}.mp4"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    # Close blender
    bpy.ops.wm.quit_blender()



if __name__ == '__main__':
    main()
