import veil_component

with veil_component.init_component(__name__):
    from .web_service import register_web_service
    from .web_service import WebFault
    from .web_service import check_web_service_dependencies
    from .web_service_client_installer import web_service_client_resource
    from .web_service_client_installer import load_web_service_client_config

    __all__ = [
        # from web_service
        register_web_service.__name__,
        WebFault.__name__,
        check_web_service_dependencies.__name__,
        # from web_service_client_installer
        web_service_client_resource.__name__,
        load_web_service_client_config.__name__
    ]