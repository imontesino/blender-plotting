""" example of adding and hdri as a texture environment
"""
import math

import bpy

from blender_plotting.utils.renderers import cycles_render, eevee_render, workbench_render
from blender_plotting.utils.background import set_hdri_background

# Delete the default cube
bpy.ops.object.delete()

# Add a sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,1))
sphere = bpy.context.active_object

# add subdivision
bpy.ops.object.modifier_add(type='SUBSURF')
sphere.modifiers[0].render_levels = 6
bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.faces_shade_smooth()

# create material
mat = bpy.data.materials.new(name='PlaneMaterial')

#assign material to plane
sphere.data.materials.append(mat)
mat.use_nodes=True

# let's create a variable to store our list of nodes
mat_nodes = mat.node_tree.nodes

mat_nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.5, 0.5, 0.5, 1.0)
mat_nodes['Principled BSDF'].inputs['Roughness'].default_value=0.0
mat_nodes['Principled BSDF'].inputs['Metallic'].default_value=1.0


C = bpy.context

set_hdri_background(C.scene, "resources/hdri/green_point_park_8k.exr")

# we first create the camera object
cam_data = bpy.data.cameras.new('camera')
cam = bpy.data.objects.new('camera', cam_data)
cam.location = (2, -2, 2)
cam.data.lens_unit = 'FOV'
cam.data.angle = math.radians(100)

# track the cube with the camera
constraint = cam.constraints.new(type='TRACK_TO')
constraint.target=sphere

# add camera to scene
scene = bpy.context.scene
scene.camera = cam

cycles_render(scene, 'renders/cycles/hdri_example.png')
eevee_render(scene, 'renders/eevee/hdri_example.png')
workbench_render(scene, 'renders/workbench/hdri_example.png')

# IMPOTANT: Close blender when done
bpy.ops.wm.quit_blender()
