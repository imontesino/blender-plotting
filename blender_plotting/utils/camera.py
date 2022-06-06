""" Conveniance functions for camera """

import math
from typing import Iterable, Optional, Tuple, Union

import bpy
import mathutils

def add_camera(name: str,
               location: tuple,
               fov: float,
               rotation: tuple = (0, 0, 0),
               track_to: Optional[Union[bpy.types.Object, Tuple[float,float,float]]] = None,
               scene: Optional[bpy.types.Scene] = None) -> bpy.types.Object:
    """Add a camera to the scene.

    Args:
        name (str): The name of the camera.
        location (tuple): The location of the camera.
        fov (float): The field of view of the camera.
        aspect_ratio (float): The aspect ratio of the camera.
        rotation (tuple, optional): The rotation of the camera. Defaults to (0, 0, 0).
        track_to (Optional[Union[bpy.types.Object, Tuple[float,float,float]]], optional):
            Point the camera to a bpy.types.Object or a position in 3d space. Overrides rotation.
            Defaults to None.
        scene (Optional[bpy.types.Scene], optional): The scene to add the camera to.

    Returns:
        bpy.types.Object: The camera object.
    """
    # we first create the camera object
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    cam.location = location
    cam.rotation_euler = rotation
    cam.data.lens_unit = 'FOV'
    cam.data.angle = math.radians(fov)

    if track_to is not None:
        if isinstance(track_to, bpy.types.Object):
            constraint = cam.constraints.new(type='TRACK_TO')
            constraint.target=track_to
        else:
            point_at(cam, track_to)

    if scene is not None:
        # add camera to scene
        scene = bpy.context.scene
        scene.camera = cam

    return cam

def point_at(obj: bpy.types.Object,
             target: Union[bpy.types.Object, Iterable[float]],
             roll=0):
    """
    Rotate obj to look at target

    :arg obj: the object to be rotated. Usually the camera
    :arg target: the location (3-tuple or Vector) to be looked at
    :arg roll: The angle of rotation about the axis from obj to target in radians.

    Based on: https://blender.stackexchange.com/a/5220/12947 (ideasman42)
    """
    if isinstance(target, bpy.types.Object):
        target = mathutils.Vector(target.matrix_world.to_translation())
    else:
        target = mathutils.Vector(target)

    loc = obj.location
    # direction points from the object to the target
    direction = target - loc

    # because new cameras points down(-Z), usually meshes point (-Y)
    tracker, rotator = (('-Z', 'Y'),'Z') if obj.type=='CAMERA' else (('X', 'Z'),'Y')
    quat = direction.to_track_quat(*tracker)

    # /usr/share/blender/scripts/addons/add_advanced_objects_menu/arrange_on_curve.py
    quat = quat.to_matrix().to_4x4()
    roll_matrix = mathutils.Matrix.Rotation(roll, 4, rotator)

    # remember the current location, since assigning to obj.matrix_world changes it
    loc = loc.to_tuple()
    #obj.matrix_world = quat * rollMatrix
    # in blender 2.8 and above @ is used to multiply matrices
    # using * still works but results in unexpected behaviour!
    obj.matrix_world = quat @ roll_matrix
    obj.location = loc

def get_perspective(camera):
    """Compute projection matrix of blender camera.

    Arguments:
        camera {bpy.types.Camera} -- Blender camera.

    Returns:
        mathutils.Matrix -- Projection matrix.
    """
    return camera.calc_matrix_camera(
        depsgraph=bpy.context.evaluated_depsgraph_get(),
        x=bpy.context.scene.render.resolution_x,
        y=bpy.context.scene.render.resolution_y,
        scale_x=bpy.context.scene.render.pixel_aspect_x,
        scale_y=bpy.context.scene.render.pixel_aspect_y)
