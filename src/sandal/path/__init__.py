import sandal.component

with sandal.component.init_component(__name__):
    from .path import path

    __all__ = [
        # from path
        path.__name__
    ]