from . import (
    init_detector_bounds,
    init_conduit_logger,
    init_default_histograms,
    generate_default_blueprint,
    PointcloudPhase,
    ClusterPhase,
    EstimationPhase,
    ConduitPipeline,
)

from spyral import (
    DetectorParameters,
    GetParameters,
    ClusterParameters,
    PadParameters,
    EstimateParameters,
    DEFAULT_MAP,
)

from spyral.trace.trace_reader import create_reader
from spyral_utils.plot import Histogrammer
import logging
from pathlib import Path
import rerun as rr
import numpy as np
import click

# Initialize histogrammer
grammer = Histogrammer()
init_default_histograms(grammer)

# handle text logs
init_conduit_logger()
logging.getLogger().addHandler(rr.LoggingHandler("logs/handler"))
logging.getLogger().setLevel(logging.WARN)
logging.info("This INFO log got added through the standard logging interface")

# Create a pipeline
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


# Use click to forward all of the required Rerun args to our parser
@click.command(help="Rerun loader for AT-TPC trace HDF5 files")
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--application-id", type=str, help="optional, recommended - ID for the application"
)
@click.option(
    "--recording-id", type=str, help="optional, recommended - ID for the recording"
)
@click.option(
    "--entity-path-prefix", type=str, help="optional - prefix for all entity paths"
)
@click.option(
    "--timeless",
    type=bool,
    default=False,
    show_default=True,
    is_flag=True,
    help="deprecated - alias for --static",
)
@click.option(
    "--static",
    type=bool,
    default=False,
    show_default=True,
    is_flag=True,
    help="optional - mark all data as static",
)
@click.option(
    "--time",
    type=str,
    help="optional - timestamps to log at (e.g. `--time sim_time=1709203426`)",
)
@click.option(
    "--sequence",
    type=str,
    help="optional - sequence to log at (e.g. `--sequence sim_frame=42`)",
)
def main(
    filepath: str,
    application_id: str,
    recording_id: str,
    entity_path_prefix: str,
    timeless: bool,
    static: bool,
    time: str,
    sequence: str,
) -> None:
    """The entry point for the rerun-loader-merged-file script"""
    rng = np.random.default_rng()

    app_id = "attpc_hdf5_data"
    if application_id is not None:
        app_id = application_id

    path = Path(filepath)
    if not path.exists() or not path.is_file() or path.suffix != ".h5":
        exit(
            rr.EXTERNAL_DATA_LOADER_INCOMPATIBLE_EXIT_CODE
        )  # Indicates to Rerun that this file was not handled by this loader

    # Create the appropriate TraceReader
    reader = create_reader(path, 0)
    if reader is None:
        exit(rr.EXTERNAL_DATA_LOADER_INCOMPATIBLE_EXIT_CODE)

    rr.init(app_id, recording_id=recording_id)
    rr.send_blueprint(generate_default_blueprint(), make_active=True, make_default=True)
    rr.stdout()  # Required for custom file loaders

    init_detector_bounds()

    for event_id in reader.event_range():
        event_data = reader.read_raw_get_event(event_id)
        if event_data is None:
            continue

        pipeline.run(event_id, event_data[:], grammer, rng)
