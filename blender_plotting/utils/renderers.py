from typing import List
import bpy


def cycles_render(scene: bpy.types.Scene,
                  file_name: str,
                  use_gpu: bool=True,
                  resolution_x: int=1920,
                  resolution_y:int =1080,
                  samples: int=128,
                  animation: bool=False):
    """Render a scene using th Cycles engine.

    Args:
        scene (bpy.types.Scene): The scene to render.
        file_name (str): The path to save the image to.
        use_gpu (bool, optional): use GPU accelerated Rendering. Defaults to True.
        resolution_x (int, optional): Defaults to 1920.
        resolution_y (int, optional): Defaults to 1080.
        samples (int, optional): Defaults to 128.
    """
    if animation:
        file_name = "animation/" + file_name
        scene.render.filepath = file_name+".avi"
    else:
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = file_name+".png"

    scene.render.engine = 'CYCLES'

    if use_gpu:
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
    else:
        # Set the device_type
        bpy.context.preferences.addons[
            "cycles"
        ].preferences.compute_device_type = "CPU"

        bpy.context.scene.cycles.device = "CPU"

        # set tile size to 64x64
        bpy.context.scene.cycles.tile_x = 64
        bpy.context.scene.cycles.tile_y = 64


    # set resolution to 4k
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y

    # set samples
    bpy.context.scene.cycles.samples = samples

    bpy.ops.render.render(write_still=1, animation=animation)

def eevee_render(scene: bpy.types.Scene,
                 file_name: str,
                 resolution_x: int=1920,
                 resolution_y:int =1080,
                 animation: bool=False):
    """Render a scene using the Eevee engine.

    Args:
        scene (bpy.types.Scene): The scene to render.
        file_name (str): The path to save the image to.
        use_gpu (bool, optional): use GPU accelerated Rendering. Defaults to True.
        resolution_x (int, optional): Defaults to 1920.
        resolution_y (int, optional): Defaults to 1080.
    """
    # Prevent segfault
    # TODO find cause
    rm_objects = remove_subsurf_modifiers(scene)

    if animation:
        file_name = "animation/" + file_name
        scene.render.filepath = file_name+".avi"
    else:
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = file_name+".png"

    if rm_objects:
        print("Warning: Removing subsurf modifiers from the following objects:")
        print(rm_objects)

    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.resolution_percentage = 100
    bpy.ops.render.render(write_still=1, animation=animation)

def workbench_render(scene: bpy.types.Scene,
                     file_name: str,
                     resolution_x: int=1920,
                     resolution_y: int=1080,
                     animation: bool=False):
    """ Render a scene using the Workbench engine.

    Very fast render for prototiping animations and positions.
    """
    # Prevent segfault
    # TODO find cause
    rm_objects = remove_subsurf_modifiers(scene)

    if animation:
        file_name = "animation/" + file_name
        scene.render.filepath = file_name+".avi"
    else:
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = file_name+".png"

    if rm_objects:
        print("Warning: Removing subsurf modifiers from the following objects:")
        print(rm_objects)

    scene.render.engine = 'BLENDER_WORKBENCH'

    # display material color
    shading = scene.display.shading
    shading.light = 'STUDIO'
    shading.color_type = 'TEXTURE'

    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.resolution_percentage = 100
    bpy.ops.render.render(write_still=1, animation=animation)


def remove_subsurf_modifiers(scene: bpy.types.Scene) -> List[str]:
    """Remove all subsurf modifiers from the scene.

    Args:
        scene (bpy.types.Scene): The scene to check.

    Returns:
        List[str]: The names of the objects with subsurf modifiers.
    """
    objects_with_subsurf = []

    objects: List[bpy.types.Object] = scene.objects

    for ob in objects:
        if ob.type == 'MESH':
            for mod in ob.modifiers:
                if mod.type == 'SUBSURF':
                    objects_with_subsurf.append(ob.name)
                    mod.show_render = False
                    ob.modifiers.remove(mod)

    return objects_with_subsurf
