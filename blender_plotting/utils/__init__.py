import os

def get_assets_path():
    """Get the path to the assets folder."""

    return os.path.dirname(os.path.realpath(__file__)) + "/blender_cli_rendering/assets"
