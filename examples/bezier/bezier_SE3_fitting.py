import argparse
from audioop import lin2adpcm

import bpy
import manifpy
import bezier_fitting
import numpy as np
import quaternion as quat

from blender_plotting.utils.background import set_solid_color_background
from blender_plotting.utils.cad import import_stl
from blender_plotting.utils.curves import draw_parametric_curve
from blender_plotting.utils.files import avi2mp4
from blender_plotting.utils.movement import rigid_movement, rotate_around_axis, set_world_pose
from blender_plotting.utils.renderers import cycles_render, eevee_render, set_animation, workbench_render
from blender_plotting.utils.scenes import create_3d_scene, draw_xyz_axes
from blender_plotting.utils.shapes import draw_arrow, draw_points
from blender_plotting.utils.text import create_text

def parse_args():
    parser = argparse.ArgumentParser(description='Draw a R2 plane.')
    parser.add_argument('--cycles', action='store_true', help='Use Cycles.')
    parser.add_argument('--eevee', action='store_true', help='Use Eevee.')
    parser.add_argument('--filename', type=str, default=None, help='Output filename.')
    parser.add_argument('--frame', type=int, default=0, help='Frame number.')
    parser.add_argument('--video', action='store_true', help='Render video.')

    args = parser.parse_args()
    return args

def circle_y(x, R):
    return np.sqrt(R**2 - x**2)

def circle_orn(x, R):
    ori_vector = np.array([x, circle_y(x, R), 0.])
    norm_ori_vector = ori_vector / np.linalg.norm(ori_vector)
    q = quat.from_rotation_vector(norm_ori_vector)
    return quat.as_float_array(q)

def main():
    args = parse_args()

    FPS = 60
    DURATION = 10
    TOTAL_FRAMES =  FPS * DURATION

    # Plot limits
    x_min = -3
    x_max = 3
    y_min = -3
    y_max = 3
    z_min = -3
    z_max = 3


    NUM_POINTS = 20
    NOISE_MAG = 0.0
    MAX_ERROR = 0.001
    R = 2

    noise = lambda : np.random.rand()*np.array([1,1,1])*NOISE_MAG

    points = np.asarray([np.array([x, circle_y(x, R), 0]) + noise() for x in np.linspace(-R, R, NUM_POINTS)])
    orns =  np.asarray([circle_orn(x, R) for x in np.linspace(-R, R, NUM_POINTS)])

    se3_points = [manifpy.SE3(np.concatenate((point, orn))) for point, orn in zip(points, orns)]


    bezier_curve_points = bezier_fitting.fit_curve_se3(se3_points, MAX_ERROR, maxIterations=5000, maxSplitsLevel=2, tgFilterSize=1)

    bezier_curves = [bezier_fitting.SE3Bezier(curve_points) for curve_points in bezier_curve_points]

    bezier_spline = bezier_fitting.se3_bezier.SE3BezierSpline(bezier_curves)


    # Create a new scene
    scene, camera = create_3d_scene([x_min, x_max], [y_min, y_max], [z_min, z_max])
    draw_xyz_axes()

    set_solid_color_background(scene, (0.009, 0.009, 0.009, 1.0))

    text = create_text(scene, 'SE3 Bezier',
                       align_y='BOTTOM',
                       size = 0.7)

    rigid_movement(text, [0,np.pi/2,np.pi/2], [0,0,1.2], rot_type='euler_ZYZ')
    # TODO fix point at camera
    rotate_around_axis(text, [0,0,1], 0.35)


    # plot the points as arrows from the origin
    draw_points(points, color=(0.7,0.,0.,0.5))

    default_vector = np.array([0,0,-0.5])

    for point in se3_points:
        position = point.coeffs()[:3]
        ori_vector = point.rotation().dot(default_vector)
        draw_arrow(position, position+ori_vector, color=(0.7,0.,0.,0.5))

    for curve in bezier_curves:
        for t in np.linspace(0,1,10):
            curve_lie_pos = curve.evaluate_se3(t).coeffs()[:3]
            rotated_vector = curve.evaluate_se3(t).rotation().dot(default_vector)

            torsion = np.linalg.norm(ori_vector)

            draw_arrow(curve_lie_pos, curve_lie_pos+rotated_vector,
                       color=(0.8,0.8,0.5, 1.0))

        # draw_parametric_curve(lambda t: curve.evaluate_se3(t).coeffs()[:3],
        #                       resolution=50,
        #                       color=(0.8,0.8,0.5, 1.0))


    draw_parametric_curve(lambda t: bezier_spline.evaluate_se3(t).coeffs()[:3],
                          resolution=200,
                          color=(1,1,1, 1.0))

    # add a stl model
    stl_q = quat.as_float_array(quat.from_rotation_vector( np.array([0,1,0])*np.pi ))
    stl_model = import_stl("resources/stl/ManetaFT.stl",
                           scale=0.01,
                           location=(-0.50,1,0),
                           rotation=stl_q
                           )

    # # Keyframes
    set_animation(scene,
                  fps=FPS,
                  frame_start=1,
                  frame_end=TOTAL_FRAMES,
                  frame_current=1,
                  file_format='AVI_JPEG')

    # rotate_around_axis
    total_cam_rot_angle = np.pi / 4
    rot_angle_increment = total_cam_rot_angle / TOTAL_FRAMES
    for i in range(1, TOTAL_FRAMES+1):
        # Rotate the camera and the text
        t = (i-1) / TOTAL_FRAMES
        rotate_around_axis(camera, 'Z', rot_angle_increment)
        rotate_around_axis(text, 'Z', rot_angle_increment)
        camera.keyframe_insert(data_path='rotation_euler', frame=i)
        camera.keyframe_insert(data_path='location', frame=i)
        text.keyframe_insert(data_path='rotation_euler', frame=i)
        text.keyframe_insert(data_path='location', frame=i)

        # Move the STL model
        se3_position = bezier_spline.evaluate_se3(t).coeffs()
        position = se3_position[:3]
        rotation = se3_position[3:] # quaternion
        print(rotation)
        set_world_pose(stl_model,
                       translation=position,
                       rotation=rotation)

        # Rotation property is 'rotation_euler' independent of the rotation method
        stl_model.keyframe_insert(data_path='rotation_euler', frame=i)
        stl_model.keyframe_insert(data_path='location', frame=i)



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

    try:
        if args.cycles:
            cycles_render(scene, imf_filename('cycles'), animation=animation)
        elif args.eevee:
            eevee_render(scene, imf_filename('eevee'), animation=animation)
        else:
            workbench_render(scene, imf_filename('workbench'), animation=animation)

        if args.video:
            filepath_avi = scene.render.filepath
            avi2mp4(filepath_avi)

    except KeyboardInterrupt:
        print("Render canceled!")

    # Close blender
    bpy.ops.wm.quit_blender()


if __name__ == '__main__':
    main()
