from __future__ import unicode_literals, print_function, division
import logging
import re
from veil.env_consts import VEIL_ENV_TYPE
from veil_installer import *
from .pip_hack import *

LOGGER = logging.getLogger(__name__)
PIP_FREEZE_OUTPUT = None
REMOTE_LATEST_VERSION = {}
LOCAL_PYTHON_PACKAGE_DIR = as_path('/opt/pypi')


@atomic_installer
def python_package_resource(name, url=None, version=None, **kwargs):
    if url and not version:
        raise Exception('package version is required if url is specified')
    installed_version = get_python_package_installed_version(name)
    downloaded_version, local_url = get_downloaded_python_package_version(name)
    latest_version = get_resource_latest_version(to_resource_key(name))
    if VEIL_ENV_TYPE not in ('development', 'test'):
        if not installed_version or installed_version != latest_version:
            while not download_python_package(name, version=latest_version):
                pass
            while not install_python_package(name, latest_version):
                pass
    else:
        remote_latest_version = None
        action = None if installed_version else 'INSTALL'
        upgrade_mode = get_upgrade_mode()
        if UPGRADE_MODE_LATEST == upgrade_mode:
            remote_latest_version = get_installed_package_remote_latest_version(name)
            action = action or 'UPGRADE'
        elif UPGRADE_MODE_FAST == upgrade_mode:
            action = action or (None if latest_version == installed_version else 'UPGRADE')
        elif UPGRADE_MODE_NO == upgrade_mode:
            pass
        else:
            raise NotImplementedError()

        dry_run_result = get_dry_run_result()
        if dry_run_result is not None:
            if should_download_while_dry_run():
                if url:
                    if not downloaded_version or downloaded_version != version:
                        LOGGER.info('To download python package %(name)s from url: %(url)s, version: %(version)s', {
                            'name': name, 'url': url, 'version': version
                        })
                        while not download_python_package(name, url=url, version=version):
                            pass

                if upgrade_mode == UPGRADE_MODE_LATEST and remote_latest_version and not (downloaded_version and downloaded_version == remote_latest_version):
                    LOGGER.debug('To download python package: %(name)s, %(downloaded_version)s, %(latest_version)s, %(remote_latest_version)s', {
                        'name': name,
                        'downloaded_version': downloaded_version,
                        'latest_version': latest_version,
                        'remote_latest_version': remote_latest_version
                    })
                    while not download_python_package(name, version=remote_latest_version):
                        pass
                elif upgrade_mode == UPGRADE_MODE_FAST and not (downloaded_version and downloaded_version == latest_version):
                    LOGGER.debug('To download python package: %(name)s, %(downloaded_version)s, %(latest_version)s', {
                        'name': name,
                        'downloaded_version': downloaded_version,
                        'latest_version': latest_version,
                    })
                    while not download_python_package(name, version=latest_version):
                        pass
            if upgrade_mode == UPGRADE_MODE_LATEST and not remote_latest_version:
                dry_run_result['python_package?{}'.format(name)] = '-'
                return
            dry_run_result['python_package?{}'.format(name)] = action or '-'
            return

        if not action:
            return

        if url:
            if not downloaded_version or downloaded_version != version:
                LOGGER.info('To download python package %(name)s from url: %(url)s, version: %(version)s', {
                    'name': name, 'url': url, 'version': version
                })
                while not download_python_package(name, url=url, version=version):
                    pass
        else:
            if not downloaded_version:
                while not download_python_package(name, version=latest_version):
                    pass
            else:
                if upgrade_mode == UPGRADE_MODE_LATEST and (downloaded_version != remote_latest_version or downloaded_version != latest_version):
                    LOGGER.debug('To download python package: %(name)s, %(upgrade_mode)s, %(installed_version)s, %(downloaded_version)s, %(latest_version)s', {
                        'name': name,
                        'upgrade_mode': upgrade_mode,
                        'installed_version': installed_version,
                        'downloaded_version': downloaded_version,
                        'latest_version': latest_version,
                    })
                    while not download_python_package(name, version=remote_latest_version or latest_version):
                        pass
                elif upgrade_mode != UPGRADE_MODE_LATEST and downloaded_version != latest_version:
                    LOGGER.debug('To download python package: %(name)s, %(downloaded_version)s, %(latest_version)s', {
                        'name': name,
                        'downloaded_version': downloaded_version,
                        'latest_version': latest_version,
                    })
                    while not download_python_package(name, version=latest_version):
                        pass

        downloaded_version, local_url = get_downloaded_python_package_version(name)
        if not installed_version:
            while not install_python_package(name, version=latest_version):
                pass
        else:
            if UPGRADE_MODE_LATEST == upgrade_mode and (installed_version != downloaded_version or latest_version != downloaded_version):
                while not install_python_package(name, version=downloaded_version):
                    pass
                set_resource_latest_version(to_resource_key(name), downloaded_version)
            elif UPGRADE_MODE_LATEST != upgrade_mode and installed_version != latest_version:
                while not install_python_package(name, version=latest_version):
                    pass
                set_resource_latest_version(to_resource_key(name), latest_version)
            LOGGER.info('python package upgraded to new version: %(name)s, %(installed_version)s, %(latest_version)s, %(downloaded_version)s', {
                'name': name,
                'installed_version': installed_version,
                'latest_version': latest_version,
                'downloaded_version': downloaded_version
            })



