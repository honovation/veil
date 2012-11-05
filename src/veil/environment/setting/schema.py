from __future__ import unicode_literals, print_function, division
from .setting import get_settings

schemas = {}
allows_missing_schema = False

def register_settings_schema(schema_name, schema):
    schemas[schema_name] = schema


def get_settings_schema(schema_name):
    if schema_name in schemas:
        return schemas[schema_name]
    if allows_missing_schema:
        return lambda *args, **kwargs: {}
    else:
        raise Exception('unknown settings schema: {}'.format(schema_name))


def get_settings_with_missing_schema():
    global allows_missing_schema
    try:
        allows_missing_schema = True
        return get_settings()
    finally:
        allows_missing_schema = False