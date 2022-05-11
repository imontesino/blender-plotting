""" Material creation and utility functions"""

from typing import Optional, Tuple, Union

import bpy

def create_material_from_pbr(name: str,
                             base_image_file: str,
                             scale: float = 1.0,
                             normal_file: Optional[str] = None,
                             specular_file: Optional[str] = None,
                             metallic_file: Optional[str] = None,
                             roughness_file: Optional[str] = None,
                             displacement_file: Optional[str] = None,
                             displacement_scale: float = 1.0,
                             occlusion_file: Optional[str] = None,
                             subsurface_file: Optional[str] = None) -> bpy.types.Material:
    """Create a new material from PBR inputs.

    Args:
        name(str): Name of the material.
        base_image_file(str): Filepath to the base image of the texture.
        normal_file(str): Filepath to the normal map image.
        specular_file(str): Filepath to the specular map image.
        metallic_file(str): Filepath to the metallic map image.
        roughness_file(str): Filepath to the roughness map image.
        displacement_file(str): Filepath to the displacement map image.
        height_factor(float): Factor to multiply the height map by.
        occlusion_file(str): Filepath to the occlusion map image.
        subsurface_file(str): Filepath to the subsurface map image.

    Returns:
        bpy.types.Material: The created material.
    """

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes=True
    nodes = mat.node_tree.nodes

    # Create principled BSDF node
    bsdf = nodes["Principled BSDF"]
    output = nodes["Material Output"]
    mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Create mapping for all the inputs
    mapping_node = nodes.new('ShaderNodeMapping')
    tex_coord = nodes.new('ShaderNodeTexCoord')
    mapping_node["Scale"] = [scale, scale, scale]
    mat.node_tree.links.new(tex_coord.outputs['UV'], mapping_node.inputs['Vector'])

    # Create an link base image texture node
    tex_image = nodes.new('ShaderNodeTexImage')
    tex_image.image = bpy.data.images.load(base_image_file)
    mat.node_tree.links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])

    # Create normal map texture node
    if normal_file is not None:
        # image node for the normal map image
        tex_normal = nodes.new('ShaderNodeTexImage')
        mat.node_tree.links.new(mapping_node.outputs["Vector"], tex_normal.inputs['Vector'])
        tex_normal.image = bpy.data.images.load(normal_file)

        # passing by a normal map
        normal_map_node = nodes.new('ShaderNodeNormalMap')
        mat.node_tree.links.new(tex_normal.outputs['Color'], normal_map_node.inputs['Color'])
        normal_map_node['Strength'] = 1.0

        # link the normal map to the principled BSDF
        mat.node_tree.links.new(normal_map_node.outputs['Normal'], bsdf.inputs['Normal'])

    # Create specular map texture node
    if specular_file is not None:
        tex_specular = nodes.new('ShaderNodeTexImage')
        mat.node_tree.links.new(mapping_node.outputs["Vector"], tex_specular.inputs['Vector'])
        tex_specular.image = bpy.data.images.load(specular_file)
        mat.node_tree.links.new(tex_specular.outputs['Color'], bsdf.inputs['Specular'])

    # Create metallic map texture node
    if metallic_file is not None:
        tex_metallic = nodes.new('ShaderNodeTexImage')
        mat.node_tree.links.new(mapping_node.outputs["Vector"], tex_metallic.inputs['Vector'])
        tex_metallic.image = bpy.data.images.load(metallic_file)
        mat.node_tree.links.new(tex_metallic.outputs['Color'], bsdf.inputs['Metallic'])

    # Create roughness map texture node
    if roughness_file is not None:
        tex_roughness = nodes.new('ShaderNodeTexImage')
        mat.node_tree.links.new(mapping_node.outputs["Vector"], tex_roughness.inputs['Vector'])
        tex_roughness.image = bpy.data.images.load(roughness_file)
        mat.node_tree.links.new(tex_roughness.outputs['Color'], bsdf.inputs['Roughness'])


    # Create displacement texture node
    if displacement_file is not None:
        tex_disp = nodes.new('ShaderNodeTexImage')
        tex_disp.image = bpy.data.images.load(displacement_file)
        disp_node = nodes.new('ShaderNodeDisplacement')

        # add a multiply node to the displacement node
        mult_node = nodes.new('ShaderNodeMath')
        mult_node.operation = 'MULTIPLY'
        mult_node.inputs[1].default_value = displacement_scale
        mat.node_tree.links.new(tex_disp.outputs['Color'], mult_node.inputs[0])
        mat.node_tree.links.new(mult_node.outputs[0], disp_node.inputs['Height'])
        mat.node_tree.links.new(disp_node.outputs['Displacement'],  output.inputs['Displacement'])


    # Create occlusion map texture node
    if occlusion_file is not None:
        tex_occlusion = nodes.new('ShaderNodeTexImage')
        mat.node_tree.links.new(mapping_node.outputs["Vector"], tex_occlusion.inputs['Vector'])
        tex_occlusion.image = bpy.data.images.load(occlusion_file)
        mat.node_tree.links.new(tex_occlusion.outputs['Color'], bsdf.inputs['Occlusion'])

    # Create subsurface scattering node
    if subsurface_file is not None:
        tex_subsurface = nodes.new('ShaderNodeTexImage')
        mat.node_tree.links.new(mapping_node.outputs["Vector"], tex_subsurface.inputs['Vector'])
        tex_subsurface.image = bpy.data.images.load(subsurface_file)
        subsurface_node = nodes.new('ShaderNodeSubsurfaceScattering')
        mat.node_tree.links.new(tex_subsurface.outputs['Color'], subsurface_node.inputs['Color'])

    # Create roughness texture node
    tex_rough = nodes.new('ShaderNodeTexImage')
    tex_rough.image = bpy.data.images.load(roughness_file)
    mat.node_tree.links.new(tex_rough.outputs['Color'], bsdf.inputs['Roughness'])

    return mat


def create_solid_material(name: str,
                          base_color: Union[Tuple[float, float, float, float],str] = (0.6, 0.6, 0.6, 1.0))-> bpy.types.Material:
    """Create a solid material.

    Args:
        name (str): Name of the material.
        base_color (Union[Tuple[float, float, float, float],str]): Base color of the material. Either
            as a tuple (r, g, b, a) or as a filepath to an image. Default is (0.6, 0.6, 0.6, 1.0).
    """

    # Create the material
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes=True
    nodes = mat.node_tree.nodes

    # Create principled BSDF node
    bsdf = nodes["Principled BSDF"]
    output = nodes["Material Output"]
    mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])


    # Create the principled BSDF node
    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Roughness'].default_value = 1.0
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Specular'].default_value = 0.0
    bsdf.inputs['Emission'].default_value = (0.0, 0.0, 0.0, 1.0)


    return mat

