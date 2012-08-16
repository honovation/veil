import sandal.component

with sandal.component.init_component(__name__):
    from .client import register_database
    from .client import transactional
    from .postgresql import postgresql_program
    from .postgresql import postgresql_settings

    __all__ = [
        # from client
        register_database.__name__,
        transactional.__name__,
        # from postgresql
        postgresql_program.__name__,
        postgresql_settings.__name__
    ]

    def init():
        from .postgresql import PostgresqlAdapter
        from .client import register_adapter_class

        register_adapter_class('postgresql', PostgresqlAdapter)