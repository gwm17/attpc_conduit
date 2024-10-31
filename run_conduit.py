from attpc_conduit.core.config import (
    Config,
)
from attpc_conduit import Conduit, init_conduit_logger
from attpc_conduit.pipeline import init_detector_bounds, ConduitPipeline
from attpc_conduit.phases import PointcloudPhase, EstimationPhase, ClusterPhase
from attpc_conduit.core.static import PAD_ELEC_PATH
from attpc_conduit.core.blueprint import generate_default_blueprint
from attpc_conduit.core.histograms import initialize_default_histograms
from attpc_conduit.core.state import RunState

from spyral_utils.plot import Histogrammer
import rerun as rr
import numpy as np
import logging
import rpyc
from typing import Any
import click


## End of initialization ##
def run_pipeline(
    conduit: Conduit, state: Any, rng: np.random.Generator, grammer: Histogrammer
):
    """Entry point for run-conduit script"""

    logging.info("Getting remote configuration...")
    config: Config = state.root.get_config()
    logging.info("Configuration retrieved. Creating ConduitPipeline...")
    pipeline = ConduitPipeline(
        [
            PointcloudPhase(config.get, config.detector, config.pads),
            ClusterPhase(config.cluster, config.detector),
            EstimationPhase(config.estimate, config.detector),
        ]
    )
    logging.info("Pipeline created! Running event loop...")
    while not state.root.should_run_stop():
        event = conduit.poll_events()  # Poll the conduit
        if event is not None:
            pipeline.run(event[0], event[1], grammer, rng)


@click.command()
@click.option(
    "--viewer-ip",
    default="localhost",
    type=str,
    help="The IP address of the machine running the Rerun Viewer",
    show_default=True,
)
@click.option(
    "--viewer-port",
    default=9876,
    type=int,
    help="The open port listening for connections to the Rerun Viewer",
    show_default=True,
)
@click.option(
    "--state-ip",
    default="localhost",
    type=str,
    help="The IP address of the machine running the RPyC state server",
    show_default=True,
)
@click.option(
    "--state-port",
    default=18861,
    type=int,
    help="The open port listening for connections to the RPyC state server",
    show_default=True,
)
def run_conduit(viewer_ip: str, viewer_port: int, state_ip: str, state_port: int):
    init_conduit_logger()  # initialize Rust logging
    rr.init("attpc_conduit_data", spawn=False)  # initialize Rerun
    if viewer_ip == "localhost":
        rr.connect(f"127.0.0.1:{viewer_port}")  # connect to a viewer
    else:
        rr.connect(f"{viewer_ip}:{viewer_port}")  # connect to a viewer

    rr.send_blueprint(generate_default_blueprint())

    # handle text logs to rerun
    logging.getLogger().addHandler(rr.LoggingHandler("logs/handler"))
    logging.getLogger().setLevel(logging.INFO)

    logging.info("Creating the Conduit and Control...")

    # Create conduit and friends
    conduit: Conduit
    with PAD_ELEC_PATH as path:
        conduit = Conduit(path)
    grammer = Histogrammer()
    rng = np.random.default_rng()
    state = rpyc.connect(state_ip, port=state_port)

    logging.info(
        "Conduit and control created succesfully, now making the histogram memory..."
    )

    # Add some histograms
    initialize_default_histograms(grammer)

    logging.info("Histograms are ready, setting up detector geometry...")
    # Setup detector bounds in rerun
    init_detector_bounds()
    logging.info("Detector ready, starting event loop...")

    # Main event loop, which can call the pipeline run event loop
    while True:
        try:
            if state.root.should_run_start():
                logging.info("Conduit recieved Start Run event! Connecting...")
                conduit.connect()
                logging.info("Connected. Starting run...")
                state.root.set_run_state(RunState.RUNNING)
                run_pipeline(conduit, state, rng, grammer)
                logging.info("Conduit received run stop signal. Disconnecting...")
                state.root.set_run_state(RunState.NOT_RUNNING)
                conduit.disconnect()
                logging.info("Disconnected.")
            elif state.root.should_shutdown():
                break
        except KeyboardInterrupt:
            logging.info("Conduit recieved KeyboardInterrupt, shutting down.")
            break
        except Exception as e:
            logging.info(
                "Oops, conduit ran into an exception! Printing to terminal and shutting down"
            )
            print(f"Conduit exception: {e}")
            break

    if conduit.is_connected():
        conduit.disconnect()
    state.root.set_run_state(RunState.NOT_RUNNING)


if __name__ == "__main__":
    run_conduit()
