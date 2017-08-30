import veil_component
with veil_component.init_component(__name__):
    from .memoize import memoize

    __all__ = [
        memoize.__name__,
    ]
