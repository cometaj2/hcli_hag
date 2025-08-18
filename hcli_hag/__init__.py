import sys
import os
import inspect

from . import config
from . import logger

sys.path.insert(0, config.root)

import falcon
import hcli_core

from hcli_core import config as c
from hcli_core.auth.cli import authenticator
from hcli_core.handler import HCLIErrorHandler
from hcli_problem_details import ProblemDetail

from dulwich.web import HTTPGitApplication
from dulwich.server import DictBackend
from dulwich.repo import Repo

from threading import RLock

log = logger.Logger("hcli_hag")
log.setLevel(logger.INFO)

# Class decorator to mark resources that need authentication or authorization.
def requires_auth(cls):
    cls.requires_authentication = True
    cls.requires_authorization = True
    return cls

def get_repos():
    try:
        repos = {}
        for d in os.listdir(config.repos):
            if d.endswith('.git'):
                repo_path = os.path.join(config.repos, d)
                try:
                    repo = Repo(repo_path)
                    repos[f"/{d}"] = repo
                except Exception as e:
                    log.error(f"Error loading repo {d}: {e}")
        return repos
    except Exception as e:
        log.error(f"Error scanning repos: {e}")
        return {}

class CustomHTTPGitApplication(HTTPGitApplication):
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '/')
        if path.startswith('/repos'):
            environ['PATH_INFO'] = path[len('/repos'):]
        return super().__call__(environ, start_response)

# Shared utility for handling Git requests
def handle_git_request(req, resp, path, git_app):
    environ = req.env.copy()
    environ['PATH_INFO'] = f"/repos/{path}"
    environ['SCRIPT_NAME'] = ''
    response_data = []
    def start_response(status, response_headers, exc_info=None):
        resp.status = status
        for name, value in response_headers:
            resp.set_header(name, value)
        def write(data):
            response_data.append(data)
        return write
    result = git_app(environ, start_response)
    response_data.extend(result)
    resp.data = b''.join(response_data)

# All GET requests go through.
class GitGetResource:

    def __init__(self, git_app):
        self.git_app = git_app

    def on_get(self, req, resp, repo):
        handle_git_request(req, resp, f"{repo}/info/refs", self.git_app)

# POST git-upload-pack are read operations from the client and can go through unauthenticated
class GitUploadResource:

    def __init__(self, git_app):
        self.git_app = git_app

    def on_post(self, req, resp, repo):
        handle_git_request(req, resp, f"{repo}/git-upload-pack", self.git_app)

# POST git-receive-pack are client repo change requests and requires authentication
@requires_auth
class GitReceiveResource:

    def __init__(self, git_app):
        self.git_app = git_app

    def on_post(self, req, resp, repo):
        handle_git_request(req, resp, f"{repo}/git-receive-pack", self.git_app)

class CustomApp:
    _instance = None
    _init_lock = RLock()

    def __new__(cls, *args, **kwargs):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, name, plugin_path=None, config_path=None):
        with self._init_lock:
            if not self._initialized:
                self._name = name
                self._git_app = CustomHTTPGitApplication(backend=DictBackend(get_repos()))
                self._cfg = c.Config(name)
                self._cfg.set_config_path(config_path)
                self._cfg.parse_configuration()
                self._initialized = True

    def server(self):
        server = falcon.App(middleware=[authenticator.SelectiveAuthenticationMiddleware(self._name)])
        error_handler = HCLIErrorHandler()
        server.add_error_handler(falcon.HTTPError, error_handler)
        server.add_error_handler(ProblemDetail, error_handler)

        server.add_route('/{user}/{repo}/info/refs', GitGetResource(self._git_app), methods=['GET']) 
        server.add_route('/{user}/{repo}/git-upload-pack', GitUploadResource(self._git_app), methods=['POST'])
        server.add_route('/{user}/{repo}/git-receive-pack', GitReceiveResource(self._git_app), methods=['POST'])

        return server

def connector(plugin_path=None, config_path=None):
    def port_router(environ, start_response):
        path = environ.get('PATH_INFO', '/')
        parts = path.lstrip('/').split('/')
        if len(parts) == 3 and parts[2] in ('info/refs', 'git-upload-pack', 'git-receive-pack'):
            custom = CustomApp(name="hag", plugin_path=plugin_path, config_path=config_path)
            server = custom.server()
            return server(environ, start_response)
        else:
            server = hcli_core.connector(plugin_path=plugin_path, config_path=config_path)
            return server(environ, start_response)
    return port_router
