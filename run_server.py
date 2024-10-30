import rpyc
import rpyc.utils
import rpyc.utils.server
from attpc_conduit.core.state import StateService
import click


@click.command()
@click.option(
    "--port",
    "-p",
    default=18861,
    type=int,
    help="The port number for the server to listen on",
    show_default=True,
)
@click.option(
    "--ip",
    "-i",
    default="0.0.0.0",
    type=str,
    help="The ip addresses listen on",
    show_default=True,
)
def run_state_server(port: int, ip: str):
    print(f"Starting state server listening on {ip}:{port}")
    server = rpyc.utils.server.ThreadedServer(StateService, hostname=ip, port=port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("Shutting down server.")
    except Exception as e:
        print(f"State Server recieved an error: {e}")
        print("Shutting down...")
    server.close()


if __name__ == "__main__":
    run_state_server()
