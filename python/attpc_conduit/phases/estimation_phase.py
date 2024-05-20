from ..core.phase import PhaseLike, PhaseResult
from ..core.static import CIRCLE_POLARS, RADIUS, N_CIRCLE_POINTS_RENDER
from spyral.core.config import EstimateParameters, DetectorParameters
from spyral.core.status_message import StatusMessage
from spyral.core.estimator import estimate_physics

from numpy.random import Generator
import numpy as np
from spyral_utils.plot import Histogrammer
import rerun as rr
from logging import warn


class EstimationPhase(PhaseLike):
    """The default Spyral estimation phase, inheriting from PhaseLike

    The goal of the estimation phase is to get reasonable estimations of
    the physical properties of a particle trajectory (B&rho; , reaction angle, etc.)
    for use in the more complex solving phase to follow. EstimationPhase should come
    after ClusterPhase and before InterpSolverPhase in the Pipeline.

    Parameters
    ----------
    estimate_params: EstimateParameters
        Parameters controlling the estimation algorithm
    det_params: DetectorParameters
        Parameters describing the detector

    Attributes
    ----------
    estimate_params: EstimateParameters
        Parameters controlling the estimation algorithm
    det_params: DetectorParameters
        Parameters describing the detector

    """

    def __init__(
        self, estimate_params: EstimateParameters, det_params: DetectorParameters
    ):
        super().__init__("Estimation")
        self.estimate_params = estimate_params
        self.det_params = det_params

    def run(
        self,
        payload: PhaseResult,
        grammer: Histogrammer,
        rng: Generator,
    ) -> PhaseResult:
        # Check that clusters exist

        result = PhaseResult(
            {
                "event": [],
                "cluster_index": [],
                "cluster_label": [],
                "ic_amplitude": [],
                "ic_centroid": [],
                "ic_integral": [],
                "ic_multiplicity": [],
                "vertex_x": [],
                "vertex_y": [],
                "vertex_z": [],
                "center_x": [],
                "center_y": [],
                "center_z": [],
                "polar": [],
                "azimuthal": [],
                "brho": [],
                "dEdx": [],
                "dE": [],
                "arclength": [],
                "direction": [],
            },
            True,
            payload.event_id,
        )

        if not payload.successful:
            result.successful = False
            return result

        for cidx in range(len(payload.artifact)):
            local_cluster = payload.artifact[cidx]
            # Cluster is loaded do some analysis
            estimate_physics(
                cidx,
                local_cluster,
                -1,
                -1,
                -1,
                -1,
                self.estimate_params,
                self.det_params,
                result.artifact,
            )

        # Log circles if they exist
        n_circles = len(result.artifact["event"])
        circle_block_data = np.zeros((n_circles, N_CIRCLE_POINTS_RENDER, 3))
        labels = [a.label for a in payload.artifact]
        for ridx in range(n_circles):
            rho = (
                result.artifact["brho"][ridx]
                / self.det_params.magnetic_field
                * 1000.0
                * np.sin(result.artifact["polar"][ridx])
            )

            # Log the circles
            circle_block_data[ridx, :, 2] = result.artifact["vertex_z"][ridx]
            circle_block_data[ridx, :, :2] = np.array(
                [
                    np.array(
                        [
                            rho * np.cos(polar) + result.artifact["center_x"][ridx],
                            rho * np.sin(polar) + result.artifact["center_y"][ridx],
                        ]
                    )
                    for polar in CIRCLE_POLARS
                ]
            )
        rr.log(
            "/event/circles",
            rr.LineStrips3D(
                circle_block_data, radii=RADIUS, colors=None, class_ids=labels
            ),
        )

        # Fill the histograms, but DO NOT LOG HERE
        grammer.fill_hist2d(
            "kinematics",
            np.array(np.rad2deg(result.artifact["polar"])),
            np.array(result.artifact["brho"]),
        )
        grammer.fill_hist2d(
            "particle_id",
            np.array(result.artifact["dEdx"]),
            np.array(result.artifact["brho"]),
        )
        grammer.fill_hist1d(
            "polar_angle", np.array(np.rad2deg(result.artifact["polar"]))
        )

        return result
