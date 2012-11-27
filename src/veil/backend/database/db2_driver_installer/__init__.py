import veil_component

with veil_component.init_component(__name__):
    from .db2_driver_installer import db2_driver_resource

    __all__ = [
        db2_driver_resource.__name__
    ]