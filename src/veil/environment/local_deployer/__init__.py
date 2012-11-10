import veil_component

with veil_component.init_component(__name__):
    from .migration import register_migration_command
    from .migration import register_reset_command

    __all__ = [
        register_migration_command.__name__,
        register_reset_command.__name__
    ]