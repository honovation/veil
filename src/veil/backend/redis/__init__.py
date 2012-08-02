import sandal.component

with sandal.component.init_component(__name__):
    from .client import register_redis
    from .server import redis_program

    __all__ = [
        # from client
        register_redis.__name__,
        # from server
        redis_program.__name__
    ]