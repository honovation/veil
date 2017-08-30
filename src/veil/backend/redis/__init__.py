import veil_component
with veil_component.init_component(__name__):
    from .redis_client import register_redis
    from .redis_client_installer import redis_client_resource
    from .redis_server_installer import redis_server_resource

    __all__ = [
        register_redis.__name__,
        redis_client_resource.__name__,
        redis_server_resource.__name__
    ]
