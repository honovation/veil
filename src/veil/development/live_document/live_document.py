# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import contextlib
import atexit
from functools import wraps
from veil_component import load_all_components, record_dynamic_dependency_provider, get_loading_component_name
from veil.development.test import *

root_context = {}
contexts = [lambda statement_name, args: root_context[statement_name](*args)]


def register_document_statement(statement_name, statement_executor):
    root_context[statement_name] = statement_executor


def execute_document_statement(statement_name, *args):
    if not get_executing_test(optional=True):
        load_all_components()
        set_up_fake_test()
        atexit.register(tear_down_fake_test)
    return contexts[-1](statement_name, args)


def document_statement(statement_name):
    def register(func):
        record_dynamic_dependency_provider(get_loading_component_name(), 'document-statement', statement_name)
        register_document_statement(statement_name, func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return register


document_statement('创建')(require_fixture)
document_statement('选择')(require_fixture)


@contextlib.contextmanager
def require_current_context_being(new_context):
    try:
        contexts.append(new_context)
        yield
    finally:
        contexts.pop()
