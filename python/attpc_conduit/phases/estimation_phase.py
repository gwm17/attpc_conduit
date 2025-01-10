from ..core.phase import PhaseLike, PhaseResult
from ..core.static import PARTICLE_ID_HISTOGRAM, KINEMATICS_HISTOGRAM, POLAR_HISTOGRAM
from spyral.core.config import EstimateParameters, DetectorParameters
from spyral.core.estimator import estimate_physics

from numpy.random import Generator
import numpy as np
from spyral_utils.plot import Histogrammer
import rerun as rr


class EstimationPhase(PhaseLike):
    """The default Conduit estimation phase, inheriting from PhaseLike

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
            list(),
            True,
            payload.event_id,
        )

        if not payload.successful:
            result.successful = False
            return result

        for cidx in range(len(payload.artifact)):
            local_cluster = payload.artifact[cidx]
            # Cluster is loaded do some analysis
            est = estimate_physics(
                cidx,
                local_cluster,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                self.estimate_params,
                self.det_params,
            )
            if est is not None:
                result.artifact.append(est)

        # Log circles if they exist
        n_circles = len(result.artifact)
        circle_block_data = np.zeros((n_circles, 6))
        used_labels = []
        for ridx, estimate in enumerate(result.artifact):
            rho = (
                estimate.brho
                / self.det_params.magnetic_field
                * 1000.0
                * np.sin(estimate.polar)
            )

            # Log the circles
            circle_block_data[ridx, 3:] = np.array(
                [
                    estimate.center_x,
                    estimate.center_y,
                    estimate.vertex_z,
                ]
            )
            circle_block_data[ridx, :3] = np.array([rho, rho, 0.0])
            used_labels.append(estimate.cluster_label)
        rr.log(
            "/event/circles",
            rr.Ellipsoids3D(
                half_sizes=circle_block_data[:, :3],
                centers=circle_block_data[:, 3:],
                colors=None,
                class_ids=used_labels,
            ),
        )

        # Fill the histograms, but DO NOT LOG HERE
        brho_array = np.array([est.brho for est in result.artifact])
        polar_array = np.array([est.polar for est in result.artifact])
        dedx_array = np.array([est.sqrt_dEdx for est in result.artifact])
        grammer.fill_hist2d(
            KINEMATICS_HISTOGRAM,
            polar_array,
            brho_array,
        )
        grammer.fill_hist2d(
            PARTICLE_ID_HISTOGRAM,
            dedx_array,
            brho_array,
        )
        grammer.fill_hist1d(POLAR_HISTOGRAM, polar_array)

        return result
