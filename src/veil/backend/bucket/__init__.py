import veil_component

with veil_component.init_component(__name__):
    from .bucket import register_bucket

    __all__ = [
        register_bucket.__name__
    ]