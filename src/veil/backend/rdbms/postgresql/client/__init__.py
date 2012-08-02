import sandal.component

with sandal.component.init_component(__name__):
    from .adapter import PostgresqlAdapter

    __all__ = [
        # from adapter
        PostgresqlAdapter.__name__
    ]
