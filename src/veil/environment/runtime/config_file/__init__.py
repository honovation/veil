import sandal.component

with sandal.component.init_component(__name__):
    def init():
        from veil.environment.deployment import register_deployment_settings_provider
        from .setting import ensure_veil_settings_consistent_with_dependencies

        register_deployment_settings_provider(ensure_veil_settings_consistent_with_dependencies, 'final')

    init()