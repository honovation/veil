from __future__ import unicode_literals, print_function, division
import logging
from veil.utility.shell import *
from veil_installer import *

LOGGER = logging.getLogger(__name__)


@atomic_installer
def local_iptables_rule_resource(table, rule):
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