from .core.pad_map import PAD_ELEC_PATH, PadMap
from .core.config import (
    Config,
    detector_param_props,
    get_param_props,
    cluster_param_props,
    estimate_param_props,
    ParamType,
)
from . import Conduit, init_conduit_logger
from .phase_pointcloud import phase_pointcloud
from .phase_cluster import phase_cluster
from .phase_estimate import phase_estimate
from .core.circle import generate_circle_points

import dearpygui.dearpygui as dpg
import logging as log
import rerun as rr
import numpy as np
import logging


RATE_IN_STRING = "Conduit Data Rate In (MB/s):"
RATE_OUT_STRING = "Conduit Data Rate Out (MB/s):"
EVENT_STRING = "Last Processed Event:"
RADIUS = 2.0

init_conduit_logger()
rr.init("attpc_conduit_data", spawn=True)
# handle text logs
logging.getLogger().addHandler(rr.LoggingHandler("logs/handler"))
logging.getLogger().setLevel(-1)
logging.info("This INFO log got added through the standard logging interface")

conduit = Conduit(PAD_ELEC_PATH)
config = Config()
pad_map = PadMap()

# log the pad plane bounds
plane = generate_circle_points(0.0, 0.0, 300.0)
rr.log("Detector2D/bounds", rr.LineStrips2D(plane), timeless=True)
# log the coordinate orientation for 3D
rr.log("Detector3D/", rr.ViewCoordinates.RIGHT_HAND_X_UP, timeless=True)
# log the detector box
rr.log(
    "Detector3D/detector_box",
    rr.Boxes3D(half_sizes=[300.0, 300.0, 500.0], centers=[0.0, 0.0, 500.0]),
    timeless=True,
)


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


def main():
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Conduit Control", True)
    while dpg.is_dearpygui_running() == True:
        event = conduit.poll_events()
        ## Do analysis here...
        if event is not None:
            rr.set_time_sequence("event_time", event[0])
            rr.log("Detector3D/cloud", rr.Clear(recursive=True))
            rr.log("Detector2D/pad_plane", rr.Clear(recursive=True))
            pc = phase_pointcloud(
                event[0],
                event[1],
                pad_map,
                config.get,
                config.detector,
            )
            radii = np.full(len(pc.cloud), RADIUS)
            rr.log(
                f"Detector3D/cloud/point_cloud",
                rr.Points3D(pc.cloud[:, :3], radii=radii),
            )
            rr.log(
                f"Detector2D/pad_plane/raw_plane",
                rr.Points2D(pc.cloud[:, :2], radii=radii),
            )
            clusters = phase_cluster(pc, config.cluster)
            if clusters is not None:
                estimates = phase_estimate(clusters, config.estimate, config.detector)

                for idx, cluster in enumerate(clusters):
                    radii = np.full(len(cluster.data), RADIUS)
                    rr.log(
                        f"Detector3D/cloud/cluster_{cluster.label}",
                        rr.Points3D(cluster.data[:, :3], radii=radii),
                    )
                    rr.log(
                        f"Detector2D/pad_plane/cluster_{cluster.label}",
                        rr.Points2D(cluster.data[:, :2], radii=radii),
                    )
                    est = estimates[idx]
                    if est.failed == False:
                        rr.log(
                            f"Detector3D/cloud/cluster_{cluster.label}/vertex",
                            rr.Points3D(est.vertex, radii=[RADIUS]),
                        )
                        rho = est.brho / config.detector.magnetic_field * 1000.0
                        circle = generate_circle_points(
                            est.center[0], est.center[1], rho
                        )
                        radii = np.full(len(circle), RADIUS)
                        rr.log(
                            f"Detector2D/pad_plane/cluster_{cluster.label}/circle",
                            rr.Points2D(circle, radii=radii),
                        )
        ## Will also call out to set UI values to update status
        dpg.render_dearpygui_frame()

    dpg.destroy_context()
