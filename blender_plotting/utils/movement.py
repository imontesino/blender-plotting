"""Utility functions to move objects in the scene."""

from typing import Optional, Union

import bpy
from mathutils import Matrix
import numpy as np
import quaternion as quat

ROTATION_TYPES = [
    'quaternion',
    'euler_ZYZ',
    'rot_mat',
    'rot_vec'
]

def rigid_movement(obj: bpy.types.Object,
                   rotation: Optional[tuple] = None,
                   translation: Optional[tuple] = None,
                   rot_type='quaternion',):
    """Rotate an object around an axis.

    Args:
        obj (bpy_types.Object): Object to rotate.
        rotation (Optional[tuple]): Rotation to apply.
        translation (Optional[tuple]): Translation to apply.
        rot_type (str): Rotation type. One of 'quaternion', 'euler_ZYZ', 'rot_mat', 'rot_vec'.
    """

    if rotation is not None:
        if rot_type == 'quaternion':
            q_rot = quat.from_float_array(rotation)
        elif rot_type == 'euler_ZYZ':
            q_rot = quat.from_euler_angles(rotation)
        elif rot_type == 'rot_mat':
            q_rot = quat.from_rotation_matrix(rotation)
        elif rot_type == 'rot_vec':
            q_rot = quat.from_rotation_vector(rotation)
        else:
            raise ValueError(f'rot_type must be one of: {ROTATION_TYPES}')

        axis_angle = quat.as_rotation_vector(q_rot)
        rot_angle = np.linalg.norm(axis_angle)
        rot_axis = axis_angle / rot_angle

        # define some rotation
        rot_mat = Matrix.Rotation(rot_angle, 4, rot_axis)
    else:
        rot_mat = Matrix.Identity(4)

    if translation is not None:
        loc_mat = Matrix.Translation(translation)
    else:
        loc_mat = Matrix.Identity(4)


    # decompose world_matrix's components, and from them assemble 4x4 matrices
    orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
    orig_loc_mat = Matrix.Translation(orig_loc)
    orig_rot_mat = orig_rot.to_matrix().to_4x4()
    x_scaling = Matrix.Scale(orig_scale[0],4,(1,0,0))
    y_scaling = Matrix.Scale(orig_scale[1],4,(0,1,0))
    z_scaling = Matrix.Scale(orig_scale[2],4,(0,0,1))
    orig_scale_mat = x_scaling @ y_scaling @ z_scaling

    # assemble the new matrix
    obj.matrix_world = (loc_mat @ orig_loc_mat) @ (rot_mat @ orig_rot_mat) @ orig_scale_mat

def rotate_around_axis(obj: bpy.types.Object,
                       axis: Union[str, tuple],
                       angle: float,):
    """Rotate an object around a global axis.

    Args:
        obj (bpy_types.Object): Object to rotate.
        axis (Union[str, tuple]): Axis to rotate around. as a vector or 'X', 'Y', 'Z'.
        angle (float): Radians to rotate by.
    """

    # define some rotation
    rot_mat = Matrix.Rotation(angle, 4, axis)   # you can also use as axis Y,Z or a custom vector like (x,y,z)

    # decompose world_matrix's components, and from them assemble 4x4 matrices
    orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
    orig_loc_mat = Matrix.Translation(orig_loc)
    orig_rot_mat = orig_rot.to_matrix().to_4x4()
    orig_scale_mat = Matrix.Scale(orig_scale[0],4,(1,0,0)) * Matrix.Scale(orig_scale[1],4,(0,1,0)) @ Matrix.Scale(orig_scale[2],4,(0,0,1))

    # assemble the new matrix
    obj.matrix_world = rot_mat @ orig_loc_mat @ orig_rot_mat @ orig_scale_mat

def set_world_pose(obj: bpy.types.Object,
                   rotation: Optional[tuple] = None,
                   translation: Optional[tuple] = None,
                   rot_type: str = 'quaternion',
                   scale: Optional[tuple] = None,):
    """Set the absoulte world pose of an object.

    If a field is not given the object's current value for that field is used.

    Args:
        obj (bpy_types.Object): Object to rotate.
        rotation (Optional[tuple]): Rotation to apply.
        translation (Optional[tuple]): Translation to apply.
        rot_type (str): Rotation type. One of 'quaternion', 'euler_ZYZ', 'rot_mat', 'rot_vec'.
        scale (Optional[tuple]): Scale to apply.
    """
    orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()

    if rotation is not None:
        if rot_type == 'quaternion':
            q_rot = quat.from_float_array(rotation)
        elif rot_type == 'euler_ZYZ':
            q_rot = quat.from_euler_angles(rotation)
        elif rot_type == 'rot_mat':
            q_rot = quat.from_rotation_matrix(rotation)
        elif rot_type == 'rot_vec':
            q_rot = quat.from_rotation_vector(rotation)
        else:
            raise ValueError(f'rot_type must be one of: {ROTATION_TYPES}')

        axis_angle = quat.as_rotation_vector(q_rot)
        rot_angle = np.linalg.norm(axis_angle)
        rot_axis = axis_angle / rot_angle

        # define some rotation
        rot_mat = Matrix.Rotation(rot_angle, 4, rot_axis)
    else:
        rot_mat = orig_rot.to_matrix().to_4x4()

    if translation is not None:
        loc_mat = Matrix.Translation(translation)
    else:
        loc_mat = Matrix.Translation(orig_loc)

    if scale is not None:
        x_scaling = Matrix.Scale(scale[0],4,(1,0,0))
        y_scaling = Matrix.Scale(scale[1],4,(0,1,0))
        z_scaling = Matrix.Scale(scale[2],4,(0,0,1))
        scale_mat = x_scaling @ y_scaling @ z_scaling
    else:
        # decompose world_matrix's components, and from them assemble 4x4 matrices
        x_scaling = Matrix.Scale(orig_scale[0],4,(1,0,0))
        y_scaling = Matrix.Scale(orig_scale[1],4,(0,1,0))
        z_scaling = Matrix.Scale(orig_scale[2],4,(0,0,1))
        scale_mat = x_scaling @ y_scaling @ z_scaling

    # assemble the new matrix
    obj.matrix_world = loc_mat @ rot_mat @ scale_mat
