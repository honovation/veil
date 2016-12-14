from __future__ import unicode_literals, print_function, division
import functools
import logging
import inspect
import importlib
import contextlib

import veil_component

LOGGER = logging.getLogger(__name__)
installed_resource_codes = set()
executing_installers = []
dry_run_result = None
application_sub_resources = None
installing = False
stack = []
upgrading = False
downloading_while_dry_run = False


def atomic_installer(func):
    assert inspect.isfunction(func)

    @functools.wraps(func)
    def wrapper(**kwargs):
        if not kwargs.pop('do_install', False):
            return '{}.{}'.format(veil_component.get_leaf_component(func.__module__), func.__name__), kwargs
        try:
            executing_installers.append(func)
            return func(**kwargs)
        finally:
            executing_installers.pop()

    return wrapper


def composite_installer(func):
    assert inspect.isfunction(func)

    @functools.wraps(func)
    def wrapper(**kwargs):
        try:
            executing_installers.append(func)
            return func(**kwargs)
        finally:
            executing_installers.pop()

    return atomic_installer(wrapper)


@atomic_installer
def application_resource(component_names, config):
    global application_sub_resources
    try:
        application_sub_resources = {}
        component_resources = [('veil_installer.component_resource', dict(name=name)) for name in component_names]
        install_resources(component_resources)
        for component_name in component_names:
            try:
                __import__(component_name)
            except Exception:
                if get_dry_run_result() is None:
                    raise
        resources = []
        for section, resource_provider in application_sub_resources.items():
            if veil_component.VEIL_ENV.is_test and section not in config:
                LOGGER.warn('no configuration for application resource: %(env)s, %(section)s', {'env': veil_component.VEIL_ENV, 'section': section})
                continue
            resources.append(resource_provider(config[section]))
        return resources
    finally:
        application_sub_resources = None


def add_application_sub_resource(section, resource_provider):
    if not is_installing():
        return
    if application_sub_resources is None:
        raise Exception('not installing any application resource')
    application_sub_resources[section] = resource_provider


def get_executing_installer():
    return executing_installers[-1]


def install_resource(resource):
    install_resources([resource])


def install_resources(resources):
    global installing
    installing = True
    resources = list(skip_installed_resources(resources))
    for resource in resources:
        more_resources = do_install(resource)
        stack.append(resource)
        try:
            if len(stack) > 30:
                LOGGER.error('failed to install sub resources: %(stack)s', {'stack': stack})
                raise Exception('too many levels')
            install_resources(more_resources)
        finally:
            stack.pop()
        installed_resource_codes.add(to_resource_code(resource))


def do_install(resource):
    installer_name, installer_args = resource
    if installer_name != 'veil_installer.component_resource':
        if '.' not in installer_name:
            raise Exception('invalid installer: {}'.format(installer_name))
        installer_module_name = get_installer_module_name(installer_name)
        if 'veil_installer' != installer_module_name:
            install_resources([('veil_installer.component_resource', dict(name=installer_module_name))])
    try:
        installer = get_installer(installer_name)
        # print('install> {}'.format(resource))
        return installer(do_install=True, **installer_args) or []
    except Exception:
        if get_dry_run_result() is None:
            raise
        else:
            return []


def get_installer(installer_name):
    module = importlib.import_module(get_installer_module_name(installer_name))
    return getattr(module, installer_name.split('.')[-1])


def get_installer_module_name(installer_name):
    return '.'.join(installer_name.split('.')[:-1])


def skip_installed_resources(resources):
    for resource in resources:
        resource_code = to_resource_code(resource)
        if resource_code not in installed_resource_codes:
            yield resource


def to_resource_code(resource):
    if len(resource) != 2:
        raise Exception('invalid resource: {}'.format(resource))
    installer_name, installer_args = resource
    if not isinstance(installer_args, dict):
        raise Exception('invalid resource: {}, {}'.format(installer_name, installer_args))
    resource_code = '{}?{}'.format(installer_name, '&'.join('{}={}'.format(k, installer_args[k]) for k in sorted(installer_args)))
    return resource_code


def parse_resource(resource_code):
    if '?' not in resource_code:
        return resource_code, {}
    installer_name, installer_args = resource_code.split('?', 1)
    if not installer_args:
        return installer_name, {}
    installer_args = [arg if '=' in arg else 'name={}'.format(arg) for arg in installer_args.split('&')]
    installer_args = dict(tuple(item.strip() for item in arg.split('=', 1)) for arg in installer_args)
    return installer_name, installer_args


def get_dry_run_result():
    return dry_run_result


@contextlib.contextmanager
def dry_run():
    global dry_run_result
    dry_run_result = {}
    try:
        yield
    finally:
        dry_run_result = None


def is_installing():
    return installing


def set_upgrading(value):
    global upgrading
    upgrading = value


def is_upgrading():
    return upgrading


def set_downloading_while_dry_run(value):
    global downloading_while_dry_run
    downloading_while_dry_run = value


def is_downloading_while_dry_run():
    return downloading_while_dry_run
