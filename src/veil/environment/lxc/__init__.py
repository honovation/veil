import veil_component
with veil_component.init_component(__name__):
    from .lxc_container_installer import lxc_container_resource
    from .lxc_container_installer import lxc_container_in_service_resource

    __all__ = [
        lxc_container_resource.__name__,
        lxc_container_in_service_resource.__name__,
    ]
