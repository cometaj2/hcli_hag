import io
import os
import json
from hcli_hag import config
# import service

from typing import Optional, Dict, Callable, List

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
                repos = {}
                for d in os.listdir(config.repos):
                    if d.endswith('.git'):
                        repos[f"/{d}"] = ''
                return repos
            except Exception as e:
                print(f"Error scanning repos: {e}")
                return {}


        repos = get_repos()
        json_string = json.dumps(repos)

        return io.BytesIO(json_string.encode('utf-8'))
