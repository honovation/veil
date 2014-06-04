from __future__ import unicode_literals, print_function, division
import logging
from veil_installer import *
from veil.utility.shell import *

LOGGER = logging.getLogger(__name__)

@atomic_installer
def iptables_rule_resource(table, rule):
    installed = rule in shell_execute('iptables-save -t {}'.format(table), capture=True)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['iptables?-t {} -A {}'.format(table, rule)] = '-' if installed else 'EXECUTE'
        return
    if installed:
        return
    LOGGER.info('install iptables rule: %(rule)s to table %(table)s...', {'rule': rule, 'table': table})
    shell_execute('iptables -t {} -A {}'.format(table, rule))
    updated_rules = shell_execute('iptables-save -t {}'.format(table), capture=True)
    if rule not in updated_rules:
        raise Exception(
            'rule doest not match the exact format of iptables-save, which will cause duplicated entry in the future, please FIX IT.\n{}'.format(
                updated_rules))


@atomic_installer
def iptables_rule_removed_resource(table, rule):
    installed = rule in shell_execute('iptables-save -t {}'.format(table), capture=True)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['iptables?-t {} -D {}'.format(table, rule)] = 'EXECUTE' if installed else ''
        return
    if installed:
        LOGGER.info('remove iptables rule: %(rule)s from table %(table)s...', {'rule': rule, 'table': table})
        shell_execute('iptables -t {} -D {}'.format(table, rule))


@atomic_installer
def iptables_policy_resource(table, chain, policy):
    installed = '{} {}'.format(chain, policy) in shell_execute('iptables-save -t {}'.format(table), capture=True)
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['iptables?-t {} -P {} {}'.format(table, chain, policy)] = '-' if installed else 'EXECUTE'
        return
    if installed:
        return
    LOGGER.info('install iptables policy: %(chain)s %(policy)s to table %(table)s...', {
        'chain': chain, 'policy': policy, 'table': table})
    shell_execute('iptables -t {} -P {} {}'.format(table, chain, policy))
