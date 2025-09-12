from hcli_core import config as c

from threading import RLock

from hcli_hag.cli.wsgiapp import wsgiapp

from . import logger

log = logger.Logger("hcli_hag")


class LazyServerManager:
    _instance = None
    _init_lock = RLock()

    def __new__(cls, *args, **kwargs):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, plugin_path=None, config_path=None):
        with self._init_lock:
            if not self._initialized:
                self.plugin_path = plugin_path
                self.config_path = config_path
                self.servers = {}  # port -> server mapping
                self.apps = {}     # type -> GitApp mapping
                self.server_lock = RLock()

                self.mgmt_port = c.Config.get_management_port(config_path)

                log.info(f"Lazy initialization...")
                self._initialized = True

    def _get_git_app(self):
        if 'hag' not in self.apps:
            log.info("================================================")
            log.info(f"Initializing Core Git application:")
            log.info(f"{self.plugin_path}")
            self.apps['hag'] = wsgiapp.GitApp("hag", self.plugin_path, self.config_path)
        return self.apps['hag']

    # Lazy initialize server for given port if it matches configuration.
    def get_server(self, port):
        if port in self.servers:
            return self.servers[port]

        with self.server_lock:
            # Check again in case another thread initialized while we waited
            if port in self.servers:
                return self.servers[port]

            # For any other port, assume it's a core server port
            if not self.mgmt_port or port != self.mgmt_port:
                gitapp = self._get_git_app()
                server = gitapp.server()
                self.servers[port] = ('hag', server)

            return self.servers.get(port)
