from .core.config import GetParameters, DetectorParameters
from .core.pad_map import PadMap
from .core.point_cloud import PointCloud
from .core.get_event import GetEvent
import logging as log

import numpy as np


def phase_pointcloud(
    event_number: int,
    event_matrix: np.ndarray,
    pad_map: PadMap,
    get_params: GetParameters,
    detector_params: DetectorParameters,
) -> PointCloud:
    """Transform an event to a point cloud

    Generate point clouds from merged AT-TPC traces. Read in an event from the Conduit and
    convert the traces into point cloud events. This is the first phase of Spyral analysis.

    Parameters
    ----------
    event_number: int
        The event number to be processed
    event_matrix: np.ndarray
        The event trace matrix
    pad_map: PadMap
        A map of pad number to geometry/hardware/calibrations
    get_params: GetParameters
        Configuration parameters for GET data signal analysis (AT-TPC pads)
    detector_params: DetectorParameters
        Configuration parameters for physical detector properties

    Returns
    -------
    PointCloud
        The converted, position-calibrated point cloud
    """
    event = GetEvent(event_matrix, event_number, get_params)

    pc = PointCloud()
    pc.load_cloud_from_get_event(event, pad_map)

    pc.calibrate_z_position(
        detector_params.micromegas_time_bucket,
        detector_params.window_time_bucket,
        detector_params.detector_length,
    )

    return pc
