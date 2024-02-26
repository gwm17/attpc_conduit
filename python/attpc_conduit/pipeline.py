from .plot.histogram import Histogrammer
from .plot.color import generate_point_colors, get_label_color
from .phase_pointcloud import phase_pointcloud
from .phase_cluster import phase_cluster
from .phase_estimate import phase_estimate
from .core.config import Config
from .core.pad_map import PadMap
from .core.circle import generate_circle_points, N_CIRCLE_POINTS
import logging as log

import rerun as rr
import numpy as np

RADIUS = 2.0

circle_points = np.empty(
    (N_CIRCLE_POINTS, 3), dtype=np.float32
)  # Some pre-allocated storage


def init_detector_bounds() -> None:
    """Setup the detector geometry in rerun"""
    # log the pad plane bounds
    plane = generate_circle_points(0.0, 0.0, 30.0)
    rr.log(
        "Detector2D/geometry/bounds",
        rr.LineStrips2D(plane, draw_order=-1000.0),
        timeless=True,
    )
    # log the coordinate orientation for 3D
    rr.log("Detector3D/", rr.ViewCoordinates.RIGHT_HAND_X_UP, timeless=True)
    # log the detector box
    rr.log(
        "Detector3D/detector_box",
        rr.Boxes3D(half_sizes=[300.0, 300.0, 500.0], centers=[0.0, 0.0, 500.0]),
        timeless=True,
    )


def init_detector_pad_plane(pad_map: PadMap):
    """Setup the pad plane hardware visualization"""
    coordinates = np.zeros((len(pad_map.map), 2))
    labels: list[str] = ["" for _ in pad_map.map.keys()]
    radii = np.full(len(pad_map.map.keys()), RADIUS)
    colors = [(1.0, 1.0, 1.0, 0.01) for _ in pad_map.map.keys()]
    for idx, pad in enumerate(pad_map.map.values()):
        coordinates[idx, 0] = pad.x
        coordinates[idx, 1] = pad.y
        labels[idx] = str(pad.hardware)
    rr.log(
        "Detector2D/geometry/pads",
        rr.Points2D(
            coordinates, radii=radii, colors=colors, labels=labels, draw_order=-20000.0
        ),
        timeless=True,
    )


def run_pipeline(
    event_id: int,
    event_matrix: np.ndarray,
    grammer: Histogrammer,
    pad_map: PadMap,
    config: Config,
) -> None:
    """The analysis pipeline

    Takes in an event from either type of source (file or online) and processes it,
    logging data to rerun as it goes. This means rerun *must* be initialized before
    running the pipeline.

    Parameters
    ----------
    event_id: int
        The event id number
    event_matrix: ndarray
        The event trace matrix
    grammer: Histogrammer
        The histogrammer being used to store data
    pad_map: PadMap
        The pad map
    config: Config
        The current conduit configuration
    """
    rr.set_time_sequence("event_time", event_id)
    rr.log("Detector3D/event", rr.Clear(recursive=True))
    rr.log("Detector2D/event", rr.Clear(recursive=True))

    pc = phase_pointcloud(event_id, event_matrix, pad_map, config.get, config.detector)
    colors = generate_point_colors(pc.cloud[:, 3])
    radii = np.full(len(pc.cloud), RADIUS)
    rr.log(
        f"Detector3D/event/point_cloud",
        rr.Points3D(
            pc.cloud[:, :3], radii=radii, colors=colors, labels=pc.get_hardware_labels()
        ),
    )
    rr.log(
        f"Detector2D/event/raw_plane",
        rr.Points2D(
            pc.cloud[:, :2],
            radii=radii,
            colors=colors,
            labels=pc.get_hardware_labels(),
        ),
    )
    result = phase_cluster(pc, config.cluster)
    if result is not None:
        clusters = result[0]
        labels = result[1]
        context = rr.AnnotationContext(
            [
                (label, f"cluster_{label}", get_label_color(idx))
                for idx, label in enumerate(np.unique(labels))
            ]
        )
        radii = np.full(len(pc.cloud), RADIUS)
        rr.log(
            "Detector3D/event/clusters",
            rr.Points3D(pc.cloud[:, :3], radii=radii, class_ids=labels),
            context,
        )
        rr.log(
            "Detector2D/event/clusters",
            rr.Points2D(pc.cloud[:, :2], radii=radii, class_ids=labels),
            context,
        )

        estimates = phase_estimate(clusters, config.estimate, config.detector)
        circles_context = rr.AnnotationContext(
            [
                (idx, f"circle_{label}", get_label_color(idx))
                for idx, label in enumerate(np.unique(labels))
            ]
        )
        rr.log("Detector3D/event/circles", circles_context)
        rr.log("Detector2D/event/circles", circles_context)
        for idx, est in enumerate(estimates):
            if est.failed == True:
                continue
            rho = est.brho / config.detector.magnetic_field * 1000.0 * np.sin(est.polar)
            circle_points[:, :2] = generate_circle_points(
                est.center[0], est.center[1], rho
            )
            circle_points[:, 2] = est.vertex[2]
            rr.log(
                f"Detector3D/event/circles/",
                rr.LineStrips3D(circle_points, radii=RADIUS, class_ids=idx),
            )

            rr.log(
                f"Detector2D/event/circles",
                rr.LineStrips2D(circle_points[:, :2], radii=RADIUS, class_ids=idx),
            )
            grammer.fill_2D("pid", est.dEdx, est.brho)
            grammer.fill_2D("kinematics", np.rad2deg(est.polar), est.brho)
            grammer.fill_1D("polar", np.rad2deg(est.polar))

            for gram in grammer.grams_1d.values():
                rr.log(
                    f"Histograms/{gram.name}",
                    rr.BarChart(gram.counts),
                )

            for gram in grammer.grams_2d.values():
                rr.log(
                    f"Histograms/{gram.name}",
                    rr.Tensor(
                        gram.counts,
                        dim_names=(gram.x_axis_title, gram.y_axis_title),
                    ),
                )