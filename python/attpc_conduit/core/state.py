from .config import Config

from rpyc import Service


class StateService(Service):
    config = Config()
    run = False
    shutdown = False

    def exposed_get_config(self) -> Config:
        return self.config

    def exposed_set_config(self, config: Config) -> None:
        self.config = config

    def exposed_is_running(self) -> bool:
        return self.run

    def exposed_stop(self) -> None:
        self.run = False

    def exposed_start(self) -> None:
        self.run = True

    def exposed_should_shutdown(self) -> bool:
        return self.shutdown

    def exposed_set_shutdown(self) -> None:
        self.shutdown = True
