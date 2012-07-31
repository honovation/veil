######## export begin
from .setting import redis_program

__all__ = [
    redis_program.__name__
]
######## export end

def init():
    from sandal.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider
    from .setting import REDIS_BASE_SETTINGS

    init_component(__name__)
    register_deployment_settings_provider(lambda settings: REDIS_BASE_SETTINGS, 'base')

init()