import veil_component

with veil_component.init_component(__name__):
    from .local_deployer import register_migration_command

    __all__ = [
        register_migration_command.__name__
    ]
    def init():
        from veil.development.self_checker import register_self_checker
        from .local_deployer import migrate

        register_self_checker('ensure-migrate', migrate)