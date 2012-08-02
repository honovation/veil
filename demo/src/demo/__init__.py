import sandal.component

with sandal.component.init_component(__name__):
    def init():
        from veil.environment.deployment import register_deployment_settings_provider
        from .setting import demo_settings_provider

        register_deployment_settings_provider(demo_settings_provider)

    init()