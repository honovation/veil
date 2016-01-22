import veil_component

with veil_component.init_component(__name__):

    from .device import is_mobile

    __all__ = [
        is_mobile.__name__,
    ]
