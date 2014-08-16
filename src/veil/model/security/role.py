from __future__ import unicode_literals, print_function, division
from veil.model.collection import *

roles = {}

def define_role(role_name):
    if role_name in roles:
        raise Exception('role already defined: {}'.format(role_name))
    roles[role_name] = Role(role_name)
    return roles[role_name]


def get_role(role_name):
    if role_name not in roles:
        raise Exception('unknown role: {}'.format(role_name))
    return roles[role_name]


class Role(DictObject):
    def __init__(self, name):
        super(Role, self).__init__()
        self.name = name
        self.granted_permissions = set()
        self.revoked_permissions = set()
        self.granted_role_names = set()
        self.revoked_role_names = set()

    def grant_permission(self, permission):
        self.granted_permissions.add(permission)
        return self

    def revoke_permission(self, permission):
        self.revoked_permissions.add(permission)
        return self

    def grant_role(self, *role_names):
        self.granted_role_names |= set(role_names)
        return self

    def grant_all_roles(self):
        self.granted_role_names = set(roles.keys()) - {self.name}
        return self

    def revoke_role(self, *role_names):
        self.revoked_role_names |= set(role_names)
        return self

    def list_granted_permissions(self):
        final_permissions = set()
        for role_name in self.granted_role_names:
            final_permissions |= get_role(role_name).list_granted_permissions()
        for role_name in self.revoked_role_names:
            final_permissions = final_permissions - get_role(role_name).list_granted_permissions()
        final_permissions |= self.granted_permissions
        final_permissions = final_permissions - self.revoked_permissions
        return final_permissions
