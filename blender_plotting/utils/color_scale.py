import colorsys
from typing import Iterable, Union

import numpy as np

COMMON_SCALES = {
    'viridis':np.asarray([
                [51, 0, 99],
                [5, 99, 88],
                [45, 173, 64],
                [255, 230, 0]
              ])/255,
    'magma': np.asarray([
                [1,0,4],
                [57,1,102],
                [225,59,80],
                [249,252,173]
              ])/255,
    'heat': np.asarray([
                [255,255,255],
                [255,236,10],
                [251,109,8],
                [252,0,5]
               ])/255,
    'rainbow': np.asarray([
                [1,0,0],
                [1,1,0],
                [0,1,0],
                [0,1,1],
                [0,0,1],
                [1,0,1],
                [1,0,0]
               ]),
    'turbo': np.asarray([
                [48,18,59],    # dark purple
                [70,102,221], # blue
                [27,229,181], # teal
                [166,250,59], # soft green
                [220,225,55], # gold
                [250,124,31], # orange
                [206,45,4],  # gold
                [122,12,2]   # garnet
              ])/255,
    'mako': np.asarray([
                [218,243,225],
                [84,202,173],
                [53,121,162],
                [62,51,103],
                [13,4,8]
            ])/255
}

def squaredlerp(points, t):
    """Returns the squared linear interpolation of the points.
    """
    points = np.asarray(points)
    N = len(points) - 1
    if N == 0:
        return points[0]

    for i, a in enumerate(np.linspace(0,1,N+1)):
        if t <= a + 1/N:
            delta = t - a
            delta = np.clip(delta / (1/N), 0, 1)  # prevent floating point errors
            if delta < 0:
                raise ValueError(f't is out of range: t: {t}, a: {a}, delta: {delta}')
            p = np.sqrt((1-delta)*points[i]**2 + delta*points[i+1]**2)
            break

    return p


# create color map
class ColorScale():
    """Class to convert a scalar value in a range to a color."""

    def __init__(self,
                 min_value: float = 0,
                 max_value: float = 1,
                 invert: bool = False,
                 colors: Union[Iterable[Iterable[float]], str] = "viridis",):
        """ Create a color scale.

        Args:
            min_value: The minimum value of the scale.
                Defaults to 0.
            max_value: The maximum value of the scale.
                Defaults to 1.
            invert: Invert the color scale direction.
                Defaults to False.
            colors: The colors to use for the scale. Either a list of normalized RGB colors,
                or a string that can be used to look up a common color scale. See
                `blender_plotting.utils.color_scale.COMMON_SCALES`.
                Default: 'viridis'
        """
        self.min_value = min_value
        self.max_value = max_value
        self.colors = colors
        self.color_map = None
        self.min_value = min_value
        self.max_value = max_value
        if isinstance(colors, str):
            self.colors = COMMON_SCALES[colors]
        else:
            self.colors = np.asarray(colors)

        if invert:
            self.colors = self.colors[::-1]

    def get_color(self,
                  value,
                  ret_type='rgb'):
        """
        Convert a scalar value to a color

        Args:
            scalar (float): value to convert
            min_value (float): minimum value
            max_value (float): maximum value
            min_color (list): RGB color for minimum value
            max_color (list): RGB color for maximum value
            ret_type (str): 'rgb', 'hsv', or 'hex'

        Returns:
            list: RGB color for scalar value
        """

        # make sure scalar is in the range
        value = max(min(value, self.max_value), self.min_value)

        # normalize the value
        value = (value - self.min_value) / (self.max_value - self.min_value)

        # Interpolate between the colors
        rgb_color = squaredlerp(self.colors, value)

        # return the color
        return self.__as_color_type(rgb_color, ret_type)

    def __as_color_type(self, rgb_color, ret_type='rgb'):
        r = rgb_color[0]
        g = rgb_color[1]
        b = rgb_color[2]
        if ret_type == 'rgb':
            return rgb_color
        elif ret_type == 'hsv':
            return colorsys.rgb_to_hsv(r, g, b)
        elif ret_type == 'hex':
            return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
        else:
            raise ValueError(f'ret_type must be one of: {["rgb", "hsv", "hex"]}')
