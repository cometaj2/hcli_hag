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

from hcli_hag.cli import proxy

from dulwich.web import HTTPGitApplication
from dulwich.server import DictBackend
from dulwich.repo import Repo

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'repos'))

def get_repos():
    try:
        repos = {}
        for d in os.listdir(REPO_DIR):
            if d.endswith('.git'):
                repo_path = os.path.join(REPO_DIR, d)
                try:
                    repo = Repo(repo_path)
                    # Use the repo name without '/repos' prefix
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
        # Log the incoming PATH_INFO for debugging
        path = environ.get('PATH_INFO', '/')
        print(f"Processing PATH_INFO: {path}")
        # Strip '/repos' prefix for Dulwich backend
        if path.startswith('/repos'):
            environ['PATH_INFO'] = path[len('/repos'):]
            print(f"Modified PATH_INFO: {environ['PATH_INFO']}")
        return super().__call__(environ, start_response)

class CustomApp:
    def __init__(self, name, plugin_path, config_path):
        self.name = name
        self.git_app = CustomHTTPGitApplication(backend=DictBackend(get_repos()))

    def server(self):
        return self.git_app

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
            # Replace with your hcli_core connector logic
            return hcli_core.connector(plugin_path=plugin_path, config_path=config_path)

    return port_router
