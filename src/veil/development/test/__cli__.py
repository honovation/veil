from __future__ import unicode_literals, print_function, division
import os
from veil.utility.path import *
from veil.frontend.cli import *
from .runner import test_package

CURRENT_DIR = as_path(os.path.dirname(__file__))

@script('self-check')
def self_check():
    package_names = ['veil']
    import __veil__
    for member_name in dir(__veil__):
        member = getattr(__veil__, member_name)
        if hasattr(member, '__path__'):
            package_names.append(member.__name__)
    test_package(*package_names)
    execute_script('development', 'test', 'check-dependencies')