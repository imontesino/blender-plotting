FROM nvidia/cuda:11.3.0-devel-ubuntu20.04

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

ARG PYTHON_VER_MAJ=3.10
ARG BLENDER_VERSION=3.1.2
ARG USER=docker

# Run the next steps with bash
SHELL ["/bin/bash", "-c"]

# Dependencies
RUN apt-get update
RUN apt-get -y install \
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
    zlib1g-dev


# Install blender
# https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu

# Get the source code
WORKDIR /home/tmp
RUN git clone https://git.blender.org/blender.git
# Get the dependencies
WORKDIR /home/tmp/lib
RUN svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/linux_centos7_x86_64  # works for debian

WORKDIR /home/tmp/blender

# Checkout the desired version and clone the submodules
RUN git checkout -b v${BLENDER_VERSION} && \
    git submodule update --init --recursive

# Build blender as a python module
RUN make bpy

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

WORKDIR /home/${USER}/

# install python 3.10 fo the user
RUN sudo apt-get install software-properties-common -y &&\
    sudo add-apt-repository -y ppa:deadsnakes/ppa && \
    sudo apt-get update && \
    sudo apt-get install -y \
    python${PYTHON_VER_MAJ} \
    python${PYTHON_VER_MAJ}-dev \
    python${PYTHON_VER_MAJ}-venv \
    python${PYTHON_VER_MAJ}-gdbm \
    python${PYTHON_VER_MAJ}-tk \
    python${PYTHON_VER_MAJ}-distutils

# install pip
RUN sudo curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

RUN echo "alias python=python${PYTHON_VER_MAJ}" >> ~/.bashrc
RUN echo "alias python3=python${PYTHON_VER_MAJ}" >> ~/.bashrc
RUN echo "alias pip='python${PYTHON_VER_MAJ} -m pip'" >> ~/.bashrc
RUN echo "alias pip3='python${PYTHON_VER_MAJ} -m pip'" >> ~/.bashrc

RUN sudo cp /home/tmp/build_linux_bpy/bin/bpy.so /usr/local/lib/python$PYTHON_VER_MAJ/dist-packages
RUN sudo cp -r /home/tmp/lib/linux_centos7_x86_64/python/lib/python$PYTHON_VER_MAJ/* /usr/local/lib/python$PYTHON_VER_MAJ/dist-packages/
RUN sudo cp -r /home/tmp/lib/linux_centos7_x86_64/python/lib/python3.10/site-packages/3.3/ /usr/local/lib/python$PYTHON_VER_MAJ/dist-packages/

COPY docker_utils/ /home/${USER}/docker_utils/

RUN cp docker_utils/bash.bashrc ~/.bashrc && \
    python${PYTHON_VER_MAJ} -m pip completion --bash >> ~/.bashrc && \
    # Optional: Colorful bash prompt
    cat docker_utils/.docker-prompt  >> ~/.bashrc && \
    # Allow bash autocompletion
    sudo apt-get install -y bash-completion && \
    source /usr/share/bash-completion/completions/git

# test if it works
RUN python3.10 -c "import bpy;print(dir(bpy.types));print(bpy.app.version_string);"

RUN mkdir $HOME/workspace

WORKDIR /home/${USER}/workspace

CMD bash
