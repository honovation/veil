from __future__ import unicode_literals, print_function, division
import veil_component
import logging

LOGGER = logging.getLogger()
INSTALLERS = {}
stack = []

def installer(name):
    def register(func):
        register_installer(name, func)
        return func

    return register


def register_installer(name, installer):
    INSTALLERS[name] = installer


def dry_run_install_resources(installer_providers, resources):
    dry_run_result = {}
    install_resources(installer_providers, resources, dry_run_result=dry_run_result)
    return dry_run_result


def install_resources(installer_providers, resources, dry_run_result=None):
    stack.append((installer_providers, resources))
    if len(stack) > 30:
        for frame in stack:
            print(frame)
        raise Exception('too many levels')
    for installer_provider in installer_providers:
        veil_component.scan_component(installer_provider, recursive=True)
        installer_provider_component = veil_component.get_root_component(installer_provider)
        installer_provider_resource = ('component', dict(name=installer_provider_component))
        install_resources([], [installer_provider_resource], dry_run_result=dry_run_result)
        try:
            __import__(installer_provider)
            if dry_run_result is not None:
                dry_run_result['@{}'.format(installer_provider)] = '-'
        except:
            if dry_run_result is not None:
                dry_run_result['@{}'.format(installer_provider)] = 'INSTALL'
            else:
                LOGGER.error('failed to load installer provider: {}'.format(installer_provider))
                raise
    for resource in resources:
        if len(resource) != 2:
            raise Exception('invalid resource: {}'.format(resource))
        installer_name, installer_args = resource
        if installer_name not in INSTALLERS:
            if dry_run_result is not None:
                continue
            raise Exception('no installer for: {} {}'.format(installer_name, installer_args))
        result = INSTALLERS[installer_name](dry_run_result=dry_run_result, **installer_args)
        if result:
            install_resources(dry_run_result=dry_run_result, *result)
    stack.pop()