from .core.conduit_log import init_conduit_logger
from .core.blueprint import generate_default_blueprint
from .pipeline import init_detector_bounds, ConduitPipeline
from .phases import PointcloudPhase, ClusterPhase, EstimationPhase
from .core.histograms import initialize_default_histograms

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
import argparse
from pathlib import Path
import rerun as rr  # pip install rerun-sdk
import numpy as np

## Initialize histogrammer ##
grammer = Histogrammer()
initialize_default_histograms(grammer)
## End histogrammer initialization ##

# handle text logs
init_conduit_logger()
logging.getLogger().addHandler(rr.LoggingHandler("logs/handler"))
logging.getLogger().setLevel(logging.WARN)
logging.info("This INFO log got added through the standard logging interface")

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

# The Rerun Viewer will always pass these two pieces of information:
# 1. The path to be loaded, as a positional arg.
# 2. A shared recording ID, via the `--recording-id` flag.
#
# It is up to you whether you make use of that shared recording ID or not.
# If you use it, the data will end up in the same recording as all other plugins interested in
# that file, otherwise you can just create a dedicated recording for it. Or both.
parser = argparse.ArgumentParser(
    description="""
This is an example executable data-loader plugin for the Rerun Viewer.
Any executable on your `$PATH` with a name that starts with `rerun-loader-` will be
treated as an external data-loader.

This particular one will log Python source code files as markdown documents, and return a
special exit code to indicate that it doesn't support anything else.

To try it out, copy it in your $PATH as `rerun-loader-python-file`, then open a Python source
file with Rerun (`rerun file.py`).
"""
)
parser.add_argument("filepath", type=str)
parser.add_argument(
    "--application-id", type=str, help="optional recommended ID for the application"
)
parser.add_argument(
    "--recording-id", type=str, help="optional recommended ID for the recording"
)
parser.add_argument(
    "--entity-path-prefix", type=str, help="optional prefix for all entity paths"
)
parser.add_argument(
    "--timeless",
    action="store_true",
    default=False,
    help="deprecated: alias for `--static`",
)
parser.add_argument(
    "--static",
    action="store_true",
    default=False,
    help="optionally mark data to be logged as static",
)
parser.add_argument(
    "--time",
    type=str,
    action="append",
    help="optional timestamps to log at (e.g. `--time sim_time=1709203426`)",
)
parser.add_argument(
    "--sequence",
    type=str,
    action="append",
    help="optional sequences to log at (e.g. `--sequence sim_frame=42`)",
)
args = parser.parse_args()


def main() -> None:
    """The entry point for the rerun-loader-merged-file script"""
    rng = np.random.default_rng()

    app_id = "attpc_hdf5_data"
    if args.application_id is not None:
        app_id = args.application_id

    path = Path(args.filepath)
    if not path.exists() or not path.is_file() or path.suffix != ".h5":
        print(f"here {path} {path.suffix}")
        exit(
            rr.EXTERNAL_DATA_LOADER_INCOMPATIBLE_EXIT_CODE
        )  # Indicates to Rerun that this file was not handled by this loader

    reader = create_reader(path, 0)
    if reader is None:
        exit(rr.EXTERNAL_DATA_LOADER_INCOMPATIBLE_EXIT_CODE)

    rr.init(app_id, recording_id=args.recording_id)
    rr.send_blueprint(generate_default_blueprint(), make_active=True, make_default=True)
    rr.stdout()  # Required for custom file loaders

    init_detector_bounds()

    for event_id in reader.event_range():
        event_data = reader.read_raw_get_event(event_id)
        if event_data is None:
            continue

        pipeline.run(event_id, event_data[:], grammer, rng)
