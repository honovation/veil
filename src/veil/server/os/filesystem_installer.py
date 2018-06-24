from __future__ import unicode_literals, print_function, division
import os
import logging
import grp
import pwd
import uuid

from veil.environment import CURRENT_USER, CURRENT_USER_GROUP
from veil.utility.encoding import *
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)


@atomic_installer
def directory_resource(path, owner='root', group='root', mode=0755, recursive=False):
    args = dict(path=path, owner=owner, group=group, mode=mode, recursive=recursive)
    dry_run_result = get_dry_run_result()
    if dry_run_result is None:
        install_directory(is_dry_run=False, **args)
    else:
        actions = install_directory(is_dry_run=True, **args)
        resource_name = 'directory?{}'.format(path)
        if actions:
            dry_run_result[resource_name] = ', '.join(actions)
        else:
            dry_run_result[resource_name] = '-'


def install_directory(is_dry_run, path, owner='root', group='root', mode=0755, recursive=False):
    actions = []
    missing_paths = []
    if not os.path.exists(path):
        if recursive:
            missing_paths = list_missing_paths(path)
            actions.append('RECURSIVELY-CREATE')
            if not is_dry_run:
                LOGGER.info('creating directory recursively: %(path)s, %(mode)s', {'path': path, 'mode': oct(mode)})
                os.makedirs(path, mode)
        else:
            actions.append('CREATE')
            if not is_dry_run:
                LOGGER.info('creating directory: %(path)s', {'path': path})
                os.mkdir(path, mode)
    if missing_paths:
        for mp in missing_paths:
            actions.extend(ensure_metadata(is_dry_run, mp, owner, group, mode=mode))
    elif os.path.exists(path):
        actions.extend(ensure_metadata(is_dry_run, path, owner, group, mode=mode))
    return actions


def list_missing_paths(path):
    missing_paths = []
    head = path
    while head and not os.path.exists(head):
        missing_paths.append(head)
        head, tail = os.path.split(head)
        if not tail or tail == os.curdir:
            head, tail = os.path.split(head)
    return missing_paths


@atomic_installer
def file_resource(path, content, owner='root', group='root', mode=0644, keep_origin=False, cmd_run_after_updated=None):
    args = dict(path=path, content=to_str(content), owner=owner, group=group, mode=mode, keep_origin=keep_origin, cmd_run_after_updated=cmd_run_after_updated)
    dry_run_result = get_dry_run_result()
    if dry_run_result is None:
        install_file(is_dry_run=False, **args)
    else:
        actions = install_file(is_dry_run=True, **args)
        resource_name = 'file?{}'.format(path)
        if actions:
            dry_run_result[resource_name] = ', '.join(actions)
        else:
            dry_run_result[resource_name] = '-'


def install_file(is_dry_run, path, content, owner='root', group='root', mode=0644, keep_origin=False, cmd_run_after_updated=None):
    assert content is not None
    actions = []
    write = False
    reason = None
    path_exists = os.path.exists(path)
    temp_path = '/tmp/{}.{}'.format(os.path.basename(path), uuid.uuid4().get_hex())
    try:
        if path_exists:
            shell_execute('sudo cp -f {} {}'.format(path, temp_path), capture=True)
            shell_execute('sudo chown {}:{} {}'.format(CURRENT_USER, CURRENT_USER_GROUP, temp_path), capture=True)
        if path_exists:
            with open(temp_path, 'rb') as fp:
                old_content = fp.read()
            if old_content:
                old_content = old_content.strip()
            if content.strip() != old_content:
                actions.append('UPDATE')
                write = not is_dry_run
                reason = "contents don't match"
        else:
            actions.append('CREATE')
            write = not is_dry_run
            reason = "it doesn't exist"
        if write:
            if path_exists and keep_origin:
                shell_execute('sudo cp -pn {path} {path}.origin'.format(path=path), capture=True, debug=True)
            with open(temp_path, 'wb') as fp:
                LOGGER.info('Writing file: %(path)s because %(reason)s', {'path': temp_path, 'reason': reason})
                fp.write(content)
            shell_execute('sudo mv -f {} {}'.format(temp_path, path), capture=True, debug=True)
            shell_execute('sudo chown {}:{} {}'.format(owner, group, path), capture=True, debug=True)
            shell_execute('sudo chmod {:o} {}'.format(mode, path), capture=True, debug=True)
    finally:
        try:
            shell_execute('sudo rm -f {}'.format(temp_path), capture=True)
        except Exception:
            LOGGER.exception('exception while removing temp file: %(temp_path)s', {'temp_path': temp_path})
    if path_exists:
        actions.extend(ensure_metadata(is_dry_run, path, owner, group, mode=mode))
    if write and cmd_run_after_updated:
        shell_execute(cmd_run_after_updated, capture=True, debug=True)
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
    if os.path.exists(path):
        if not os.path.islink(path):
            raise Exception('trying to create a symlink with the same name as an existing file or directory: {}'.format(path))
        old_path = os.path.realpath(path)
        if old_path == to:
            return
        action = 'UPDATE'
        if not is_dry_run:
            LOGGER.info("replacing old symlink: %(path)s from %(old_path)s to %(to)s", {'path': path, 'old_path': old_path, 'to': to})
            shell_execute('sudo rm {}'.format(path), capture=True, debug=True)
    if not action:
        action = 'CREATE'
    if not is_dry_run:
        LOGGER.info('Creating symbolic: %(path)s to %(to)s', {'path': path, 'to': to})
        shell_execute('sudo ln -s {} {}'.format(to, path), capture=True, debug=True)
        shell_execute('sudo chown -h {}:{} {}'.format(CURRENT_USER, CURRENT_USER_GROUP, path), capture=True, debug=True)
    return action


def ensure_metadata(is_dry_run, path, user, group, mode=None):
    actions = []
    if mode:
        existing_mode = int(shell_execute("sudo stat -c '%a' {}".format(path), capture=True), 8)
        if existing_mode != mode:
            actions.append('CHMOD')
            if not is_dry_run:
                LOGGER.info('changing permission: for %(path)s from %(existing_mode)s to %(mode)s', {
                    'path': path,
                    'existing_mode': oct(existing_mode),
                    'mode': oct(mode)
                })
                shell_execute('sudo chmod {:0} {}'.format(existing_mode, path), capture=True, debug=True)
    if user:
        uid = coerce_uid(user)
        existing_owner = shell_execute("sudo stat -c '%u' {}".format(path), capture=True)
        if existing_owner != uid:
            actions.append('CHOWN')
            if not is_dry_run:
                LOGGER.info('changing owner: for %(path)s from %(existing_owner)s to %(user)s', {
                    'path': path,
                    'existing_owner': existing_owner,
                    'user': user
                })
                shell_execute('sudo chown {} {}'.format(uid, path), capture=True, debug=True)
    if group:
        gid = coerce_gid(group)
        existing_group = shell_execute("sudo stat -c '%g' {}".format(path), capture=True)
        if existing_group != gid:
            actions.append('CHGRP')
            if not is_dry_run:
                LOGGER.info('changing group: for %(path)s from %(existing_group)s to %(group)s', {
                    'path': path,
                    'existing_group': existing_group,
                    'group': group
                })
                os.chown(path, -1, gid)
                shell_execute('sudo chgrp {} {}'.format(gid, path), capture=True, debug=True)
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
