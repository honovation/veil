import veil_component

with veil_component.init_component(__name__):
    from .memorize import memorize

    __all__ = [
        memorize.__name__,
    ]
