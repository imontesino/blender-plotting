"""Tools for working with background images."""
from typing import Iterable
import bpy

def set_hdri_background(scene: bpy.types.Scene,
                        hdri_image_path: str,) -> None:
    """Set the background image to the given image path."""

    # Get the environment node tree of the current scene
    node_tree = scene.world.node_tree
    tree_nodes = node_tree.nodes

    # Clear all nodes
    tree_nodes.clear()

    # Add Background node
    node_background = tree_nodes.new(type='ShaderNodeBackground')

    # Add Environment Texture node
    node_environment = tree_nodes.new('ShaderNodeTexEnvironment')
    # Load and assign the image to the node property
    node_environment.image = bpy.data.images.load(hdri_image_path)
    node_environment.location = -300, 0

    # Add Output node
    node_output = tree_nodes.new(type='ShaderNodeOutputWorld')
    node_output.location = 200, 0

    # Link all nodes
    links = node_tree.links
    # Environment_[Color] -> [Color]_Background_[Background] --> [Surface]_World
    links.new(node_environment.outputs["Color"], node_background.inputs["Color"])
    links.new(node_background.outputs["Background"], node_output.inputs["Surface"])

def set_pastel_background(scene: bpy.types.Scene,
                          color: Iterable = (0.5, 0.5, 0.5, 0.1)) -> None:
    """Set the background to a pastel color."""

    # Get the environment node tree of the current scene
    node_tree = scene.world.node_tree
    tree_nodes = node_tree.nodes

    # Clear all nodes
    tree_nodes.clear()

    # Connect color out of Grad node to Color in of Background node

    # Add Background node
    node_background = tree_nodes.new(type='ShaderNodeBackground')
    node_background.inputs['Color'].default_value = color

    # Add Output node
    node_output = tree_nodes.new(type='ShaderNodeOutputWorld')
    node_output.location = 200, 0

    # Link all nodes
    links = node_tree.links
    links.new(node_background.outputs["Background"], node_output.inputs["Surface"])
