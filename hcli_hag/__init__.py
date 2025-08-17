import sys
import os
import inspect

from . import config

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

def get_repos():
    try:
        repos = {}
        for d in os.listdir(config.repos):
            if d.endswith('.git'):
                repo_path = os.path.join(config.repos, d)
                try:
                    repo = Repo(repo_path)
                    repos[f"/{d}"] = repo
                except NotGitRepository:
                    pass
                except Exception as e:
                    print(f"Error loading repo {d}: {e}")
        return repos
    except Exception as e:
        print(f"Error scanning repos: {e}")
        return {}

class CustomHTTPGitApplication(HTTPGitApplication):
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '/')
        print(f"Processing PATH_INFO: {path}")
        if path.startswith('/repos'):
            environ['PATH_INFO'] = path[len('/repos'):]
            print(f"Modified PATH_INFO: {environ['PATH_INFO']}")
        return super().__call__(environ, start_response)

class GitResource:
    def __init__(self, git_app):
        self.git_app = git_app

    def on_get(self, req, resp, path):
        self._handle_request(req, resp, path)

    def on_post(self, req, resp, path):
        self._handle_request(req, resp, path)

    def _handle_request(self, req, resp, path):
        environ = req.env.copy()
        environ['PATH_INFO'] = f"/repos/{path}"
        environ['SCRIPT_NAME'] = ''
        print(f"GitResource PATH_INFO: {environ['PATH_INFO']}")

        response_data = []

        def start_response(status, response_headers, exc_info=None):
            resp.status = status
            for name, value in response_headers:
                resp.set_header(name, value)
            def write(data):
                response_data.append(data)
            return write

        result = self.git_app(environ, start_response)
        response_data.extend(result)
        resp.data = b''.join(response_data)
        print(f"Response data: {resp.data!r}")

class CustomApp:
    def __init__(self, name, plugin_path, config_path):
        self.name = name
        self.git_app = CustomHTTPGitApplication(backend=DictBackend(get_repos()))

    def server(self):
        server = falcon.App()
        server.add_route('/repos/{path:path}', GitResource(self.git_app))
        return server

def connector(plugin_path=None, config_path=None):
    def port_router(environ, start_response):
        path = environ.get('PATH_INFO', '/')
        print(f"Incoming path: {path}")
        print(f"Available repos: {get_repos()}")

        if path.startswith('/repos'):
            custom = CustomApp(name="hagproxy", plugin_path=plugin_path, config_path=config_path)
            server = custom.server()
            return server(environ, start_response)
        else:
            return hcli_core.connector(plugin_path=plugin_path, config_path=config_path)

    return port_router
