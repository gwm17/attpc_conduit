from .core.config import ClusterParameters
from .core.point_cloud import PointCloud
from .core.cluster import LabeledCloud, Cluster, convert_labeled_to_cluster
from .core.circle import least_squares_circle

from sklearn.cluster import HDBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np
import logging

NOISE_LABEL: int = 4096


def join_clusters(
    clusters: list[LabeledCloud], params: ClusterParameters, labels: np.ndarray
) -> tuple[list[LabeledCloud], np.ndarray]:
    """Join clusters until either only one cluster is left or no clusters meet the criteria to be joined together.

    Parameters
    ----------
    clusters: list[LabeledCloud]
        the set of clusters to examine
    params: ClusterParameters
        contains parameters controlling the joining algorithm

    Returns
    -------
    list[LabeledCloud]
        the set of joined clusters
    """
    jclusters = clusters.copy()
    before = len(jclusters)
    after = 0
    while before != after and len(jclusters) > 1:
        before = len(jclusters)
        jclusters, labels = join_clusters_step(jclusters, params, labels)
        after = len(jclusters)
    return (jclusters, labels)


def join_clusters_step(
    clusters: list[LabeledCloud], params: ClusterParameters, labels: np.ndarray
) -> tuple[list[LabeledCloud], np.ndarray]:
    """A single step of joining clusters

    Combine clusters based on the center around which they orbit. This is necessary because often times tracks are
    fractured or contain regions of varying density which causes clustering algorithms to separate them.

    Parameters
    ----------
    clusters: list[LabeledCloud]
        the set of clusters to examine
    params: ClusterParameters
        contains the parameters controlling the joining algorithm (max_center_distance)

    Returns
    -------
    list[LabeledCloud]
        the set of joined clusters
    """
    # Can't join 1 or 0 clusters
    if len(clusters) < 2:
        return (clusters, labels)

    event_number = clusters[0].point_cloud.event_number

    # Fit the clusters with circles
    centers = np.zeros((len(clusters), 3))
    for idx, cluster in enumerate(clusters):
        centers[idx, 0], centers[idx, 1], centers[idx, 2], _ = least_squares_circle(
            cluster.point_cloud.cloud[:, 0], cluster.point_cloud.cloud[:, 1]
        )

    # Make a dictionary of center groups
    # First everyone is in their own group
    groups: dict[int, list[int]] = {}
    group_labels: dict[int, list[int]] = {}
    for idx, cluster in enumerate(clusters):
        groups[cluster.label] = [idx]
        group_labels[cluster.label] = [cluster.label]
    # Now regroup, searching for clusters whose circles mostly overlap
    for idx, center in enumerate(centers):
        cluster = clusters[idx]
        # Reject noise
        if cluster.label == NOISE_LABEL or np.isnan(center[0]) or center[2] < 10.0:
            continue
        radius: float = float(np.linalg.norm(center[:2]))
        area = np.pi * radius**2.0

        for cidx, comp_cluster in enumerate(clusters):
            comp_center = centers[cidx]
            comp_radius = float(np.linalg.norm(comp_center[:2]))
            comp_area = np.pi * comp_radius**2.0
            if (
                comp_cluster.label == NOISE_LABEL
                or np.isnan(comp_center[0])
                or center[2] < 10.0
                or cidx == idx
            ):
                continue

            # Calculate area of overlap between the two circles
            # See Wolfram MathWorld https://mathworld.wolfram.com/Circle-CircleIntersection.html
            center_distance = np.sqrt(
                (center[0] - comp_center[0]) ** 2.0
                + (center[1] - comp_center[1]) ** 2.0
            )
            term1 = (center_distance**2.0 + radius**2.0 - comp_radius**2.0) / (
                2.0 * center_distance * radius
            )
            term2 = (center_distance**2.0 + comp_radius**2.0 - radius**2.0) / (
                2.0 * center_distance * comp_radius
            )
            term3 = (
                (-center_distance + radius + comp_radius)
                * (center_distance + radius - comp_radius)
                * (center_distance - radius + comp_radius)
                * (center_distance + radius + comp_radius)
            )
            if term3 < 0.0:  # term3 cant be negative, inside sqrt
                continue
            term1 = min(
                1.0, max(-1.0, term1)
            )  # clamp to arccos range to avoid silly floating point precision errors
            term2 = min(1.0, max(-1.0, term2))
            area_overlap = (
                radius**2.0 * np.arccos(term1)
                + comp_radius**2.0 * np.arccos(term2)
                - 0.5 * np.sqrt(term3)
            )

            smaller_area = min(area, comp_area)
            comp_mean_charge = np.mean(comp_cluster.point_cloud.cloud[:, 4], axis=0)
            mean_charge = np.mean(cluster.point_cloud.cloud[:, 4], axis=0)
            charge_diff = np.abs(mean_charge - comp_mean_charge)
            threshold = params.fractional_charge_threshold * np.max(
                [comp_mean_charge, mean_charge]
            )
            if (
                (area_overlap > params.circle_overlap_ratio * smaller_area)
                and (cidx not in groups[cluster.label])
                and (charge_diff < threshold)
            ):
                comp_group = groups.pop(comp_cluster.label)
                comp_labels = group_labels.pop(comp_cluster.label)
                for subs in comp_group:
                    clusters[subs].label = cluster.label
                groups[cluster.label].extend(comp_group)
                group_labels[cluster.label].extend(comp_labels)

    # Now reform the clouds such that there is one cloud per group
    new_clusters: list[LabeledCloud] = []
    for g in groups.keys():
        if g == NOISE_LABEL:
            continue

        new_cluster = LabeledCloud(g, PointCloud())
        new_cluster.point_cloud.event_number = event_number
        new_cluster.point_cloud.cloud = np.zeros(
            (0, len(clusters[0].point_cloud.cloud[0]))
        )
        for idx in groups[g]:
            new_cluster.point_cloud.cloud = np.concatenate(
                (new_cluster.point_cloud.cloud, clusters[idx].point_cloud.cloud), axis=0
            )
        new_clusters.append(new_cluster)

    new_labels = labels
    for g in group_labels.keys():
        if g == NOISE_LABEL:
            continue
        for label in group_labels[g]:
            new_labels[labels == label] = g
    return (new_clusters, new_labels)


