import veil.component

with veil.component.init_component(__name__):
    from .server import postgresql_program
    from .server import postgresql_settings

    __all__ = [
        # from server
        postgresql_program.__name__,
        postgresql_settings.__name__
    ]
