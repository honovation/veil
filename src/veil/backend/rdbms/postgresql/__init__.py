import sandal.component

with sandal.component.init_component(__name__):
    from .client import PostgresqlAdapter
    from .server import postgresql_program

    __all__ = [
        # from client
        PostgresqlAdapter.__name__,
        # from server
        postgresql_program.__name__
    ]