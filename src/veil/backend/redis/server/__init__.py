import sandal.component

with sandal.component.init_component(__name__):
    from .setting import redis_program

    __all__ = [
        # from setting
        redis_program.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_provider
        from .setting import REDIS_BASE_SETTINGS

        register_settings_provider(lambda settings: REDIS_BASE_SETTINGS, 'base')