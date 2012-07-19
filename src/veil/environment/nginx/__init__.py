######## export begin
from .setting import NGINX_BASE_SETTINGS

NGINX_BASE_SETTINGS = NGINX_BASE_SETTINGS

__all__ = [
    'NGINX_BASE_SETTINGS'
]
######## export end

def init():
    from sandal.component import init_component
    from ..setting import register_environment_settings_provider

    init_component(__name__)
    register_environment_settings_provider(lambda: NGINX_BASE_SETTINGS)

init()