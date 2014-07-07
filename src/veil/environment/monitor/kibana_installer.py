# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.environment.environment import *
from veil.server.config import *
from veil.utility.shell import *
from veil_installer import *

KIBANA_DIR = OPT_DIR / 'kibana-latest'


@composite_installer
def kibana_resource(config):
    if not (OPT_DIR / 'kibana-latest.zip').exists():
        shell_execute('wget http://download.elasticsearch.org/kibana/kibana/kibana-latest.zip', cwd=OPT_DIR)
    else:
        current_kibana_md5 = shell_execute('md5sum kibana-latest.zip', cwd=OPT_DIR, capture=True).split()[0]
        shell_execute('wget -N http://download.elasticsearch.org/kibana/kibana/kibana-latest.zip', cwd=OPT_DIR)
        new_kibana_md5 = shell_execute('md5sum kibana-latest.zip', cwd=OPT_DIR, capture=True).split()[0]
        if current_kibana_md5 != new_kibana_md5:
            shell_execute('rm -rf kibana-latest', cwd=OPT_DIR)
        else:
            print('no change for kibana-latest')
            return
    shell_execute('unzip -o kibana-latest.zip', cwd=OPT_DIR)
    if (KIBANA_DIR / 'app/dashboards/logstash.json').exists():
        shell_execute('mv logstash.json default.json', cwd=KIBANA_DIR / 'app/dashboards')

    resources = [
        os_ppa_repository_resource(name='nginx/stable'),
        os_package_resource(name='nginx-extras'),
        os_service_resource(state='not_installed', name='nginx'),
        file_resource(path=VEIL_ETC_DIR / 'nginx.conf', content=render_config('nginx.conf.j2', kibana_root=KIBANA_DIR)),
        file_resource(path=KIBANA_DIR / 'config.js', content=render_config('kibana.config.js.j2', **config))
    ]

    return resources