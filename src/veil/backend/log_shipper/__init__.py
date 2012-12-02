import veil_component

with veil_component.init_component(__name__):
    from .log_shipper_installer import log_shipper_resource

    __all__ = [
        log_shipper_resource.__name__
    ]