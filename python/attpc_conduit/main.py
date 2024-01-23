from attpc_conduit import Conduit, init_conduit_logger
from attpc_conduit.pad_map import PAD_ELEC_PATH
import dearpygui.dearpygui as dpg
import logging as log

RATE_IN_STRING = "Conduit Data Rate In (MB/s):"
RATE_OUT_STRING = "Conduit Data Rate In (MB/s):"
EVENT_STRING = "Last Processed Event:"

init_conduit_logger()
conduit = Conduit(PAD_ELEC_PATH)


def start_conduit_callback():
    conduit.start_services()


def stop_conduit_callback():
    conduit.stop_services()


def change_rate_in(rate: float):
    dpg.set_value("rate_in", f"{RATE_IN_STRING} {rate:.2}")


def change_rate_out(rate: float):
    dpg.set_value("rate_out", f"{RATE_OUT_STRING} {rate:.2}")


def change_event(event: int):
    dpg.set_value("event", f"{EVENT_STRING} {event}")


dpg.create_context()
dpg.create_viewport(title="AT-TPC Conduit", width=600, height=300)

with dpg.viewport_menu_bar():
    with dpg.menu(label="File"):
        dpg.add_menu_item(label="Save...")
        dpg.add_menu_item(label="Load...")

with dpg.window(label="Conduit Control", min_size=(600, 300)):
    dpg.add_text(f"{RATE_IN_STRING} 0.0", tag="rate_in")
    dpg.add_text(f"{RATE_OUT_STRING} 0.0", tag="rate_out")
    dpg.add_text(f"{EVENT_STRING} 0", tag="event")
    with dpg.group(horizontal=True):
        dpg.add_button(
            label="Start Conduit", callback=start_conduit_callback, tag="start"
        )
        dpg.add_button(label="Stop Conduit", callback=stop_conduit_callback, tag="stop")


def main():
    dpg.setup_dearpygui()
    dpg.show_viewport()
    while dpg.is_dearpygui_running() == True:
        event = conduit.poll_events()
        ## Do analysis here...
        ## Will also call out to set UI values to update status
        dpg.render_dearpygui_frame()
    dpg.destroy_context()
