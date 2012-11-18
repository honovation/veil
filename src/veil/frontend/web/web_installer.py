from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.frontend.template import *

@composite_installer('website')
@using_isolated_template
def install_website(purpose, config, dependencies):
    resources = list(BASIC_LAYOUT_RESOURCES)
    for dependency in dependencies:
        resources.append(component_resource(dependency))
    resources.append(file_resource(VEIL_ETC_DIR / '{}_website.cfg'.format(purpose), content=get_template(
        'website.cfg.j2').render(config=config)))
    return [], resources