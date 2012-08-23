from __future__ import unicode_literals, print_function, division
import os
import veil.component
from veil.utility.path import *
from veil.frontend.cli import *
from .runner import test_package

CURRENT_DIR = as_path(os.path.dirname(__file__))

@script('self-check')
def self_check():
    package_names = ['veil']
    import __veil__

    for component in __veil__.COMPONENTS:
        package_names.append(component.__name__)
    test_package(*package_names)
    check_dependencies()


def check_dependencies():
    import __veil__

    for component_name, dependencies in __veil__.ARCHITECTURE.items():
        veil.component.assert_component_dependencies(
            component_name, dependencies)
