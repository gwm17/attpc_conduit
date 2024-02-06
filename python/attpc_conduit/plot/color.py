from cmap import Colormap
import numpy as np

# Hardcoded for now
POINT_COLORMAP: Colormap = Colormap("viridis")
LABEL_COLORMAP: Colormap = Colormap("seaborn:tab10")


def generate_point_colors(
    values: np.ndarray,
) -> list[tuple[float, float, float, float]]:
    max_val = np.max(values)
    return [POINT_COLORMAP(value / max_val).rgba for value in values]


def get_label_color(label: int) -> tuple[float, float, float, float]:
    color_label = label
    if color_label > 9:
        color_label %= 9
    return LABEL_COLORMAP(label).rgba
