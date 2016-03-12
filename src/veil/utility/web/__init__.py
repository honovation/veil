import veil_component

with veil_component.init_component(__name__):
    from .web import parse_user_agent
    from .web import is_mobile_device
    from .web import is_web_spider
    from .web import is_ajax_request
    from .web import is_weixin_request

    __all__ = [
        parse_user_agent.__name__,
        is_mobile_device.__name__,
        is_web_spider.__name__,
        is_ajax_request.__name__,
        is_weixin_request.__name__,
    ]
