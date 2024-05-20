from ..core.phase import PhaseLike, PhaseResult
from ..core.color import generate_point_colors
from ..core.static import RADIUS
from spyral.core.status_message import StatusMessage
from spyral.core.config import (
    FribParameters,
    GetParameters,
    DetectorParameters,
    PadParameters,
)
from spyral.correction import (
    generate_electron_correction,
    create_electron_corrector,
    ElectronCorrector,
)
from spyral.core.pad_map import PadMap
from spyral.trace.get_event import GetEvent
from spyral.core.point_cloud import PointCloud

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

        result = PhaseResult(PointCloud(), True, payload.event_id)

        event = GetEvent(payload.artifact, payload.event_id, self.get_params, rng)
        result.artifact.load_cloud_from_get_event(event, self.pad_map)
        result.artifact.calibrate_z_position(
            self.det_params.micromegas_time_bucket,
            self.det_params.window_time_bucket,
            self.det_params.detector_length,
        )
        result.artifact.sort_in_z()
        if len(result.artifact.cloud) == 0:
            result.successful = False
            return result
        colors = generate_point_colors(result.artifact.cloud[:, 3])
        rr.log(
            "/event/cloud",
            rr.Points3D(result.artifact.cloud[:, :3], radii=RADIUS, colors=colors),
        )
        return result
