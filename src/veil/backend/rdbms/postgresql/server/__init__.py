######## export begin
from .setting import postgresql_program

__all__ = [
    postgresql_program.__name__
]
######## export end

def init():
    from veil.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider
    from .setting import POSTGRESQL_BASE_SETTINGS

    init_component(__name__)
    register_deployment_settings_provider(lambda settings: POSTGRESQL_BASE_SETTINGS, 'base')

init()