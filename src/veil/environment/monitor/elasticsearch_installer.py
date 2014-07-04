# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

APT_SOURCES_LIST_DIR = as_path('/etc/apt/sources.list.d')


@composite_installer
def elasticsearch_resource():
    shell_execute('wget -O - http://packages.elasticsearch.org/GPG-KEY-elasticsearch | apt-key add -')

    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        file_resource(path=APT_SOURCES_LIST_DIR / 'elasticsearch.list', content=render_config('elasticsearch.list')),
        os_package_resource(name='elasticsearch=1.1.1'),
        os_service_resource(name='elasticsearch', state='not_installed')
    ])

    return resources