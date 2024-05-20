from .core.phase import PhaseLike, PhaseResult
from .core.static import CIRCLE_POLARS, RADIUS
from spyral_utils.plot import Histogrammer, Hist1D, Hist2D


import rerun as rr
import numpy as np


def init_detector_bounds() -> None:
    """Setup the detector geometry in rerun"""
    # log the coordinate orientation for 3D
    rr.log("/", rr.ViewCoordinates.RIGHT_HAND_X_UP, static=True)
    # log the detector box
    rr.log(
        "/bounds/box",
        rr.Boxes3D(half_sizes=[300.0, 300.0, 500.0], centers=[0.0, 0.0, 500.0]),
        static=True,
    )


# def init_detector_pad_plane(pad_map: PadMap):
#     """Setup the pad plane hardware visualization"""
#     coordinates = np.zeros((len(pad_map.map), 2))
#     labels: list[str] = ["" for _ in pad_map.map.keys()]
#     radii = np.full(len(pad_map.map.keys()), RADIUS)
#     colors = [(1.0, 1.0, 1.0, 0.01) for _ in pad_map.map.keys()]
#     for idx, pad in enumerate(pad_map.map.values()):
#         coordinates[idx, 0] = pad.x
#         coordinates[idx, 1] = pad.y
#         labels[idx] = str(pad.hardware)
#     rr.log(
#         "Detector2D/geometry/pads",
#         rr.Points2D(coordinates, radii=radii, colors=colors, labels=labels),
#         static=True,
#     )


# def run_pipeline(
#     event_id: int,
#     event_matrix: np.ndarray,
#     grammer: Histogrammer,
#     pad_map: PadMap,
#     config: Config,
# ) -> None:
#     """The analysis pipeline

#     Takes in an event from either type of source (file or online) and processes it,
#     logging data to rerun as it goes. This means rerun *must* be initialized before
#     running the pipeline.

#     Parameters
#     ----------
#     event_id: int
#         The event id number
#     event_matrix: ndarray
#         The event trace matrix
#     grammer: Histogrammer
#         The histogrammer being used to store data
#     pad_map: PadMap
#         The pad map
#     config: Config
#         The current conduit configuration
#     """
#     rr.set_time_sequence("event_time", event_id)
#     rr.log("raw", rr.Clear(recursive=True))
#     rr.log("clusters", rr.Clear(recursive=True))
#     rr.log("circles", rr.Clear(recursive=True))

#     pc = phase_pointcloud(event_id, event_matrix, pad_map, config.get, config.detector)
#     if len(pc.cloud) < 2:
#         return
#     pc.sort_in_z()
#     colors = generate_point_colors(pc.cloud[:, 3])
#     radii = np.full(len(pc.cloud), RADIUS)
#     rr.log(
#         f"raw/cloud",
#         rr.Points3D(
#             pc.cloud[:, :3], radii=radii, colors=colors, labels=pc.get_hardware_labels()
#         ),
#     )
#     rr.log(
#         f"raw/plane",
#         Points2D(
#             pc.cloud[:, :2],
#             radii=radii,
#             colors=colors,
#             labels=pc.get_hardware_labels(),
#         ),
#     )
#     result = phase_cluster(pc, config.cluster)
#     if result is not None:
#         clusters = result[0]
#         labels = result[1]
#         context = rr.AnnotationContext(
#             [
#                 (label, f"cluster_{label}", get_label_color(label))
#                 for label in np.unique(labels)
#             ]
#         )
#         radii = np.full(len(pc.cloud), RADIUS)
#         rr.log(
#             "clusters/cloud",
#             rr.Points3D(pc.cloud[:, :3], radii=radii, class_ids=labels),
#             context,
#         )
#         rr.log(
#             "clusters/plane",
#             rr.Points2D(pc.cloud[:, :2], radii=radii, class_ids=labels),
#             context,
#         )

#         estimates = phase_estimate(clusters, config.estimate, config.detector)
#         circles_context = rr.AnnotationContext(
#             [
#                 (idx, f"circle_{label}", get_label_color(idx))
#                 for idx, label in enumerate(np.unique(labels))
#             ]
#         )
#         any_est = False
#         for idx, est in enumerate(estimates):
#             if est.failed == True:
#                 continue
#             rho = est.brho / config.detector.magnetic_field * 1000.0 * np.sin(est.polar)
#             circle_points[:, :2] = generate_circle_for_render(
#                 est.center[0], est.center[1], rho
#             )
#             circle_points[:, 2] = est.vertex[2]
#             rr.log(
#                 f"circles/cloud",
#                 rr.LineStrips3D(circle_points, radii=RADIUS, class_ids=idx),
#                 circles_context,
#             )

#             rr.log(
#                 f"circles/plane",
#                 rr.LineStrips2D(circle_points[:, :2], radii=RADIUS, class_ids=idx),
#                 circles_context,
#             )
#             grammer.fill_2D("pid", est.dEdx, est.brho)
#             grammer.fill_2D("kinematics", np.rad2deg(est.polar), est.brho)
#             grammer.fill_1D("polar", np.rad2deg(est.polar))
#             any_est = True

#         if any_est:
#             for gram in grammer.grams_1d.values():
#                 rr.log(
#                     f"Histograms/{gram.name}",
#                     rr.BarChart(gram.counts),
#                 )

#             for gram in grammer.grams_2d.values():
#                 rr.log(
#                     f"Histograms/{gram.name}",
#                     rr.Tensor(
#                         gram.counts,
#                         dim_names=(gram.x_axis_title, gram.y_axis_title),
#                     ),
#                 )


class ConduitPipeline:
    """A customized representation of an analysis pipeline in Spyral

    This pipeline is customized to run with the conduit. It is a little different from the
    "normal" pipeline. But the core concept is the same. The main difference is that this pipeline
    works event-by-event rather than run-by-run

    Parameters
    ----------
    phases: list[PhaseLike]
        The Phases of the analysis pipeline

    Attributes
    ----------
    phases: list[PhaseLike]
        The Phases of the analysis pipeline

    Methods
    -------
    validate()
        Validate the pipeline by comparing the schema of the phases.
    run(event_id, event, grammer, seed)
        Run the pipeline for an event

    """

    def __init__(
        self,
        phases: list[PhaseLike],
    ):
        self.phases = phases

    def run(
        self,
        event_id: int,
        event: np.ndarray,
        grammer: Histogrammer,
        rng: np.random.Generator,
    ) -> None:
        """Run the pipeline for a set of runs

        Each Phase is only run if it is active. Any artifact requested
        from an inactive Phase is expected to have already been created.

        Parameters
        ----------
        run_list: list[int]
            List of run numbers to be processed
        msg_queue: multiprocessing.SimpleQueue
            A queue to transmit progress messages through
        seed: numpy.random.SeedSequence
            A seed to initialize the pipeline random number generator

        """
        # Clear the previous event data
        print("here")
        rr.set_time_sequence("event_time", event_id)
        rr.log("/event", rr.Clear(recursive=True))
        result = PhaseResult(artifact=event, successful=True, event_id=event_id)
        for phase in self.phases:
            print("Running..")
            result = phase.run(result, grammer, rng)

        # Now we can log histograms. This way they only ever get logged once an event
        for gram in grammer.histograms.values():
            if isinstance(gram, Hist1D):
                rr.log(f"/histograms/{gram.name}", rr.BarChart(gram.counts))
            elif isinstance(gram, Hist2D):
                rr.log(f"/histograms/{gram.name}", rr.Tensor(gram.counts))
