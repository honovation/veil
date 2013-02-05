import veil_component

with veil_component.init_component(__name__):
    from .security import permission_protected
    from .security import grant_permissions
    from .security import list_granted_permissions

    __all__ = [
        permission_protected.__name__,
        grant_permissions.__name__,
        list_granted_permissions.__name__
    ]