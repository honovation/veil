import veil.component

with veil.component.init_component(__name__):
    from .captcha import generate

    __all__ = [
        generate.__name__
    ]