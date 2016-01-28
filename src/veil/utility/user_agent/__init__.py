import veil_component

with veil_component.init_component(__name__):
    from .ua import is_mobile_device
    from .ua import is_web_spider

    __all__ = [
        is_mobile_device.__name__,
        is_web_spider.__name__,
    ]
