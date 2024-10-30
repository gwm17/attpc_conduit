from .config import Config

from rpyc import Service
from enum import Enum


class RunState(Enum):
    START_RUN: int = 0
    STOP_RUN: int = 1
    RUNNING: int = 2
    NOT_RUNNING: int = 3


class StateService(Service):
    config = Config()
    run = RunState.NOT_RUNNING

    def exposed_get_config(self) -> Config:
        return self.config

    def exposed_set_config(self, config: Config) -> None:
        self.config = config

    def exposed_get_run_state(self) -> RunState:
        return self.run

    def exposed_set_run_state(self, state: RunState):
        self.run = state

    def exposed_should_run_start(self) -> bool:
        if self.run == RunState.START_RUN:
            return True
        else:
            return False

    def exposed_should_run_stop(self) -> bool:
        if self.run == RunState.STOP_RUN:
            return True
        else:
            return False

    def exposed_is_running(self) -> bool:
        if self.run == RunState.RUNNING:
            return True
        else:
            return False
