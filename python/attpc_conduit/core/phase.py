from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np
from spyral_utils.plot import Histogrammer
from typing import Any


@dataclass
class PhaseResult:
    """Dataclass representing the result of a Phase

    Attributes
    ----------
    artifact: Any
        The artifact created by this Phase
    successful: bool
        True if the Phase was successful or False if it failed
    event_id: int
        The event that was analyzed

    Methods
    -------
    invalid_result(run_number)
        Create an invalid PhaseResult
    """

    artifact: Any
    successful: bool
    event_id: int

    @staticmethod
    def invalid_result(event_id: int):
        return PhaseResult(None, False, event_id)


class PhaseLike(ABC):
    """Abstract Base Class all Phases inherit from

    Parameters
    ----------
    name: str
        The name of the Phase (Pointcloud, Cluster, Estimation, etc.)
    incoming_schema: ArtifactSchema | None
        Optional schema describing the expected incoming artifact (payload).
        Default is None.
    outgoing_schema: ArtifactSchema | None
        Optional schema describing the expected outgoing artifact (result).
        Default is None.

    Attributes
    ----------
    name: str
        The name of the Phase (Pointcloud, Cluster, Estimation, etc.)
    incoming_schema: ArtifactSchema | None
        Schema describing the expected incoming artifact (payload).
    outgoing_schema: ArtifactSchema | None
        Schema describing the expected outgoing artifact (result).

    Methods
    -------
    run(payload, workspace_path, msg_queue, rng)
        Run the phase. This is an abstract method.
    """

    def __init__(
        self,
        name: str,
    ):
        self.name = name

    def __str__(self) -> str:
        return f"{self.name}Phase"

    @abstractmethod
    def run(
        self,
        payload: PhaseResult,
        grammer: Histogrammer,
        rng: np.random.Generator,
    ) -> PhaseResult:
        """Run the phase. This is an abstract method.

        It must be overriden by any child class.

        Parameters
        ----------
        payload: PhaseResult
            The result from the previous Phase
        workspace_path: pathlib.Path
            The path to the workspace
        msg_queue: multiprocessing.SimpleQueue
            The queue for submitting progress messages
        rng: numpy.random.Generator
            A random number generator

        Returns
        -------
        PhaseResult
            The result of this phase containing the artifact information
        """
        raise NotImplementedError
