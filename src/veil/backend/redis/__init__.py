import veil.component

with veil.component.init_component(__name__):
    from .redis_client import register_redis
    from .redis_setting import redis_settings

    __all__ = [
        register_redis.__name__,
        redis_settings.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_coordinator
        from .redis_setting import copy_redis_settings_to_veil

        register_settings_coordinator(copy_redis_settings_to_veil)