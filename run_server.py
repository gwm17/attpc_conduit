import rpyc
import rpyc.utils
import rpyc.utils.server
from attpc_conduit.core.state import StateService


def main():
    server = rpyc.utils.server.ThreadedServer(StateService, port=18861)
    server.start()


if __name__ == "__main__":
    main()
