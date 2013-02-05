from __future__ import unicode_literals, print_function, division
import functools
import contextlib
import logging

LOGGER = logging.getLogger(__name__)
granted_permissions = set()

def permission_protected(*permissions):
    permissions = set(permissions)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            missing_permissions = permissions - grant_permissions
            if missing_permissions:
                LOGGER.warn('permission denied: missing %(missing_permissions)s', {
                    'missing_permissions': missing_permissions
                })
                raise PermissionDenied('missing {}'.format(missing_permissions))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def list_granted_permissions():
    return granted_permissions


@contextlib.contextmanager
def grant_permissions(*permissions):
    global granted_permissions
    new_permissions = set(permissions) - granted_permissions
    granted_permissions = granted_permissions.union(new_permissions)
    try:
        yield
    finally:
        granted_permissions = granted_permissions - new_permissions


class PermissionDenied(Exception):
    pass

