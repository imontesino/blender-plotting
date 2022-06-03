ARG BASE_IMAGE=ubuntu:20.04

#-- Setup common build envorinment for all versions --#
FROM ${BASE_IMAGE} AS base

LABEL mantainer="Ignacio Montesino"

RUN apt-get update

# Set Locales
RUN apt-get -y install locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV TZ=Europe/Madrid
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG USER=docker

# install sudo
RUN apt-get -y install sudo

# Create new user `${USER}` and disable
# password and gecos for later
# --gecos explained well here:
# https://askubuntu.com/a/1195288/635348
RUN adduser --disabled-password \
    --gecos '' ${USER}

#  Add new user ${USER} to sudo group
RUN adduser ${USER} sudo

# Ensure sudo group users are not
# asked for a password when using
# sudo command by ammending sudoers file
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> \
/etc/sudoers

# now we can set USER to the
# user we just created
USER ${USER}


# Run the next steps with bash
SHELL ["/bin/bash", "-c"]

# Dependencies
RUN sudo apt-get update
RUN sudo apt-get -y install \
    build-essential \
    bzip2 \
    cmake \
    curl \
    file \
    git \
    libffi-dev \
    libfreetype6 \
    libgl1-mesa-dev \
    libglew-dev \
    libglu1-mesa \
    libssl-dev \
    libx11-dev \
    libxcursor-dev \
    libxi-dev \
    libxi6 \
    libxinerama-dev \
    libxrandr-dev \
    libxrender1 \
    libxxf86vm-dev \
    nano \
    ncdu \
    subversion \
    sudo \
    wget \
    zlib1g-dev \
    ffmpeg
    # ffmpeg is required to save videos as mp4


# create the directory structure for blender source and dependencies

RUN mkdir -p /home/${USER}/blender_tmp/

# Get the source code
WORKDIR /home/${USER}/blender_tmp/
RUN git clone https://git.blender.org/blender.git



#-- Build blender for specified blender and python versions --#
FROM base as blender_builder

# ARGS are forgotten when building new intermediate image
ARG PYTHON_MAJ_MIN=3.10
ARG BLENDER_GH_TAG=3.1
ARG USER=docker

# install python to build blender
RUN sudo apt-get install software-properties-common -y &&\
    sudo add-apt-repository -y ppa:deadsnakes/ppa && \
    sudo apt-get update && \
    sudo apt-get install -y \
    python${PYTHON_MAJ_MIN} \
    python${PYTHON_MAJ_MIN}-dev \
    python${PYTHON_MAJ_MIN}-venv \
    python${PYTHON_MAJ_MIN}-gdbm \
    python${PYTHON_MAJ_MIN}-tk \
    python${PYTHON_MAJ_MIN}-distutils

# install pip
RUN sudo curl -sS https://bootstrap.pypa.io/get-pip.py | python${PYTHON_MAJ_MIN}

WORKDIR /home/${USER}/blender_tmp/blender

# Checkout the desired version and clone the submodules
RUN git checkout ${BLENDER_GH_TAG} && \
    git submodule update --init --recursive

# Copy the modified bpy cmake variables
COPY docker_utils/bpy_module.cmake /home/${USER}/blender_tmp/blender/build_files/cmake/config

# Get the dependencies
ARG BLENDER_SVN_DEPS_TAG=blender-3.1-release

# TODO make optional through arguments or separate dockerfiles?
# use prebuilt dependencies
RUN mkdir -p /home/${USER}/blender_tmp/lib
WORKDIR /home/${USER}/blender_tmp/lib
RUN svn checkout https://svn.blender.org/svnroot/bf-blender/tags/${BLENDER_SVN_DEPS_TAG}/lib/linux_centos7_x86_64/

# # Dependencies for building the blender dependencies
# RUN sudo apt-get install -y autoconf automake libtool yasm nasm tcl
# # command to build dependencies
# RUN cmake -H /build_files/build_environment \
# 	      -B build_linux/deps \
#           -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
# 	      -DHARVEST_TARGET=/home/${USER}/blender_tmp/lib/linux/ \
#           --log-level=ERROR
# # build dependencies
# RUN make -C build_linux/deps -j $(NPROCS)
# # install dependencies
# RUN sudo make -C build_linux/deps install

WORKDIR /home/${USER}/blender_tmp/blender
RUN make bpy
# BUILD_CMAKE_ARGS="-D PYTHON_VERSION=${PYTHON_MAJ_MIN} -D CMAKE_POSITION_INDEPENDENT_CODE=ON -U --log-level=ERROR"

#-- Install blender and other utilities for usage in docker --#

FROM blender_builder AS blender_installer

# ARGS are forgotten when building new intermediate image
ARG PYTHON_MAJ_MIN=3.10
ARG USER=docker
ARG BLENDER_VERSION=3.1

WORKDIR /home/${USER}/

RUN echo "alias python=python${PYTHON_MAJ_MIN}" >> ~/.bashrc
RUN echo "alias python3=python${PYTHON_MAJ_MIN}" >> ~/.bashrc
RUN echo "alias pip='python${PYTHON_MAJ_MIN} -m pip'" >> ~/.bashrc
RUN echo "alias pip3='python${PYTHON_MAJ_MIN} -m pip'" >> ~/.bashrc

RUN sudo cp /home/${USER}/blender_tmp/build_linux_bpy/bin/bpy.so /usr/local/lib/python${PYTHON_MAJ_MIN}/dist-packages
RUN sudo cp -r /home/${USER}/blender_tmp/build_linux_bpy/bin/${BLENDER_VERSION} /usr/local/lib/python${PYTHON_MAJ_MIN}/dist-packages/
RUN sudo cp -r /home/${USER}/blender_tmp/lib/linux_centos7_x86_64/python/lib/python${PYTHON_MAJ_MIN}/* /usr/local/lib/python${PYTHON_MAJ_MIN}/dist-packages/

COPY docker_utils/ /home/${USER}/docker_utils/

RUN cp docker_utils/bash.bashrc ~/.bashrc && \
    python${PYTHON_MAJ_MIN} -m pip completion --bash >> ~/.bashrc && \
    # Optional: Colorful bash prompt
    cat docker_utils/.docker-prompt  >> ~/.bashrc && \
    # Allow bash autocompletion
    sudo apt-get install -y bash-completion && \
    source /usr/share/bash-completion/completions/git

# # test if it works
RUN python${PYTHON_MAJ_MIN} -c "import bpy;print(dir(bpy.types));print(bpy.app.version_string);"

RUN sudo apt-get install python3-pip -y

# install stub file for IDE autocompletion
ARG BPY_STUB_VERSION=3.1.0.26.dev2145740619
RUN pip install blender-stubs==${BPY_STUB_VERSION}

RUN mkdir $HOME/workspace

WORKDIR /home/${USER}/workspace

# Set entrypoint as bash after loading bashrc
ENTRYPOINT ["/bin/bash"]
