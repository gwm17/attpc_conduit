from dataclasses import dataclass
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

    This is a different definition from Spyral, customized to better fit the needs of
    the conduit. Spyral operates at the file level, while the  conduit must operate
    on single event streams.

    Parameters
    ----------
    name: str
        The name of the Phase (Pointcloud, Cluster, Estimation, etc.)

    Attributes
    ----------
    name: str
        The name of the Phase (Pointcloud, Cluster, Estimation, etc.)

    Methods
    -------
    run(payload, grammer, rng)
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
        grammer: Histogrammer
            The histogram manager
        rng: numpy.random.Generator
            A random number generator

        Returns
        -------
        PhaseResult
            The result of this phase containing the artifact information
        """
        raise NotImplementedError
