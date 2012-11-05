from __future__ import unicode_literals, print_function, division
import os
import logging
import grp
import pwd

LOGGER = logging.getLogger(__name__)

def directory_resource(path, **args):
    return 'directory', dict(args, path=path)


def install_directory(dry_run_result, **args):
    resource_name = 'directory?{}'.format('&'.join(['{}={}'.format(k, v) for k, v in args.items()]))
    if dry_run_result is None:
        _create_directory(is_dry_run=False, **args)
    else:
        actions = _create_directory(is_dry_run=True, **args)
        if actions:
            dry_run_result[resource_name] = ', '.join(actions)
        else:
            dry_run_result[resource_name] = '-'


def _create_directory(is_dry_run, path, owner='root', group='root', mode=0755, recursive=False):
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