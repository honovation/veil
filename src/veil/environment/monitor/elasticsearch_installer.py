# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.environment.environment import OPT_DIR
from veil.profile.installer import *


@composite_installer
def elasticsearch_resource():
    if not (OPT_DIR / 'elasticsearch-1.1.1.tar.gz').exists():
        shell_execute('wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.1.1.tar.gz')
    if not (OPT_DIR / 'elasticsearch-1.1.1').exists():
        shell_execute('tar zxf elasticsearch-1.1.1.tar.gz')

    return list(BASIC_LAYOUT_RESOURCES)