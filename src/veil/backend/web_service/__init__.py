import veil_component

with veil_component.init_component(__name__):
    from .web_service import register_web_service
    from .web_service import WebFault
    from .web_service import check_web_service_dependencies

    __all__ = [
        register_web_service.__name__,
        WebFault.__name__,
        check_web_service_dependencies.__name__
    ]