import numpy as np
from pathlib import Path

class Conduit:
    """This class represents the communication conduit

    Provides a communication interface between the GET data acquisition and an analysis
    pipeline. The Conduit is a mulithreaded, async runtime that handles the receiving
    of GET data traces and merging them into into composed events. The events can then
    be polled in an analysis pipeline.

    Parameters
    ----------
    pad_path: Path
        The path to a pad map

    Methods
    -------
    connect(max_cache_size)
        Start the Conduit, creating the communication channels and async tasks.
    disconnect()
        Stop the Conduit, destroying communication channels and tasks.
    poll_events() -> tuple[int, ndarray] | None
        Poll the Conduit, asking if an event is ready for analysis
    is_connected() -> bool
        Check if the conduit is connected to the data streams
    """

    def __init__(self, pad_path: Path):
        """Create a new Conduit object

        This initializes the async runtime (tokio) and sets up some default pathing.

        Parameters
        ----------
        pad_path: Path
            The path to a file containing the mapping of AT-TPC electronics to pad
            number on the AT-TPC pad plane

        Returns
        -------
        Conduit
            The conduit object
        """
        ...
    def connect(self, max_cache_size: int):
        """Start the Conduit, creating the communication channels and async tasks.

        This spawns the async tasks to the runtime and starts the process of receiving data
        from the GET data acquisition and listening on the included server. This should
        almost always be run when starting your application.

        Parameters
        ----------
        max_cache_size: int
            The maximum size the event cache is allowed to reach (in GRAW frames)
            before events are emitted. Each Event can be populated by at most one frame
            per AsAd. This means that for the AT-TPC, which has 44 AsAds, the max_cache_size
            should be given in units of 44.
        """
        ...
    def disconnect(self):
        """Stop the Conduit, destroying communication channels and tasks.

        This submits a message to cancel any async tasks and awaits their
        completion.
        """
        ...
    def poll_events(self) -> tuple[int, np.ndarray] | None:
        """Poll the Conduit, asking if an event is ready to be analyzed

        The poll is synchronous but does not block.

        Returns
        -------
        tuple[int, numpy.ndarray] | None
            If there are no events ready, returns None. Otherwise, returns a tuple of
            the event number integer and an ndarray of the the trace matrix. The trace
            matrix is NxM where N is the number of traces and M is the length of the
            trace data. The first 5 columns are the hardware information (CoBo, AsAd,
            AGET, channel, pad) and the remaining 512 elements are the trace in GET
            time buckets. Each element of the trace matrix is a 16-bit integer.

        """
        ...

    def is_connected(self) -> bool:
        """Check if the conduit has been connected to the data streams

        Returns
        -------
        bool
            True if connected, False if disconnected
        """
        ...
