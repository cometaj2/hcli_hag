import os
import io
import inspect
import falcon
import gzip

from hcli_core import config as c
from hcli_core.server import HCLICoreWSGIApp
from hcli_core.auth.cli import authenticator
from hcli_core.auth.cli.authenticator import requires_authentication, requires_authorization
from hcli_core.handler import HCLIErrorHandler
from hcli_problem_details import *

from dulwich.web import HTTPGitApplication
from dulwich.server import DictBackend
from dulwich.repo import Repo

from threading import RLock

from hcli_hag.cli import config
from hcli_hag.cli import logger

log = logger.Logger("hcli_hag")
log.setLevel(logger.INFO)


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

@requires_authentication
class GitReceivePackResource:

    def __init__(self, git_app):
        self.git_app = git_app

    def on_post(self, req, resp, user, repo):

        # Check if authenticated user matches the user in the path
        auth_user = c.ServerContext.get_current_user()
        if not auth_user:
            resp.append_header('WWW-Authenticate', 'Basic realm="default"')
            raise AuthenticationError(detail='No authenticated user found', instance=req.path)
        if auth_user != user:
            resp.append_header('WWW-Authenticate', 'Basic realm="default"')
            raise AuthorizationError( detail=f"User '{auth_user}' does not match repository owner '{user}'",
                instance=req.path
            )

        handle_git_request(req, resp, f"{user}/{repo}/git-receive-pack", self.git_app)

class GzipDecompressionMiddleware:
    def process_request(self, req, resp):
        # Check if the request has a Content-Encoding: gzip header
        if req.get_header('Content-Encoding') == 'gzip':
            try:

                # Read and decompress the request body
                compressed_data = req.bounded_stream.read()
                decompressed_data = gzip.decompress(compressed_data)

                # Update the WSGI environment with the decompressed data
                req.env['wsgi.input'] = io.BytesIO(decompressed_data)

                # Update Content-Length to reflect the decompressed data size
                req.env['CONTENT_LENGTH'] = str(len(decompressed_data))

                # Remove the Content-Encoding header to prevent downstream confusion
                del req.headers['Content-Encoding'.upper()]

            except gzip.BadGzipFile as e:
                raise BadRequestError( detail=f"The gzip-compressed request body could not be decompressed.")

class WSGIApp(HCLICoreWSGIApp):
    def __init__(self, name, plugin_path=None, config_path=None):
        super().__init__(name, plugin_path, config_path)
        self.git_app = HTTPGitApplication(backend=DictBackend(get_repos()))

    def server(self):
        server = falcon.App(middleware=[GzipDecompressionMiddleware(),
                                        authenticator.SelectiveAuthenticationMiddleware(self.name)])
        error_handler = HCLIErrorHandler()
        server.add_error_handler(falcon.HTTPError, error_handler)
        server.add_error_handler(ProblemDetail, error_handler)
        server.add_route('/{user}/{repo}/info/refs', GitInfoRefsResource(self.git_app), methods=['GET'])
        server.add_route('/{user}/{repo}/git-upload-pack', GitUploadPackResource(self.git_app), methods=['POST'])
        server.add_route('/{user}/{repo}/git-receive-pack', GitReceivePackResource(self.git_app), methods=['POST'])
        return server
