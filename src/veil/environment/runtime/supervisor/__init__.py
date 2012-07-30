######## export begin
from .setting import SUPERVISOR_BASE_SETTINGS

SUPERVISOR_BASE_SETTINGS = SUPERVISOR_BASE_SETTINGS

__all__ = [
    'SUPERVISOR_BASE_SETTINGS'
]
######## export end

def init():
    from veil.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider

    init_component(__name__)
    register_deployment_settings_provider(lambda: SUPERVISOR_BASE_SETTINGS)

init()