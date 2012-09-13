import veil.component

with veil.component.init_component(__name__):
    from .pillow_installer import register_pillow_dependency_provider
    from .pillow_installer import install_pillow

    __all__ = [
        # from pillow_installer
        register_pillow_dependency_provider.__name__,
        install_pillow.__name__
    ]