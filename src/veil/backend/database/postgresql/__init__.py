import veil.component

with veil.component.init_component(__name__):
    from .pg_setting import postgresql_settings

    __all__ = [
        postgresql_settings.__name__
    ]

    def init():
        from veil.backend.database.client import register_adapter_class
        from veil.environment.setting import register_settings_coordinator
        from .pg_setting import copy_postgresql_settings_into_veil
        from .adapter import PostgresqlAdapter

        register_adapter_class('postgresql', PostgresqlAdapter)
        register_settings_coordinator(copy_postgresql_settings_into_veil)
