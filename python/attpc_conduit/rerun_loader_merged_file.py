from .core.conduit_log import init_conduit_logger
from .core.config import Config
from .core.blueprint import generate_default_blueprint
from .pipeline import init_detector_bounds, ConduitPipeline
from .phases import PointcloudPhase, ClusterPhase, EstimationPhase
from .core.histograms import initialize_default_histograms

from spyral_utils.plot import Histogrammer
import h5py as h5
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


def get_event_range(trace_file: h5.File) -> tuple[int, int]:
    """
    The merger doesn't use attributes for legacy reasons, so everything is stored in datasets. Use this to retrieve the min and max event numbers.

    Parameters
    ----------
    trace_file: h5py.File
        File handle to a hdf5 file with AT-TPC traces

    Returns
    -------
    tuple[int, int]
        A pair of integers (first event number, last event number)
    """
    try:
        meta_group = trace_file["meta"]
        if not isinstance(meta_group, h5.Group):
            return (0, 0)
        meta_data = meta_group["meta"]
        if not isinstance(meta_data, h5.Dataset):
            return (0, 0)
        return (int(meta_data[0]), int(meta_data[2]))
    except Exception:
        return (0, 0)


def main() -> None:
    """The entry point for the rerun-loader-merged-file script"""
    config = Config(Path("config.json"))
    pipeline = ConduitPipeline(
        [
            PointcloudPhase(config.get, config.detector, config.pads),
            ClusterPhase(config.cluster, config.detector),
            EstimationPhase(config.estimate, config.detector),
        ]
    )
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

    file = h5.File(path)
    get_group = None
    try:
        get_group = file["get"]
    except Exception:
        file.close()
        exit(rr.EXTERNAL_DATA_LOADER_INCOMPATIBLE_EXIT_CODE)
    if not isinstance(get_group, h5.Group):
        file.close()
        exit(rr.EXTERNAL_DATA_LOADER_INCOMPATIBLE_EXIT_CODE)
    min_event, max_event = get_event_range(file)
    if min_event == 0 and max_event == 0:
        file.close()
        exit(rr.EXTERNAL_DATA_LOADER_INCOMPATIBLE_EXIT_CODE)

    rr.init(
        app_id,
        recording_id=args.recording_id,
    )
    rr.send_blueprint(generate_default_blueprint(), make_active=True, make_default=True)
    rr.stdout()  # type: ignore  # Required for custom file loaders

    init_detector_bounds()

    for event_id in range(min_event, max_event):
        event_data = None
        try:
            event_data = get_group[f"evt{event_id}_data"]
        except Exception:
            continue

        if not isinstance(event_data, h5.Dataset):
            continue

        pipeline.run(event_id, event_data[:], grammer, rng)
