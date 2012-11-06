import veil_component

with veil_component.init_component(__name__):
    from .redis_client import register_redis

    __all__ = [
        register_redis.__name__
    ]
