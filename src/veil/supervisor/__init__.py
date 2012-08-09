import sandal.component

with sandal.component.init_component(__name__):
    def init():
        from veil.environment.deployment import register_deployment_settings_provider
        from .setting import SUPERVISOR_BASE_SETTINGS

        register_deployment_settings_provider(lambda settings: SUPERVISOR_BASE_SETTINGS, 'base')

    init()