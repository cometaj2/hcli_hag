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
        for user in os.listdir(config.repos):
            user_path = os.path.join(config.repos, user)
            if os.path.isdir(user_path):
                for repo in os.listdir(user_path):
                    if repo.endswith('.git'):
                        repo_path = os.path.join(user_path, repo)
                        try:
                            repo_obj = Repo(repo_path)
                            repos[f"/{user}/{repo}"] = repo_obj
                        except Exception as e:
                            log.error(f"Error loading repo {user}/{repo}: {e}")
        return repos
    except Exception as e:
        log.error(f"Error scanning repos: {e}")
        return {}

# Shared utility for handling Git requests
def handle_git_request(req, resp, path, git_app):
    environ = req.env.copy()
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

class GitInfoRefsResource:

    def __init__(self, git_app):
        self.git_app = git_app

    def on_get(self, req, resp, user, repo):
        handle_git_request(req, resp, f"{user}/{repo}/info/refs", self.git_app)

class GitUploadPackResource:

    def __init__(self, git_app):
        self.git_app = git_app

    def on_post(self, req, resp, user, repo):
        handle_git_request(req, resp, f"{user}/{repo}/git-upload-pack", self.git_app)

@requires_auth
class GitReceivePackResource:

    def __init__(self, git_app):
        self.git_app = git_app

    def on_post(self, req, resp, user, repo):
        handle_git_request(req, resp, f"{user}/{repo}/git-receive-pack", self.git_app)

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
                self._server_lock = RLock()
                self._name = name
                self._git_app = HTTPGitApplication(backend=DictBackend(get_repos()))
                self._cfg = c.Config(name)
                self._cfg.set_config_path(config_path)
                self._cfg.parse_configuration()
                self._initialized = True

    def server(self):
        with self._server_lock:
            server = falcon.App(middleware=[authenticator.SelectiveAuthenticationMiddleware(self._name)])
            error_handler = HCLIErrorHandler()
            server.add_error_handler(falcon.HTTPError, error_handler)
            server.add_error_handler(ProblemDetail, error_handler)
            server.add_route('/{user}/{repo}/info/refs', GitInfoRefsResource(self._git_app), methods=['GET'])
            server.add_route('/{user}/{repo}/git-upload-pack', GitUploadPackResource(self._git_app), methods=['POST'])
            server.add_route('/{user}/{repo}/git-receive-pack', GitReceivePackResource(self._git_app), methods=['POST'])
            return server

def connector(plugin_path=None, config_path=None):
    def port_router(environ, start_response):
        path = environ.get('PATH_INFO', '/')
        parts = path.split('/', 3)
        if parts[3] in ('info/refs', 'git-upload-pack', 'git-receive-pack'):
            custom = CustomApp(name="hag", plugin_path=plugin_path, config_path=config_path)
            server = custom.server()
            return server(environ, start_response)
        else:
            server = hcli_core.connector(plugin_path=plugin_path, config_path=config_path)
            return server(environ, start_response)
    return port_router
