import veil_component

with veil_component.init_component(__name__):
    from .pg_setting import postgresql_settings

    __all__ = [
        postgresql_settings.__name__
    ]

    def init():
        from veil.backend.database.client import register_adapter_class
        from veil.environment.setting import register_settings_coordinator
        from veil.development.self_checker import register_self_checker
        from .pg_setting import copy_postgresql_settings_into_veil
        from .adapter import PostgresqlAdapter
        from .maintainence.pg_maintainence import check_if_locked_migration_scripts_being_changed

        register_adapter_class('postgresql', PostgresqlAdapter)
        register_settings_coordinator(copy_postgresql_settings_into_veil)
        register_self_checker('migration-scripts', check_if_locked_migration_scripts_being_changed)
