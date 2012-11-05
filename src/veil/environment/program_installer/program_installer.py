from __future__ import unicode_literals, print_function, division
import functools
from veil_installer import register_installer
from veil.frontend.template import *

def program_installer(name):
# install program normally requires:
# basic layout in place: ETC/VAR/LOG
# using jinja2 to write out the program configuration
    def register(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with require_current_template_directory_relative_to(func):
                return func(*args, **kwargs)

        register_installer(name, wrapper)
        return wrapper

    return register