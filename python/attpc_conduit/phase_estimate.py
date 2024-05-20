# from .core.cluster import Cluster
# from .core.config import DetectorParameters, EstimateParameters
# from .core.circle import least_squares_circle, generate_circle_points

# from dataclasses import dataclass, field
# import numpy as np
# from enum import Enum
# from scipy.stats import linregress


# class Direction(Enum):
#     """Enum for the direction of a trajectory

#     Attributes
#     ----------
#     NONE: int
#         Invalid value (-1)
#     FORWARD: int
#         Trajectory traveling in the positive z-direction (0)
#     BACKWARD: int
#         Trajectory traveling in the negative z-direction (1)
#     """

#     NONE: int = -1
#     FORWARD: int = 0
#     BACKWARD: int = 1


# @dataclass
# class EstimateResult:
#     vertex: np.ndarray = field(default_factory=lambda: np.zeros(3))
#     center: np.ndarray = field(default_factory=lambda: np.zeros(3))
#     polar: float = 0.0
#     azimuthal: float = 0.0
#     brho: float = 0.0
#     dEdx: float = 0.0
#     failed: bool = True
#     direction: Direction = Direction.NONE


# def estimate_physics(
#     cluster: Cluster,
#     estimate_params: EstimateParameters,
#     detector_params: DetectorParameters,
# ) -> EstimateResult:
#     """Run the physics parameter estimation

#     Does a multi-pass system. If the first estimate was "bad" we can try running
#     again with a better guess.

#     Parameters
#     ----------
#     cluster: Cluster
#         The cluster to estimate
#     estimate_params:
#         Configuration parameters controlling the estimation algorithm
#     detector_params:
#         Configuration parameters for the physical detector properties

#     Returns
#     -------
#     EstimateResult
#         The estimated physics values
#     """
#     # Run estimation where we attempt to guess the right direction
#     result = estimate_physics_pass(
#         cluster,
#         estimate_params,
#         detector_params,
#     )

#     # If estimation was consistent or didn't meet valid criteria were done
#     if not result.failed or (result.failed and result.direction == Direction.NONE):
#         return result
#     # If we made a bad guess, try the other direction
#     elif result.direction == Direction.FORWARD:
#         result = estimate_physics_pass(
#             cluster,
#             estimate_params,
#             detector_params,
#             Direction.BACKWARD,
#         )
#     else:
#         result = estimate_physics_pass(
#             cluster,
#             estimate_params,
#             detector_params,
#             Direction.FORWARD,
#         )
#     return result


# def choose_direction(cluster: Cluster) -> Direction:
#     """Estimate which direction the cluster is going

#     Use the distance to the z-axis to estimate the direction of the trajectory

#     Parameters
#     ----------
#     cluster: Cluster
#         The trajectory data

#     Returns
#     -------
#     Direction
#         The estimated direction

#     """
#     rhos = np.linalg.norm(cluster.data[:, :2], axis=1)  # cylindrical coordinates rho
#     direction = Direction.NONE

#     # See if in-spiraling to the window or microgmegas, sets the direction and guess of z-vertex
#     if rhos[0] < rhos[-1]:
#         direction = Direction.FORWARD
#     else:
#         direction = Direction.BACKWARD

#     return direction


# def estimate_physics_pass(
#     cluster: Cluster,
#     estimate_params: EstimateParameters,
#     detector_params: DetectorParameters,
#     chosen_direction: Direction = Direction.NONE,
# ) -> EstimateResult:
#     """Estimate the physics parameters for a cluster which could represent a particle trajectory

#     Estimation is an imprecise process (by definition), and as such this algorithm requires a lot of
#     manipulation of the data.

#     Parameters
#     ----------
#     cluster: Cluster
#         The cluster to estimate
#     estimate_params:
#         Configuration parameters controlling the estimation algorithm
#     detector_params:
#         Configuration parameters for the physical detector properties
#     chosen_direction: Direction
#         Can be used to specify the direction, over-riding the direction estimation. If NONE, use the direction
#         estimation value.

#     Returns
#     -------
#     EstimateResult
#         The estimated physics values
#     """
#     result = EstimateResult()
#     # Do some cleanup, reject clusters which have too few points
#     if len(cluster.data) < estimate_params.min_total_trajectory_points:
#         return result
#     beam_region_fraction = float(
#         len(
#             cluster.data[
#                 np.linalg.norm(cluster.data[:, :2], axis=1)
#                 < detector_params.beam_region_radius
#             ]
#         )
#     ) / float(len(cluster.data))
#     if beam_region_fraction > 0.9:
#         return result

#     if chosen_direction == Direction.NONE:
#         result.direction = choose_direction(cluster)
#     else:
#         result.direction = chosen_direction

#     if result.direction == Direction.BACKWARD:
#         cluster.data = np.flip(cluster.data, axis=0)

