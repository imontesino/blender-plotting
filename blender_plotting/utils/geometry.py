""" Geometric functions for plotting. """

from typing import List, Union

import numpy as np
import quaternion as quat


def quaternion_to_euler(quaternion: Union[List,tuple,np.ndarray, quat.quaternion],
                        convention: str = "ZYX") -> np.ndarray:
    """ Convert a quaternion to euler angles. """

    if isinstance(quaternion, quat.quaternion):
        q = quat.as_float_array(quaternion)

    if convention == "ZYX":
        phi = np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]), 1 - 2 * (q[1] ** 2 + q[2] ** 2))
        theta = np.arcsin(2 * (q[0] * q[2] - q[3] * q[1]))
        psi = np.arctan2(2 * (q[0] * q[3] + q[1] * q[2]), 1 - 2 * (q[2] ** 2 + q[3] ** 2))
    else:
        raise ValueError(f"Unknown convention: {convention}, Valid: ZYX")

    return np.array([phi, theta, psi])