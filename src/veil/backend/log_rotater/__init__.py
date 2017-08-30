import veil_component
with veil_component.init_component(__name__):
    from .log_rotater_installer import log_rotater_resource

    __all__ = [
        log_rotater_resource.__name__
    ]