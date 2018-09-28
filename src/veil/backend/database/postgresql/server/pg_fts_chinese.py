# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

SCWS_RESOURCE_KEY = 'veil.backend.database.postgresql.pg_fts_chinese_scws_resource'
SCWS_RESOURCE_VERSION = '1.2.3'
SCWS_PACKAGE_NAME = 'scws-{}.tar.bz2'.format(SCWS_RESOURCE_VERSION)
SCWS_DOWNLOAD_URL = 'http://www.xunsearch.com/scws/down/{}'.format(SCWS_PACKAGE_NAME)
SCWS_HOME = as_path('{}/scws-{}'.format(DEPENDENCY_INSTALL_DIR, SCWS_RESOURCE_VERSION))
SCWS_BIN_PATH = as_path('/usr/local/bin/scws')
SCWS_RULES_PATH = as_path('/usr/local/etc/rules.utf8.ini')

ZHPARSER_RESOURCE_KEY = 'veil.backend.database.postgresql.pg_fts_chinese_zhparser_resource'
ZHPARSER_RESOURCE_VERSION = '0.2.0'
ZHPARSER_PACKAGE_NAME = 'zhparser-{}.zip'.format(ZHPARSER_RESOURCE_VERSION)
ZHPARSER_DOWNLOAD_URL = 'https://github.com/amutu/zhparser/archive/v{}.zip'.format(ZHPARSER_RESOURCE_VERSION)
ZHPARSER_HOME = as_path('{}/zhparser-{}'.format(DEPENDENCY_INSTALL_DIR, ZHPARSER_RESOURCE_VERSION))

SCWS_DICT_RESOURCE_KEY = 'veil.backend.database.postgresql.pg_fts_chinese_scws_dict_resource'
SCWS_DICT_NAME = 'dict.utf8.xdb'
SCWS_DICT_RESOURCE_VERSION = '20160224'
SCWS_DICT_PACKAGE_NAME = 'scws-dict-chs-utf8-{}.tar.bz2'.format(SCWS_DICT_RESOURCE_VERSION)
SCWS_DICT_DOWNLOAD_URL = 'http://www.xunsearch.com/scws/down/scws-dict-chs-utf8.tar.bz2'
SCWS_DICT_HOME = as_path('{}/scws-dict-{}'.format(DEPENDENCY_INSTALL_DIR, SCWS_DICT_RESOURCE_VERSION))


@atomic_installer
def scws_dict_resource(pg_tsearch_data_dir):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if is_downloading_while_dry_run():
            download_scws_dict()
        dry_run_result['scws_dict'] = '-' if is_scws_dict_installed(pg_tsearch_data_dir) else 'INSTALL'
        return
    install_scws_dict(pg_tsearch_data_dir)


def download_scws_dict():
    if (SCWS_DICT_HOME / SCWS_DICT_NAME).exists():
        return
    local_path = DEPENDENCY_DIR / SCWS_DICT_PACKAGE_NAME
    if not local_path.exists():
        shell_execute('wget -c {} -O {}'.format(SCWS_DICT_DOWNLOAD_URL, local_path))
    if not SCWS_DICT_HOME.exists():
        shell_execute('mkdir {}'.format(SCWS_DICT_HOME))
    shell_execute('tar jxvf {} -C {}'.format(local_path, SCWS_DICT_HOME))


def install_scws_dict(pg_tsearch_data_dir):
    if is_scws_dict_installed(pg_tsearch_data_dir):
        if (VEIL_ENV.is_dev or VEIL_ENV.is_test) and SCWS_DICT_RESOURCE_VERSION != get_resource_latest_version(SCWS_DICT_RESOURCE_KEY):
            set_resource_latest_version(SCWS_DICT_RESOURCE_KEY, SCWS_DICT_RESOURCE_VERSION)
        return
    download_scws_dict()
    shell_execute('sudo cp {} {}'.format(SCWS_DICT_HOME / SCWS_DICT_NAME, pg_tsearch_data_dir))
    if VEIL_ENV.is_dev or VEIL_ENV.is_test:
        set_resource_latest_version(SCWS_DICT_RESOURCE_KEY, SCWS_DICT_RESOURCE_VERSION)


