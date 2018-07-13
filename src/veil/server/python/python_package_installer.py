from __future__ import unicode_literals, print_function, division
import logging
import re
import imp
from pkg_resources import safe_name, safe_version, parse_version, to_filename
from veil_component import VEIL_ENV
from veil.environment import PYPI_ARCHIVE_DIR, get_current_veil_server, get_current_veil_env
from veil.utility.shell import *
from veil_installer import *
from veil.frontend.cli import *

LOGGER = logging.getLogger(__name__)


@atomic_installer
def python_package_resource(name, version=None, url=None, reload_after_install=False, **kwargs):
    name = safe_name(name)
    if version:
        version = safe_version(version)
    if url:
        if not version:
            raise Exception('python package version not specified for <{}> with url <{}>'.format(name, url))
        if version not in url:
            LOGGER.warn('please double check and ensure python package version is consistent with url: %(version)s, %(url)s', {
                'version': version,
                'url': url
            })

    upgrading = is_upgrading()
    installed_version = get_python_package_installed_version(name)
    downloaded_version = get_downloaded_python_package_version(name, version)
    latest_version = get_resource_latest_version(to_resource_key(name))
    if upgrading:
        may_update_resource_latest_version = VEIL_ENV.is_dev or VEIL_ENV.is_test
        if installed_version:
            if version:
                if version == installed_version:
                    need_install = False
                    need_download = False
                    action = None
                else:
                    need_install = True
                    need_download = downloaded_version != version
                    action = 'UPGRADE'
            else:
                need_install = None
                need_download = True
                action = 'UPGRADE'
        else:
            need_install = True
            need_download = not version or downloaded_version != version
            action = 'INSTALL'
    else:
        may_update_resource_latest_version = (VEIL_ENV.is_dev or VEIL_ENV.is_test) and (not latest_version or version and version != latest_version or not version and latest_version < installed_version)
        need_install = not installed_version or (version or latest_version) and (version or latest_version) != installed_version
        need_download = need_install and (not downloaded_version or (version or latest_version) and (version or latest_version) != downloaded_version)
        if need_install:
            action = 'UPGRADE' if installed_version else 'INSTALL'
        else:
            action = None

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if need_download and is_downloading_while_dry_run():
            new_downloaded_version = download_python_package(name, version or (None if upgrading else latest_version), url=url, **kwargs)
            if new_downloaded_version != downloaded_version:
                LOGGER.debug('python package with new version downloaded: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s, %(new_downloaded_version)s, %(url)s', {
                    'name': name,
                    'installed_version': installed_version,
                    'latest_version': latest_version,
                    'downloaded_version': downloaded_version,
                    'new_downloaded_version': new_downloaded_version,
                    'url': url
                })
                downloaded_version = new_downloaded_version
            if upgrading and action == 'UPGRADE' and installed_version == downloaded_version:
                action = None
        dry_run_result['python_package?{}'.format(name)] = action or '-'
        return

    if need_download:
        new_downloaded_version = download_python_package(name, version or (None if upgrading else latest_version), url=url, **kwargs)
        if new_downloaded_version != downloaded_version:
            LOGGER.debug('python package with new version downloaded: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s, %(new_downloaded_version)s, %(url)s', {
                'name': name,
                'installed_version': installed_version,
                'latest_version': latest_version,
                'downloaded_version': downloaded_version,
                'new_downloaded_version': new_downloaded_version,
                'url': url
            })
            downloaded_version = new_downloaded_version
        if upgrading and need_install is None:
            need_install = installed_version != downloaded_version

    if need_install:
        if installed_version:
            LOGGER.info('upgrading python package: %(name)s, %(latest_version)s, %(installed_version)s, %(version_to_install)s', {
                'name': name,
                'latest_version': latest_version,
                'installed_version': installed_version,
                'version_to_install': downloaded_version
            })
        else:
            LOGGER.info('installing python package: %(name)s, %(latest_version)s, %(version_to_install)s', {
                'name': name,
                'latest_version': latest_version,
                'version_to_install': downloaded_version
            })
        installed_version = install_python_package(name, downloaded_version, url=url, **kwargs)
        if reload_after_install:
            reload_python_package(name)

    if may_update_resource_latest_version and installed_version and installed_version != latest_version:
        set_resource_latest_version(to_resource_key(name), installed_version)
        LOGGER.info('updated python package resource latest version: %(name)s, %(latest_version)s, %(new_latest_version)s', {
            'name': name,
            'latest_version': latest_version,
            'new_latest_version': installed_version
        })


