import io
import os
import json

from hcli_hag.cli import config
from hcli_hag.cli.utils import formatting

from hcli_core import logger

from typing import Optional, Dict, Callable, List

log = logger.Logger(name="hag")


class CLI:

    def __init__(self, commands: List[str], inputstream: Optional[io.BytesIO] = None):
        self.commands = commands
        self.inputstream = inputstream
        self.handlers: Dict[str, Callable] = {
            'ls':  self._handle_ls,
        }

    def execute(self) -> Optional[io.BytesIO]:
        if len(self.commands) > 1 and self.commands[1] in self.handlers:
            return self.handlers[self.commands[1]]()

        return None

    def _handle_ls(self) -> Optional[io.BytesIO]:
        def get_repos():
            try:
                base_url = config.core_wsgiapp_base_url
                repos = []
                for user in os.listdir(config.repos):
                    user_path = os.path.join(config.repos, user)
                    if os.path.isdir(user_path):
                        for repo in os.listdir(user_path):
                            log.info(user_path)
                            if repo.endswith('.git'):
                                repo_path = os.path.join(user_path, repo)
                                log.info(repo_path)
                                try:
                                    repos.append({
                                            'user': user,
                                            'repo': f"{base_url}/{user}/{repo}"
                                    })

                                    #repos[f"/{user}/{repo}"] = 1
                                except Exception as e:
                                    log.error(f"Error loading repo {user}/{repo}: {e}")
                return repos
            except Exception as e:
                log.error(f"Error scanning repos: {e}")
                return {}

        repos = get_repos()
        json_string = json.dumps(repos, indent=4)

        return io.BytesIO(formatting.format_rows(repos).encode('utf-8'))
#         return io.BytesIO(json_string.encode('utf-8'))
