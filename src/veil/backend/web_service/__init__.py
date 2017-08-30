import veil_component
with veil_component.init_component(__name__):
    from .web_service import register_web_service
    from .web_service import log_web_fault
    from .web_service import WebService
    from .web_service import Object
    from .web_service_client_installer import web_service_resource
    from .web_service_client_installer import web_service_config

    __all__ = [
        # from web_service
        register_web_service.__name__,
        log_web_fault.__name__,
        Object.__name__,
        WebService.__name__,
        # from web_service_client_installer
        web_service_resource.__name__,
        web_service_config.__name__,
    ]