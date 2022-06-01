import argparse

import bpy
import numpy as np

from blender_plotting.utils.background import set_solid_color_background
from blender_plotting.utils.renderers import cycles_render, eevee_render, workbench_render
from blender_plotting.utils.scenes import create_2d_scene, draw_xy_axes
from blender_plotting.utils.functions import draw_vector_field

def parse_args():
    parser = argparse.ArgumentParser(description='Draw a R2 plane.')
    parser.add_argument('--cycles', action='store_true', help='Use Cycles.')
    parser.add_argument('--eevee', action='store_true', help='Use Eevee.')

    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    # Create a new scene
    scene, _ = create_2d_scene([-3,3], [-3,3])

    # Set the background to a pastel color
    set_solid_color_background(scene, [0.009, 0.009, 0.009, 1])

    # Draw the axes
    draw_xy_axes()

    # 90 degree rotation matrix
    R = np.array([[0, 1], [-1, 0]])

    # Vector field rotation
    f = lambda x, y: R @ np.array([x, y])

    max_length = np.linalg.norm(np.array([2, 2]))
    min_length = 0

    # Draw the vector field
    draw_vector_field(f,
                      x_min=-3,
                      x_max=3,
                      y_min=-3,
                      y_max=3,
                      min_vector_magnitude=min_length,
                      max_vector_magnitude=max_length,
                      vector_length=0.3,
                      vector_thickness=4,
                      resolution=2,
                      colors='turbo')

    # Render the scene
    imf_filename = 'renders/draw_vector_field/vector_field.png'

    if args.cycles:
        cycles_render(scene, imf_filename)
    elif args.eevee:
        eevee_render(scene, imf_filename)
    else:
        workbench_render(scene, imf_filename)

    # Close blender
    bpy.ops.wm.quit_blender()


if __name__ == '__main__':
    main()
