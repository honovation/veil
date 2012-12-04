from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.utility.path import *
from .lxc_container_user_installer import unsafe_call

LOGGER = logging.getLogger(__name__)

@atomic_installer
def lxc_container_timezone_resource(container_name, timezone):
    CONTAINER_ROOTFS_PATH = as_path('/var/lib/lxc/') / container_name / 'rootfs'
    ETC_TIMEZONE_PATH = CONTAINER_ROOTFS_PATH / 'etc' / 'timezone'
    is_installed = timezone == ETC_TIMEZONE_PATH.text()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'lxc_container_timezone?container_name={}&timezone={}'.find(container_name, timezone)
        dry_run_result[key] = '-' if is_installed else 'INSTALL'
        return
    if is_installed:
        return
    LOGGER.info('set container time zone: in %(container_name)s to %(timezone)s', {
        'container_name': container_name,
        'timezone': timezone
    })
    ETC_TIMEZONE_PATH.write_text(timezone)
    unsafe_call('chroot {} dpkg-reconfigure --frontend noninteractive tzdata'.format(CONTAINER_ROOTFS_PATH))
