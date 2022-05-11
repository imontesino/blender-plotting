# WIP

import glob
import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

data_files = []
directories = glob.glob('blender_plotting/blender_cli_rendering/assets/**/*')
for directory in directories:
    files = glob.glob(directory+'*')
    data_files.append((directory, files))

# This call to setup() does all the work
setup(
    name="blender-plotting",
    version="0.1.0",
    description="A package for plotting data with Blender as a module",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/imontesino/blender-plotting",
    author="Ignacio Montesino",
    author_email="monte.igna@gmail.com",
    license="GPLv3",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(),
    data_files=data_files,
    include_package_data=True,
)
