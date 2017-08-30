import veil_component
with veil_component.init_component(__name__):
    from .oracle_driver_installer import oracle_driver_resource

    __all__ = [
        oracle_driver_resource.__name__,
    ]