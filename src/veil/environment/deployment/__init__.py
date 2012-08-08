import sandal.component

with sandal.component.init_component(__name__):
    from .setting import register_deployment_settings_provider
    from .setting import get_deployment_settings
    from .ubuntu_package import install_ubuntu_package
    from .ubuntu_package import remove_service_auto_start
    from .python_package import install_python_package
    from .filesystem import create_file
    from .filesystem import delete_file
    from .filesystem import create_directory
    from .filesystem import create_symbolic_link
    from .script import deployment_script

    __all__ = [
        # from setting
        register_deployment_settings_provider.__name__,
        get_deployment_settings.__name__,
        # from ubuntu_package
        install_ubuntu_package.__name__,
        remove_service_auto_start.__name__,
        # from python_package
        install_python_package.__name__,
        # from filesystem
        create_file.__name__,
        delete_file.__name__,
        create_directory.__name__,
        create_symbolic_link.__name__,
        # from script
        deployment_script.__name__
    ]
