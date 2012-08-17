import sandal.component

with sandal.component.init_component(__name__):
    def init():
        from .adapter import PostgresqlAdapter
        from veil.backend.database.client import register_adapter_class

        register_adapter_class('postgresql', PostgresqlAdapter)
