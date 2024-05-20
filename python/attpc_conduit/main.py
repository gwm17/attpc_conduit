from .core.config import (
    Config,
    detector_param_props,
    get_param_props,
    cluster_param_props,
    estimate_param_props,
    ParamType,
)
from . import Conduit, init_conduit_logger
from .pipeline import init_detector_bounds, ConduitPipeline
from .phases import PointcloudPhase, EstimationPhase, ClusterPhase
from .core.static import PAD_ELEC_PATH
from .core.blueprint import generate_default_blueprint

from spyral_utils.plot import Histogrammer
import dearpygui.dearpygui as dpg
import logging as log
import rerun as rr
import numpy as np
import logging


RATE_IN_STRING = "Conduit Data Rate In (MB/s):"
RATE_OUT_STRING = "Conduit Data Rate Out (MB/s):"
EVENT_STRING = "Last Processed Event:"
RADIUS = 2.0

## Initialize a whole mess of global data ##

init_conduit_logger()  # initialize Rust logging
rr.init("attpc_conduit_data", spawn=True)  # initialize Rerun

rr.send_blueprint(generate_default_blueprint())

# handle text logs
logging.getLogger().addHandler(rr.LoggingHandler("logs/handler"))
logging.getLogger().setLevel(logging.INFO)
logging.info("This INFO log got added through the standard logging interface")

# Create conduit and friends
conduit: Conduit
with PAD_ELEC_PATH as path:
    conduit = Conduit(path)
config = Config()
grammer = Histogrammer()
rng = np.random.default_rng()
pipeline = ConduitPipeline(
    [
        PointcloudPhase(config.get, config.detector, config.pads),
        ClusterPhase(config.cluster, config.detector),
        EstimationPhase(config.estimate, config.detector),
    ]
)

# Add some histograms
grammer.add_hist2d("particle_id", (512, 512), ((0.0, 5.0e3), (0.0, 3.0)))
grammer.add_hist2d("kinematics", (180, 512), ((0.0, 180.0), (0.0, 3.0)))
grammer.add_hist1d("polar", 180, (0.0, 180.0))

# Setup detector bounds in rerun
init_detector_bounds()

## End of initialization ##


## DearPyGui Callbacks and Handlers ##


def set_sliders_enabled(enabled: bool):
    for key in config.detector.__dict__.keys():
        dpg.configure_item(key, enabled=enabled)
    for key in config.get.__dict__.keys():
        dpg.configure_item(key, enabled=enabled)
    for key in config.cluster.__dict__.keys():
        dpg.configure_item(key, enabled=enabled)
    for key in config.estimate.__dict__.keys():
        dpg.configure_item(key, enabled=enabled)


def set_sliders_values():
    for key, value in config.detector.__dict__.items():
        dpg.set_value(key, value)
    for key, value in config.get.__dict__.items():
        dpg.set_value(key, value)
    for key, value in config.cluster.__dict__.items():
        dpg.set_value(key, value)
    for key, value in config.estimate.__dict__.items():
        dpg.set_value(key, value)


def set_start_enabled(enabled: bool):
    dpg.configure_item("start", enabled=enabled)


def set_stop_enabled(enabled: bool):
    dpg.configure_item("stop", enabled=enabled)


def start_conduit_callback():
    conduit.start_services()
    set_sliders_enabled(False)
    set_stop_enabled(True)
    set_start_enabled(False)


def stop_conduit_callback():
    print("Here")
    conduit.stop_services()
    set_sliders_enabled(True)
    set_stop_enabled(False)
    set_start_enabled(True)


def change_rate_in(rate: float):
    dpg.set_value("rate_in", f"{RATE_IN_STRING} {rate:.2}")


def change_rate_out(rate: float):
    dpg.set_value("rate_out", f"{RATE_OUT_STRING} {rate:.2}")


def change_event(event: int):
    dpg.set_value("event", f"{EVENT_STRING} {event}")


def detector_field_callback(sender: str):
    if sender in config.detector.__dict__:
        config.detector.__dict__[sender] = dpg.get_value(sender)
    else:
        log.error(f"Detector key error. Sender: {sender}")


def get_field_callback(sender: str):
    if sender in config.get.__dict__:
        config.get.__dict__[sender] = dpg.get_value(sender)
    else:
        log.error(f"GET key error. Sender: {sender}")


def cluster_field_callback(sender: str):
    if sender in config.cluster.__dict__:
        config.cluster.__dict__[sender] = dpg.get_value(sender)
    else:
        log.error(f"Cluster key error. Sender: {sender}")


def estimate_field_callback(sender: str):
    if sender in config.estimate.__dict__:
        config.estimate.__dict__[sender] = dpg.get_value(sender)
    else:
        log.error(f"Estimate key error. Sender: {sender}")


def save_callback(sender: str, app_data):
    config.save(app_data["file_path_name"])


def load_callback(sender: str, app_data):
    config.load(app_data["file_path_name"])
    set_sliders_values()


