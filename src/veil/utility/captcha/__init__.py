import veil_component

with veil_component.init_component(__name__):
    from .captcha import register_captcha

    __all__ = [
        register_captcha.__name__
    ]