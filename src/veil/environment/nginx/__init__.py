######## export begin
from .setting import NGINX_BASE_SETTINGS
from .setting import create_nginx_server_settings

NGINX_BASE_SETTINGS = NGINX_BASE_SETTINGS

__all__ = [
    'NGINX_BASE_SETTINGS',
    create_nginx_server_settings.__name__
]
######## export end

def init():
    from sandal.component import init_component
    from ..setting import register_environment_settings_provider

    init_component(__name__)
    register_environment_settings_provider(lambda: NGINX_BASE_SETTINGS)

init()