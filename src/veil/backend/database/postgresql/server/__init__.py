import veil.component

with veil.component.init_component(__name__):
    from .setting import postgresql_program
    from .setting import postgresql_settings

    __all__ = [
        postgresql_program.__name__,
        postgresql_settings.__name__
    ]

    def init():
        from veil.environment.setting import register_settings_coordinator
        from .setting import copy_postgresql_settings_into_veil

        register_settings_coordinator(copy_postgresql_settings_into_veil)