import veil.component

with veil.component.init_component(__name__):
    from .web_service import register_web_service
    from .web_service_setting import web_service_settings
    from suds.client import WebFault

    __all__ = [
        register_web_service.__name__,
        web_service_settings.__name__,
        WebFault.__name__
    ]