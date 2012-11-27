import veil_component

with veil_component.init_component(__name__):
    from .nginx_installer import nginx_resource

    __all__ = [
        nginx_resource.__name__
    ]