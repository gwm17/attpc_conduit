from attpc_conduit.controller.ui import build_controller
import rpyc
import click
from nicegui import ui


@click.command()
@click.option(
    "--ip",
    "-i",
    default="localhost",
    type=str,
    help="The ip address of the state server",
    show_default=True,
)
@click.option(
    "--port",
    "-p",
    default=18861,
    type=int,
    help="The port which the state server is listening on",
    show_default=True,
)
def run_controller(ip: str, port: int):
    remote_state = rpyc.connect(host=ip, port=18861)
    build_controller(remote_state)


if __name__ in {"__main__", "__mp_main__"}:
    if __name__ == "__mp_main__":
        run_controller()
    ui.run()
