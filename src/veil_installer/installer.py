from __future__ import unicode_literals, print_function, division
import functools
import logging
import inspect
import importlib
import contextlib
import veil_component

LOGGER = logging.getLogger()
installed_resource_codes = set()
executing_composite_installer = None
dry_run_result = None

def atomic_installer(func):
    assert inspect.isfunction(func)

    @functools.wraps(func)
    def wrapper(**kwargs):
        if not kwargs.pop('do_install', False):
            return '{}.{}'.format(
                veil_component.get_leaf_component(func.__module__),
                func.__name__), kwargs
        return func(**kwargs)

    wrapper.is_composite_installer = False
    return wrapper


def composite_installer(func):
    assert inspect.isfunction(func)

    @functools.wraps(func)
    def wrapper(**kwargs):
        global executing_composite_installer

        if not kwargs.pop('do_install', False):
            return '{}.{}'.format(
                veil_component.get_leaf_component(func.__module__),
                func.__name__), kwargs
        try:
            if executing_composite_installer:
                raise Exception('@composite_installer can not be nested')
            executing_composite_installer = func
            return func(**kwargs)
        finally:
            executing_composite_installer = None

    wrapper.is_composite_installer = True
    return wrapper


def get_executing_composite_installer():
    return executing_composite_installer


def install_resources(dry_run_result, resources):
    resources = list(skip_installed_resources(resources))
    for resource in resources:
        more_resources = do_install(resource)
        install_resources(dry_run_result, more_resources)


def do_install(resource):
    installer_name, installer_args = resource
    if installer_name != 'veil_installer.component_resource':
        if '.' not in installer_name:
            raise Exception('invalid installer: {}'.format(installer_name))
        installer_module_name = get_installer_module_name(installer_name)
        install_resources(dry_run_result, [('veil_installer.component_resource', dict(name=installer_module_name))])
    installer = get_installer(installer_name)
    return installer(do_install=True, **installer_args) or []


def get_installer(installer_name):
    module = importlib.import_module(get_installer_module_name(installer_name))
    return getattr(module, installer_name.split('.')[-1])


def get_installer_module_name(installer_name):
    return '.'.join(installer_name.split('.')[:-1])


def skip_installed_resources(resources):
    for resource in resources:
        resource_code = to_resource_code(resource)
        if resource_code not in installed_resource_codes:
            installed_resource_codes.add(resource_code)
            yield resource


def to_resource_code(resource):
    if len(resource) != 2:
        raise Exception('invalid resource: {}'.format(resource))
    installer_name, installer_args = resource
    if not isinstance(installer_args, dict):
        raise Exception('invalid resource: {}, {}'.format(installer_name, installer_args))
    resource_code = '{}?{}'.format(installer_name, '&'.join(
        ['{}={}'.format(k, installer_args[k])
         for k in sorted(installer_args.keys())]))
    return resource_code


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