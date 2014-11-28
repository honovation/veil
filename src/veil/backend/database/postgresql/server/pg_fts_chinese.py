# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

#TODO: upgrade mechanism for scws & zhparser, and record scws & zhparser versions
SCWS_RESOURCE_VERSION = '1.2.2'
SCWS_RESOURCE_KEY = 'veil.backend.database.postgresql.pg_fts_chinese_scws_resource'
SCWS_PACKAGE_NAME = 'scws-{}.tar.bz2'.format(SCWS_RESOURCE_VERSION)
SCWS_HOME = as_path('{}/scws-{}'.format(DEPENDENCY_INSTALL_DIR, SCWS_RESOURCE_VERSION))
SCWS_BIN_PATH = as_path('/usr/local/bin/scws')

ZHPARSER_RESOURCE_VERSION = '0.1.4'
ZHPARSER_RESOURCE_KEY = 'veil.backend.database.postgresql.pg_fts_chinese_zhparser_resource'
ZHPARSER_PACKAGE_NAME = 'zhparser-zhparser-{}.zip'.format(ZHPARSER_RESOURCE_VERSION)
ZHPARSER_HOME = as_path('{}/zhparser-zhparser-{}'.format(DEPENDENCY_INSTALL_DIR, ZHPARSER_RESOURCE_VERSION))
ZHPARSER_SO_PATH = as_path('{}/zhparser.so'.format(ZHPARSER_HOME))


@atomic_installer
def scws_resource():
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if is_downloading_while_dry_run():
            download_scws()
        dry_run_result['scws'] = '-' if is_scws_installed() else 'INSTALL'
    else:
        install_scws()


def download_scws():
    if SCWS_HOME.exists():
        return
    local_path = DEPENDENCY_DIR / SCWS_PACKAGE_NAME
    if not local_path.exists():
        shell_execute('wget -c {}/{} -O {}'.format(DEPENDENCY_URL, SCWS_PACKAGE_NAME, local_path))
    shell_execute('tar jxvf {} -C {}'.format(local_path, DEPENDENCY_INSTALL_DIR))


def install_scws():
    if is_scws_installed():
        if VEIL_ENV_TYPE in {'development', 'test'} and SCWS_RESOURCE_VERSION != get_resource_latest_version(SCWS_RESOURCE_KEY):
            set_resource_latest_version(SCWS_RESOURCE_KEY, SCWS_RESOURCE_VERSION)
        return
    download_scws()
    shell_execute('./configure;make install', cwd=SCWS_HOME)
    if VEIL_ENV_TYPE in {'development', 'test'}:
        set_resource_latest_version(SCWS_RESOURCE_KEY, SCWS_RESOURCE_VERSION)


def is_scws_installed():
    return SCWS_BIN_PATH.exists()


@atomic_installer
def zhparser_resource():
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if is_downloading_while_dry_run():
            download_zhparser()
        dry_run_result['zhparser'] = '-' if is_zhparser_installed() else 'INSTALL'
    else:
        install_zhparser()


def download_zhparser():
    if ZHPARSER_HOME.exists():
        return
    local_path = DEPENDENCY_DIR / ZHPARSER_PACKAGE_NAME
    if not local_path.exists():
        shell_execute('wget -c {}/{} -O {}'.format(DEPENDENCY_URL, ZHPARSER_PACKAGE_NAME, local_path))
    shell_execute('unzip {}'.format(local_path), cwd=DEPENDENCY_INSTALL_DIR)


def install_zhparser():
    if is_zhparser_installed():
        if VEIL_ENV_TYPE in {'development', 'test'} and ZHPARSER_RESOURCE_VERSION != get_resource_latest_version(ZHPARSER_RESOURCE_KEY):
            set_resource_latest_version(ZHPARSER_RESOURCE_KEY, ZHPARSER_RESOURCE_VERSION)
        return
    download_zhparser()
    shell_execute('SCWS_HOME=/usr/local make && make install', cwd=ZHPARSER_HOME)
    if VEIL_ENV_TYPE in {'development', 'test'}:
        set_resource_latest_version(ZHPARSER_RESOURCE_KEY, ZHPARSER_RESOURCE_VERSION)


def is_zhparser_installed():
    return ZHPARSER_SO_PATH.exists()
