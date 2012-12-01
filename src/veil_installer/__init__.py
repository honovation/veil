import veil_component

with veil_component.init_component(__name__):
    from .installer import atomic_installer
    from .installer import composite_installer
    from .installer import get_dry_run_result
    from .installer import do_install
    from .installer import application_resource
    from .installer import add_application_sub_resource
    from .installer import get_executing_composite_installer
    from .component_installer import component_resource
    from .component_installer import installer_resource

    __all__ = [
        # from installer
        atomic_installer.__name__,
        composite_installer.__name__,
        get_dry_run_result.__name__,
        do_install.__name__,
        application_resource.__name__,
        add_application_sub_resource.__name__,
        get_executing_composite_installer.__name__,
        # from component_installer
        component_resource.__name__,
        installer_resource.__name__
    ]
