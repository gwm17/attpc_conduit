from attpc_conduit.controller.ui import create_and_run_controller
import rpyc


remote_state = rpyc.connect("localhost", 18861)
create_and_run_controller(remote_state)
