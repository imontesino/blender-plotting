#!/usr/bin/env python3
""" CLI Tool to build bpy docker images and package the python modules.
"""
import argparse
import subprocess

import pandas as pd
from packaging import version


def parse_args():
    parser = argparse.ArgumentParser(description='Build bpy docker images and package the python modules.')
    parser.add_argument('--blender_version', '-b', type=str, default=None,
                        help='Build container for that blender version.')
    parser.add_argument('--python_version', '--py', type=str, default=None,
                        help='Build container to build the module for that python version.')
    parser.add_argument('--gpu', action='store_true', help='Build container with GPU support.')
    parser.add_argument('--gpu_image', type=str, default='nvidia/cuda:11.3.0-devel-ubuntu20.04',
                        help='GPU image to use for the GPU build. IMPORTANT: must match the drivers in the host pc.')
    parser.add_argument('--tag', '-t', type=str, default='None',
                        help='Tag for the docker image.')
    parser.add_argument('--no_cache', action='store_true', help='Build without cache.')
    parser.add_argument('--builder_cpus', type=int, default=0,
                        help='Number of CPUs to use for the build.')
    parser.add_argument('--dummy', action='store_true',
                        help='Print the docker build command without executing it.')
    args = parser.parse_args()
    return args

def set_bpy_options(python_major_minor, gpu_support=False):
    file_in = "docker_utils/bpy_module.cmake.template"
    file_out = "docker_utils/bpy_module.cmake"
    file_gpu = "docker_utils/add_gpu_support.cmake"

    # Read in the file
    with open(file_in, 'r') as file :
        filedata = file.read()

    # Replace the python version
    filedata = filedata.replace('<PYTHON_MIN_MAJ>', python_major_minor)

    # add gpu support if needed
    if gpu_support:
        with open(file_gpu, 'r') as file :
            filedata += file.read()

    # Write the file out again
    with open(file_out, 'w') as file:
        file.write(filedata)


def main():
    args = parse_args()

    blender_version = args.blender_version
    python_version = args.python_version
    gpu_support = args.gpu
    image_tag = args.tag
    builder_cpus = args.builder_cpus



    # Read the csv as strings
    df = pd.read_csv ('blender_python_table.csv', converters={i: str for i in range(100)})

    if blender_version is None:
        blender_version = '3.1'

    blender_versions = df['blender_version'].unique()

    if blender_version not in blender_versions:
        raise ValueError(f'Blender version {blender_version} not valid. Valid versions are {blender_versions}')

    min_python_version = df.loc[df['blender_version'] == blender_version, 'python_min_version'].values[0]

    if python_version is None:
        default_python = True
        python_version = min_python_version
    else:
        if version.parse(python_version) < version.parse(min_python_version):
            err_msg = f'Python version {python_version} is lower than the minimum version {min_python_version}'
            err_msg += f' for blender version {blender_version}'
            raise ValueError(err_msg)
        if python_version != min_python_version:
            default_python = False


    # Get the options dependent on the blender version
    gh_tag = df.loc[df['blender_version'] == blender_version, 'blender_gh_tag'].values[0]
    bpy_stubs = df.loc[df['blender_version'] == blender_version, 'bpy_stubs'].values[0]
    blender_svn_deps_tag = df.loc[df['blender_version'] == blender_version, 'blender_svn_deps_tag'].values[0]

    PYTHON_MAJ_MIN = python_version
    BLENDER_GH_TAG = gh_tag
    BPY_STUB_VERSION = bpy_stubs
    USER = 'docker'
    if image_tag is None:
        IMAGE_TAG = f'bpy-{PYTHON_MAJ_MIN}'
    if gpu_support:
        BASE_IMAGE = args.gpu_image
        IMAGE_TAG += '-gpu'
    else:
        BASE_IMAGE = 'ubuntu:20.04'

    # Set the bpy cmake options
    set_bpy_options(PYTHON_MAJ_MIN, gpu_support=gpu_support)

    # Build the docker image
    build_command = f'docker build -t {IMAGE_TAG}:{blender_version}'
    if args.no_cache:
        build_command += ' --no-cache'
        # set number of cpus via --cpuset-mems
    if builder_cpus > 0:
        build_command += f" --cpuset-cpus=0-{builder_cpus - 1}"
    build_command += f' --build-arg USER={USER}'
    build_command += f' --build-arg BASE_IMAGE={BASE_IMAGE}'
    build_command += f' --build-arg BLENDER_VERSION={blender_version}'
    build_command += f' --build-arg BLENDER_GH_TAG={BLENDER_GH_TAG}'
    build_command += f' --build-arg BLENDER_SVN_DEPS_TAG={blender_svn_deps_tag}'
    build_command += f' --build-arg PYTHON_MAJ_MIN={PYTHON_MAJ_MIN}'
    build_command += f' --build-arg BPY_STUB_VERSION={BPY_STUB_VERSION}'
    if not default_python:
        # TODO add argument to choose between building or using prebuilt deps
        raise NotImplementedError('Building with diffrent python version is not implemented yet')
    build_command += f' .'

    # Run the build command
    if args.dummy:
        print(build_command)
    else:
        subprocess.run(build_command, shell=True, check=True)

if __name__ == '__main__':
    main()
