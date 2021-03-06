import veil_component
with veil_component.init_component(__name__):
    from .server.pg_server_installer import postgresql_server_resource
    from .server.pg_server_installer import postgresql_user_resource
    from .server.pg_server_installer import postgresql_physical_replication_slot_resource
    from .server.pg_server_installer import postgresql_cluster_resource
    from .server.pg_server_installer import postgresql_cluster_upgrading_resource
    from .server.pg_server_installer import postgresql_maintenance_config
    from .server.pg_server_installer import postgresql_server_running

    from .server.pg_barman_installer import pgbarman_resource

    from .server.pg_fts_chinese import scws_resource
    from .server.pg_fts_chinese import zhparser_resource
    from .server.pg_fts_chinese import scws_dict_resource

    __all__ = [
        postgresql_server_resource.__name__,
        postgresql_user_resource.__name__,
        postgresql_physical_replication_slot_resource.__name__,
        postgresql_cluster_resource.__name__,
        postgresql_cluster_upgrading_resource.__name__,
        postgresql_maintenance_config.__name__,
        postgresql_server_running.__name__,

        pgbarman_resource.__name__,

        scws_resource.__name__,
        zhparser_resource.__name__,
        scws_dict_resource.__name__,
    ]

    def init():
        from veil.backend.database.client import register_adapter_class
        from .adapter import PostgresqlAdapter

        register_adapter_class(PostgresqlAdapter.type, PostgresqlAdapter)
