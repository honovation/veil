# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.environment.environment import *
from veil.profile.installer import *


@composite_installer
def elasticsearch_resource(config):
    if not (OPT_DIR / 'elasticsearch-1.1.1.tar.gz').exists():
        shell_execute('wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.1.1.tar.gz', cwd=OPT_DIR)
    if not (OPT_DIR / 'elasticsearch-1.1.1').exists():
        shell_execute('tar zxf elasticsearch-1.1.1.tar.gz', cwd=OPT_DIR)

    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        file_resource(
            path=VEIL_ETC_DIR / 'elasticsearch.yml',
            content=render_config('elasticsearch.yml.j2', log_dir=VEIL_LOG_DIR, data_dir=VEIL_VAR_DIR, **config))
    ])

    return resources