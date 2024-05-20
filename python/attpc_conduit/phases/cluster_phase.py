from ..core.phase import PhaseLike, PhaseResult
from ..core.color import get_label_color
from spyral.core.config import ClusterParameters, DetectorParameters
from spyral.core.status_message import StatusMessage
from spyral.core.point_cloud import PointCloud
from spyral.core.clusterize import form_clusters, join_clusters, cleanup_clusters

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
        clusters = form_clusters(payload.artifact, self.cluster_params)
        joined = join_clusters(clusters, self.cluster_params)
        result.artifact = cleanup_clusters(joined, self.cluster_params)
        if len(result.artifact) == 0:
            result.successful = False
            return result
        # For now we don't log clusters... Need to make Spyral more online friendly here
        # This will also need to change a bit, I guess maybe? Probably would like to include noise...
        labels = [c.label for c in result.artifact]
        rr.log(
            "/event",
            rr.AnnotationContext(
                [
                    (label, f"cluster_{label}", get_label_color(label))
                    for label in labels
                ]
            ),
        )
        return result
