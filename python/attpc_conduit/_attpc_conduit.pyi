import numpy as np

class Conduit:
    """This class represents the communication conduit

    Provides a communication interface between the GET data acquisition and an analysis pipeline. The Conduit is a 
    mulithreaded, async runtime that handles the receiving of GET data traces and merging them into into composed events.
    The events could then be polled in an analysis pipeline. Point clouds (raw data) can be emitted to a server if desired
    (Server may be removed depending on testing.)

    Methods
    -------
    Conduit()
        Create a new Conduit object. There should only ever be one Conduit per pipeline.
    start_services()
        Start the Conduit, creating the communication channels and async tasks.
    stop_services()
        Stop the Conduit, destroying communication channels and tasks.
    poll_events() -> tuple[int, ndarray] | None
        Poll the Conduit, asking if any events have been recieved and merged.
    submit_point_cloud(cloud_buffer: ndarray)
        Submit a point cloud to the server
    """

    def __init__(self):
        """Create a new Conduit object

        This initializes the async runtime (tokio) and sets up some default pathing.

        Returns
        -------
        Conduit
            The conduit object
        """
        ...

    def start_services(self):
        """Start the Conduit, creating the communication channels and async tasks.

        This spawns the async tasks to the runtime and starts the process of receiving data
        from the GET data acquisition and listening on the included server. This should
        almost always be run when starting your application.
        """
        ...

    def stop_services(self):
        """Stop the Conduit, destroying communication channels and tasks.

        This submits a message to cancel any async tasks and awaits their
        completion.
        """
        ...

    def poll_events(self) -> tuple[int, np.ndarray] | None:
        """Poll the Conduit, asking if any events have been recieved and merged.

        The poll is synchronous but does not block.

        Returns
        -------
        tuple[int, ndarray] | None
            If there are no events ready, returns None. Otherwise, returns a tuple of the event number integer
            and an ndarray of the the trace matrix. The trace matrix is NxM where N is the number of traces and
            M is the length of the trace data. The first 5 columns are the hardware information (CoBo, AsAd, AGET, channel, pad)
            and the remaining 512 elements are the trace in GET time buckets. Each element of the trace matrix is a 16-bit integer.

        """
        ...