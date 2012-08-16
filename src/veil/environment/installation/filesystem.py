from __future__ import unicode_literals, print_function, division
import logging
import grp
import pwd
import os.path

LOGGER = logging.getLogger(__name__)

def create_file(path, content, owner='root', group='root', mode=0644):
    write = False
    if not os.path.exists(path):
        write = True
        reason = "it doesn't exist"
    else:
        if content is not None:
            with open(path, "rb") as fp:
                old_content = fp.read()
            if content != old_content:
                write = True
                reason = "contents don't match"

    if write:
        LOGGER.info('Writing {} because {}'.format(path, reason))
        with open(path, 'wb') as fp:
            if content:
                fp.write(content)

    ensure_metadata(path, owner, group, mode=mode)

def delete_file(path):
    if os.path.exists(path):
        LOGGER.info('Delete {}'.format(path))
        os.remove(path)


def create_directory(path, owner='root', group='root', mode=0755, recursive=False):
    if not os.path.exists(path):
        LOGGER.info('Creating directory {}'.format(path))
        if recursive:
            os.makedirs(path, mode or 0755)
        else:
            os.mkdir(path, mode or 0755)
    ensure_metadata(path, owner, group, mode=mode)


def create_symbolic_link(path, to):
    if os.path.lexists(path):
        oldpath = os.path.realpath(path)
        if oldpath == to:
            return
        if not os.path.islink(path):
            raise Exception(
                '%{} trying to create a symlink with the same name as an existing file or directory'.format(path))
        LOGGER.info("replacing old symlink {} from {} to {}".format(path, oldpath, to))
        os.unlink(path)

    LOGGER.info('Creating symbolic {} to {}'.format(path, to))
    os.symlink(to, path)


def ensure_metadata(path, user, group, mode=None):
    stat = os.stat(path)

    if mode:
        existing_mode = stat.st_mode & 07777
        if existing_mode != mode:
            LOGGER.info("Changing permission for %s from %o to %o" % (path, existing_mode, mode))
            os.chmod(path, mode)

    if user:
        uid = coerce_uid(user)
        if stat.st_uid != uid:
            LOGGER.info("Changing owner for %s from %d to %s" % (path, stat.st_uid, user))
            os.chown(path, uid, -1)

    if group:
        gid = coerce_gid(group)
        if stat.st_gid != gid:
            LOGGER.info("Changing group for %s from %d to %s" % (path, stat.st_gid, group))
            os.chown(path, -1, gid)


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