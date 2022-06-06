import pathlib
import uuid
from typing import Tuple

import bpy

from blender_plotting.utils.materials import create_solid_material

# find the directory of this file
base_module_dir = pathlib.Path(__file__).parent.parent

# import CMU Fonts
for font_file in base_module_dir.glob('resources/fonts/*.ttf'):
    bpy.data.fonts.load(filepath=str(font_file))

def create_text(
    scene: bpy.types.Scene,
    body: str,
    name: str = None,
    align_x: str = 'CENTER',
    align_y: str = 'CENTER',
    size: float = 1.0,
    font_name: str = "CMU Serif Roman",
    extrude: float = 0.0,
    space_line: float = 1.0,
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0, 1.0),
) -> bpy.types.Object:

    if name is None:
        name = 'text-'+str(uuid.uuid4())


    new_text_data: bpy.types.Curve = bpy.data.curves.new(name=name, type='FONT')

    new_text_data.body = body
    new_text_data.align_x = align_x
    new_text_data.align_y = align_y
    new_text_data.size = size
    new_text_data.font = bpy.data.fonts[font_name]
    new_text_data.space_line = space_line
    new_text_data.extrude = extrude

    new_object: bpy.types.Object = bpy.data.objects.new(name, new_text_data)
    scene.collection.objects.link(new_object)

    new_object.location = location
    new_object.rotation_quaternion = rotation

    mat = create_solid_material(color)

    new_object.data.materials.append(mat)

    return new_object
