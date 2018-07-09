# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.environment import VEIL_BACKUP_MIRROR_ROOT, VEIL_ENV, get_current_veil_server
from veil.frontend.cli import *
from veil.utility.shell import *
from veil.utility.timer import *


@script('barman-backup')
def bring_up_barman_backup(crontab_expression, purpose):
    @run_every(crontab_expression)
    def work():
        try:
            shell_execute('barman backup {}'.format(purpose), capture=True)
        except:
            pass

    work()


@script('barman-recover')
def bring_up_barman_recover(crontab_expression, purpose):
    @run_every(crontab_expression)
    def work():
        ssh_command = 'ssh -p {} -i /etc/ssh/id_ed25519-barman {}@{}'.format(backup_mirror.ssh_port, backup_mirror.ssh_user, backup_mirror.host_ip)
        path = VEIL_BACKUP_MIRROR_ROOT / VEIL_ENV.name / 'latest-database-recover' / purpose
        assert path.startswith('~/')
        try:
            shell_execute('barman recover --remote-ssh-command "{}" {} latest {}'.format(ssh_command, purpose, path[2:]), capture=True)
        except:
            pass

    server = get_current_veil_server()
    if not server.is_barman:
        raise AssertionError('only barman but not {} should be able to run barman recover'.format(server.fullname))
    backup_mirror = server.backup_mirror

    work()
