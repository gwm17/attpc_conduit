from .core.cluster import Cluster
from .core.config import DetectorParameters, EstimateParameters
from .core.circle import least_squares_circle, generate_circle_points

from dataclasses import dataclass, field
import numpy as np
from enum import Enum
from scipy.stats import linregress


@dataclass
class EstimateResult:
    vertex: np.ndarray = field(default_factory=lambda: np.zeros(3))
    center: np.ndarray = field(default_factory=lambda: np.zeros(3))
    polar: float = 0.0
    azimuthal: float = 0.0
    brho: float = 0.0
    dEdx: float = 0.0
    eloss: float = 0.0
    failed: bool = True


class Direction(Enum):
    """Enum for the direction of a trajectory

    Attributes
    ----------
    NONE: int
        Invalid value (-1)
    FORWARD: int
        Trajectory traveling in the positive z-direction (0)
    BACKWARD: int
        Trajectory traveling in the negative z-direction (1)
    """

    NONE: int = -1
    FORWARD: int = 0
    BACKWARD: int = 1


def estimate_physics(
    cluster: Cluster,
    estimate_params: EstimateParameters,
    detector_params: DetectorParameters,
) -> EstimateResult:
    """Estimate the physics parameters for a cluster which could represent a particle trajectory

    Estimation is an imprecise process (by definition), and as such this algorithm requires a lot of
    manipulation of the data.

    Parameters
    ----------
    cluster: Cluster
        The cluster to estimate
    estimate_params:
        Configuration parameters controlling the estimation algorithm
    detector_params:
        Configuration parameters for the physical detector properties

    Returns
    -------
    EstimateResult
        The estimated physics values
    """
    result = EstimateResult()
    # Do some cleanup, reject clusters which have too few points
    if len(cluster.data) < estimate_params.min_total_trajectory_points:
        return result
    beam_region_fraction = float(
        len(
            cluster.data[
                np.linalg.norm(cluster.data[:, :2], axis=1)
                < detector_params.beam_region_radius
            ]
        )
    ) / float(len(cluster.data))
    if beam_region_fraction > 0.9:
        return result

    rhos = np.linalg.norm(cluster.data[:, :2], axis=1)  # cylindrical coordinates rho
    direction = Direction.NONE

    halfway = int(len(cluster.data) * 0.5)
    _, _, begin_radius, _ = least_squares_circle(
        cluster.data[:halfway, 0], cluster.data[:halfway, 1]
    )
    _, _, end_radius, _ = least_squares_circle(
        cluster.data[halfway:, 0], cluster.data[halfway:, 1]
    )
    max_rho_index = int(np.argmax(rhos))

    # See if in-spiraling to the window or microgmegas, sets the direction and guess of z-vertex
    # If backward, flip the ordering of the cloud to simplify algorithm
    # First check if max rho is at the end of the track. If so, didn't make a complete arc
    # Else use circle fits to begin/end
    if max_rho_index > int(0.9 * len(rhos)):
        if rhos[0] < rhos[-1]:
            direction = Direction.FORWARD
        else:
            direction = Direction.BACKWARD
    elif begin_radius < end_radius:
        direction = Direction.BACKWARD
    else:
        direction = Direction.FORWARD

    if direction == Direction.BACKWARD:
        rhos = np.flip(rhos, axis=0)
        cluster.data = np.flip(cluster.data, axis=0)

    # Guess that the vertex is the first point
    result.vertex[:] = cluster.data[0, :3]

    # Find the first point that is furthest from the vertex in rho (maximum) to get the first arc of the trajectory
    rho_to_vertex = np.linalg.norm(cluster.data[1:, :2] - result.vertex[:2], axis=1)
    maximum = int(np.argmax(rho_to_vertex))
    first_arc = cluster.data[: (maximum + 1)]

    # Fit a circle to the first arc and extract some physics
    result.center[0], result.center[1], radius, _ = least_squares_circle(
        first_arc[:, 0], first_arc[:, 1]
    )
    circle = generate_circle_points(result.center[0], result.center[1], radius)
    # Re-estimate vertex using the fitted circle. Extrapolate back to point closest to beam axis
    vertex_estimate_index = np.argsort(np.linalg.norm(circle, axis=1))[0]
    result.vertex[:2] = circle[vertex_estimate_index]
    # Re-calculate distance to vertex
    rho_to_vertex = np.linalg.norm((cluster.data[:, :2] - result.vertex[:2]), axis=1)

    # Do a linear fit to small segment of trajectory to extract rho vs. z and extrapolate vertex z
    test_index = max(10, int(maximum * 0.5))
    fit = linregress(cluster.data[:test_index, 2], rho_to_vertex[:test_index])
    vertex_rho = float(np.linalg.norm(result.vertex[:2]))
    result.vertex[2] = (vertex_rho - fit.intercept) / fit.slope
    result.center[2] = result.vertex[2]

    # Toss tracks whose verticies are not close to the origin in x,y
    if vertex_rho > estimate_params.max_distance_from_beam_axis:
        return result

    result.polar = np.arctan(fit.slope)
    if direction is Direction.BACKWARD:
        result.polar += np.pi

    # From the trigonometry of the system to the center
    result.azimuthal = np.arctan2(
        result.vertex[1] - result.center[1], result.vertex[0] - result.center[0]
    )
    if result.azimuthal < 0:
        result.azimuthal += 2.0 * np.pi
    result.azimuthal -= np.pi * 1.5
    if result.azimuthal < 0:
        result.azimuthal += 2.0 * np.pi

    result.brho = (
        detector_params.magnetic_field * radius * 0.001 / (np.sin(result.polar))
    )
    if np.isnan(result.brho):
        result.brho = 0.0

    arclength = 0.0
    for idx in range(len(first_arc) - 1):
        arclength += float(np.linalg.norm(first_arc[idx + 1, :3] - first_arc[idx, :3]))
    if arclength == 0.0:
        return result
    charge_deposited = float(np.sum(first_arc[:, 3]))
    result.dEdx = charge_deposited / arclength

    integral_len = float(np.linalg.norm(cluster.data[0, :3] - result.vertex))
    result.eloss = cluster.data[0, 3]
    cutoff = 700.0  # mm
    index = 1
    while True:
        if index == len(cluster.data):
            break
        elif integral_len > cutoff:
            break
        result.eloss += cluster.data[index, 3]
        integral_len += float(
            np.linalg.norm(cluster.data[index, :3] - cluster.data[index - 1, :3])
        )
        index += 1
    result.failed = False
    return result


def phase_estimate(
    clusters: list[Cluster],
    estimate_params: EstimateParameters,
    detector_params: DetectorParameters,
) -> list[EstimateResult]:
    """The core loop of the estimate phase

    Estimate physics parameters (Brho, polar angle, vertex position, etc) for clusters from the cluster phase. This phase serves two purposes which are related. The
    first is to estimate initial values for the upcoming solving phase where ODE solutions are fit to the data (hence the name estimate). The second is to generate
    parameters (Brho, dEdx) to be used in a particle ID, which is also necessary for the solving phase.

    Parameters
    ----------
    clusters: list[Clusters]
        The clusters to be processed
    estimate_params: EstimateParameters
        Configuration parameters controlling the estimation algorithm
    detector_params: DetectorParameters
        Configuration parameters for physical detector properties

    Returns
    -------
    list[EstimateResult]
        A list of estimate results of the same length as the clusters Parameter. If the failed field of the EstimateResult is set
        to True, the estimation analysis failed and the result should be discarded
    """
    # Create the results
    results = [
        estimate_physics(cluster, estimate_params, detector_params)
        for cluster in clusters
    ]

    # Toss any failures
    results = [res for res in results if not res.failed]

    return results
