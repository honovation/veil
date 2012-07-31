def init():
    from veil.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider
    from .setting import SUPERVISOR_BASE_SETTINGS

    init_component(__name__)
    register_deployment_settings_provider(lambda settings: SUPERVISOR_BASE_SETTINGS, 'base')

init()