def cleanup_clusters(
    clusters: list[LabeledCloud], params: ClusterParameters, labels: np.ndarray
) -> tuple[list[Cluster], np.ndarray]:
    """Converts the LabeledClouds to Clusters and bins the data in z

    Parameters
    ----------
    clusters: list[LabeledCloud]
        clusters to clean
    params: ClusterParameters
        Configuration parameters controlling the clustering algorithms

    Returns
    -------
    list[Cluster]
        The cleaned clusters
    """
    cleaned = []
    for cluster in clusters:
        if cluster.label == NOISE_LABEL:
            continue
        cluster, outliers = convert_labeled_to_cluster(cluster, params)
        cleaned.append(cluster)
        if len(outliers) == 0 or len(outliers) > len(labels == cluster.label):
            continue
        labels[labels == cluster.label][outliers] = NOISE_LABEL
    return (cleaned, labels)


def form_clusters(
    pc: PointCloud, params: ClusterParameters
) -> tuple[list[LabeledCloud], np.ndarray]:
    """Apply the HDBSCAN clustering algorithm to a PointCloud

    Analyze a point cloud, and group the points into clusters which in principle should correspond to particle trajectories. This analysis contains several steps,
    and revolves around the HDBSCAN clustering algorithm implemented in scikit-learn (see [their description](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html) for details)
    First the point cloud is smoothed by averaging over nearest neighbors (defined by the smoothing_neighbor_distance parameter) to remove small deviations.
    The data is then scaled where each coordinate (x,y,z,int) is centered to its mean and then scaled to its std deviation using the scikit-learn StandardScaler. This data is then
    clustered by HDBSCAN and the clusters are returned.

    Parameters
    ----------
    pc: PointCloud
        The point cloud to be clustered
    params: ClusterParameters
        Configuration parameters controlling the clustering algorithms

    Returns
    --------
    list[LabeledCloud]
        List of clusters found by the algorithm with labels
    """
    if len(pc.cloud) < params.min_cloud_size:
        return ([], np.empty(0))
    pc.smooth_cloud(params.smoothing_neighbor_distance)

    clusterizer = None
    n_points = len(pc.cloud)
    if n_points > params.big_event_cutoff:
        clusterizer = HDBSCAN(
            min_cluster_size=params.min_size_big_event,
            min_samples=params.min_points,
            allow_single_cluster=True,
        )
    elif n_points > params.min_size_small_event:
        clusterizer = HDBSCAN(
            min_cluster_size=params.min_size_small_event,
            min_samples=params.min_points,
            allow_single_cluster=True,
        )
    else:
        return ([], np.empty(0))

    # Smooth out the point cloud by averaging over neighboring points within a distance, droping any duplicate points

    # Use spatial dimensions and integrated charge
    cluster_data = np.empty(shape=(len(pc.cloud), 4))
    cluster_data[:, :3] = pc.cloud[:, :3]
    cluster_data[:, 3] = pc.cloud[:, 4]

    # Unfiy feature ranges to their means and std deviations. StandardScaler calculates mean, and std for each feature
    cluster_data = StandardScaler().fit_transform(cluster_data)

    fitted_clusters = clusterizer.fit(cluster_data)
    fitted_clusters.labels_[fitted_clusters.labels_ == -1] = NOISE_LABEL
    labels = np.unique(fitted_clusters.labels_)

    # Select out data into clusters
    clusters: list[LabeledCloud] = []
    for idx, label in enumerate(labels):
        clusters.append(LabeledCloud(label, PointCloud()))
        mask = fitted_clusters.labels_ == label
        clusters[idx].point_cloud.cloud = pc.cloud[mask]
        clusters[idx].point_cloud.event_number = pc.event_number

    return (clusters, fitted_clusters.labels_)


def phase_cluster(
    pc: PointCloud, params: ClusterParameters
) -> tuple[list[Cluster], np.ndarray] | None:
    """Convert a point cloud into a set of trajectory clusters

    Take the point clouds and break them into clusters which should represent particle trajectories.
    First the data is run through the HDBSCAN algorithm to generate initial clusters. Clusters are then joined
    based on their overlap and charge to make trajectory clusters. The trajectory clusters are then cleaned and
    smoothed.

    Parameters
    ----------
    pc: PointCloud
        The point cloud to be processed
    params: ClusterParameters
        Configuration parameters controlling the clustering algorithm

    Returns
    -------
    list[Cluster] | None
        A list of trajectory clusters. If no valid clusters were found, returns None.
    """

    clusters, labels = form_clusters(pc, params)
    if len(clusters) == 0:
        return None
    joined, joined_labels = join_clusters(clusters, params, labels)
    if len(joined) == 0:
        return None
    cleaned, cleaned_labels = cleanup_clusters(joined, params, joined_labels)
    if len(cleaned) == 0:
        return None

    return (cleaned, cleaned_labels)
