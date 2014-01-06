from __future__ import unicode_literals, print_function, division
import contextlib
import httplib
from veil.frontend.web.tornado import *
from veil.model.security import *

RESOURCE_URI_PREFIX = '/r'


class RoutePermissionProtector(object):
    def list_granting_permissions(self):
        raise NotImplementedError()

    def list_route_permissions(self, route):
        raise NotImplementedError()

    def on_permission_denied(self):
        raise NotImplementedError()

    @classmethod
    def as_context_manager(cls, *args, **kwargs):
        protector = cls(*args, **kwargs)
        def route_permission_protected(*args, **kwargs):
            current_route = get_current_http_context().route
            permissions = set(protector.list_route_permissions(current_route))
            granting_permissions = protector.list_granting_permissions()
            with grant_permissions(*granting_permissions):
                granted_permissions = list_granted_permissions()
                missing_permissions = permissions - granted_permissions
                if missing_permissions:
                    protector.on_permission_denied()
                yield

        return contextlib.contextmanager(route_permission_protected)


class TagBasedRoutePermissionProtector(RoutePermissionProtector):
    def __init__(self, requires_permission, except_having_tag, login_url):
        super(TagBasedRoutePermissionProtector, self).__init__()
        self.requires_permission = requires_permission
        self.except_having_tag = except_having_tag
        self.login_url = login_url

    def list_route_permissions(self, route):
        if self.except_having_tag in route.tags:
            return set()
        return {self.requires_permission}

    def on_permission_denied(self):
        if get_current_http_request().uri.startswith(RESOURCE_URI_PREFIX):
            set_http_status_code(httplib.FORBIDDEN)
            end_http_request_processing()
        return redirect_to(self.login_url)