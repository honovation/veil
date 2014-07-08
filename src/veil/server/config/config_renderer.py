from __future__ import unicode_literals, print_function, division
import importlib
import os
from veil_installer import *

def render_config(template_path, **kwargs):
    return get_template_from_file(template_path).render(**kwargs)


def get_template_from_file(template_path):
    if not os.path.isabs(template_path):
        func = get_executing_installer()
        if not func:
            raise Exception('can only render_config from installer')
        current_template_directory = os.path.dirname(os.path.abspath(importlib.import_module(func.__module__).__file__))
        template_path = os.path.join(current_template_directory, template_path)
    template = create_environment().get_template('root:{}'.format(template_path))
    return template


def create_environment():
    import jinja2
    return jinja2.Environment(
        loader=jinja2.PrefixLoader({'root': jinja2.FileSystemLoader('/')}, delimiter=':'),
        trim_blocks=True,
        autoescape=False,
        extensions=[],
        undefined=jinja2.StrictUndefined)
