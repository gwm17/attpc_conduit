from .pad_map import PadMap
from .constants import INVALID_EVENT_NUMBER
from .get_event import GetEvent

import numpy as np


class PointCloud:
    """Representation of a AT-TPC event

    A PointCloud is a geometric representation of an event in the AT-TPC
    The GET traces are converted into points in space within the AT-TPC

    Attributes
    ----------
    event_number: int
        The event number
    cloud: ndarray
        The Nx8 array of points in AT-TPC space
        Each row is [x,y,z,amplitude,integral,pad id,time,scale]

    Methods
    -------
    PointCloud()
        Create an empty point cloud
    load_cloud_from_get_event(event: GetEvent, pmap: PadMap, corrector: ElectronCorrector)
        Load a point cloud from a GetEvent
    load_cloud_from_hdf5_data(data: ndarray, event_number: int)
        Load a point cloud from an hdf5 file dataset
    is_valid() -> bool
        Check if the point cloud is valid
    retrieve_spatial_coordinates() -> ndarray
        Get the positional data from the point cloud
    calibrate_z_position(micromegas_tb: float, window_tb: float, detector_length: float, ic_correction: float = 0.0)
        Calibrate the cloud z-position from the micromegas and window time references
    smooth_cloud(max_distance: float = 10.0)
        Smooth the point cloud data using an neighborhood of radius max_distance
    sort_in_z()
        Sort the internal point cloud array by z-position
    """

    def __init__(self):
        """Create an empty point cloud

        Returns
        -------
        PointCloud
            An empty point cloud
        """
        self.event_number: int = INVALID_EVENT_NUMBER
        self.cloud: np.ndarray = np.empty(0, dtype=np.float64)
        self.hw_labels: list[str] | None = None

    def load_cloud_from_get_event(self, event: GetEvent, pmap: PadMap):
        """Load a point cloud from a GetEvent

        Loads the points from the signals in the traces and applies
        the Garfield electron drift correction, pad relative gain correction,
        and the pad time correction

        Parameters
        ----------
        event: GetEvent
            The GetEvent whose data should be loaded
        pmap: PadMap
            The PadMap used to get pad correction values
        corrector: ElectronCorrector
            The Garfield electron drift correction
        """
        self.event_number = event.number
        count = 0
        for trace in event.traces:
            count += trace.get_number_of_peaks()
        self.cloud = np.zeros((count, 7))
        self.hw_labels = []
        idx = 0
        for trace in event.traces:
            if trace.get_number_of_peaks() == 0:
                continue

            pid = trace.hw_id.pad_id
            check = pmap.get_pad_from_hardware(trace.hw_id)
            if check is None:
                continue
            if check != pid:
                pid = check
            pad = pmap.get_pad_data(check)
            if pad is None:
                continue

            for peak in trace.get_peaks():
                self.cloud[idx, 0] = pad.x  # X-coordinate, geometry
                self.cloud[idx, 1] = pad.y  # Y-coordinate, geometry
                self.cloud[idx, 2] = (
                    peak.centroid + pad.time_offset
                )  # Z-coordinate, time with correction until calibrated with calibrate_z_position()
                self.cloud[idx, 3] = peak.amplitude
                self.cloud[idx, 4] = peak.integral
                self.cloud[idx, 5] = trace.hw_id.pad_id
                self.cloud[idx, 6] = (
                    peak.centroid + pad.time_offset
                )  # Time bucket with correction
                idx += 1
                self.hw_labels.append(str(trace.hw_id))
        good_rows = np.flatnonzero(self.cloud[:, 3])  # Non-zero elements only
        self.cloud = self.cloud[good_rows]

    def load_cloud_from_hdf5_data(
        self, data: np.ndarray, event_number: int, pmap: PadMap
    ):
        """Load a point cloud from an hdf5 file dataset

        Parameters
        ----------
        data: ndarray
            This should be a copy of the point cloud data from the hdf5 file
        event_number: int
            The event number
        """
        self.event_number: int = event_number
        self.cloud = data
        self.hw_labels = [str(pmap.get_pad_data(row[5]).hardware) for row in data]

    def is_valid(self) -> bool:
        """Check if the PointCloud is valid

        Returns
        -------
        bool
            True if the PointCloud is valid
        """
        return self.event_number != INVALID_EVENT_NUMBER

    def retrieve_spatial_coordinates(self) -> np.ndarray:
        """Get only the spatial data from the point cloud


        Returns
        -------
        ndarray
            An Nx3 array of the spatial data of the PointCloud
        """
        return self.cloud[:, 0:3]

    def get_hardware_labels(self) -> list[str]:
        if self.hw_labels is not None:
            return self.hw_labels
        else:
            return []

    def calibrate_z_position(
        self,
        micromegas_tb: float,
        window_tb: float,
        detector_length: float,
        ic_correction: float = 0.0,
    ):
        """Calibrate the cloud z-position from the micromegas and window time references

        Also applies the ion chamber time correction if given

        Parameters
        ----------
        micromegas_tb: float
            The micromegas time reference in GET Time Buckets
        window_tb: float
            The window time reference in GET Time Buckets
        detector_length: float
            The detector length in mm
        ic_correction: float
            The ion chamber time correction in GET Time Buckets (default=0.0)
        """
        for idx, point in enumerate(self.cloud):
            self.cloud[idx][2] = (window_tb - point[6]) / (
                window_tb - micromegas_tb
            ) * detector_length - ic_correction

    def smooth_cloud(self, max_distance: float = 10.0):
        """Smooth the point cloud by averaging over nearest neighbors by distance, weighted by the integrated charge.

        The neighborhood is defined to be a sphere of radius max_distance centered on the point being considered
        This modifies the underlying point cloud array.

        Note: in the conduit version, this also destroys the hardware labels, as they have no meaning after smoothing.

        Parameters
        ----------
        max_distance: float
            The maximum distance between two neighboring points
        """
        self.hw_labels = None
        smoothed_cloud = np.zeros(self.cloud.shape)
        for idx, point in enumerate(self.cloud):
            mask = (
                np.linalg.norm((self.cloud[:, :3] - point[:3]), axis=1) < max_distance
            )
            neighbors = self.cloud[mask]
            if len(neighbors) < 2:
                continue
            # Weight points
            weighted_average = np.average(neighbors, axis=0, weights=neighbors[:, 3])
            if np.isclose(weighted_average[4], 0.0):
                continue
            smoothed_cloud[idx] = weighted_average
        # Removes duplicate points
        smoothed_cloud = smoothed_cloud[smoothed_cloud[:, 3] != 0.0]
        _, indicies = np.unique(
            np.round(smoothed_cloud[:, :3], decimals=2), axis=0, return_index=True
        )
        self.cloud = smoothed_cloud[indicies]

    def sort_in_z(self):
        """Sort the internal point cloud array by the z-coordinate"""
        indicies = np.argsort(self.cloud[:, 2])
        self.cloud = self.cloud[indicies]
        if self.hw_labels is not None:
            self.hw_labels = [self.hw_labels[index] for index in indicies]
