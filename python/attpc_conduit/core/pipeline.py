from .phase import PhaseLike, PhaseResult
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
                rr.log(
                    f"/histograms/{gram.name}", rr.Tensor(gram.counts.T), static=True
                )
