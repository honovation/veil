def init():
    from veil.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider
    from .setting import demo_settings_provider

    init_component(__name__)
    register_deployment_settings_provider(demo_settings_provider)

init()