import argparse
import os

import bpy
import numpy as np
from blender_plotting.utils.curves import draw_function
from blender_plotting.utils.files import avi2mp4
from blender_plotting.utils.renderers import (cycles_render, eevee_render,
                                              workbench_render)
from blender_plotting.utils.scenes import create_2d_scene, draw_xy_axes
from blender_plotting.utils.shapes import draw_points


def parse_args():
    parser = argparse.ArgumentParser(description='Draw a R2 plane.')
    parser.duration = parser.add_argument('--duration', type=float, default=10,
                                          help='Animation duration in seconds.')
    parser.add_argument('--cycles', action='store_true', help='Use Cycles.')
    parser.add_argument('--eevee', action='store_true', help='Use Eevee.')

    args = parser.parse_args()
    return args


def set_animation(scene: bpy.types.Scene,
                  fps: int = 24,
                  frame_start: int = 1,
                  frame_end: int = 48,
                  frame_current: int = 1,
                  file_extension: str = 'FFMPEG') -> None:
    scene.render.fps = fps
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    scene.frame_current = frame_current
    scene.render.image_settings.file_format = file_extension
    if file_extension == 'FFMPEG':
        scene.render.ffmpeg.codec = 'H264'

def main():
    args = parse_args()

    FPS = 60
    DURATION = 2
    TOTAL_FRAMES =  FPS * DURATION

    # Plot limits
    x_min = -3
    x_max = 3
    y_min = -3
    y_max = 3


    # Create a new scene
    scene, _ = create_2d_scene([x_min, x_max], [y_min, y_max])

    # Create the axes
    draw_xy_axes(axes_length=1.0)

    # Create the function
    f = lambda x: np.sin(x**2)

    # Draw the function
    draw_function(f, x_min, x_max, resolution=1000)

    # draw sphere
    sphere = draw_points([(x_min, f(x_min), 0)], color=(1, 1, 0, 1.0), radius=0.05)[0]

    # Keyframes
    set_animation(scene,
                  fps=FPS,
                  frame_start=1,
                  frame_end=TOTAL_FRAMES,
                  frame_current=1,
                  file_extension='AVI_JPEG')


    x_length = x_max - x_min
    for i in range(1, TOTAL_FRAMES+1):
        t = (i-1) / TOTAL_FRAMES
        x = x_min + t * x_length
        sphere.location = (x, f(x), 0)
        print(f" frame {i}: t = {t}, location = {sphere.location}")
        sphere.keyframe_insert(data_path='location', frame=i)



    # Render the scene
    imf_filename = 'draw_function'
    if args.cycles:
        cycles_render(scene, imf_filename, animation=True)
    elif args.eevee:
        eevee_render(scene, imf_filename, animation=True)
    else:
        workbench_render(scene, imf_filename, animation=True)

    # avi to mp4
    filepath_avi = scene.render.filepath
    avi2mp4(filepath_avi)

    # Delete avi file
    os.remove(filepath_avi)

    # Close blender
    bpy.ops.wm.quit_blender()



if __name__ == '__main__':
    main()
