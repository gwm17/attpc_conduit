from attpc_conduit.core.config import (
    Config,
)
from attpc_conduit import Conduit, init_conduit_logger
from attpc_conduit.pipeline import init_detector_bounds, ConduitPipeline
from attpc_conduit.phases import PointcloudPhase, EstimationPhase, ClusterPhase
from attpc_conduit.core.static import PAD_ELEC_PATH
from attpc_conduit.core.blueprint import generate_default_blueprint
from attpc_conduit.core.histograms import initialize_default_histograms

from spyral_utils.plot import Histogrammer
import rerun as rr
import numpy as np
import logging
import rpyc
from typing import Any

RATE_IN_STRING = "Conduit Data Rate In (MB/s):"
RATE_OUT_STRING = "Conduit Data Rate Out (MB/s):"
EVENT_STRING = "Last Processed Event:"


## End of initialization ##
def run(conduit: Conduit, state: Any, rng: np.random.Generator, grammer: Histogrammer):
    """Entry point for run-conduit script"""

    config: Config = state.root.get_config()

    pipeline = ConduitPipeline(
        [
            PointcloudPhase(config.get, config.detector, config.pads),
            ClusterPhase(config.cluster, config.detector),
            EstimationPhase(config.estimate, config.detector),
        ]
    )
    # Start the gui
    while state.root.is_running():
        event = conduit.poll_events()  # Poll the conduit
        ## Do analysis here...
        if event is not None:
            pipeline.run(event[0], event[1], grammer, rng)
        ## Will also call out to set UI values to update status


def main():
    init_conduit_logger()  # initialize Rust logging
    rr.init("attpc_conduit_data", spawn=False)  # initialize Rerun
    rr.connect("127.0.0.1:9876")  # connect to a viewer

    rr.send_blueprint(generate_default_blueprint())

    # handle text logs
    logging.getLogger().addHandler(rr.LoggingHandler("logs/handler"))
    logging.getLogger().setLevel(logging.INFO)
    logging.info("This INFO log got added through the standard logging interface")

    # Create conduit and friends
    conduit: Conduit
    with PAD_ELEC_PATH as path:
        conduit = Conduit(path)
    conduit.start_services()  # Figure out how to do this better...
    grammer = Histogrammer()
    rng = np.random.default_rng()
    state = rpyc.connect("localhost", port=18861)

    # Add some histograms
    initialize_default_histograms(grammer)

    # Setup detector bounds in rerun
    init_detector_bounds()
    while True:
        if state.root.is_running():
            run(conduit, state, rng, grammer)


if __name__ == "__main__":
    main()
