import veil_component

with veil_component.init_component(__name__):
    from .path import Path

    as_path = Path

    __all__ = [
        # from path
        Path.__name__,
        'as_path'
    ]