def create_detector_sliders():
    for key in config.detector.__dict__.keys():
        props = detector_param_props[key]
        match props.type:
            case ParamType.FLOAT:
                dpg.add_drag_float(
                    label=props.label,
                    min_value=props.min_val,
                    max_value=props.max_val,
                    default_value=props.default,
                    width=150,
                    callback=detector_field_callback,
                    tag=key,
                )
            case ParamType.INT:
                dpg.add_drag_int(
                    label=props.label,
                    min_value=props.min_val,
                    max_value=props.max_val,
                    default_value=props.default,
                    width=150,
                    callback=detector_field_callback,
                    tag=key,
                )
            case ParamType.UNUSED:
                pass


def create_get_sliders():
    for key in config.get.__dict__.keys():
        props = get_param_props[key]
        match props.type:
            case ParamType.FLOAT:
                dpg.add_drag_float(
                    label=props.label,
                    min_value=props.min_val,
                    max_value=props.max_val,
                    default_value=props.default,
                    width=150,
                    callback=get_field_callback,
                    tag=key,
                )
            case ParamType.INT:
                dpg.add_drag_int(
                    label=props.label,
                    min_value=props.min_val,
                    max_value=props.max_val,
                    default_value=props.default,
                    width=150,
                    callback=get_field_callback,
                    tag=key,
                )
            case ParamType.UNUSED:
                pass


def create_cluster_sliders():
    for key in config.cluster.__dict__.keys():
        props = cluster_param_props[key]
        match props.type:
            case ParamType.FLOAT:
                dpg.add_drag_float(
                    label=props.label,
                    min_value=props.min_val,
                    max_value=props.max_val,
                    default_value=props.default,
                    width=150,
                    callback=cluster_field_callback,
                    tag=key,
                )
            case ParamType.INT:
                dpg.add_drag_int(
                    label=props.label,
                    min_value=props.min_val,
                    max_value=props.max_val,
                    default_value=props.default,
                    width=150,
                    callback=cluster_field_callback,
                    tag=key,
                )
            case ParamType.UNUSED:
                pass


def create_estimate_sliders():
    for key in config.estimate.__dict__.keys():
        props = estimate_param_props[key]
        match props.type:
            case ParamType.FLOAT:
                dpg.add_drag_float(
                    label=props.label,
                    min_value=props.min_val,
                    max_value=props.max_val,
                    default_value=props.default,
                    width=150,
                    callback=estimate_field_callback,
                    tag=key,
                )
            case ParamType.INT:
                dpg.add_drag_int(
                    label=props.label,
                    min_value=props.min_val,
                    max_value=props.max_val,
                    default_value=props.default,
                    width=150,
                    callback=estimate_field_callback,
                    tag=key,
                )
            case ParamType.UNUSED:
                pass


## Setup DearPyGui ##

dpg.create_context()
dpg.create_viewport(title="AT-TPC Conduit", width=600, height=900)

with dpg.file_dialog(
    show=False,
    callback=save_callback,
    tag="save_file_dialog",
    default_filename="",
    height=600,
    width=400,
):
    dpg.add_file_extension(".json", color=(0, 255, 0))

with dpg.file_dialog(
    show=False,
    callback=load_callback,
    tag="load_file_dialog",
    default_filename="",
    height=600,
    width=400,
):
    dpg.add_file_extension(".json", color=(0, 255, 0))

with dpg.window(label="Conduit Control", tag="Conduit Control"):
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(
                label="Save...", callback=lambda: dpg.show_item("save_file_dialog")
            )
            dpg.add_menu_item(
                label="Load...", callback=lambda: dpg.show_item("load_file_dialog")
            )
    dpg.add_text("Control")
    dpg.add_separator()
    dpg.add_text(f"{RATE_IN_STRING} 0.0", tag="rate_in")
    dpg.add_text(f"{RATE_OUT_STRING} 0.0", tag="rate_out")
    dpg.add_text(f"{EVENT_STRING} 0", tag="event")
    with dpg.group(horizontal=True):
        dpg.add_button(
            label="Start Conduit", callback=start_conduit_callback, tag="start"
        )
        dpg.add_button(
            label="Stop Conduit",
            callback=stop_conduit_callback,
            enabled=False,
            tag="stop",
        )
    dpg.add_separator()
    dpg.add_text("Analysis Configuration")
    dpg.add_separator()
    dpg.add_text("Detector Parameters")
    create_detector_sliders()
    dpg.add_separator()
    dpg.add_text("GET Parameters")
    create_get_sliders()
    dpg.add_separator()
    dpg.add_text("Cluster Parametrs")
    create_cluster_sliders()
    dpg.add_separator()
    dpg.add_text("Estimate Parameters")
    create_estimate_sliders()
    dpg.add_separator()

## Finish DearPyGui setup ##


def main():
    """Entry point for run-conduit script"""

    # Start the gui
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Conduit Control", True)
    # This is the main DearPyGui event loop.
    # The more stuff shoved in here, the less
    # responsive the ConduitPanel will be
    while dpg.is_dearpygui_running() == True:
        event = conduit.poll_events()  # Poll the conduit
        ## Do analysis here...
        if event is not None:
            pipeline.run(event[0], event[1], grammer, rng)
        ## Will also call out to set UI values to update status
        dpg.render_dearpygui_frame()

    dpg.destroy_context()
