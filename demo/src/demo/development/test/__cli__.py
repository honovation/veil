from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
import veil.component

@script('check-dependencies')
def check_dependencies():
    veil.component.assert_component_dependencies('demo.model.item', [
        'veil.backend.redis', 'veil.model', 'veil.profile.model',
        'veil.backend.database', 'veil.utility.clock'])
