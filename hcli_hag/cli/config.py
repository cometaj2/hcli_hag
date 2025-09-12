import os
import inspect

root = os.path.dirname(inspect.getfile(lambda: None))
home = os.getenv('HAG_HOME') or os.path.expanduser("~")
repos = os.path.abspath(os.path.join(home, '.hag'))