@script('print-remote-latest-version')
def print_remote_latest_version(name):
    print(get_installed_package_remote_latest_version(name))


def get_installed_package_remote_latest_version(name):
    if not REMOTE_LATEST_VERSION:
        LOGGER.info('fetching installed packages remote latest version...')
        fetch_remote_latest_version()
    return REMOTE_LATEST_VERSION.get(name)


def to_resource_key(pip_package):
    return 'veil.server.python.python_package_resource?{}'.format(pip_package)


@script('print-installed-package-version')
def print_get_python_package_installed_version(name):
    print(get_python_package_installed_version(name))


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


@script('download-package')
def download_python_package(name, version=None, url=None):
    if url and not version:
        raise Exception('package version is required if url is specified')
    if version:
        try:
            shell_execute('ls {} | grep {} | grep {}'.format(LOCAL_PYTHON_PACKAGE_DIR, name, version), capture=True, shell=True)
        except Exception as e:
            pass
        else:
            return True
    pip_args = '-i http://pypi.douban.com/simple --extra-index-url https://pypi.python.com/simple'
    try:
        if url:
            shell_execute('pip install {} -d {} {}'.format(url, LOCAL_PYTHON_PACKAGE_DIR, pip_args), capture=True)
        elif version:
            shell_execute('pip install {}=={} -d {} {}'.format(name, version, LOCAL_PYTHON_PACKAGE_DIR, pip_args), capture=True)
        else:
            shell_execute('pip install {} -d {} {}'.format(name, LOCAL_PYTHON_PACKAGE_DIR, pip_args), capture=True)
    except Exception as e:
        return False
    else:
        return True


@script('install-package')
def install_python_package(name, version=None):
    try:
        if version:
            shell_execute('pip install --no-index --find-links {} {}=={}'.format(LOCAL_PYTHON_PACKAGE_DIR, name, version), capture=True)
        else:
            shell_execute('pip install --no-index --find-links {} {}'.format(LOCAL_PYTHON_PACKAGE_DIR, name), capture=True)
    except Exception as e:
        return False
    else:
        return True


def fetch_remote_latest_version():
    try:
        could_update_packages = shell_execute('pip list -o | grep Current:', capture=True, shell=True)
    except Exception as e:
        LOGGER.info('found no updated python packages or something went wrong')
    else:
        for line in could_update_packages.split('\n'):
            if line:
                name, versions = line.split(' ', 1)
                match = re.match('.*Current: (.*?) Latest: (.*)\)', versions)
                if match:
                    current_version = match.group(1)
                    remote_latest_version = match.group(2)
                else:
                    raise Exception('can not find package version')
                REMOTE_LATEST_VERSION[name] = remote_latest_version
                LOGGER.info(
                    'found updated python package: %(name)s, current installed version: %(c_version)s, remote latest version: %(r_version)s', {
                        'name': name, 'r_version': remote_latest_version, 'c_version': current_version
                    }
                )


def upgrade_python_package(name):
    try:
        shell_execute('pip install {} --upgrade --find-links {}'.format(name, LOCAL_PYTHON_PACKAGE_DIR), capture=True)
    except Exception as e:
        return False
    else:
        return True