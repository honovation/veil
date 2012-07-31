def init():
    from veil.component import init_component
    from veil.environment.deployment import register_deployment_settings_provider
    from .setting import ensure_veil_settings_consistent_with_dependencies

    init_component(__name__)
    register_deployment_settings_provider(ensure_veil_settings_consistent_with_dependencies, 'final')

init()