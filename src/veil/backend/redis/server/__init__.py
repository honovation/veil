from .setting import REDIS_BASE_SETTINGS

def init():
    from veil.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider

    init_component(__name__)
    register_deployment_settings_provider(lambda: REDIS_BASE_SETTINGS)

init()