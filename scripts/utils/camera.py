""" Conveniance functions for camera """

import math
from typing import Optional

import bpy
import mathutils
import numpy as np


def add_camera(name: str,
               location: tuple,
               fov: float,
               track_to: Optional[bpy.types.Object] = None,
               scene: Optional[bpy.types.Scene] = None) -> bpy.types.Object:
    """Add a camera to the scene.

    Args:
        name (str): The name of the camera.
        location (tuple): The location of the camera.
        fov (float): The field of view of the camera.
        aspect_ratio (float): The aspect ratio of the camera.
        track_to (Optional[bpy.types.Object], optional): The object to track.
        scene (Optional[bpy.types.Scene], optional): The scene to add the camera to.

    Returns:
        bpy.types.Object: The camera object.
    """
    # we first create the camera object
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    cam.location = location
    cam.data.lens_unit = 'FOV'
    cam.data.angle = math.radians(fov)

    if track_to is not None:
        # track the cube with the camera
        constraint = cam.constraints.new(type='TRACK_TO')
        constraint.target=track_to

    if scene is not None:
        # add camera to scene
        scene = bpy.context.scene
        scene.camera = cam

    return cam

def point_at(obj: bpy.types.Object,
             target: bpy.types.Object,
             roll=0):
    """
    Rotate obj to look at target

    :arg obj: the object to be rotated. Usually the camera
    :arg target: the location (3-tuple or Vector) to be looked at
    :arg roll: The angle of rotation about the axis from obj to target in radians.

    Based on: https://blender.stackexchange.com/a/5220/12947 (ideasman42)
    """
    target = mathutils.Vector(target.matrix_world.to_translation())
    loc = obj.location
    # direction points from the object to the target
    direction = target - loc
    tracker, rotator = (('-Z', 'Y'),'Z') if obj.type=='CAMERA' else (('X', 'Z'),'Y') #because new cameras points down(-Z), usually meshes point (-Y)
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

def rotation_matrix(axis: tuple,
                    angle: float) -> mathutils.Matrix:
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(angle / 2.0)
    b, c, d = -axis * math.sin(angle / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])
