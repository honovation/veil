from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *

LOGGER = logging.getLogger(__name__)

@atomic_installer
def iptables_rule_resource(table, rule):
    is_installed = rule in shell_execute('iptables-save -t {}'.format(table), capture=True)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['iptables?-t {} -A {}'.format(table, rule)] = '-' if is_installed else 'EXECUTE'
        return
    if is_installed:
        return
    LOGGER.info('install iptables rule: %(rule)s to table %(table)s...', {'rule': rule, 'table': table})
    shell_execute('iptables -t {} -A {}'.format(table, rule))


@atomic_installer
def iptables_rule_removed_resource(table, rule):
    is_installed = rule in shell_execute('iptables-save -t {}'.format(table), capture=True)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['iptables?-t {} -D {}'.format(table, rule)] = 'EXECUTE' if is_installed else ''
        return
    if is_installed:
        LOGGER.info('remove iptables rule: %(rule)s from table %(table)s...', {'rule': rule, 'table': table})
        shell_execute('iptables -t {} -D {}'.format(table, rule))