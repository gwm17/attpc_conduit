from ..core.config import (
    Config,
    ParamType,
    get_param_props,
    detector_param_props,
    cluster_param_props,
    estimate_param_props,
)
from pathlib import Path
from nicegui import ui
from typing import Any


RATE_IN_STRING = "Conduit Data Rate In (MB/s):"
RATE_OUT_STRING = "Conduit Data Rate Out (MB/s):"
EVENT_STRING = "Last Processed Event:"

## Initialize a whole mess of global data ##


class AppState:
    def __init__(self, state: Any):
        self.enabled = True
        self.stopable = False
        self.connection = state
        self.shutdown = False

    def set_start(self, config: Config):
        self.enabled = False
        self.stopable = True
        self.connection.root.set_config(config)
        self.connection.root.set_start()

    def set_stop(self, config: Config):
        self.enabled = True
        self.stopable = False
        self.connection.root.set_stop()

    def load_config(self, path: Path) -> Config:
        config = Config(path)
        self.connection.root.set_config(config)
        return config


## DearPyGui Callbacks and Handlers ##


def save_callback(config: Config, path: str):
    config.save(Path(path))


def load_callback(config: Config, path: str):
    config.load(Path(path))


def create_detector_sliders(config: Config, state: AppState):
    with ui.row().classes("w-full"):
        for key in config.detector.__dict__.keys():
            props = detector_param_props[key]
            match props.type:
                case ParamType.FLOAT:
                    ui.number(
                        label=props.label,
                        min=props.min_val,
                        max=props.max_val,
                        format="%.3f",
                        value=props.default,
                    ).bind_enabled(state).bind_value(config.detector, key).classes(
                        "w-1/4"
                    )
                case ParamType.INT:
                    ui.number(
                        label=props.label,
                        min=props.min_val,
                        max=props.max_val,
                        format="%d",
                        value=props.default,
                    ).bind_enabled(state).bind_value(config.detector, key).classes(
                        "w-1/4"
                    )
                case ParamType.UNUSED:
                    pass


def create_get_sliders(config: Config, state: AppState):
    with ui.row().classes("w-full"):
        for key in config.get.__dict__.keys():
            props = get_param_props[key]
            match props.type:
                case ParamType.FLOAT:
                    ui.number(
                        label=props.label,
                        min=props.min_val,
                        max=props.max_val,
                        format="%.3f",
                        value=props.default,
                    ).bind_enabled(state).bind_value(config.get, key).classes("w-1/4")
                case ParamType.INT:
                    ui.number(
                        label=props.label,
                        min=props.min_val,
                        max=props.max_val,
                        format="%d",
                        value=props.default,
                    ).bind_enabled(state).bind_value(config.get, key).classes("w-1/4")
                case ParamType.UNUSED:
                    pass


def create_cluster_sliders(config: Config, state: AppState):
    with ui.row().classes("w-full"):
        for key in config.cluster.__dict__.keys():
            props = cluster_param_props[key]
            match props.type:
                case ParamType.FLOAT:
                    ui.number(
                        label=props.label,
                        min=props.min_val,
                        max=props.max_val,
                        format="%.3f",
                        value=props.default,
                    ).bind_enabled(state).bind_value(config.cluster, key).classes(
                        "w-1/4"
                    )
                case ParamType.INT:
                    ui.number(
                        label=props.label,
                        min=props.min_val,
                        max=props.max_val,
                        format="%d",
                        value=props.default,
                    ).bind_enabled(state).bind_value(config.cluster, key).classes(
                        "w-1/4"
                    )
                case ParamType.UNUSED:
                    pass


def create_estimate_sliders(config: Config, state: AppState):
    with ui.row().classes("w-full"):
        for key in config.estimate.__dict__.keys():
            props = estimate_param_props[key]
            match props.type:
                case ParamType.FLOAT:
                    ui.number(
                        label=props.label,
                        min=props.min_val,
                        max=props.max_val,
                        format="%.3f",
                        value=props.default,
                    ).bind_enabled(state).bind_value(config.cluster, key).classes(
                        "w-1/4"
                    )
                case ParamType.INT:
                    ui.number(
                        label=props.label,
                        min=props.min_val,
                        max=props.max_val,
                        format="%d",
                        value=props.default,
                    ).bind_enabled(state).bind_value(config.cluster, key).classes(
                        "w-1/4"
                    )
                case ParamType.UNUSED:
                    pass


def create_and_run_controller(remote_state: Any):
    config = Config()
    state = AppState(remote_state)
    ui.dark_mode(True)
    ui.page_title("Conduit Control")
    with ui.row().classes("w-full"):
        with ui.button(icon="menu"):
            with ui.menu() as menu:
                ui.menu_item("Save")
                ui.menu_item("Load")
                ui.separator()
                ui.menu_item("Close", menu.close())
        ui.label("Conduit Control Panel").classes("text-xl")
    ui.separator()
    with ui.row().classes("w-full"):
        ui.button(
            "Start Conduit", on_click=lambda: state.set_start(config)
        ).bind_enabled(state)
        ui.button("Stop Conduit", on_click=lambda: state.set_stop(config)).bind_enabled(
            state, "stopable"
        )
    ui.separator()
    ui.label("Detector Parameters").classes("text-lg")
    create_detector_sliders(config, state)
    ui.separator()
    ui.label("GET Parameters").classes("text-lg")
    create_get_sliders(config, state)
    ui.separator()
    ui.label("Cluster Parameters").classes("text-lg")
    create_cluster_sliders(config, state)
    ui.separator()
    ui.label("Estimation Parameters").classes("text-lg")
    create_estimate_sliders(config, state)
    ui.separator()
    ui.run()
