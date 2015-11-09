import veil_component

with veil_component.init_component(__name__):
    from .region import parse_address
    __all__ = [
        parse_address.__name__,
    ]