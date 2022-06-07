import argparse
from audioop import lin2adpcm

import bpy
import manifpy
import bezier_fitting
from mathutils import Matrix, Quaternion
import numpy as np
import quaternion as quat

from blender_plotting.utils.background import set_solid_color_background
from blender_plotting.utils.cad import import_stl
from blender_plotting.utils.color_scale import ColorScale
from blender_plotting.utils.curves import draw_parametric_curve, draw_polyline
from blender_plotting.utils.files import avi2mp4
from blender_plotting.utils.geometry import rot_diff
from blender_plotting.utils.movement import rigid_movement, rotate_around_axis, set_world_pose
from blender_plotting.utils.renderers import cycles_render, eevee_render, set_animation, workbench_render
from blender_plotting.utils.scenes import create_3d_scene, draw_xyz_axes
from blender_plotting.utils.shapes import draw_arrow
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
    DURATION = 40
    TOTAL_FRAMES =  FPS * DURATION

    if args.video:
        print(f"Total frames: {TOTAL_FRAMES}")

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


    points = np.asarray([
        [
            [1, 0, 0],
            [0, 1, 0],
            [-0.2, -0.5, 0.5],
            [-1, 0, 0],
        ],
        [
            [-1, 0, 0],
            [0, 0, -1],
            [0.5, -0.5, 1],
            [-1, -1, 0],
        ]
    ])*np.array([2,4,2])

    points[1,0] = points[0,3]  # C0 continuitiy
    alpha = 1
    points[1,1] = points[1,0] + alpha*(points[0,3]-points[0,2])  # G1 continuity

    orns = np.asarray([
        [
            [0, 0, 0, 1],
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
        ],
        [
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [1, 0, 0, 0],
            [0, 0, 1, 0]
        ]
    ])

    orns[1,0] = orns[0,3]  # C0 continuitiy
    q_diff = quat.from_float_array(alpha*(rot_diff(orns[0,3], orns[0,2])))
    orns[1,1] = quat.as_float_array(q_diff*quat.from_float_array(orns[1,0])) # G1 continuity

    rot_color_scale = ColorScale(min_value=-np.pi,
                                max_value=np.pi,
                                colors='turbo')

    se3_origin = Matrix.Translation(points[0,0,:]).to_4x4() @ Quaternion(orns[0,0,:]).to_matrix().to_4x4()


    def draw_vector_representation(position, rot_quaternion):
        """ Transforms se3_points in the bezier curve into a vector representation."""
        position = np.asarray(position)
        rot_quaternion = np.asarray(rot_quaternion)
        scale = 0.4
        # se3_point = Matrix.Translation(position).to_4x4() @ Quaternion(rot_quaternion).to_matrix().to_4x4()
        # vec_reprs, vec_origin = se3_as_vector(se3_point, se3_origin=se3_origin, scale=0.2)
        rot_vector = quat.as_rotation_vector(quat.from_float_array(rot_quaternion))
        vec_reprs = rot_diff(orns[0,0], rot_vector, rot_type='rot_vec')
        color = rot_color_scale.get_color(np.linalg.norm(vec_reprs))
        return draw_arrow(position, position+vec_reprs*scale, color=list(color)+[1.0])

    def pq2se3(points, orns):
        return [manifpy.SE3(p, q) for p, q in zip(points, orns)]

    bezier_curve_points = [pq2se3(p, q) for p, q in zip(points, orns)]

    print("points:", points)
    print("curve points:", [p.coeffs() for p in bezier_curve_points[0]])
    print("curve points:", [p.coeffs() for p in bezier_curve_points[1]])

    bezier_curves = [bezier_fitting.SE3Bezier(curve_points) for curve_points in bezier_curve_points]
    bezier_spline = bezier_fitting.se3_bezier.SE3BezierSpline(bezier_curves)


    # Create a new scene
    scene, camera = create_3d_scene([x_min, x_max], [y_min, y_max], [z_min, z_max], camera_distance=15)
    draw_xyz_axes()

    set_solid_color_background(scene, (0.009, 0.009, 0.009, 1.0))

    text = create_text(scene, 'SE3 Bezier',
                       align_y='BOTTOM',
                       size = 0.7)

    rigid_movement(text, [0,np.pi/2,np.pi/2], [0,0,1.2], rot_type='euler_ZYZ')
    # TODO fix point at camera
    rotate_around_axis(text, [0,0,1], 0.35)

    # plot the points as arrows from the origin
    for bez_points in points:
        draw_polyline([bez_points[0], bez_points[1]],
                      color=(0.1, 0.2, 1., 1.0),
                      draw_markers=True,
                      marker_radius=0.1)
        draw_polyline([bez_points[2], bez_points[3]],
                      color=(0.1, 0.2, 1., 1.0),
                      draw_markers=True,
                      marker_radius=0.1)


    for bez_points, bez_quats in zip(points, orns):
        for p, q in zip(bez_points, bez_quats):
            draw_vector_representation(p, q)



    for t in np.linspace(0,1,100):
        curve_lie_pos = bezier_spline.evaluate_se3(t).coeffs()[:3]
        curve_lie_quat = bezier_spline.evaluate_se3(t).coeffs()[3:]

        draw_vector_representation(curve_lie_pos, curve_lie_quat)



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
    total_cam_rot_angle = np.pi / 2
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
            print("saved as " + avi2mp4(filepath_avi))


    except KeyboardInterrupt:
        print("Render canceled!")

    # Close blender
    bpy.ops.wm.quit_blender()


if __name__ == '__main__':
    main()
