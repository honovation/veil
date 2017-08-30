import veil_component
with veil_component.init_component(__name__):
    from .veil_server_installer import veil_server_resource

    __all__ = [
        veil_server_resource.__name__
    ]