def to_resource_key(package_name):
    return 'veil.server.python.python_package_resource?{}'.format(package_name)


installed_package_name2version = None


def get_python_package_installed_version(name, from_cache=True):
    global installed_package_name2version
    if not from_cache:
        installed_package_name2version = None
    if installed_package_name2version is None:
        installed_package_name2version = {}
        pip_freeze_output = shell_execute('pip freeze', capture=True, debug=True)
        for line in pip_freeze_output.splitlines():
            parts = line.split('==', 1)
            if len(parts) == 2:
                installed_package_name2version[parts[0]] = parts[1]
    return installed_package_name2version.get(safe_name(name))


RE_OUTDATED_PACKAGE = re.compile(r'^(.+) \(Current: .+ Latest: (.+)\)$')
outdated_package_name2latest_version = None


def get_installed_package_remote_latest_version(name):
    global outdated_package_name2latest_version
    if outdated_package_name2latest_version is None:
        outdated_package_name2latest_version = {}
        server = get_current_veil_server()
        if name == 'tornado':
            lines = shell_execute('pip list -l -o | grep Latest:', capture=True, debug=True).splitlines()
        else:
            pip_index_args = '-i {}'.format(server.pypi_index_url) if server.pypi_index_url else ''
            lines = shell_execute('pip list {} -l -o | grep Latest:'.format(pip_index_args), capture=True, debug=True).splitlines()
        for line in lines:
            match = RE_OUTDATED_PACKAGE.match(line)
            outdated_package_name2latest_version[match.group(1)] = match.group(2)
    return outdated_package_name2latest_version.get(name)


def download_python_package(name, version=None, url=None, **kwargs):
    tries = 0
    max_tries = 3
    server = get_current_veil_server()
    pip_index_args = '-i {}'.format(server.pypi_index_url) if server.pypi_index_url else ''
    name_term = '{}{}'.format(name, '=={}'.format(version) if version else '')
    while True:
        tries += 1
        try:
            if url:
                shell_execute('pip download {} --timeout 30 -d {} {}'.format(pip_index_args, PYPI_ARCHIVE_DIR, url),
                              capture=True, debug=True, **kwargs)
            else:
                if name == 'tornado':
                    shell_execute('pip download --timeout 30 -d {} {}'.format(PYPI_ARCHIVE_DIR, name_term),
                                  capture=True, debug=True, **kwargs)
                elif name == 'ibm-db':
                    shell_execute(
                        'pip download --timeout 180 {} -d {} {}'.format(pip_index_args, PYPI_ARCHIVE_DIR, name_term),
                        capture=True, debug=True, **kwargs)
                else:
                    shell_execute(
                        'pip download {} --timeout 30 -d {} {}'.format(pip_index_args, PYPI_ARCHIVE_DIR, name_term),
                        capture=True, debug=True, **kwargs)
        except Exception:
            if tries >= max_tries:
                raise
        else:
            break
    downloaded_version = get_downloaded_python_package_version(name, version)
    assert not version or version == downloaded_version, \
        'the downloaded version of python package {} is {}, different from the specific version {}'.format(name, downloaded_version, version)
    return downloaded_version


RE_ARCHIVE_FILENAME = re.compile(r'^.+\-(.+)\-$')


def get_downloaded_python_package_version(name, version=None):
    versions = []
    prefix = '{}-'.format(name)
    prefix1 = '{}-'.format(to_filename(name))
    for archive_file in set(PYPI_ARCHIVE_DIR.files('{}*'.format(prefix)) + PYPI_ARCHIVE_DIR.files('{}*'.format(prefix1))):
        archive_filename = archive_file.basename()
        pos = archive_filename.find('.tar.')
        if pos == -1:
            pos = archive_filename.find('.zip')
        if pos == -1 and archive_file.ext == '.whl':
            pos = archive_filename[len(prefix):].find('-')
            if pos != -1:
                pos += len(prefix)
        if pos == -1:
            continue
        archive_version = archive_filename[len(prefix): pos]
        if version:
            if version == archive_version:
                return version
        else:
            versions.append(archive_version)
    versions.sort(key=lambda v: parse_version(v), reverse=True)
    return versions[0] if versions else None


