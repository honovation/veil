import veil_component

with veil_component.init_component(__name__):
    from .server_backup import server_backup_resource

    __all__ = [
        server_backup_resource.__name__
    ]