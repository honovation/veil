from __future__ import unicode_literals, print_function, division
import os
import logging
import grp
import pwd
from .installer import atomic_installer
from .installer import get_dry_run_result

LOGGER = logging.getLogger(__name__)

@atomic_installer
def directory_resource(path, owner='root', group='root', mode=0755, recursive=False):
    args = dict(path=path, owner=owner, group=group, mode=mode, recursive=recursive)
    resource_name = 'directory?{}'.format(path)
    dry_run_result = get_dry_run_result()
    if dry_run_result is None:
        install_directory(is_dry_run=False, **args)
    else:
        actions = install_directory(is_dry_run=True, **args)
        if actions:
            dry_run_result[resource_name] = ', '.join(actions)
        else:
            dry_run_result[resource_name] = '-'


def install_directory(is_dry_run, path, owner='root', group='root', mode=0755, recursive=False):
    actions = []
    if not os.path.exists(path):
        if recursive:
            actions.append('RECURSIVELY-CREATE')
            if not is_dry_run:
                LOGGER.info('creating directory recursively: %(path)s', {'path': path})
                os.makedirs(path, mode or 0755)
        else:
            actions.append('CREATE')
            if not is_dry_run:
                LOGGER.info('creating directory: %(path)s', {'path': path})
                os.mkdir(path, mode or 0755)
    if os.path.exists(path):
        actions.extend(ensure_metadata(is_dry_run, path, owner, group, mode=mode))
    return actions


@atomic_installer
def file_resource(path, content, owner='root', group='root', mode=0644):
    resource_name = 'file?{}'.format(path)
    args = dict(path=path, content=content, owner=owner, group=group, mode=mode)
    dry_run_result = get_dry_run_result()
    if dry_run_result is None:
        install_file(is_dry_run=False, **args)
    else:
        actions = install_file(is_dry_run=True, **args)
        if actions:
            dry_run_result[resource_name] = ', '.join(actions)
        else:
            dry_run_result[resource_name] = '-'


def install_file(is_dry_run, path, content, owner='root', group='root', mode=0644):
    write = False
    actions = []
    if not os.path.exists(path):
        write = True
        actions.append('CREATE')
        reason = "it doesn't exist"
    else:
        if content is not None:
            with open(path, "rb") as fp:
                old_content = fp.read()
            if content != old_content:
                write = True
                actions.append('UPDATE')
                reason = "contents don't match"

    if write:
        if not is_dry_run and content:
            with open(path, 'wb') as fp:
                LOGGER.info('Writing file: %(path)s because %(reason)s', {
                    'path': path,
                    'reason': reason
                })
                fp.write(content)

    if os.path.exists(path):
        actions.extend(ensure_metadata(is_dry_run, path, owner, group, mode=mode))

    return actions


@atomic_installer
def symbolic_link_resource(path, to):
    resource_name = 'symbolic_link?path={}'.format(path)
    args = dict(path=path, to=to)
    dry_run_result = get_dry_run_result()
    if dry_run_result is None:
        install_symbolic_link(is_dry_run=False, **args)
    else:
        action = install_symbolic_link(is_dry_run=True, **args)
        dry_run_result[resource_name] = action if action else '-'


def install_symbolic_link(is_dry_run, path, to):
    action = None
    if os.path.lexists(path):
        old_path = os.path.realpath(path)
        if old_path == to:
            return
        if not os.path.islink(path):
            raise Exception(
                '%{} trying to create a symlink with the same name as an existing file or directory'.format(path))
        action = 'UPDATE'
        if not is_dry_run:
            LOGGER.info("replacing old symlink: %(path)s from %(old_path)s to %(to)s", {
                'path': path,
                'old_path': old_path,
                'to': to
            })
            os.unlink(path)
    if not action:
        action = 'CREATE'
    if not is_dry_run:
        LOGGER.info('Creating symbolic: %(path)s to %(to)s', {
            'path': path,
            'to': to
        })
        os.symlink(to, path)
    return action


def ensure_metadata(is_dry_run, path, user, group, mode=None):
    actions = []
    stat = os.stat(path)

    if mode:
        existing_mode = stat.st_mode & 07777
        if existing_mode != mode:
            actions.append('CHMOD')
            if not is_dry_run:
                LOGGER.info('changing permission: for %(path)s from %(existing_mode)s to %(mode)s', {
                    'path': path,
                    'existing_mode': existing_mode,
                    'mode': mode
                })
                os.chmod(path, mode)

    if user:
        uid = coerce_uid(user)
        if stat.st_uid != uid:
            actions.append('CHOWN')
            if not is_dry_run:
                LOGGER.info('changing owner: for %(path)s from %(existing_owner)s to %(user)s', {
                    'path': path,
                    'existing_owner': stat.st_uid,
                    'user': user
                })
                os.chown(path, uid, -1)

    if group:
        gid = coerce_gid(group)
        if stat.st_gid != gid:
            actions.append('CHGRP')
            if not is_dry_run:
                LOGGER.info('changing group: for %(path)s from %(existing_group)s to %(group)s', {
                    'path': path,
                    'existing_group': stat.st_gid,
                    'group': group
                })
                os.chown(path, -1, gid)
    return actions


def coerce_gid(group):
    try:
        gid = int(group)
    except ValueError:
        gid = grp.getgrnam(group).gr_gid
    return gid


def coerce_uid(user):
    try:
        uid = int(user)
    except ValueError:
        uid = pwd.getpwnam(user).pw_uid
    return uid