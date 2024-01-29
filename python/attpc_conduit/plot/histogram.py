import numpy as np
from dataclasses import dataclass, field
from math import floor


def is_in_range(min_val, max_val, value) -> bool:
    return value > min_val and value < max_val


@dataclass
class Histogram1D:
    name: str = ""
    x_min: float = 0.0
    x_max: float = 0.0
    x_bins: int = 0
    x_bin_width: float = 0.0
    x_axis_title: str = ""
    y_axis_title: str = "Counts"
    counts: np.ndarray = field(default_factory=lambda: np.empty(0))


@dataclass
class Histogram2D:
    name: str = ""
    x_min: float = 0.0
    x_max: float = 0.0
    x_bins: int = 0
    x_bin_width: float = 0.0
    x_axis_title: str = ""
    y_min: float = 0.0
    y_max: float = 0.0
    y_bins: int = 0
    y_bin_width: float = 0.0
    y_axis_title: str = ""
    counts: np.ndarray = field(default_factory=lambda: np.empty(0))


class Histogrammer:
    def __init__(self):
        self.grams_1d: dict[str, Histogram1D] = {}
        self.grams_2d: dict[str, Histogram2D] = {}

    def add_1D(
        self,
        name: str,
        x_min: float,
        x_max: float,
        x_bins: int,
        x_axis_title: str,
    ):
        x_bin_width = (x_max - x_min) / float(x_bins)
        counts = np.zeros(x_bins, dtype=int)
        self.grams_1d[name] = Histogram1D(
            name, x_min, x_max, x_bins, x_bin_width, x_axis_title, "Counts", counts
        )

    def add_2D(
        self,
        name: str,
        x_min: float,
        x_max: float,
        x_bins: int,
        x_axis_title: str,
        y_min: float,
        y_max: float,
        y_bins: int,
        y_axis_title: str,
    ):
        x_bin_width = (x_max - x_min) / float(x_bins)
        y_bin_width = (y_max - y_min) / float(y_bins)
        counts = np.zeros((x_bins, y_bins), dtype=int)
        self.grams_2d[name] = Histogram2D(
            name,
            x_min,
            x_max,
            x_bins,
            x_bin_width,
            x_axis_title,
            y_min,
            y_max,
            y_bins,
            y_bin_width,
            y_axis_title,
            counts,
        )

    def fill_1D(self, name: str, x_value: float):
        if not name in self.grams_1d:
            return

        gram = self.grams_1d[name]
        x_bin = floor((x_value - gram.x_min) / gram.x_bin_width)
        if x_bin < 0 or x_bin >= gram.x_bins:
            return
        gram.counts[x_bin] += 1

    def fill_2D(self, name: str, x_value: float, y_value: float):
        if not name in self.grams_2d:
            return

        gram = self.grams_2d[name]
        x_bin = floor((x_value - gram.x_min) / gram.x_bin_width)
        y_bin = floor((y_value - gram.y_min) / gram.y_bin_width)
        if x_bin < 0 or x_bin >= gram.x_bins or y_bin < 0 or y_bin >= gram.y_bins:
            return

        gram.counts[x_bin, y_bin] += 1
