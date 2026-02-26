import os
import inspect

from configparser import ConfigParser
from hcli_core import logger

log = logger.Logger(name="hag")

root = os.path.dirname(inspect.getfile(lambda: None))
home = os.getenv('HAG_HOME') or os.path.expanduser("~")
repos = os.path.abspath(os.path.join(home, '.hag'))
hcli_core_home = os.getenv('hcli_core_home') or os.path.expanduser("~")
hag_config_path = os.path.join(hcli_core_home, ".hcli_core", "etc", "hag", "config")

_parser = ConfigParser(interpolation=None)
_loaded = False

def _load():
    global _loaded
    if _loaded:
        return
    if os.path.exists(hag_config_path):
        _parser.read(hag_config_path)
        _loaded = True
    else:
        log.warning(f"hag config file not found at {hag_config_path}. Using defaults")

def get_core_wsgiapp_base_url() -> str:
    _load()

    # 1. Explicit user override (recommended for production)
    if _parser.has_section("default") and _parser.has_option("default", "core.wsgiapp.base.url"):
        url = _parser.get("default", "core.wsgiapp.base.url").rstrip("/")
        log.debug(f"Using explicit core.wsgiapp.base.url = {url}")
        return url

    # 2. Fallback: build from the port that is already in hag's own config
    port = 10000
    if _parser.has_section("default") and _parser.has_option("default", "core.wsgiapp.port"):
        try:
            port = int(_parser.get("default", "core.wsgiapp.port"))
        except (ValueError, TypeError):
            log.warning("Invalid core.wsgiapp.port. Assuming default 10000")

    url = f"http://localhost:{port}"
    log.debug(f"Using fallback core wsgiapp base URL: {url}")
    return url

core_wsgiapp_base_url = get_core_wsgiapp_base_url()
