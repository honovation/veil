from __future__ import unicode_literals, print_function, division
from veil.utility.json import *
from veil.utility.http import *
from veil.environment import *
from .template import template_filter
from .template import template_utility

# keep this one minimal, it is global


@template_filter
def json(value):
    return to_json(value)


@template_filter('quote_plus')
def render_quote_plus(value):
    return quote_plus(value)


@template_utility
def get_veil_env_type():
    return VEIL_ENV_TYPE
