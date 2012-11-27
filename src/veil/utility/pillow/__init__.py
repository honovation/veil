import veil_component

with veil_component.init_component(__name__):
    from .pillow_installer import pillow_resource

    __all__ = [
        pillow_resource.__name__
    ]