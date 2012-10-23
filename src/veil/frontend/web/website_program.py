from __future__ import unicode_literals, print_function, division
import veil.component

veil.component.add_must_load_module(__name__)

from veil.frontend.template import *
from veil.frontend.cli import *
from veil.environment.installation import *
from veil.environment.setting import *

website_components = {} # website => components

def website_program(website, **updates):
    program = {
        'execute_command': 'veil frontend web up {}'.format(website),
        'install_command': 'veil frontend web install {}'.format(website)}
    if updates:
        program.update(updates)
    return program

@installation_script()
def install_website(website=None):
    if not website:
        return
    for component in website_components.get(website, []):
        install_dependency(component.__name__, install_dependencies_of_dependency=True)


def assert_website_components_loaded(website):
    components = website_components.get(website, ())
    for component in components:
        if component:
            veil.component.assert_component_loaded(component.__name__)


def register_website_component(website):
    loading_component = veil.component.get_loading_component()
    if website in website_components:
        if loading_component:
            website_components[website].add(loading_component)
    else:
        website_components.setdefault(website, set()).add(loading_component)
