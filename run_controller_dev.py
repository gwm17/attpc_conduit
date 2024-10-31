from attpc_conduit.controller.ui import build_controller
import rpyc
from nicegui import ui

remote_state = rpyc.connect(host="localhost", port=18861)
build_controller(remote_state)
ui.run()
