from __future__ import unicode_literals, print_function, division
import logging
import re
import xmlrpclib
from veil_installer import *
from veil.utility.env_consts import *
from .pip_hack import *

LOGGER = logging.getLogger(__name__)
PIP_FREEZE_OUTPUT = None


@atomic_installer
def python_package_resource(name, url=None, **kwargs):
    installed_version = get_python_package_installed_version(name)
    downloaded_version, local_url = get_downloaded_python_package_version(name)
    latest_version = get_resource_latest_version(to_resource_key(name))
    action = None if installed_version else 'INSTALL'
    upgrade_mode = get_upgrade_mode()
    if UPGRADE_MODE_LATEST == upgrade_mode:
        action = action or 'UPGRADE'
    elif UPGRADE_MODE_FAST == upgrade_mode:
        action = action or (None if latest_version == installed_version else 'UPGRADE')
    elif UPGRADE_MODE_NO == upgrade_mode:
        pass
    else:
        raise NotImplementedError()
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if should_download_while_dry_run() and not url:
            remote_latest_version = get_remote_latest_version(name)
            if not (downloaded_version and downloaded_version == remote_latest_version):
                LOGGER.debug('To download python package: %(name)s, %(downloaded_version)s, %(latest_version)s, %(remote_latest_version)s', {
                    'name': name,
                    'downloaded_version': downloaded_version,
                    'latest_version': latest_version,
                    'remote_latest_version': remote_latest_version
                })
                new_downloaded_version, _ = download_latest(name, **kwargs)
                if new_downloaded_version != downloaded_version:
                    LOGGER.warn('python package with new version downloaded: %(name)s, %(downloaded_version)s, %(new_downloaded_version)s', {
                        'name': name,
                        'downloaded_version': downloaded_version,
                        'new_downloaded_version': new_downloaded_version
                    })
        dry_run_result['python_package?{}'.format(name)] = action or '-'
        return
    if not action:
        return
    if not url: # url can be pinned to specific version or custom build
        remote_latest_version = get_remote_latest_version(name)
        if (UPGRADE_MODE_LATEST == upgrade_mode and not (downloaded_version and downloaded_version == remote_latest_version)) or (UPGRADE_MODE_LATEST != upgrade_mode and installed_version != latest_version and downloaded_version != latest_version):
            LOGGER.debug('To download python package: %(name)s, %(upgrade_mode)s, %(installed_version)s, %(downloaded_version)s, %(latest_version)s, %(remote_latest_version)s', {
                'name': name,
                'upgrade_mode': upgrade_mode,
                'installed_version': installed_version,
                'downloaded_version': downloaded_version,
                'latest_version': latest_version,
                'remote_latest_version': remote_latest_version
            })
            downloaded_version, local_url = download_latest(name, **kwargs)
        url = local_url
    if not installed_version or (UPGRADE_MODE_LATEST == upgrade_mode and (installed_version != downloaded_version or latest_version != downloaded_version)) or (UPGRADE_MODE_LATEST != upgrade_mode and installed_version != latest_version):
        LOGGER.info('installing python package: %(name)s from %(url)s...', {'name': name, 'url': url})
        pip_arg = '--upgrade' if 'UPGRADE' == action else ''
        shell_execute('pip install {} --no-index -f file:///opt/pypi {}'.format(url, pip_arg), capture=True, **kwargs)
        if downloaded_version != latest_version:
            if VEIL_ENV_TYPE in ('development', 'test'):
                set_resource_latest_version(to_resource_key(name), downloaded_version)
                LOGGER.info('python package upgraded to new version: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s', {
                    'name': name,
                    'installed_version': installed_version,
                    'latest_version': latest_version,
                    'downloaded_version': downloaded_version
                })
            else:
                LOGGER.warn('PYTHON PACKAGE UPGRADED TO A VERSION OTHER THAN LATEST VERSION: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s', {
                    'name': name,
                    'installed_version': installed_version,
                    'latest_version': latest_version,
                    'downloaded_version': downloaded_version
                })


@script('print-remote-latest-version')
def print_remote_latest_version(package):
    print(get_remote_latest_version(package))


def get_remote_latest_version(name):
    version = None
    server = xmlrpclib.Server('http://pypi.python.org/pypi')
    versions = server.package_releases(name)
    if versions:
        version = versions[0].strip().replace('-', '_')
    else:
        # TODO: idb-db hack
        if 'ibm-db' == name:
            return get_remote_latest_version('ibm_db')
    if version is None:
        LOGGER.error('get remote latest version for python package failed: %(name)s', {'name': name})
    return version


@script('download-latest')
def download_latest(name, **kwargs):
    LOGGER.info('downloading python package: %(name)s ...', {'name': name})
    version, url = download_package(name, **kwargs)[name]
    return version, url


def to_resource_key(pip_package):
    return 'veil.server.python.python_package_resource?{}'.format(pip_package)


def get_python_package_installed_version(pip_package, from_cache=True):
    global PIP_FREEZE_OUTPUT
    if not from_cache:
        PIP_FREEZE_OUTPUT = None
    if not PIP_FREEZE_OUTPUT:
        PIP_FREEZE_OUTPUT = shell_execute('pip freeze', capture=True)
    lines = PIP_FREEZE_OUTPUT.splitlines(False)
    for line in lines:
        match = re.match('{}==(.*)'.format(pip_package), line)
        if match:
            return match.group(1)
    return None