import veil_component

with veil_component.init_component(__name__):
    from .env_backup import env_backup_resource

    __all__ = [
        env_backup_resource.__name__
    ]