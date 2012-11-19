from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.frontend.template import *

@composite_installer('website')
@using_isolated_template
def install_website(purpose, config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(VEIL_ETC_DIR / '{}-website.cfg'.format(purpose), content=get_template(
        'website.cfg.j2').render(config=config)))
    return [], resources