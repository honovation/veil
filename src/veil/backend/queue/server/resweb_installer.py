from __future__ import unicode_literals, print_function, division
from veil.environment import *
from veil.frontend.template import *
from veil_installer import *

@composite_installer('resweb')
@using_isolated_template
def install_resweb(resweb_host, resweb_port, queue_host, queue_port):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.extend([
        python_package_resource('resweb'),
        file_resource(VEIL_ETC_DIR / 'resweb.cfg', content=get_template('resweb.cfg.j2').render(config={
            'resweb_host': resweb_host,
            'resweb_port': resweb_port,
            'queue_host': queue_host,
            'queue_port': queue_port
        }))
    ])
    return [], resources