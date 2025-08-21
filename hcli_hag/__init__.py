import sys
import os
import inspect
import hcli_core

from . import config
from . import logger
from . import gitserver

log = logger.Logger("hcli_hag")
log.setLevel(logger.INFO)


def connector(plugin_path=None, config_path=None):
    server_manager = gitserver.LazyServerManager(plugin_path, config_path)

    def port_router(environ, start_response):
        server_port = int(environ.get('SERVER_PORT', 0))
        path = environ.get('PATH_INFO', '/')
        parts = path.split('/', 3)
        if parts[3] in ('info/refs', 'git-upload-pack', 'git-receive-pack'):
            server_type, server = server_manager.get_server(server_port)
            return server(environ, start_response)
        else:
            server = hcli_core.connector(plugin_path=plugin_path, config_path=config_path)
            return server(environ, start_response)
    return port_router
