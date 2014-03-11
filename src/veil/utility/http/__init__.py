import veil_component

with veil_component.init_component(__name__):
    from .http import http_call
    from .web_spider import is_web_spider

    __all__ = [
        # from http
        http_call.__name__,
        # from web_spider
        is_web_spider.__name__,
    ]