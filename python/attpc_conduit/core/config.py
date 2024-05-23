from pathlib import Path
import json
from enum import Enum
from typing import TypeVar, Generic
from spyral import (
    PadParameters,
    GetParameters,
    DetectorParameters,
    ClusterParameters,
    EstimateParameters,
    INVALID_PATH,
)


class ParamType(Enum):
    FLOAT = 0
    INT = 1
    UNUSED = 2


# This is a generic type alias used for param properties
T = TypeVar("T", int, float)


# By giving this class a generic, it can represent parameters for both Integer and Floating point values
# and still be readable to the type checker (in comparision to defining as int | float which works but is
# not readable to the type checker when values are called)
class ParamProperties(Generic[T]):
    """Class providing parameter validation to UI"""

    def __init__(
        self,
        label: str,
        min_val: T,
        max_val: T,
        default: T,
        ptype: ParamType,
    ):
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.default = default
        self.type = ptype


detector_param_props: dict[str, ParamProperties] = {
    "magnetic_field": ParamProperties(
        "Magnetic Field (T)", 0.0, 6.0, 3.0, ParamType.FLOAT
    ),
    "electric_field": ParamProperties(
        "Electric Field (V/m)", 0.0, 80000.0, 45000.0, ParamType.FLOAT
    ),
    "detector_length": ParamProperties(
        "Detector Length (mm)", 0.0, 2000.0, 1000.0, ParamType.FLOAT
    ),
    "beam_region_radius": ParamProperties(
        "Beam Region Radius (mm)", 0.0, 100.0, 30.0, ParamType.FLOAT
    ),
    "micromegas_time_bucket": ParamProperties(
        "MM Time Bucket", 0.0, 600.0, 40.0, ParamType.FLOAT
    ),
    "window_time_bucket": ParamProperties(
        "Window Time Bucket", 0.0, 600.0, 420.0, ParamType.FLOAT
    ),
    "get_frequency": ParamProperties(
        "GET Freq. (MHz)", 0.0, 6.25, 3.125, ParamType.FLOAT
    ),
    "garfield_file_path": ParamProperties(
        "Gafield File", 0.0, 1.0, "bleh", ParamType.UNUSED
    ),
    "do_garfield_correction": ParamProperties(
        "Apply Gafield File", 0.0, 1.0, False, ParamType.UNUSED
    ),
}


get_param_props: dict[str, ParamProperties] = {
    "baseline_window_scale": ParamProperties(
        "Baseline Scale", 0.0, 200.0, 20.0, ParamType.FLOAT
    ),
    "peak_separation": ParamProperties(
        "Peak Separation", 0.0, 200.0, 50.0, ParamType.FLOAT
    ),
    "peak_prominence": ParamProperties(
        "Peak Prominence", 0.0, 200.0, 20.0, ParamType.FLOAT
    ),
    "peak_max_width": ParamProperties(
        "Peak Max Width", 0.0, 200.0, 100.0, ParamType.FLOAT
    ),
    "peak_threshold": ParamProperties(
        "Peak Max Width", 0.0, 200.0, 25.0, ParamType.FLOAT
    ),
}


cluster_param_props: dict[str, ParamProperties] = {
    "min_cloud_size": ParamProperties(
        "Min Cloud Size (points)", 0, 300, 50, ParamType.INT
    ),
    "min_points": ParamProperties("Min Points", 0, 10, 3, ParamType.INT),
    "min_size_scale_factor": ParamProperties(
        "Min Size Scale Factor", 0.0, 0.3, 0.05, ParamType.FLOAT
    ),
    "min_size_lower_cutoff": ParamProperties(
        "Min Size Lower Limit", 0, 20, 10, ParamType.INT
    ),
    "cluster_selection_epsilon": ParamProperties(
        "Cluster Selection Epsilon", 0.0, 30.0, 10.0, ParamType.FLOAT
    ),
    "circle_overlap_ratio": ParamProperties(
        "Circle Overlap Ratio", 0.0, 1.0, 0.5, ParamType.FLOAT
    ),
    "outlier_scale_factor": ParamProperties(
        "Outlier Test Scale Factor", 0.0, 1.0, 0.05, ParamType.FLOAT
    ),
}


