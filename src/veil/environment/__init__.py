######## export begin
from ..layout import VEIL_HOME
from .nginx import NGINX_BASE_SETTINGS
from .nginx import create_nginx_server_settings
from .setting import register_environment_settings_provider

VEIL_HOME = VEIL_HOME
NGINX_BASE_SETTINGS = NGINX_BASE_SETTINGS

__all__ = [
    # from layout
    'VEIL_HOME',
    # from nginx
    'NGINX_BASE_SETTINGS',
    create_nginx_server_settings.__name__,
    # from setting
    register_environment_settings_provider.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()