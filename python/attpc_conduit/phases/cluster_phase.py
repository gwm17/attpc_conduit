from ..core.phase import PhaseLike, PhaseResult
from ..core.color import get_label_color
from ..core.static import RADIUS, UNSIGNED_NOISE_LABEL
from spyral.core.config import ClusterParameters, DetectorParameters
from spyral.core.clusterize import (
    form_clusters,
    join_clusters,
    cleanup_clusters,
    NOISE_LABEL,
)

from numpy.random import Generator
from spyral_utils.plot import Histogrammer
import rerun as rr


class ClusterPhase(PhaseLike):
    """The default Spyral clustering phase, inheriting from PhaseLike

    The goal of the clustering phase is to take in a point cloud
    and separate the points into individual particle trajectories. In
    the default version here, we use scikit-learn's HDBSCAN clustering
    algorithm. The clustering phase should come after the Pointcloud/PointcloudLegacy
    Phase in the Pipeline and before the EstimationPhase.

    Parameters
    ----------
    cluster_params: ClusterParameters
        Parameters controlling the clustering algorithm
    det_params: DetectorParameters
        Parameters describing the detector

    Attributes
    ----------
    cluster_params: ClusterParameters
        Parameters controlling the clustering algorithm
    det_params: DetectorParameters
        Parameters describing the detector

    """

    def __init__(
        self, cluster_params: ClusterParameters, det_params: DetectorParameters
    ) -> None:
        super().__init__("Cluster")
        self.cluster_params = cluster_params
        self.det_params = det_params

    def run(
        self,
        payload: PhaseResult,
        grammer: Histogrammer,
        rng: Generator,
    ) -> PhaseResult:
        # Check that point clouds exist
        result = PhaseResult(None, True, payload.event_id)
        if not payload.successful:
            result.successful = False
            return result

        clusters, labels = form_clusters(payload.artifact, self.cluster_params)
        joined, labels = join_clusters(clusters, self.cluster_params, labels)
        result.artifact, labels = cleanup_clusters(joined, self.cluster_params, labels)
        if len(result.artifact) == 0:
            result.successful = False
            return result
        unique_labels = [c.label for c in result.artifact]
        unique_labels.append(UNSIGNED_NOISE_LABEL)

        labels[labels == NOISE_LABEL] = UNSIGNED_NOISE_LABEL

        rr.log(
            "/event",
            rr.AnnotationContext(
                [
                    (label, f"cluster_{label}", get_label_color(label))
                    for label in unique_labels
                ]
            ),
        )
        rr.log(
            "/event/clusters",
            rr.Points3D(payload.artifact.cloud[:, :3], radii=RADIUS, class_ids=labels),
        )
        return result
