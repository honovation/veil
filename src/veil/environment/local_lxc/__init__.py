import veil_component

with veil_component.init_component(__name__):
    from .lxc_container_installer import lxc_container_resource
    from .lxc_container_installer import lxc_container_running_resource
    from .lxc_container_installer import lxc_container_stopped_resource
    from .lxc_container_installer import lxc_container_ready_resource
    from .lxc_container_user_installer import lxc_container_user_resource
    from .lxc_container_user_installer import lxc_container_user_password_resource
    from .lxc_container_user_installer import lxc_container_user_group_resource

    __all__ = [
        lxc_container_resource.__name__,
        lxc_container_running_resource.__name__,
        lxc_container_stopped_resource.__name__,
        lxc_container_ready_resource.__name__,
        lxc_container_user_resource.__name__,
        lxc_container_user_password_resource.__name__,
        lxc_container_user_group_resource.__name__
    ]