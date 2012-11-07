from __future__ import unicode_literals, print_function, division
import os
import logging
import grp
import pwd
from .installer import installer

LOGGER = logging.getLogger(__name__)

def directory_resource(path, **args):
    return 'directory', dict(args, path=path)


@installer('directory')
def install_directory(dry_run_result, **args):
    resource_name = 'directory?{}'.format(args['path'])
    if dry_run_result is None:
        _install_directory(is_dry_run=False, **args)
    else:
        actions = _install_directory(is_dry_run=True, **args)
        if actions:
            dry_run_result[resource_name] = ', '.join(actions)
        else:
            dry_run_result[resource_name] = '-'


def _install_directory(is_dry_run, path, owner='root', group='root', mode=0755, recursive=False):
    actions = []
    if not os.path.exists(path):
        if recursive:
            actions.append('RECURSIVELY-CREATE')
            if not is_dry_run:
                LOGGER.info('creating directory {} recursively'.format(path))
                os.makedirs(path, mode or 0755)
        else:
            actions.append('CREATE')
            if not is_dry_run:
                LOGGER.info('creating directory {}'.format(path))
                os.mkdir(path, mode or 0755)
    if os.path.exists(path):
        actions.extend(ensure_metadata(is_dry_run, path, owner, group, mode=mode))
    return actions


def file_resource(path, content, **args):
    return 'file', dict(args, path=path, content=content)


@installer('file')
def install_file(dry_run_result, **args):
    resource_name = 'file?{}'.format(args['path'])
    if dry_run_result is None:
        _install_file(is_dry_run=False, **args)
    else:
        actions = _install_file(is_dry_run=True, **args)
        if actions:
            dry_run_result[resource_name] = ', '.join(actions)
        else:
            dry_run_result[resource_name] = '-'


def _install_file(is_dry_run, path, content, owner='root', group='root', mode=0644):
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
                LOGGER.info('Writing {} because {}'.format(path, reason))
                fp.write(content)

    if os.path.exists(path):
        actions.extend(ensure_metadata(is_dry_run, path, owner, group, mode=mode))

    return actions


def symbolic_link_resource(path, to, **args):
    return 'symbolic_link', dict(args, path=path, to=to)


@installer('symbolic_link')
def install_symbolic_link(dry_run_result, **args):
    resource_name = 'symbolic_link?path={}'.format(args['path'])
    if dry_run_result is None:
        _install_symbolic_link(is_dry_run=False, **args)
    else:
        action = _install_symbolic_link(is_dry_run=True, **args)
        dry_run_result[resource_name] = action if action else '-'


def _install_symbolic_link(is_dry_run, path, to):
    action = None
    if os.path.lexists(path):
        oldpath = os.path.realpath(path)
        if oldpath == to:
            return
        if not os.path.islink(path):
            raise Exception(
                '%{} trying to create a symlink with the same name as an existing file or directory'.format(path))
        action = 'UPDATE'
        if not is_dry_run:
            LOGGER.info("replacing old symlink {} from {} to {}".format(path, oldpath, to))
            os.unlink(path)
    if not action:
        action = 'CREATE'
    if not is_dry_run:
        LOGGER.info('Creating symbolic {} to {}'.format(path, to))
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
                LOGGER.info("changing permission for %s from %o to %o" % (path, existing_mode, mode))
                os.chmod(path, mode)

    if user:
        uid = coerce_uid(user)
        if stat.st_uid != uid:
            actions.append('CHOWN')
            if not is_dry_run:
                LOGGER.info("changing owner for %s from %d to %s" % (path, stat.st_uid, user))
                os.chown(path, uid, -1)

    if group:
        gid = coerce_gid(group)
        if stat.st_gid != gid:
            actions.append('CHGRP')
            if not is_dry_run:
                LOGGER.info("changing group for %s from %d to %s" % (path, stat.st_gid, group))
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