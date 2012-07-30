######## export begin
from .setting import POSTGRESQL_BASE_SETTINGS
from .adapter import PostgresqlAdapter

POSTGRESQL_BASE_SETTINGS = POSTGRESQL_BASE_SETTINGS

__all__ = [
    # from setting
    'POSTGRESQL_BASE_SETTINGS',
    # from adapter
    PostgresqlAdapter.__name__
]
######## export end

def init():
    from veil.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider

    init_component(__name__)
    register_deployment_settings_provider(lambda: POSTGRESQL_BASE_SETTINGS)

init()