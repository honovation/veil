import veil_component

with veil_component.init_component(__name__):
    from .http import http_call
    from .web_spider import is_web_spider
    from .http_service_client_installer import register_http_service_config
    from .http_service_client_installer import http_service_config
    from .http_service_client_installer import http_service_resource

    __all__ = [
        http_call.__name__,
        is_web_spider.__name__,
        register_http_service_config.__name__,
        http_service_config.__name__,
        http_service_resource.__name__,
    ]