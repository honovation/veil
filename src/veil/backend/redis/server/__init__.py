import veil.component

with veil.component.init_component(__name__):
    from .redis_server_settings import redis_program
    from .redis_server_settings import redis_settings

    __all__ = [
        # from setting
        redis_program.__name__,
        redis_settings.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_coordinator
        from .redis_server_settings import copy_redis_settings_to_veil

        register_settings_coordinator(copy_redis_settings_to_veil)