from __future__ import unicode_literals, print_function, division
import logging
from veil.env_const import VEIL_OS
from veil_component import as_path
from veil_installer import *
from veil.utility.shell import *
from .lxc_container_installer import is_lxc_container_running

LOGGER = logging.getLogger(__name__)


@atomic_installer
def lxc_container_timezone_resource(container_name, timezone):
    container_rootfs_path = as_path('/var/lib/lxc/') / container_name / 'rootfs'
    etc_timezone_path = container_rootfs_path / 'etc' / 'timezone'
    installed = timezone == etc_timezone_path.text()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        key = 'lxc_container_timezone?container_name={}&timezone={}'.find(container_name, timezone)
        dry_run_result[key] = '-' if installed else 'INSTALL'
        return
    if installed:
        return
    LOGGER.info('set container time zone: in %(container_name)s to %(timezone)s', {
        'container_name': container_name,
        'timezone': timezone
    })
    etc_timezone_path.write_text(timezone)
    shell_execute('chroot {} dpkg-reconfigure --frontend noninteractive tzdata'.format(container_rootfs_path), capture=True)
    if is_lxc_container_running(container_name) and VEIL_OS.codename != 'precise': # precise has issue with lxc-attach
        shell_execute('lxc-attach -n {} -- service cron restart'.format(container_name), capture=True)