def install_python_package_remotely(name, version, url, **kwargs):
    tries = 0
    max_tries = 3
    server = get_current_veil_server()
    pip_index_args = '-i {}'.format(server.pypi_index_url) if server.pypi_index_url else ''
    while True:
        tries += 1
        try:
            if url:
                shell_execute('pip install {} --timeout 30 {}'.format(pip_index_args, url), capture=True, debug=True,
                              **kwargs)
            else:
                if name == 'tornado':
                    shell_execute('pip install --timeout 30 {}=={}'.format(name, version), capture=True, debug=True,
                                  **kwargs)
                elif name == 'ibm-db':
                    shell_execute('pip install --timeout 180 {} {}=={}'.format(pip_index_args, name, version),
                                  capture=True, debug=True, **kwargs)
                else:
                    shell_execute('pip install {} --timeout 30 {}=={}'.format(pip_index_args, name, version),
                                  capture=True, debug=True, **kwargs)
        except Exception:
            if tries >= max_tries:
                raise
        else:
            break


def install_python_package(name, version, url=None, **kwargs):
    try:
        shell_execute('pip install --no-index --find-links {} {}=={}'.format(PYPI_ARCHIVE_DIR, name, version), capture=True, debug=True, **kwargs)
    except ShellExecutionError:
        LOGGER.warn('cannot install from local and try install from remote', exc_info=1)
        install_python_package_remotely(name, version, url, **kwargs)
    return version


@script('upgrade-pip')
def upgrade_pip(setuptools_version, wheel_version, pip_version):
    env = get_current_veil_env()
    pip_index_args = '-i {}'.format(env.pypi_index_url) if env.pypi_index_url else ''
    shell_execute('pip install {} --upgrade pip=={}'.format(pip_index_args, pip_version), capture=True, debug=True)
    shell_execute('pip install {} --upgrade setuptools=={}'.format(pip_index_args, setuptools_version), capture=True, debug=True)
    shell_execute('pip install {} --upgrade wheel=={}'.format(pip_index_args, wheel_version), capture=True, debug=True)


@atomic_installer
def python_sourcecode_package_resource(package_dir, name, version, env=None):
    assert version is not None
    upgrading = is_upgrading()
    installed_version = get_python_package_installed_version(name)
    latest_version = get_resource_latest_version(to_resource_key(name))
    need_update_resource_latest_version = (VEIL_ENV.is_dev or VEIL_ENV.is_test) and version != latest_version
    if upgrading:
        if installed_version:
            if version == installed_version:
                need_install = False
                action = None
            else:
                need_install = True
                action = 'UPGRADE'
        else:
            need_install = True
            action = 'INSTALL'
    else:
        need_install = version != installed_version
        if need_install:
            action = 'UPGRADE' if installed_version else 'INSTALL'
        else:
            action = None

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        dry_run_result['python_sourcecode_package?{}'.format(name)] = action or '-'
        return

    if need_install:
        if installed_version:
            LOGGER.info('upgrading python source package: %(name)s, %(latest_version)s, %(installed_version)s, %(version_to_install)s', {
                'name': name,
                'latest_version': latest_version,
                'installed_version': installed_version,
                'version_to_install': version
            })
        else:
            LOGGER.info('installing python source package: %(name)s, %(latest_version)s, %(version_to_install)s', {
                'name': name,
                'latest_version': latest_version,
                'version_to_install': version
            })
        shell_execute('python setup.py build install', env=env, cwd=package_dir)

    if need_update_resource_latest_version:
        set_resource_latest_version('veil.server.python.python_sourcecode_package_resource?{}'.format(name), version)
        LOGGER.info('updated python source package resource latest version: %(name)s, %(latest_version)s, %(new_latest_version)s', {
            'name': name,
            'latest_version': latest_version,
            'new_latest_version': version
        })


def reload_python_package(name):
    try:
        try:
            __import__(name)
        except (ImportError, IOError):
            fp, pathname, description = imp.find_module(name)
            try:
                imp.load_module(name, fp, pathname, description)
            finally:
                # Since we may exit via an exception, close fp explicitly.
                if fp:
                    fp.close()
    except Exception:
        LOGGER.warn('cannot reload python package: %(name)s', {'name': name}, exc_info=1)
