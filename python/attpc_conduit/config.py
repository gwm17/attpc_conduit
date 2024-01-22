from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class DetectorParameters:
    """Parameters describing the detector configuration

    Attributes
    ----------
    magnetic_field: float
        The magnitude of the magnetic field in Tesla
    electric_field: float
        The magnitude of the electric field in V/m
    detector_length: float
        The detector length in mm
    beam_region_radius: float
        The beam region radius in mm
    micromegas_time_bucket: float
        The micromegas time reference in GET time buckets
    window_time_bucket: float
        The window time reference in GET time buckets
    get_frequency: float
        The GET DAQ sampling frequency in MHz. Typically 3.125 or 6.25

    """

    magnetic_field: float = 0.0  # Tesla
    electric_field: float = 0.0  # V/m
    detector_length: float = 0.0  # mm
    beam_region_radius: float = 0.0  # mm
    micromegas_time_bucket: float = 0.0
    window_time_bucket: float = 0.0
    get_frequency: float = 0.0  # MHz


@dataclass
class GetParameters:
    """Parameters for GET trace signal analysis

    Attributes
    ----------
    baseline_window_scale: float
        The scale factor for the basline correction algorithm
    peak_separation: float
        The peak separation parameter used in scipy.signal.find_peaks
    peak_prominence: float
        The peak prominence parameter used in scipy.signal.find_peaks
    peak_max_width: float
        The maximum peak width parameter used in scipy.signal.find_peaks
    peak_threshold: float
        The minimum amplitude of a valid peak
    """

    baseline_window_scale: float = 20.0
    peak_separation: float = 50.0
    peak_prominence: float = 20.0
    peak_max_width: float = 100.0
    peak_threshold: float = 25.0


@dataclass
class ClusterParameters:
    """Parameters for clustering, cluster joining, and cluster cleaning

    Attributes
    ----------
    min_cloud_size: int
        The minimum size for a point cloud to be clustered
    smoothing_neighbor_distance: float
        Size of neighborhood radius in mm for smoothing
    min_points: int
        min_samples parameter in scikit-learns' HDBSCAN algorithm
    big_event_cutoff: int
        the cutoff between big events and small events in units of points in the
        point cloud
    min_size_big_event: int
        min_cluster_size parameter in scikit-learn's HDBSCAN algorithm for events with more
        points than `big_event_cutoff`. The minimum size of a cluster.
    min_size_small_event: int
        min_cluster_size parameter in scikit-learn's HDBSCAN algorithm for events with fewer
        points than `big_event_cutoff`. The minimum size of a cluster.
    circle_overlap_ratio: float
        minimum overlap ratio between two circles in the cluster joining algorithm
    fractional_charge_threshold: float
        The maximum allowed difference between two clusters mean charge (relative to the larger mean charge of the two)
        for them to be joined
    n_neighbors_outlier_test: int
        Number of neighbors to use in scikit-learn's LocalOutlierFactor test
    """

    min_cloud_size: int = 0
    smoothing_neighbor_distance: float = 0.0  # mm
    min_points: int = 0
    big_event_cutoff: int = 0
    min_size_big_event: int = 0
    min_size_small_event: int = 0
    circle_overlap_ratio: float = 0.0
    fractional_charge_threshold: float = 0.0
    n_neighbors_outiler_test: int = 0


@dataclass
class EstimateParameters:
    """Parameters for physics estimation

    Attributes
    ----------
    min_total_trajectory_points: int
        minimum number of points in a cluster for the cluster to be considered a particle trajectory
    max_distance_from_beam_axis: float
        maximum distance from beam axis for a trajectory vertex to be considered valid
    """

    min_total_trajectory_points: int = 0
    max_distance_from_beam_axis: float = 0.0  # mm


class Conifg:
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
        self.detector = DetectorParameters()
        self.get = GetParameters()
        self.cluster = ClusterParameters()
        self.estimate = EstimateParameters()

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
            self.detector.magnetic_field = det_params["magnetic_field(T)"]
            self.detector.electric_field = det_params["electric_field(V/m)"]
            self.detector.detector_length = det_params["detector_length(mm)"]
            self.detector.beam_region_radius = det_params["beam_region_radius(mm)"]
            self.detector.micromegas_time_bucket = det_params["micromegas_time_bucket"]
            self.detector.window_time_bucket = det_params["window_time_bucket"]
            self.detector.get_frequency = det_params["get_frequency(MHz)"]

            get_params = config_data["GET"]
            self.get.baseline_window_scale = get_params["baseline_window_scale"]
            self.get.peak_separation = get_params["peak_separation"]
            self.get.peak_prominence = get_params["peak_prominence"]
            self.get.peak_max_width = get_params["peak_max_width"]
            self.get.peak_threshold = get_params["peak_threshold"]

            cluster_params = config_data["Cluster"]
            self.cluster.min_cloud_size = cluster_params["min_cloud_size"]
            self.cluster.smoothing_neighbor_distance = cluster_params[
                "smoothing_neighbor_distance(mm)"
            ]
            self.cluster.big_event_cutoff = cluster_params["big_event_cutoff"]
            self.cluster.min_size_big_event = cluster_params["minimum_size_big_event"]
            self.cluster.min_size_small_event = cluster_params[
                "minimum_size_small_event"
            ]
            self.cluster.min_points = cluster_params["minimum_points"]
            self.cluster.circle_overlap_ratio = cluster_params["circle_overlap_ratio"]
            self.cluster.fractional_charge_threshold = cluster_params[
                "fractional_charge_threshold"
            ]
            self.cluster.n_neighbors_outiler_test = cluster_params[
                "n_neighbors_outlier_test"
            ]

            est_params = config_data["Estimate"]
            self.estimate.min_total_trajectory_points = est_params[
                "mininum_total_trajectory_points"
            ]
            self.estimate.max_distance_from_beam_axis = est_params[
                "maximum_distance_from_beam_axis"
            ]
