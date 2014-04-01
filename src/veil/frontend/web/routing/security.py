from __future__ import unicode_literals, print_function, division
import contextlib
from veil.model.security import *


class RoutePermissionProtector(object):
    def list_granting_permissions(self):
        raise NotImplementedError()

    @classmethod
    def as_context_manager(cls, *args, **kwargs):
        protector = cls(*args, **kwargs)

        def route_permission_protected(*args, **kwargs):
            granting_permissions = protector.list_granting_permissions()
            with grant_permissions(*granting_permissions):
                yield

        return contextlib.contextmanager(route_permission_protected)
