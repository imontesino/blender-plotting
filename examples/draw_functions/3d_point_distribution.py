import argparse

import bpy
import numpy as np

from blender_plotting.utils.background import set_solid_color_background
from blender_plotting.utils.color_scale import ColorScale
from blender_plotting.utils.renderers import (cycles_render, eevee_render,
                                              workbench_render)
from blender_plotting.utils.scenes import create_3d_scene, draw_xyz_axes
from blender_plotting.utils.shapes import draw_points


def parse_args():
    parser = argparse.ArgumentParser(description='Draw a R2 plane.')
    parser.add_argument('--cycles', action='store_true', help='Use Cycles.')
    parser.add_argument('--eevee', action='store_true', help='Use Eevee.')

    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    bounding_box = np.array([[0, 3], [0, 3], [0, 2]])
    box_center = np.mean(bounding_box, axis=1)

    # Create a new scene
    scene, _ = create_3d_scene(bounding_box[0], bounding_box[1], bounding_box[2])

    # Set the background to a pastel color
    set_solid_color_background(scene, [0.009, 0.009, 0.009, 1])

    # Draw the axes
    x_axis, y_axis, z_axis = draw_xyz_axes(axes_length=1.0)

    # Scatter random points in a box
    max_dist_from_center = np.linalg.norm(bounding_box[:, 1] - box_center) * 0.75
    color_scale = ColorScale(min_value=0, max_value=max_dist_from_center/2,
                             invert=True,
                             colors ="viridis")

    for _ in range(200):
        point = np.random.normal(box_center, np.abs(bounding_box[:,0] - bounding_box[:,1])/8)

        distance_from_center = np.linalg.norm(point - box_center)

        color = list(color_scale.get_color(distance_from_center)) + [0.5]  # alpha

        draw_points([point], color=color, radius=0.03)

    # Render the scene

    current_filename = __file__.split("/")[-1].split(".")[0]
    imf_filename = lambda s: f'renders/{current_filename}/{current_filename}_{s}'

    if args.cycles:
        cycles_render(scene, imf_filename('cycles'))
    elif args.eevee:
        eevee_render(scene, imf_filename('eevee'))
    else:
        workbench_render(scene, imf_filename('workbench'))

    # Close blender
    bpy.ops.wm.quit_blender()


if __name__ == '__main__':
    main()
