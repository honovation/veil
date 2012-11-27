import veil_component

with veil_component.init_component(__name__):
    from .maintenance.pg_maintenance import check_if_locked_migration_scripts_being_changed
    from .server.pg_server_installer import postgresql_server_resource
    from .server.pg_server_installer import postgresql_global_bin_resource
    from .server.pg_server_installer import postgresql_user_resource
    from .server.pg_server_installer import postgresql_cluster_resource

    __all__ = [
        check_if_locked_migration_scripts_being_changed.__name__,
        postgresql_server_resource.__name__,
        postgresql_global_bin_resource.__name__,
        postgresql_user_resource.__name__,
        postgresql_cluster_resource.__name__
    ]

    def init():
        from veil.backend.database.client import register_adapter_class
        from .adapter import PostgresqlAdapter
        from .maintenance.pg_maintenance import check_if_locked_migration_scripts_being_changed

        register_adapter_class('postgresql', PostgresqlAdapter)