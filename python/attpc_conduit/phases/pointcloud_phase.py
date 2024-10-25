from ..core.phase import PhaseLike, PhaseResult
from ..core.color import generate_point_colors
from ..core.static import RADIUS
from spyral.core.config import (
    GetParameters,
    DetectorParameters,
    PadParameters,
)
from spyral.core.pad_map import PadMap
from spyral.trace.get_event import GetEvent
from spyral.core.point_cloud import (
    point_cloud_from_get,
    sort_point_cloud_in_z,
    calibrate_point_cloud_z,
)

import numpy as np
from spyral_utils.plot import Histogrammer
import rerun as rr


class PointcloudPhase(PhaseLike):
    """The point cloud phase, inheriting from PhaseLike

    The goal of the point cloud phase is to convert AT-TPC trace data
    into point clouds. It uses a combination of Fourier transform baseline removal
    and scipy.signal.find_peaks to extract signals from the traces. PointcloudPhase
    is expected to be the first phase in the Pipeline.

    Parameters
    ----------
    get_params: GetParameters
        Parameters controlling the GET-DAQ signal analysis
    frib_params: FribParameters
        Parameters controlling the FRIBDAQ signal analysis
    detector_params: DetectorParameters
        Parameters describing the detector
    pad_params: PadParameters
        Parameters describing the pad plane mapping

    Attributes
    ----------
    get_params: GetParameters
        Parameters controlling the GET-DAQ signal analysis
    frib_params: FribParameters
        Parameters controlling the FRIBDAQ signal analysis
    det_params: DetectorParameters
        Parameters describing the detector
    pad_map: PadMap
        Map which converts trace ID to pad ID

    """

    def __init__(
        self,
        get_params: GetParameters,
        detector_params: DetectorParameters,
        pad_params: PadParameters,
    ):
        super().__init__(
            "Pointcloud",
        )
        self.get_params = get_params
        self.det_params = detector_params
        self.pad_map = PadMap(pad_params)

    def run(
        self,
        payload: PhaseResult,
        grammer: Histogrammer,
        rng: np.random.Generator,
    ) -> PhaseResult:
        # Process the data

        result = PhaseResult(None, False, payload.event_id)
        event = GetEvent(payload.artifact, payload.event_id, self.get_params, rng)
        cloud = point_cloud_from_get(event, self.pad_map)
        calibrate_point_cloud_z(cloud, self.det_params)
        sort_point_cloud_in_z(cloud)
        if len(cloud) == 0:
            return result
        colors = generate_point_colors(cloud.data[:, 3])
        result.artifact = cloud
        result.successful = True
        rr.log(
            "/event/cloud",
            rr.Points3D(cloud.data[:, :3], radii=RADIUS, colors=colors),
        )
        return result
