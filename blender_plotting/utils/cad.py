import bpy

from .materials import create_solid_material
from .movement import set_world_pose

def import_stl(filepath: str,
               scale: float = 1.0,
               location: tuple = (0.0, 0.0, 0.0),
               rotation: tuple = (0.0, 0.0, 0.0, 0.0),
               color: tuple = (1.0, 1.0, 1.0, 1.0)) -> bpy.types.Object:
    """Import an STL file.

    Args:
        filepath (str): Filepath of the STL file.
        scale (float): Scale of the imported object.
        location (tuple): Location of the imported object.
        rotation (tuple): Rotation of the imported object.
        color (tuple): Color of the imported object.

    Returns:
        bpy_types.Object: Imported object.
    """

    bpy.ops.import_mesh.stl(filepath=filepath)
    stl_mesh = bpy.context.object
    stl_mesh.data.materials.append(create_solid_material(color))

    set_world_pose(stl_mesh,
                   translation=location,
                   rotation=rotation,
                   scale=(scale, scale, scale))

    return stl_mesh
