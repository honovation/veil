import veil_component
with veil_component.init_component(__name__):
    from .collectd_installer import collectd_resource

    __all__ = [
        collectd_resource.__name__
    ]