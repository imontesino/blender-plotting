""" Create a scene with a cube and a plane and render it to a png """
import math

import bpy

from utils.renderers import cycles_gpu_render

# Delete the default cube
bpy.ops.object.delete()

bpy.ops.mesh.primitive_cube_add(size=3, location=(0,0,1))# save cube to

# save cube to variable
cube = bpy.context.active_object

# create a plane
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -1.5))

plane = bpy.context.active_object

# add light
light_data = bpy.data.lights.new('light', type='POINT')
light = bpy.data.objects.new('light', light_data)
bpy.context.collection.objects.link(light)

light.location = (3, 4, -5)
light.data.energy = 200.0
light_data = bpy.data.lights.new('light', type='SUN')
light.data.energy = 200

# we first create the camera object
cam_data = bpy.data.cameras.new('camera')
cam = bpy.data.objects.new('camera', cam_data)
cam.location = (25, -3, 3)
cam.data.lens_unit = 'FOV'
cam.data.angle = math.radians(45)

bpy.context.collection.objects.link(cam)

# add camera to scene
scene = bpy.context.scene
scene.camera = cam

# create material
cube_mat = bpy.data.materials.new(name='CubeMaterial')

cube.data.materials.append(cube_mat)
cube_mat.use_nodes=True

# let's create a variable to store our list of nodes
cube_mat_nodes = cube_mat.node_tree.nodes

# let's set the metallic to 1.0
cube_mat_nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.05, 0.0185, 0.8, 1.0)
cube_mat_nodes['Principled BSDF'].inputs['Metallic'].default_value=0.95
cube_mat_nodes['Principled BSDF'].inputs['Roughness'].default_value=0.5

# create material
plane_mat = bpy.data.materials.new(name='PlaneMaterial')

#assign material to plane
plane.data.materials.append(plane_mat)
plane_mat.use_nodes=True

# let's create a variable to store our list of nodes
plane_mat_nodes = plane_mat.node_tree.nodes

plane_mat_nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.010, 0.0065, 0.8, 1.0)
plane_mat_nodes['Principled BSDF'].inputs['Roughness'].default_value=0.0

# track the cube with the camera
constraint = cam.constraints.new(type='TRACK_TO')
constraint.target=cube

cycles_gpu_render(scene, 'hello_blender.png')
