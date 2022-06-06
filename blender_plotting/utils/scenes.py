from typing import Iterable, Tuple

import bpy
import numpy as np

from .camera import add_camera
from .utils import clean_objects
from .shapes import draw_arrow

def draw_xy_axes(axes_length: float = 1.0,
                 origin: Tuple[float, float, float] = (0, 0, 0)):

    origin = np.array([0, 0, 0])

    vector = np.array([1, 0, 0]) * axes_length
    x_axis = draw_arrow(origin, vector,
                       name = 'x_axis',
                       color = (1, 0, 0, 1.0))

    vector = np.array([0, 1, 0]) * axes_length
    y_axis = draw_arrow(origin, vector,
                       name = 'y_axis',
                       color = (0, 1, 0, 1.0))

    return x_axis, y_axis

def draw_xyz_axes(axes_length: float = 1.0,
                  origin: Tuple[float, float, float] = (0, 0, 0)):

    origin = np.array([0, 0, 0])

    vector = np.array([1, 0, 0]) * axes_length
    x_axis = draw_arrow(origin, vector,
                       name = 'x_axis',
                       color = (1, 0, 0, 1.0))

    vector = np.array([0, 1, 0]) * axes_length
    y_axis = draw_arrow(origin, vector,
                       name = 'y_axis',
                       color = (0, 1, 0, 1.0))

    vector = np.array([0, 0, 1]) * axes_length
    z_axis = draw_arrow(origin, vector,
                       name = 'z_axis',
                       color = (0.3, 0.3, 1, 1.0))

    return x_axis, y_axis, z_axis

def create_2d_scene(x_lim: Iterable[float],
                    y_lim: Iterable[float],
                    fov: float = 45.0,
                    margin: float = 0.1,
                    light_energy: float = 2.0) -> Tuple[bpy.types.Scene, bpy.types.Camera]:
    """Create a 2D scene.

    Delete all objects and create a new scene.
    """
    clean_objects()

    scene = bpy.context.scene

    diagonal = np.sqrt( (x_lim[1] - x_lim[0])**2 + (y_lim[1] - y_lim[0])**2 )

    camera_height = diagonal / (2 * np.tan(fov / 2.0)) * 1.1  # 10% margin

    center = (x_lim[0] + x_lim[1]) / 2.0, (y_lim[0] + y_lim[1]) / 2.0

    # add a camera pointing down
    camera = add_camera("main_camera",
                        location=(center[0], center[1], camera_height),
                        fov=fov,
                        rotation=(0, 0, 0),
                        scene=scene)

    # add a sun light pointing down

    # Create light datablock
    light_data = bpy.data.lights.new(name="Sun-light-data", type='SUN')

    # Create new object, pass the light data
    light_object = bpy.data.objects.new(name="Sun-light-object", object_data=light_data)

    # Link object to collection in context
    bpy.context.collection.objects.link(light_object)

    # point down
    light_object.rotation_euler = (0, 0, 0)

    # less power
    light_data.energy = light_energy

    return scene, camera


def create_3d_scene(x_lim: Tuple[float],
                    y_lim: Tuple[float],
                    z_lim: Tuple[float],
                    light_energy: float = 1.0) -> Tuple[bpy.types.Scene, bpy.types.Camera]:
    """Create a 3D scene.

    Delete all objects and create a new scene.
    """
    clean_objects()

    # FOV = 2 arctan (d / (2 f))
    fov = 45.0
    # d = 35*0.001  # 35 mm
    # focal_length = 1/2 * np.tan(np.deg2rad(fov)/2) * d

    scene = bpy.context.scene


    center = (x_lim[0] + x_lim[1]) / 2.0, (y_lim[0] + y_lim[1]) / 2.0, (z_lim[0] + z_lim[1]) / 2.0

    # r: radius
    # theta: (90 - theta) from z axis
    # gamma: angle from x axis
    s2c = lambda r, theta, gamma : np.array([
        r * np.cos(gamma) * np.cos(theta),
        r * np.sin(gamma) * np.cos(theta),
        r * np.sin(theta)
    ])

    # TODO Make camera distance dependent on the scene size
    camera_distance = 8.0

    # Camera position
    camera_theta = np.radians(20)
    camera_gamma = np.radians(20)

    # lighting position
    theta_offs = np.radians(25)
    gamma_offs = np.radians(30)

    camera_offset = s2c(camera_distance, camera_theta, camera_gamma)

    camera_location = np.asarray(center) + camera_offset


    # add a camera pointing down
    camera = add_camera("main_camera",
                        location=camera_location,
                        fov=fov,
                        track_to=center,
                        scene=scene)

    # projection_matrix = get_perspective(camera)

    # add two area lights

    light_energies = np.array([4000, 1000, 1000]) * light_energy
    for i in range(2):
        light_name = f'point-light-{i}'
        # Create light datablock
        light_data = bpy.data.lights.new(name=light_name+"-data", type='POINT')
        light_data.energy = light_energies[i]

        # Create new object, pass the light data
        light_object = bpy.data.objects.new(name=light_name+"-object", object_data=light_data)

        # Link object to collection in context
        bpy.context.collection.objects.link(light_object)

        position = s2c(camera_distance, camera_theta+theta_offs, camera_gamma+gamma_offs*(-(-1)**i))

        light_object.location = position

    return scene, camera
