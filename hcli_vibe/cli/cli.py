import json
import io
from utils import formatting

from typing import Optional, Dict, Callable, List

class CLI:
   def __init__(self, commands: List[str], inputstream: Optional[io.BytesIO] = None):
       self.commands = commands
       self.inputstream = inputstream
       self.service = service.Service()
       self.handlers: Dict[str, Callable] = {
           'git':  self._handle_git,
       }

   def execute(self) -> Optional[io.BytesIO]:
       if len(self.commands) > 1 and self.commands[1] in self.handlers:
           return self.handlers[self.commands[1]]()

       return None

   def _handle_git(self) -> Optional[io.BytesIO]:
       if len(self.commands) == 1 and self.commands[1] == 'sig':
           repo_sig = self.service.sig()
           return io.BytesIO(repo_sig.encode('utf-8'))
       if len(self.commands) == 2 and self.commands[2] == 'sig':
           repo_sig = self.service.sig(self.commands[3])
           return io.BytesIO(repo_sig.encode('utf-8'))

       return None
