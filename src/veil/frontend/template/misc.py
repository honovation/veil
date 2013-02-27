from __future__ import unicode_literals, print_function, division
from veil.utility.json import *
from veil.environment import *
from .template import template_filter
from .template import template_utility

# keep this one minimal, it is global

@template_filter
def json(value):
    return to_json(value)


@template_utility
def get_veil_env():
    return VEIL_ENV