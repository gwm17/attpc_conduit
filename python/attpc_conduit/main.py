from .pad_map import PAD_ELEC_PATH
from .config import (
    Config,
    detector_param_props,
    get_param_props,
    cluster_param_props,
    estimate_param_props,
    ParamType,
)
from . import Conduit, init_conduit_logger
import dearpygui.dearpygui as dpg
import logging as log

RATE_IN_STRING = "Conduit Data Rate In (MB/s):"
RATE_OUT_STRING = "Conduit Data Rate In (MB/s):"
EVENT_STRING = "Last Processed Event:"

init_conduit_logger()
conduit = Conduit(PAD_ELEC_PATH)
config = Config()


def set_sliders_enabled(enabled: bool):
    for key in config.detector.__dict__.keys():
        dpg.configure_item(key, enabled=enabled)
    for key in config.get.__dict__.keys():
        dpg.configure_item(key, enabled=enabled)
    for key in config.cluster.__dict__.keys():
        dpg.configure_item(key, enabled=enabled)
    for key in config.estimate.__dict__.keys():
        dpg.configure_item(key, enabled=enabled)


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

with dpg.window(label="Conduit Control", tag="Conduit Control"):
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Save...")
            dpg.add_menu_item(label="Load...")
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
        ## Will also call out to set UI values to update status
        dpg.render_dearpygui_frame()

    dpg.destroy_context()
