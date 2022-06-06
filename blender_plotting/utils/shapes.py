from typing import Iterable, List, Optional, Tuple

import bpy
import bmesh
import mathutils
import numpy as np
from blender_plotting.utils.materials import create_solid_material


def draw_arrow(vector_origin: np.ndarray,
              vector_end: np.ndarray,
              name: Optional[str] = None,
              thickness: float = 1,
              color: tuple = (1, 0, 0, 1.0)) -> Tuple[bpy.types.Object, bpy.types.Object]:
    """Add a 3D arrow model to the scene.

    Args:
        vector_origin (np.ndarray): Origin of the arrow.
        vector_end (np.ndarray): End of the arrow.
        name (Optional[str]): Name of the arrow.
        thickness (float): relative thickness of the arrow.
        color (tuple): Color of the arrow.

    Returns:
        Tuple[bpy.types.Object, bpy.types.Object]: The arrow body and the arrow head.
    """
    # as np.array
    vector_origin = np.array(vector_origin)
    vector_end = np.array(vector_end)


    if vector_origin.size == 2:
        vector_origin = np.append(vector_origin, 0)
    if vector_end.size == 2:
        vector_end = np.append(vector_end, 0)


    np_vector = vector_end - vector_origin
    v = mathutils.Vector(np_vector)
    up = mathutils.Vector((0,0,1))  # Z-Axis up convention
    if v!=-up:
        rot = up.rotation_difference(v)
    else:
        rot = mathutils.Quaternion((1,0,0),np.pi)

    head_ratio = 0.2 + 0.3 * np.clip((thickness - 1)/3, 0, 1)

    # Create the cylinder part
    cyl_length = v.length*(1-head_ratio)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,
                                        radius=v.length*0.01*thickness,
                                        depth=cyl_length,
                                        end_fill_type='NGON',
                                        enter_editmode=False)
    cylinder = bpy.context.active_object
    cylinder.location = vector_origin + cyl_length/2 * v.normalized()
    cylinder.rotation_mode = 'QUATERNION'
    cylinder.rotation_quaternion = rot
    if name is not None:
        cylinder.name = name + '_body'

    # Create the cone part
    cone_length = v.length*head_ratio
    bpy.ops.mesh.primitive_cone_add(
        radius1=v.length*0.05*thickness,
        radius2=0,
        depth=cone_length,
        enter_editmode=False)
    # bpy.ops.mesh.faces_shade_smooth()
    cone = bpy.context.active_object
    cone.location = vector_origin + (cyl_length + cone_length/2) * v.normalized()
    cone.rotation_mode = 'QUATERNION'
    cone.rotation_quaternion = rot
    if name is not None:
        cone.name = name + '_head'

    # Create the material
    if name is None:
        arrow_mat = create_solid_material(color)
    else:
        arrow_mat = create_solid_material(color, name=name + '_color')

    cylinder.data.materials.append(arrow_mat)
    cone.data.materials.append(arrow_mat)

    return (cylinder, cone)

def draw_points(points: Iterable[Tuple[float, float, float]],
                color: Tuple[float, float, float, float] = (1, 0, 0, 1.0),
                radius: float = 0.05) -> List[bpy.types.Object]:
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
        # shade smooth
        bpy.ops.object.shade_smooth()

    return points_objs


def draw_sphere(center: Tuple[float, float, float],
                radius: float,
                segments: int = 32,
                rings: int = 16,
                color: Tuple[float, float, float, float] = (1, 0, 0, 1.0)):
    """Draws a sphere.

    Args:
        center (Tuple[float, float, float]): Center of the sphere.
        radius (float): Radius of the sphere.
        color (Tuple[float, float, float, float]): Color of the sphere.

    Returns:
        bpy.types.Object: The sphere.
    """

    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius,
                                         location=center,
                                         segments=segments,
                                         ring_count=rings)
    sphere = bpy.context.object
    sphere.data.materials.append(create_solid_material(color))

    # shade smooth
    for face in sphere.data.polygons:
        face.use_smooth = True

    return sphere
