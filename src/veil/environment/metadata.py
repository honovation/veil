import logging
import grp
import pwd
import os.path

LOGGER = logging.getLogger(__name__)

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