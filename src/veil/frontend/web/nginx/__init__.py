import sandal.component

with sandal.component.init_component(__name__):
    from .setting import nginx_reverse_proxy_server
    from .setting import nginx_program

    __all__ = [
        nginx_reverse_proxy_server.__name__,
        nginx_program.__name__
    ]

    def init():
        from veil.environment.deployment import register_deployment_settings_provider
        from .setting import NGINX_BASE_SETTINGS
        from .setting import ensure_veil_settings_consistent

        register_deployment_settings_provider(lambda settings: NGINX_BASE_SETTINGS, 'base')
        register_deployment_settings_provider(ensure_veil_settings_consistent, 'final')