from __future__ import unicode_literals, print_function, division
from .template import template_filter
from sandal.json import *

@template_filter
def json(value):
    return to_json(value)