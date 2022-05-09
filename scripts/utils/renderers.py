import bpy

def cycles_gpu_render(scene, image_path,
                      resolution_x=1920,
                      resolution_y=1080,
                      samples=128):
    scene.render.engine = 'CYCLES'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = 'renders/'+image_path

    # Set the device_type
    bpy.context.preferences.addons[
        "cycles"
    ].preferences.compute_device_type = "CUDA"

    # Set the device and feature set
    bpy.context.scene.cycles.device = "GPU"

    # get_devices() to let Blender detects GPU device
    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    print(bpy.context.preferences.addons["cycles"].preferences.compute_device_type)
    for d in bpy.context.preferences.addons["cycles"].preferences.devices:
        d["use"] = 1 # Using all devices, include GPU and CPU
        print(d["name"], d["use"])

    # set tile size to 256x256
    bpy.context.scene.cycles.tile_x = 256
    bpy.context.scene.cycles.tile_y = 256

    # set resolution to 4k
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y

    # set samples
    bpy.context.scene.cycles.samples = samples

    bpy.ops.render.render(write_still=1)

def eevee_render(scene, image_path,
                 resolution_x=1920,
                 resolution_y=1080):
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = 'renders/'+image_path
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.resolution_percentage = 100
    bpy.ops.render.render(write_still=1)
