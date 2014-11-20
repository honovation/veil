import veil_component

with veil_component.init_component(__name__):
    from .installer import atomic_installer
    from .installer import composite_installer
    from .installer import get_dry_run_result
    from .installer import install_resource
    from .installer import install_resources
    from .installer import application_resource
    from .installer import add_application_sub_resource
    from .installer import get_executing_installer
    from .installer import is_upgrading
    from .installer import is_downloading_while_dry_run
    from .installer import to_resource_code
    from .component_installer import component_resource
    from .component_installer import installer_resource
    from .latest_version_cache import set_resource_latest_version
    from .latest_version_cache import get_resource_latest_version

    __all__ = [
        # from installer
        atomic_installer.__name__,
        composite_installer.__name__,
        get_dry_run_result.__name__,
        install_resource.__name__,
        install_resources.__name__,
        application_resource.__name__,
        add_application_sub_resource.__name__,
        get_executing_installer.__name__,
        is_upgrading.__name__,
        is_downloading_while_dry_run.__name__,
        to_resource_code.__name__,
        # from component_installer
        component_resource.__name__,
        installer_resource.__name__,
        # from latest_version_cache
        set_resource_latest_version.__name__,
        get_resource_latest_version.__name__
    ]