#     # Guess that the vertex is the first point; make sure to copy! not reference
#     result.vertex[:] = cluster.data[0, :3]

#     # Find the first point that is furthest from the vertex in rho (maximum) to get the first arc of the trajectory
#     rho_to_vertex = np.linalg.norm(cluster.data[1:, :2] - result.vertex[:2], axis=1)
#     maximum = np.argmax(rho_to_vertex)
#     first_arc = cluster.data[: (maximum + 1)]

#     # Fit a circle to the first arc and extract some physics
#     result.center[0], result.center[1], radius, _ = least_squares_circle(
#         first_arc[:, 0], first_arc[:, 1]
#     )
#     # better_radius = np.linalg.norm(cluster.data[0, :2] - center[:2])
#     circle = generate_circle_points(result.center[0], result.center[1], radius)
#     # Re-estimate vertex using the fitted circle. Extrapolate back to point closest to beam axis
#     vertex_estimate_index = np.argsort(np.linalg.norm(circle, axis=1))[0]
#     result.vertex[:2] = circle[vertex_estimate_index]
#     # Re-calculate distance to vertex, maximum, first arc
#     rho_to_vertex = np.linalg.norm((cluster.data[:, :2] - result.vertex[:2]), axis=1)
#     maximum = np.argmax(rho_to_vertex)
#     first_arc = cluster.data[: (maximum + 1)]

#     # Do a linear fit to small segment of trajectory to extract rho vs. z and extrapolate vertex z
#     test_index = max(10, int(maximum * 0.5))
#     # test_index = 10
#     fit = linregress(cluster.data[:test_index, 2], rho_to_vertex[:test_index])
#     vertex_rho = np.linalg.norm(result.vertex[:2])
#     result.vertex[2] = (vertex_rho - fit.intercept) / fit.slope
#     result.center[2] = result.vertex[2]

#     # Toss tracks whose verticies are not close to the origin in x,y
#     if vertex_rho > detector_params.beam_region_radius:
#         return result

#     result.polar = np.arctan(fit.slope)
#     # We have a self consistency case here. Polar should match chosen Direction
#     if (result.polar > 0.0 and result.direction == Direction.BACKWARD) or (
#         result.polar < 0.0 and result.direction == Direction.FORWARD
#     ):
#         return result
#     elif result.direction is Direction.BACKWARD:
#         result.polar += np.pi

#     # From the trigonometry of the system to the center
#     azimuthal = np.arctan2(
#         result.vertex[1] - result.center[1], result.vertex[0] - result.center[0]
#     )
#     if azimuthal < 0:
#         azimuthal += 2.0 * np.pi
#     azimuthal += np.pi * 0.5
#     if azimuthal > np.pi * 2.0:
#         azimuthal -= 2.0 * np.pi

#     result.brho = (
#         detector_params.magnetic_field * radius * 0.001 / (np.sin(result.polar))
#     )
#     if np.isnan(result.brho):
#         result.brho = 0.0

#     arclength = 0.0
#     charge_deposited = first_arc[0, 3]
#     for idx in range(len(first_arc) - 1):
#         # Stop integrating if we leave the small pad region
#         if np.linalg.norm(first_arc[idx + 1, :2]) > 152.0:
#             break
#         arclength += np.linalg.norm(first_arc[idx + 1, :3] - first_arc[idx, :3])
#         charge_deposited += first_arc[idx + 1, 3]
#     if arclength == 0.0:
#         result.direction = Direction.NONE
#         return result
#     result.dEdx = charge_deposited / arclength

#     result.failed = False
#     return result


# def phase_estimate(
#     clusters: list[Cluster],
#     estimate_params: EstimateParameters,
#     detector_params: DetectorParameters,
# ) -> list[EstimateResult]:
#     """The core loop of the estimate phase

#     Estimate physics parameters (Brho, polar angle, vertex position, etc) for clusters from the cluster phase. This phase serves two purposes which are related. The
#     first is to estimate initial values for the upcoming solving phase where ODE solutions are fit to the data (hence the name estimate). The second is to generate
#     parameters (Brho, dEdx) to be used in a particle ID, which is also necessary for the solving phase.

#     Parameters
#     ----------
#     clusters: list[Clusters]
#         The clusters to be processed
#     estimate_params: EstimateParameters
#         Configuration parameters controlling the estimation algorithm
#     detector_params: DetectorParameters
#         Configuration parameters for physical detector properties

#     Returns
#     -------
#     list[EstimateResult]
#         A list of estimate results of the same length as the clusters Parameter. If the failed field of the EstimateResult is set
#         to True, the estimation analysis failed and the result should be discarded
#     """
#     # Create the results
#     results = [
#         estimate_physics(cluster, estimate_params, detector_params)
#         for cluster in clusters
#     ]

#     return results
