from __future__ import unicode_literals, print_function, division
import logging

LOGGER = logging.getLogger()
INSTALLERS = {}

def register_installer(name, installer):
    INSTALLERS[name] = installer


def dry_run_install_resources(installer_providers, resources):
    dry_run_result = {}
    install_resources(installer_providers, resources, dry_run_result=dry_run_result)
    return dry_run_result


def install_resources(installer_providers, resources, dry_run_result=None):
    for installer_provider in installer_providers:
        installer_provider_resource = ('component', dict(name=installer_provider))
        install_resources([], [installer_provider_resource], dry_run_result=dry_run_result)
        try:
            __import__(installer_provider)
        except:
            LOGGER.error('failed to load installer provider: {}'.format(installer_provider))
            raise
    for resource in resources:
        installer_name, installer_args = resource
        if installer_name not in INSTALLERS:
            raise Exception('no installer for: {} {}'.format(installer_name, installer_args))
        result = INSTALLERS[installer_name](dry_run_result=dry_run_result, **installer_args)
        if result:
            install_resources(dry_run_result=dry_run_result, *result)