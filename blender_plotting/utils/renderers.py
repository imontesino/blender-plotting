from typing import List
import bpy

def bake_textures():
    """Bake all the textures in the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.bake(type='DIFFUSE', save_mode='EXTERNAL')

def common_setup(scene: bpy.types.Scene,
                 resolution_x: int=1920,
                 resolution_y: int=1080,
                 transparent: bool=False,
                 ):
    scene.render.use_persistent_data = True

    # set resolution
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y

    # Performance optimizations
    scene.render.use_sequencer = False
    scene.render.use_compositing = False

    # set transparent background
    if transparent:
        bpy.context.scene.render.film_transparent = transparent
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'


def set_animation(scene: bpy.types.Scene,
                  fps: int = 24,
                  frame_start: int = 1,
                  frame_end: int = 48,
                  frame_current: int = 1,
                  file_format: str = 'FFMPEG') -> None:
    """ Set the scene to render an animation.

    Args:
        scene (bpy.types.Scene): The scene to set.
        fps (int, optional): The frames per second. Defaults to 24.
        frame_start (int, optional): The first frame. Defaults to 1.
        frame_end (int, optional): The last frame. Defaults to 48.
        frame_current (int, optional): The current frame. Defaults to 1.
        file_format (str, optional): The file extension. Defaults to 'FFMPEG'.
    """
    scene.render.fps = fps
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    scene.frame_current = frame_current
    scene.render.image_settings.file_format = file_format
    if file_format == 'FFMPEG':
        scene.render.ffmpeg.codec = 'H264'

def cycles_render(scene: bpy.types.Scene,
                  file_name: str,
                  use_gpu: bool=True,
                  resolution_x: int=1920,
                  resolution_y:int =1080,
                  samples: int=128,
                  transparent: bool=False,
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
    common_setup(scene)

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

        # for d in bpy.context.preferences.addons["cycles"].preferences.devices:
        #     print(d["name"], d["use"])

        # set tile size to 256x256
        bpy.context.scene.cycles.tile_x = 2048
        bpy.context.scene.cycles.tile_y = 2048
    else:
        # Set the device_type
        bpy.context.preferences.addons[
            "cycles"
        ].preferences.compute_device_type = "CPU"

        bpy.context.scene.cycles.device = "CPU"

        # set tile size to 64x64
        bpy.context.scene.cycles.tile_x = 64
        bpy.context.scene.cycles.tile_y = 64

    # Set Optix as denoiser
    # bpy.context.scene.view_layers['View Layer'].cycles.use_denoising = True

    # set samples
    bpy.context.scene.cycles.samples = samples

    bpy.ops.render.render(write_still=1, animation=animation)

def eevee_render(scene: bpy.types.Scene,
                 file_name: str,
                 resolution_x: int=1920,
                 resolution_y:int =1080,
                 transparent: bool=False,
                 animation: bool=False):
    """Render a scene using the Eevee engine.

    Args:
        scene (bpy.types.Scene): The scene to render.
        file_name (str): The path to save the image to.
        use_gpu (bool, optional): use GPU accelerated Rendering. Defaults to True.
        resolution_x (int, optional): Defaults to 1920.
        resolution_y (int, optional): Defaults to 1080.
    """
    common_setup(scene)

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
                     transparent: bool=False,
                     animation: bool=False):
    """ Render a scene using the Workbench engine.

    Very fast render for prototiping animations and positions.
    """
    common_setup(scene)

    # Prevent segfault
    # TODO find cause
    rm_objects = remove_subsurf_modifiers(scene)

    # # add exposure (workbench renders are very dark)
    # scene.render.image_settings.view_settings.exposure *= 10
    # scene.view_settings.exposure *= 10

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
    shading.color_type = 'MATERIAL'

    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.resolution_percentage = 100

    # set transparent background
    if transparent:
        scene.render.alpha_mode = 'TRANSPARENT'

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
