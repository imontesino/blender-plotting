""" Geometric functions for plotting. """

from typing import Tuple, Union
from mathutils import Matrix
import numpy as np
import quaternion as quat

ACCEPTED_ROT_TYPES = (
    'quaternion',
    'euler_ZYZ',
    'rot_vector',
    'axis_angle',
    'rot_mat',
    'matrix'
)

def so3_as_vector(so3_point: Matrix,
                  so3_origin: Matrix = Matrix.Identity(3),
                  scale: float = 1.0) -> Tuple[float, float, float]:
    """
    Returns the SO(3) point as a represented as a vector.

    Where the vector direction is the new z axis, and the vector length is the rotation around the new z axis.

    Args:
        so3_point (Matrix): SO(3) point.
        so3_origin (Matrix): SO(3) origin.

    Returns:
        Tuple[float, float, float]: Vector representation of the SO(3) point.

    """

    so3_origin = Matrix(so3_origin)
    so3_point = Matrix(so3_point)

    # Get the rot_vector beween the origin and the point
    z_origin = so3_origin.col[2]
    z_point = so3_point.col[2]

    rot_diff = z_point.rotation_difference(z_origin)

    # apply the rotation to the origin coordinate system
    rot_origin = so3_origin.to_3x3()
    rot_origin.rotate(rot_diff)

    # get the rotation beween either the old and the new x axis or the old and the new y axis
    x_origin = rot_origin.col[0]


    # Get the rotation matrix
    x_origin = so3_origin.col[2]
    x_point = so3_point.col[2]

    rot_diff = x_point.rotation_difference(x_origin)

    # transform to rotation vector
    rot_vector, rot_angle = rot_diff.to_axis_angle()

    return rot_vector * rot_angle * scale

def se3_as_vector(se3_point: Matrix,
                  se3_origin: Matrix = Matrix.Identity(4),
                  scale:float = 1.0) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """
    Returns the SE(3) point represented as a vector.

    Where the vector direction is the new z axis, and the vector length is the rotation around the new z axis.

    Args:
        se3_point (Matrix): SE(3) point.
        se3_origin (Matrix): SE(3) origin.

    Returns:
        Tuple[Tuple[float, float, float], Tuple[float, float, float]]: Vector representation of the SE(3) point, and
            its origin.
    """

    _        ,  orig_rot, _ = se3_origin.decompose()
    point_loc, point_rot, _ = se3_point.decompose()

    # get the so3 as vector
    rot_vector = so3_as_vector(point_rot.to_matrix(), orig_rot.to_matrix(), scale=scale)

    vector_origin = point_loc

    return rot_vector, vector_origin

def rot_diff(rot_a,
             rot_b,
             rot_type='quaternion'):
    """
    Returns the rotation difference between two rotation matrices.

    Args:
        rot_a (Matrix): First rotation matrix.
        rot_b (Matrix): Second rotation matrix.

    Returns:
        Rotation difference.

    """

    q_a: quat.quaternion = to_quaternion(rot_a, type='quat')
    q_b: quat.quaternion = to_quaternion(rot_b, type='quat')

    q_diff = q_a * q_b.conjugate()

    return as_rot_type(q_diff, rot_type)

def to_quaternion(rot, type='tuple') -> Union[Tuple[float, float, float, float], quat.quaternion]:
    """
    Tries to identify teh rotation type and returns the quaternion representation.

    Args:
        rot: rotation as a matrix (3x3 or 4x4), euler_ZYZ, rot_vectoror axis_angle.
        type: return quaternion as a tuple or a numpy-quaternion object.

    Returns:
        Tuple[float, float, float, float]: Quaternion representation of the rotation matrix.

    """

    if len(rot) == 2:
        quat.from_rotation_vector(np.asarray(rot[0])*rot[1])
    else:
        rot_np = np.asarray(rot)
        if rot_np.shape == (3, 3):
            q = quat.from_rotation_matrix(rot_np)
        elif rot_np.shape == (4, 4):
            q = quat.from_rotation_matrix(rot_np[0:3, 0:3])
        elif rot_np.shape == (3,):
            q = quat.from_rotation_vector(rot_np)
        elif rot_np.shape == (4,):
            q = quat.from_float_array(rot_np)
        else:
            raise ValueError(f"Unknown rotation type {rot}")

    if type == 'tuple':
        return q.x, q.y, q.z, q.w
    elif type == 'quat':
        return q

def as_rot_type(q: Tuple[float, float, float, float],
                rot_type='quaternion'):
    """
    Returns the quaternion as a rotation type.

    Args:
        q (Tuple[float, float, float, float]): Quaternion.
    """
    if rot_type == 'quaternion':
        return quat.as_float_array(q)
    elif rot_type == 'euler_ZYZ':
        return quat.as_euler_angles(q)
    elif rot_type == 'rot_mat':
        return quat.as_rotation_matrix(q)
    elif rot_type == 'rot_vec':
        return quat.as_rotation_vector(q)
    elif rot_type == 'axis_angle':
        rot_vec = quat.as_rotation_vector(q)
        angle = np.linalg.norm(rot_vec)
        axis = rot_vec / angle
        return axis, angle
    elif rot_type == 'matrix':
        rigid_mat = np.identity(4)
        rot_mat = quat.as_rotation_matrix(q)
        rigid_mat[0:3, 0:3] = rot_mat
        return rigid_mat
    else:
        raise ValueError(f'rot_type must be one of: {ACCEPTED_ROT_TYPES}')
