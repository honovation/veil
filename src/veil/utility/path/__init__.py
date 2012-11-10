import veil_component

with veil_component.init_component(__name__):
    from .path import as_path


    __all__ = [
        as_path.__name__
    ]