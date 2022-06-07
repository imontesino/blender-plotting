import bpy
from blender_plotting.utils.background import set_hdri_background

from blender_plotting.utils.renderers import cycles_render, eevee_render, workbench_render

# from blender_plotting.utils.renderers import cycles_render, eevee_render

C = bpy.context
scene = C.scene

TEXTURE_DIR = "resources/textures/castle_brick_02_red_4k/textures/"
TX_IMG = TEXTURE_DIR+"castle_brick_02_red_diff_4k.jpg"
TX_DISP = TEXTURE_DIR+"castle_brick_02_red_disp_4k.png"
TX_NORMAL = TEXTURE_DIR+"castle_brick_02_red_nor_gl_4k.exr"
TX_ROUGH = TEXTURE_DIR+"castle_brick_02_red_rough_4k.jpg"

# Delete the default cube
bpy.ops.object.delete()

# select the light and delete it
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['Light'].select_set(True)
bpy.ops.object.delete()

bpy.ops.mesh.primitive_uv_sphere_add()

# save sphere to variable
sphere = bpy.context.active_object

sphere.scale = (2.5, 2.5, 2.5)

# add subdivision
bpy.ops.object.modifier_add(type='SUBSURF')

sphere.modifiers[0].render_levels = 6
bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.faces_shade_smooth()

mat = bpy.data.materials.new(name="Brick_material")
sphere.data.materials.append(mat)
mat.use_nodes=True

nodes = mat.node_tree.nodes

# Create principled BSDF node
bsdf = mat.node_tree.nodes["Principled BSDF"]
output = mat.node_tree.nodes["Material Output"]

# Create an link base image texture node
texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
texImage.image = bpy.data.images.load(TX_IMG)
mat.node_tree.links.new(texImage.outputs['Color'], bsdf.inputs['Base Color'])

# Create displacement texture node
tex_disp = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex_disp.image = bpy.data.images.load(TX_DISP)
disp_node = mat.node_tree.nodes.new('ShaderNodeDisplacement')
# add a multiply node to the displacement node
mult_node = mat.node_tree.nodes.new('ShaderNodeMath')
mult_node.operation = 'MULTIPLY'
mult_node.inputs[1].default_value = 0.1
mat.node_tree.links.new(tex_disp.outputs['Color'], mult_node.inputs[0])
mat.node_tree.links.new(mult_node.outputs[0], disp_node.inputs['Height'])
mat.node_tree.links.new(disp_node.outputs['Displacement'],  output.inputs['Displacement'])

# Create normal map texture node
tex_normal = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex_normal.image = bpy.data.images.load(TX_NORMAL)
normal_node = mat.node_tree.nodes.new('ShaderNodeNormalMap')
mat.node_tree.links.new(tex_normal.outputs['Color'], bsdf.inputs['Normal'])

# Create roughness texture node
tex_rough = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex_rough.image = bpy.data.images.load(TX_ROUGH)
mat.node_tree.links.new(tex_rough.outputs['Color'], bsdf.inputs['Roughness'])

mat.cycles.displacement_method = 'BOTH'

set_hdri_background(C.scene, "resources/hdri/green_point_park_8k.exr")

cycles_render(scene, 'renders/cycles/texture_import.png')
eevee_render(scene, 'renders/eevee/texture_import.png')
workbench_render(scene, 'renders/workbench/texture_import.png')

# IMPOTANT: Close blender when done
bpy.ops.wm.quit_blender()
