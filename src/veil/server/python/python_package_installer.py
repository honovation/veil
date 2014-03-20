from __future__ import unicode_literals, print_function, division
import logging
import re
from pkg_resources import safe_name, safe_version, parse_version, to_filename
from veil.env_const import VEIL_ENV_TYPE
from veil.utility.shell import *
from veil_component import *
from veil_installer import *
from veil.frontend.cli import *

LOGGER = logging.getLogger(__name__)

PYPI_INDEX_URL = '-i http://pypi.douban.com/simple/' # the official url "https://pypi.python.org/simple/" is blocked
LOCAL_ARCHIVE_DIR = as_path('/opt/pypi')
LOCAL_ARCHIVE_DIR.makedirs()


@atomic_installer
def python_package_resource(name, version=None, url=None, **kwargs):
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

    upgrade_mode = get_upgrade_mode()
    if upgrade_mode == UPGRADE_MODE_LATEST and VEIL_ENV_TYPE not in ('development', 'test'):
        raise Exception('please upgrade latest under development or test environment')

    installed_version = get_python_package_installed_version(name)
    downloaded_version = get_downloaded_python_package_version(name, version)
    latest_version = get_resource_latest_version(to_resource_key(name))
    if UPGRADE_MODE_LATEST == upgrade_mode:
        may_update_resource_latest_version = VEIL_ENV_TYPE in ('development', 'test')
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
            need_download = True
            action = 'INSTALL'
    elif UPGRADE_MODE_FAST == upgrade_mode:
        may_update_resource_latest_version = VEIL_ENV_TYPE in ('development', 'test') and not latest_version
        need_install = (version or latest_version) and (version or latest_version) != installed_version
        need_download = need_install and (version or latest_version) != downloaded_version
        if need_install:
            action = 'UPGRADE' if installed_version else 'INSTALL'
        else:
            action = None
    else:
        assert upgrade_mode == UPGRADE_MODE_NO
        may_update_resource_latest_version = need_install = need_download = False
        action = None

    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if need_download and should_download_while_dry_run():
            new_downloaded_version = download_python_package(name, (version or latest_version) if UPGRADE_MODE_FAST == upgrade_mode else version,
                url=url, **kwargs)
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
            if UPGRADE_MODE_LATEST == upgrade_mode and action == 'UPGRADE' and installed_version == downloaded_version:
                action = None
        dry_run_result['python_package?{}'.format(name)] = action or '-'
        return

    if need_download:
        new_downloaded_version = download_python_package(name, (version or latest_version) if UPGRADE_MODE_FAST == upgrade_mode else version, url=url,
            **kwargs)
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
        if UPGRADE_MODE_LATEST == upgrade_mode and need_install is None:
            need_install = installed_version != downloaded_version

    if need_install:
        if installed_version:
            LOGGER.info('upgrading python package: %(name)s, %(latest_version)s, %(installed_version)s, %(new_installed_version)s', {
                'name': name,
                'latest_version': latest_version,
                'installed_version': installed_version,
                'new_installed_version': downloaded_version
            })
        else:
            LOGGER.info('installing python package: %(name)s, %(latest_version)s, %(new_installed_version)s', {
                'name': name,
                'latest_version': latest_version,
                'new_installed_version': downloaded_version
            })
        installed_version = install_python_package(name, downloaded_version, url=url, **kwargs)

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
        for line in pip_freeze_output.splitlines(False):
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
        for line in shell_execute('pip list {} -l -o | grep Latest:'.format(PYPI_INDEX_URL), capture=True, debug=True).splitlines(False):
            match = RE_OUTDATED_PACKAGE.match(line)
            outdated_package_name2latest_version[match.group(1)] = match.group(2)
    return outdated_package_name2latest_version.get(name)


def download_python_package(name, version=None, url=None, **kwargs):
    tries = 0
    max_tries = 3
    while True:
        tries += 1
        try:
            if url:
                shell_execute('pip install {} --timeout 30 --download-cache {} -d {} {}'.format(PYPI_INDEX_URL, LOCAL_ARCHIVE_DIR, LOCAL_ARCHIVE_DIR,
                    url), capture=True, debug=True, **kwargs)
            else:
                shell_execute('pip install {} --timeout 30 --download-cache {} -d {} {}{}'.format(PYPI_INDEX_URL, LOCAL_ARCHIVE_DIR,
                    LOCAL_ARCHIVE_DIR, name, '=={}'.format(version) if version else ''), capture=True, debug=True, **kwargs)
        except:
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
    for archive_file in set(LOCAL_ARCHIVE_DIR.files('{}*'.format(prefix)) +
            LOCAL_ARCHIVE_DIR.files('{}*'.format(prefix1))):
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
    while True:
        tries += 1
        try:
            if url:
                shell_execute('pip install {} --timeout 30 --download-cache {} {}'.format(PYPI_INDEX_URL, LOCAL_ARCHIVE_DIR, url), capture=True,
                    debug=True, **kwargs)
            else:
                shell_execute('pip install {} --timeout 30 --download-cache {} {}=={}'.format(PYPI_INDEX_URL, LOCAL_ARCHIVE_DIR, name, version),
                    capture=True, debug=True, **kwargs)
        except:
            if tries >= max_tries:
                raise
        else:
            break


def install_python_package(name, version, url=None, **kwargs):
    try:
        shell_execute('pip install --no-index --find-links {} {}=={}'.format(LOCAL_ARCHIVE_DIR, name, version), capture=True, debug=True, **kwargs)
    except:
        LOGGER.warn('cannot install from local and try install from remote', exc_info=1)
        install_python_package_remotely(name, version, url, **kwargs)
    return version


@script('upgrade-pip')
def upgrade_pip(pip_version, setuptools_version):
    shell_execute('pip install {} --upgrade --download-cache {} pip=={}'.format(PYPI_INDEX_URL, LOCAL_ARCHIVE_DIR, pip_version), capture=True,
        debug=True)
    shell_execute('pip install {} --upgrade --download-cache {} setuptools=={}'.format(PYPI_INDEX_URL, LOCAL_ARCHIVE_DIR, setuptools_version),
        capture=True, debug=True)
