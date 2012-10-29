import veil.component

with veil.component.init_component(__name__):
    from .captcha import register_captcha
    from .captcha import captcha_settings

    __all__ = [
        register_captcha.__name__,
        captcha_settings.__name__
    ]