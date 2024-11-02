from attpc_conduit import Conduit, init_conduit_logger
from attpc_conduit.pipeline import init_detector_bounds, ConduitPipeline
from attpc_conduit.phases import PointcloudPhase, EstimationPhase, ClusterPhase
from attpc_conduit.core.static import PAD_ELEC_PATH
from attpc_conduit.core.blueprint import generate_default_blueprint
from attpc_conduit.core.histograms import initialize_default_histograms

from spyral import (
    PadParameters,
    DetectorParameters,
    GetParameters,
    ClusterParameters,
    EstimateParameters,
    DEFAULT_MAP,
)

from pathlib import Path
from spyral_utils.plot import Histogrammer
import rerun as rr
import numpy as np
import logging
import click

pad_params = PadParameters(
    pad_geometry_path=DEFAULT_MAP,
    pad_time_path=DEFAULT_MAP,
    pad_electronics_path=DEFAULT_MAP,
    pad_scale_path=DEFAULT_MAP,
)
detector_params = DetectorParameters(
    magnetic_field=3.0,
    electric_field=45000.0,
    detector_length=1000.0,
    beam_region_radius=30.0,
    micromegas_time_bucket=10,
    window_time_bucket=560,
    get_frequency=6.25,
    garfield_file_path=Path("Invalid"),  # We don't use this
    do_garfield_correction=False,
)
get_params = GetParameters(
    baseline_window_scale=20.0,
    peak_separation=50.0,
    peak_prominence=20.0,
    peak_max_width=100.0,
    peak_threshold=25.0,
)
cluster_params = ClusterParameters(
    min_cloud_size=50,
    min_points=3,
    min_size_scale_factor=0.05,
    min_size_lower_cutoff=10,
    cluster_selection_epsilon=10.0,
    min_cluster_size_join=15,
    circle_overlap_ratio=0.5,
    outlier_scale_factor=0.5,
)
estimate_params = EstimateParameters(
    min_total_trajectory_points=30, smoothing_factor=100.0
)
pipeline = ConduitPipeline(
    [
        PointcloudPhase(get_params, detector_params, pad_params),
        ClusterPhase(cluster_params, detector_params),
        EstimationPhase(estimate_params, detector_params),
    ]
)


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
def run_conduit(viewer_ip: str, viewer_port: int):
    init_conduit_logger()  # initialize Rust logging

    logging.info("Connecting to rerun Viewer...")
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
    logging.info("Setting up Conduit...")
    conduit: Conduit
    with PAD_ELEC_PATH as path:
        conduit = Conduit(path)

    try:
        conduit.connect()
    except Exception as e:
        logging.error(f"Conduit failed to connect: {e}")
        return
    logging.info("Conduit succesfully connected.")

    logging.info("Creating histograms...")

    grammer = Histogrammer()
    rng = np.random.default_rng()
    # Add some histograms
    initialize_default_histograms(grammer)

    logging.info("Histograms are ready, setting up detector geometry...")
    # Setup detector bounds in rerun
    init_detector_bounds()
    logging.info("Detector ready, starting event loop...")

    # Main event loop, which can call the pipeline run event loop
    while True:
        try:
            event = conduit.poll_events()  # Poll the conduit
            if event is not None:
                pipeline.run(event[0], event[1], grammer, rng)
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


if __name__ == "__main__":
    run_conduit()
