from cmap import Colormap
import numpy as np

# Hardcoded for now
POINT_COLORMAP: Colormap = Colormap("viridis")
LABEL_COLORMAP: Colormap = Colormap("seaborn:tab10")


def generate_point_colors(
    values: np.ndarray,
) -> list[tuple[float, float, float, float]]:
    """Convert a 1-D array of values to a set of colors

    Use the cmap Colormap to convert a 1-D array of values to colors

    Parameters
    ----------
    values: ndarray
        Set of values to be colored. The max value in the array will be used to set the scale.

    Returns
    -------
    list[tuple[float, float, float, float]]
        The list of sRGBA values
    """
    max_val = np.max(values)
    return [POINT_COLORMAP(value / max_val).rgba for value in values]


def get_label_color(label: int) -> tuple[float, float, float, float]:
    """Convert a label integer into a color

    Use the cmap Colormap to convert a single integer into a color

    Parameters
    ----------
    label: int
        The label to be converted into a color.
    Returns
    -------
    tuple[float, float, float, float]
        The sRGBA value
    """
    color_label = label
    if color_label > 9:
        color_label %= 9
    return LABEL_COLORMAP(label).rgba
