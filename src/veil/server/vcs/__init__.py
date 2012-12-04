import veil_component

with veil_component.init_component(__name__):
    from .subversion_installer import subversion_repository_resource
    from .subversion_installer import subversion_repository_checked_out_resource
    from .subversion_installer import subversion_repository_updated_resource

    __all__ = [
        # from subversion_installer
        subversion_repository_resource.__name__,
        subversion_repository_checked_out_resource.__name__,
        subversion_repository_updated_resource.__name__
    ]
