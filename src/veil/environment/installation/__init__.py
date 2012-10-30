import veil_component

with veil_component.init_component(__name__):
    from .installation import installation_script
    from .installation import install_dependency
    from .installation import require_component_only_install_once
    from .ubuntu_package import install_ubuntu_package
    from .ubuntu_package import remove_service_auto_start
    from .python_package import install_python_package
    from .filesystem import create_file
    from .filesystem import delete_file
    from .filesystem import create_directory
    from .filesystem import create_symbolic_link

    __all__ = [
        # from installation
        installation_script.__name__,
        install_dependency.__name__,
        require_component_only_install_once.__name__,
        # from ubuntu_package
        install_ubuntu_package.__name__,
        remove_service_auto_start.__name__,
        # from python_package
        install_python_package.__name__,
        # from filesystem
        create_file.__name__,
        delete_file.__name__,
        create_directory.__name__,
        create_symbolic_link.__name__
    ]
