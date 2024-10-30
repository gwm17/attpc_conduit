from attpc_conduit.controller.ui import create_and_run_controller
import rpyc
import click


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
    create_and_run_controller(remote_state)
