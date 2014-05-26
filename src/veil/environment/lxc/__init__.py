import veil_component

with veil_component.init_component(__name__):
    from .lxc_container_installer import lxc_container_created_resource
    from .lxc_container_installer import lxc_container_in_service_resource
    from .lxc_container_installer import lxc_container_resource
    from .lxc_container_user_installer import lxc_container_user_resource
    from .lxc_container_user_installer import lxc_container_user_group_resource
    from .lxc_container_timezone_installer import lxc_container_timezone_resource
    from .lxc_container_network_installer import lxc_container_network_resource
    from .lxc_container_network_installer import lxc_container_nameservers_resource

    __all__ = [
        # from lxc_container_installer
        lxc_container_created_resource.__name__,
        lxc_container_in_service_resource.__name__,
        lxc_container_resource.__name__,
        # from lxc_container_user_installer
        lxc_container_user_resource.__name__,
        lxc_container_user_group_resource.__name__,
        # from lxc_container_timezone_installer
        lxc_container_timezone_resource.__name__,
        # from lxc_container_network_installer
        lxc_container_network_resource.__name__,
        lxc_container_nameservers_resource.__name__
    ]