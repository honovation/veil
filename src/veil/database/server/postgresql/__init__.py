######## export begin
from .setting import POSTGRESQL_BASE_SETTINGS

POSTGRESQL_BASE_SETTINGS = POSTGRESQL_BASE_SETTINGS

__all__ = [
    'POSTGRESQL_BASE_SETTINGS'
]
######## export end

def init():
    from sandal.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider

    init_component(__name__)
    register_deployment_settings_provider(lambda: POSTGRESQL_BASE_SETTINGS)

init()