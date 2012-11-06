import veil_component

with veil_component.init_component(__name__):
    def init():
        from veil.backend.database.client import register_adapter_class
        from veil.development.self_checker import register_self_checker
        from .adapter import PostgresqlAdapter
        from .maintainence.pg_maintainence import check_if_locked_migration_scripts_being_changed
        from .server.pg_server_installer import install_postgresql_server

        register_adapter_class('postgresql', PostgresqlAdapter)
        register_self_checker('migration-scripts', check_if_locked_migration_scripts_being_changed)
