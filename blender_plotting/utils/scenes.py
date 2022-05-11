from typing import Iterable

import bpy
import numpy as np
from mathutils import Vector

from .camera import add_camera
from .utils import clean_objects


def create_2d_scene(x_lim: Iterable[float],
                    y_lim: Iterable[float],
                    fov: float = 45.0,
                    light_energy: float = 2.0) -> bpy.types.Scene:
    """Create a 2D scene.

    Delete all objects and create a new scene.
    """
    clean_objects()

    scene = bpy.context.scene

    diagonal = (x_lim[1] - x_lim[0])**2 + (y_lim[1] - y_lim[0])**2

    camera_height = diagonal / (2 * np.tan(fov / 2.0))

    # add a camera pointing down
    camera = add_camera("main_camera",
                        location=(0, 0, camera_height),
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