estimate_param_props: dict[str, ParamProperties] = {
    "min_total_trajectory_points": ParamProperties(
        "Min Points", 0, 600, 50, ParamType.INT
    ),
    "smoothing_factor": ParamProperties(
        "Smoothing", 0.0, 500.0, 100.0, ParamType.FLOAT
    ),
}


class Config:
    """Class representing a Conduit configuration

    Attributes
    ----------
    detector: DetectorParameters
        Parameters which express the physical properties of the detector
    get: GetParameters
        Parameters which control the GET signal analysis
    cluster: ClusterParameters
        Parameters which control the clustering analysis
    estimate: EstimateParameters
        Paramters which control the physics estimation analysis

    Methods
    -------
    Config(path: Path | None = None)
        Construct the Config object. If a Path is given, load the configuration from that file path (JSON).
    load(path: Path)
        Load the configuration stored in the JSON file at Path.
    """

    def __init__(self, path: Path | None = None):
        """Construct the Config object.

        If a path is given, the data stored in the associated file (JSON) is loaded. Otherwise,
        the Config is initialized with default (invalid) values.

        Parameters
        ----------
        path: Path | None
            An optional path to a JSON file containing a valid configuration

        Returns
        -------
        Config:
            The Config object
        """
        # Idk how to switch this yet
        self.pads = PadParameters(
            is_default=True,
            is_default_legacy=False,
            pad_gain_path=INVALID_PATH,
            pad_geometry_path=INVALID_PATH,
            pad_time_path=INVALID_PATH,
            pad_electronics_path=INVALID_PATH,
            pad_scale_path=INVALID_PATH,
        )
        self.detector = DetectorParameters(
            magnetic_field=3.0,
            electric_field=45000.0,
            detector_length=1000.0,
            beam_region_radius=30.0,
            micromegas_time_bucket=10,
            window_time_bucket=560,
            get_frequency=6.25,
            garfield_file_path=INVALID_PATH,
            do_garfield_correction=False,
        )
        self.get = GetParameters(
            baseline_window_scale=20.0,
            peak_separation=50.0,
            peak_prominence=20.0,
            peak_max_width=100.0,
            peak_threshold=25.0,
        )
        self.cluster = ClusterParameters(
            min_cloud_size=50,
            min_points=3,
            min_size_scale_factor=0.05,
            min_size_lower_cutoff=10,
            cluster_selection_epsilon=10.0,
            circle_overlap_ratio=0.5,
            outlier_scale_factor=0.5,
        )
        self.estimate = EstimateParameters(
            min_total_trajectory_points=30, smoothing_factor=100.0
        )

        if path is not None:
            self.load(path)

    def load(self, path: Path):
        """Load (deserialize) a configuration from a JSON file

        Parameters
        ----------
        path: Path
            The path to a JSON file containing a valid configuration
        """
        with open(path, "r") as config_file:
            config_data = json.load(config_file)
            det_params = config_data["Detector"]
            for key in det_params.keys():
                self.detector.__dict__[key] = det_params[key]
            get_params = config_data["GET"]
            for key in get_params.keys():
                self.get.__dict__[key] = get_params[key]
            cluster_params = config_data["Cluster"]
            for key in cluster_params.keys():
                self.cluster.__dict__[key] = cluster_params[key]
            est_params = config_data["Estimate"]
            for key in est_params.keys():
                self.estimate.__dict__[key] = est_params[key]

    def save(self, path: Path):
        with open(path, "w") as json_file:
            json.dump(
                self,
                json_file,
                default=lambda obj: {
                    "Detector": obj.detector.__dict__,
                    "GET": obj.get.__dict__,
                    "Cluster": obj.cluster.__dict__,
                    "Estimate": obj.estimate.__dict__,
                },
                indent=4,
            )
