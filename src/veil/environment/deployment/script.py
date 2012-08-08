from __future__ import unicode_literals, print_function, division
import functools
from veil.frontend.cli import script
from veil.environment.layout import *
from .filesystem import create_directory

# create basic layout before deployment
def deployment_script(*args, **kwargs):
    decorator = script(*args, **kwargs)
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            create_layout()
            return func(*args, **kwargs)
        return decorator(wrapper)
    return decorate

def create_layout():
    create_directory(VEIL_HOME / 'log')
    create_directory(VEIL_LOG_DIR)
    create_directory(VEIL_HOME / 'etc')
    create_directory(VEIL_ETC_DIR)
    create_directory(VEIL_HOME / 'var')
    create_directory(VEIL_VAR_DIR)