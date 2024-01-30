import numpy as np
from dataclasses import dataclass, field
from math import floor


def is_in_range(min_val: float, max_val: float, value: float) -> bool:
    """Check if a value is within a range

    Parameters
    ----------
    min_val: float
        The range minimum
    max_val: float
        The range maximum
    value: float
        The value to check

    Returns
    -------
    bool
        True if value is within the range, false otherwise
    """
    return value > min_val and value < max_val


@dataclass
class Histogram1D:
    """A 1D histogram dataclass

    Attributes
    ----------
    name: str
        The histogram name
    x_min: float
        The minimum value of the histogram x-axis
    x_max: float
        The maximum value of the histogram x-axis
    x_bins: int
        The number of bins along the histogram x-axis
    x_bin_width: float
        The width of a bin along the histogram x-axis
    x_axis_title: str
        The histogram x-axis title
    y_axis_title: str
        The histogram y-axis title
    counts: ndarray
        The histogram
    """

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
    """A 2D histogram dataclass

    Attributes
    ----------
    name: str
        The histogram name
    x_min: float
        The minimum value of the histogram x-axis
    x_max: float
        The maximum value of the histogram x-axis
    x_bins: int
        The number of bins along the histogram x-axis
    x_bin_width: float
        The width of a bin along the histogram x-axis
    x_axis_title: str
        The histogram x-axis title
    y_min: float
        The minimum value of the histogram y-axis
    y_max: float
        The maximum value of the histogram y-axis
    y_bins: int
        The number of bins along the histogram y-axis
    y_bin_width: float
        The width of a bin along the histogram y-axis
    y_axis_title: str
        The histogram y-axis title
    counts: ndarray
        The histogram
    """

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
    """Class for handling histogramming data

    Many histogramming tools in Python are designed around receiving columnar dataformats
    and efficiently binning chunks of data (i.e. pandas, polars, etc). But for online analysis
    this isn't effective. We would need to store enoromous dataframes or databases of long running experiments
    and constantly append to them. Instead, we create the histograms and fill them with data by incrementing the bin
    values.

    Attributes
    ----------
    grams_1d: dict[str, Histogram1D]
        The dictionary of Histogram1D's
    grams_2d: dict[str, Histogram2D]
        The dictionary of Histogram2D's

    Methods
    -------
    Histogrammer()
        Create the Histogrammer
    add_1D(name: str, x_min: float, x_max: float, x_bins: int, x_axis_title: str)
        Add a new 1D histogram to the Histogrammer
    add_2D(name: str, x_min: float, x_max: float, x_bins: int, x_axis_title: str, y_min: float, y_max: float, y_bins: int, y_axis_title: str)
        Add a new 2D histogram to the Histogrammer
    fill_1D(name, x_value: float)
        Fill a 1D histogram with a value
    fill_2D(name, x_value: float, y_value: float)
        Fill a 2D histogram with a value
    """

    def __init__(self):
        """Create the Histogrammer"""
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
        """Add a new 1D histogram to the Histogrammer

        Parameters
        ----------
        name: str
            The histogram name
        x_min: float
            The minimum value of the histogram x-axis
        x_max: float
            The maximum value of the histogram x-axis
        x_bins: int
            The number of bins along the histogram x-axis
        x_axis_title: str
            The histogram x-axis title
        """
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
        """Add a new 2D histogram to the Histogrammer

        Parameters
        ----------
        name: str
            The histogram name
        x_min: float
            The minimum value of the histogram x-axis
        x_max: float
            The maximum value of the histogram x-axis
        x_bins: int
            The number of bins along the histogram x-axis
        x_axis_title: str
            The histogram x-axis title
        y_min: float
            The minimum value of the histogram y-axis
        y_max: float
            The maximum value of the histogram y-axis
        y_bins: int
            The number of bins along the histogram y-axis
        y_axis_title: str
            The histogram y-axis title
        """
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
        """Fill a 1D histogram with a value

        Parameters
        ----------
        name: str
            The name of the histogram to be filled
        x_value: float
            The value along the histogram x-axis
        """
        if not name in self.grams_1d:
            return

        gram = self.grams_1d[name]
        x_bin = floor((x_value - gram.x_min) / gram.x_bin_width)
        if x_bin < 0 or x_bin >= gram.x_bins:
            return
        gram.counts[x_bin] += 1

    def fill_2D(self, name: str, x_value: float, y_value: float):
        """Fill a 2D histogram with a value

        Parameters
        ----------
        name: str
            The name of the histogram to be filled
        x_value: float
            The value along the histogram x-axis
        y_value: float
            The value along the histogram y-axis
        """
        if not name in self.grams_2d:
            return

        gram = self.grams_2d[name]
        x_bin = floor((x_value - gram.x_min) / gram.x_bin_width)
        y_bin = floor((y_value - gram.y_min) / gram.y_bin_width)
        if x_bin < 0 or x_bin >= gram.x_bins or y_bin < 0 or y_bin >= gram.y_bins:
            return

        gram.counts[x_bin, y_bin] += 1
