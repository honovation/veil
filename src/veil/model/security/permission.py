# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import functools
import contextlib

LOGGER = logging.getLogger(__name__)

need_verify_permissions = False
granted_permissions = set()


def permission_protected(*permissions):
    permissions = set(permissions)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if need_verify_permissions:
                missing_permissions = permissions - granted_permissions
                if missing_permissions:
                    LOGGER.warn('permission denied: missing %(missing_permissions)s', {'missing_permissions': missing_permissions})
                    raise PermissionDenied('权限不足：{}'.format('，'.join(missing_permissions)))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def list_granted_permissions():
    return granted_permissions


def grant_permissions(list_permissions):
    @contextlib.contextmanager
    def f():
        global need_verify_permissions
        global granted_permissions
        current_flag = need_verify_permissions
        need_verify_permissions = True
        new_permissions = list_permissions() - granted_permissions
        granted_permissions |= new_permissions
        try:
            yield
        finally:
            granted_permissions = granted_permissions - new_permissions
            need_verify_permissions = current_flag

    return f


class PermissionDenied(Exception):
    pass