def is_scws_dict_installed(pg_tsearch_data_dir):
    if not (SCWS_DICT_HOME / SCWS_DICT_NAME).exists() or not (pg_tsearch_data_dir / SCWS_DICT_NAME).exists():
        return False
    output = shell_execute('cmp {} {}'.format(SCWS_DICT_HOME / SCWS_DICT_NAME, pg_tsearch_data_dir / SCWS_DICT_NAME),
                           capture=True)
    return '' == output


@atomic_installer
def scws_resource(pg_tsearch_data_dir):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if is_downloading_while_dry_run():
            download_scws()
        dry_run_result['scws'] = '-' if is_scws_installed() else 'INSTALL'
        return
    install_scws(pg_tsearch_data_dir)


def download_scws():
    if SCWS_HOME.exists():
        return
    local_path = DEPENDENCY_DIR / SCWS_PACKAGE_NAME
    if not local_path.exists():
        shell_execute('wget -c {} -O {}'.format(SCWS_DOWNLOAD_URL, local_path))
    shell_execute('tar jxvf {} -C {}'.format(local_path, DEPENDENCY_INSTALL_DIR))


def install_scws(pg_tsearch_data_dir):
    if is_scws_installed():
        if (VEIL_ENV.is_dev or VEIL_ENV.is_test) and SCWS_RESOURCE_VERSION != get_resource_latest_version(SCWS_RESOURCE_KEY):
            set_resource_latest_version(SCWS_RESOURCE_KEY, SCWS_RESOURCE_VERSION)
        return
    download_scws()
    shell_execute('./configure && make && sudo make install', cwd=SCWS_HOME)
    shell_execute('sudo cp {} {}'.format(SCWS_RULES_PATH, pg_tsearch_data_dir))
    if VEIL_ENV.is_dev or VEIL_ENV.is_test:
        set_resource_latest_version(SCWS_RESOURCE_KEY, SCWS_RESOURCE_VERSION)


def is_scws_installed():
    if not SCWS_BIN_PATH.exists():
        return False
    output = shell_execute('{} -v'.format(SCWS_BIN_PATH), capture=True)
    return output and SCWS_RESOURCE_VERSION in output


@atomic_installer
def zhparser_resource(pg_lib_dir, pg_bin_dir, pg_tsearch_data_dir):
    dry_run_result = get_dry_run_result()
    if dry_run_result is not None:
        if is_downloading_while_dry_run():
            download_zhparser()
        dry_run_result['zhparser'] = '-' if is_zhparser_installed(pg_lib_dir) else 'INSTALL'
        return
    install_zhparser(pg_lib_dir, pg_bin_dir, pg_tsearch_data_dir)


def download_zhparser():
    if ZHPARSER_HOME.exists():
        return
    local_path = DEPENDENCY_DIR / ZHPARSER_PACKAGE_NAME
    if not local_path.exists():
        shell_execute('wget -c {} -O {}'.format(ZHPARSER_DOWNLOAD_URL, local_path))
    shell_execute('unzip {}'.format(local_path), cwd=DEPENDENCY_INSTALL_DIR)


def install_zhparser(pg_lib_dir, pg_bin_dir, pg_tsearch_data_dir):
    if is_zhparser_installed(pg_lib_dir):
        if (VEIL_ENV.is_dev or VEIL_ENV.is_test) and ZHPARSER_RESOURCE_VERSION != get_resource_latest_version(ZHPARSER_RESOURCE_KEY):
            set_resource_latest_version(ZHPARSER_RESOURCE_KEY, ZHPARSER_RESOURCE_VERSION)
        return
    download_zhparser()
    shell_execute('PG_CONFIG={}/pg_config make && sudo make install'.format(pg_bin_dir), cwd=ZHPARSER_HOME)
    shell_execute('sudo cp {} {}'.format(SCWS_RULES_PATH, pg_tsearch_data_dir))
    shell_execute('sudo cp {} {}'.format(SCWS_DICT_HOME / SCWS_DICT_NAME, pg_tsearch_data_dir))
    if VEIL_ENV.is_dev or VEIL_ENV.is_test:
        set_resource_latest_version(ZHPARSER_RESOURCE_KEY, ZHPARSER_RESOURCE_VERSION)


def is_zhparser_installed(pg_lib_dir):
    zhparser_so_path = pg_lib_dir / 'zhparser.so'
    if not zhparser_so_path.exists():
        return False
    output = shell_execute("grep -w '{}' {} | wc -l".format(ZHPARSER_RESOURCE_VERSION, zhparser_so_path), capture=True)
    return 1 == int(output)
