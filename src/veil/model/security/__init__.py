import veil_component

with veil_component.init_component(__name__):
    from .permission import permission_protected
    from .permission import grant_permissions
    from .permission import list_granted_permissions
    from .permission import PermissionDenied
    from .role import define_role
    from .role import get_role

    __all__ = [
        # from permission
        permission_protected.__name__,
        grant_permissions.__name__,
        list_granted_permissions.__name__,
        PermissionDenied.__name__,
        # from role
        define_role.__name__,
        get_role.__name__
    ]