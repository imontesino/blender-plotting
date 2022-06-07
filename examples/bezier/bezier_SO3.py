import argparse

import bpy
import bezier_fitting
import numpy as np

import quaternion as quat
from blender_plotting.utils.background import set_solid_color_background
from blender_plotting.utils.color_scale import ColorScale
from blender_plotting.utils.curves import draw_parametric_curve
from blender_plotting.utils.files import avi2mp4
from blender_plotting.utils.movement import rigid_movement, rotate_around_axis, set_world_pose
from blender_plotting.utils.renderers import (cycles_render, eevee_render,
                                              set_animation, workbench_render)
from blender_plotting.utils.scenes import create_3d_scene
from blender_plotting.utils.shapes import draw_arrow, draw_points, draw_sphere
from blender_plotting.utils.text import create_text
from blender_plotting.utils.cad import import_stl


def parse_args():
    parser = argparse.ArgumentParser(description='Draw a SO3 Bezier.')
    parser.add_argument('--cycles', action='store_true', help='Use Cycles.')
    parser.add_argument('--eevee', action='store_true', help='Use Eevee.')
    parser.add_argument('--filename', type=str, default=None, help='Output filename.')
    parser.add_argument('--frame', type=int, default=0, help='Frame number.')
    parser.add_argument('--video', action='store_true', help='Render video.')

    args = parser.parse_args()
    return args

def circle_y(x):
    R = 1
    return np.sqrt(R**2 - x**2)

def circle_orn(x):
    ori_vector = np.array([x, circle_y(x), 0.])
    norm_ori_vector = ori_vector / np.linalg.norm(ori_vector)
    q = quat.from_rotation_vector(norm_ori_vector)
    return quat.as_float_array(q)

def main():
    args = parse_args()

    FPS = 15
    DURATION = 2
    TOTAL_FRAMES =  FPS * DURATION

    # Plot limits
    x_min = -3
    x_max = 3
    y_min = -3
    y_max = 3
    z_min = -3
    z_max = 3

    SPHERE_R = 0.8
    SPHERE_CENTER = np.array([0.2, -1.5, 0])


    # # Create Points ( on the sphere )
    def s2c(radius, theta, gamma):
        return np.asarray([
            radius * np.cos(gamma) * np.cos(theta),
            radius * np.sin(gamma) * np.cos(theta),
            radius * np.sin(theta)
        ])

    min_torsion = SPHERE_R * 0.5
    max_torsion = SPHERE_R * 1


    torsion_color_scale = ColorScale(min_value=min_torsion,
                                     max_value=max_torsion,
                                     colors='turbo')

    D = np.pi

    # a bit farther away to prevent clipping
    p0 = s2c(SPHERE_R, D/4, 0)
    p1 = s2c(SPHERE_R, 0,   0)
    p2 = s2c(SPHERE_R, D/4, D/2)
    p3 = s2c(SPHERE_R, 0,   D/2)

    control_points = [p0, p1, p2, p3]

    # Create a new scene
    scene, _ = create_3d_scene([x_min, x_max], [y_min, y_max], [z_min, z_max])
    # draw_xyz_axes()

    set_solid_color_background(scene, (0.009, 0.009, 0.009, 1.0))


    # plot the points as arrows from the origin
    for p in control_points:
        torsion = np.linalg.norm(p)
        color_val = list(torsion_color_scale.get_color(torsion)) + [1.0]
        draw_arrow(SPHERE_CENTER, SPHERE_CENTER+p, color=color_val)
        draw_points([SPHERE_CENTER+p], color=color_val)

    # draw sphere
    draw_sphere(SPHERE_CENTER, SPHERE_R,
                rings=32,
                color=(0.5, 0.5, 0.7, 0.1))


    # plot the so3 bezier interpolation
    so3_curve = bezier_fitting.SO3Bezier(control_points, rot_type='rot_vec')

    def curve(t):
        rot = so3_curve.evaluate_so3(t)
        return quat.as_rotation_vector(np.quaternion(*rot.coeffs()))

    def curve_quaternion(t):
        rot = so3_curve.evaluate_so3(t)
        return quat.from_float_array(rot.coeffs())

    text = create_text(scene, 'Lie Lerp',
                       align_y='BOTTOM',
                       size = 0.7)

    rigid_movement(text, [0,np.pi/2,np.pi/2], [0,0,1.2], rot_type='euler_ZYZ')
    # TODO fix point at camera
    rotate_around_axis(text, [0,0,1], 0.35)


    # interpolation curve

    # plot the rotation vectors as arrow from the origin
    for t in np.linspace(0, 1, 20):
        # evaluate orientation with squad
        p = curve(t)
        torsion = np.linalg.norm(p)
        color_val = list(torsion_color_scale.get_color(torsion)) + [1.0]
        draw_arrow(SPHERE_CENTER, p+SPHERE_CENTER, color=color_val)

    # plot the rot_vector line
    draw_parametric_curve(lambda t : curve(t) + SPHERE_CENTER,
                          color=(1.0, 1.0, 0.0, 1.0),
                          resolution=30)
    bezier_point = draw_points([curve(0) + SPHERE_CENTER], color=(1.0, 1.0, 0.0, 1.0))[0]

    # Keyframes
    set_animation(scene,
                  fps=FPS,
                  frame_start=1,
                  frame_end=TOTAL_FRAMES,
                  frame_current=1,
                  file_format='AVI_JPEG')


    # add a stl model
    stl_q = quat.as_float_array(quat.from_rotation_vector( np.array([0,1,0])*np.pi ))
    stl_model = import_stl("resources/stl/ManetaFT.stl",
                           scale=0.01,
                           location=(-0.50,1,0),
                           rotation=stl_q
                           )

    # rotate_around_axis

    for i in range(1, TOTAL_FRAMES+1):
        rotation = np.quaternion(curve_quaternion(i/TOTAL_FRAMES)) * np.quaternion(*stl_q)
        set_world_pose(stl_model,
                       rotation=quat.as_float_array(rotation))

        axis_angle = curve(i/TOTAL_FRAMES)
        color_val = list(torsion_color_scale.get_color(np.linalg.norm(axis_angle))) + [1.0]
        set_world_pose(bezier_point,
                       translation=axis_angle + SPHERE_CENTER)
        stl_model.keyframe_insert(data_path='rotation_euler', frame=i)
        bezier_point.keyframe_insert(data_path='location', frame=i)

        bezier_point.active_material.diffuse_color = color_val
        bezier_point.active_material.keyframe_insert(data_path='diffuse_color', frame=i)



    # Render the scene
    if args.filename is None:
        filename = __file__.split("/")[-1].split(".")[0]
    else:
        filename = args.filename
    imf_filename = lambda s: f'renders/{filename}/{filename}_{s}'

    if args.video:
        animation = True
    else:
        animation = False
        bpy.context.scene.frame_set(args.frame)

    if args.cycles:
        cycles_render(scene, imf_filename('cycles'), animation=animation)
    elif args.eevee:
        eevee_render(scene, imf_filename('eevee'), animation=animation)
    else:
        workbench_render(scene, imf_filename('workbench'), animation=animation)

    if args.frame is None:
        filepath_avi = scene.render.filepath
        avi2mp4(filepath_avi)

    # Close blender
    bpy.ops.wm.quit_blender()



if __name__ == '__main__':
    main()
