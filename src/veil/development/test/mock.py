from __future__ import unicode_literals, print_function, division
import functools
import uuid
from veil.env_const import VEIL_ENV_TYPE
from .case import get_executing_test

mockable_functions = {}
mock_functions = {}
enabled = True

def enable_mock():
    global enabled
    enabled = True


def disable_mock():
    global enabled
    enabled = False


def mockable(func):
    if 'test' == VEIL_ENV_TYPE:
        mockable_code = uuid.uuid4().get_hex()
        func.__dict__['mockable_code'] = mockable_code
        mockable_functions[mockable_code] = func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return execute_mock_function(func, args, kwargs)

        return wrapper

    return func


def execute_mock_function(mockable_function, args, kwargs):
    if not enabled:
        return mockable_function(*args, **kwargs)
    mockable_code = mockable_function.__dict__['mockable_code']
    for mock_func in mock_functions.get(mockable_code, []):
        try:
            return mock_func(mockable_function, *args, **kwargs)
        except NotImplementedError:
            pass # it is ok to only mock for certain known input
    raise NotImplementedError('did not specify how to mock {} with args: {} and kwargs: {}'.format(mockable_function, args, kwargs))


def mock_function(mockable_func, mock_func, append=True):
    get_executing_test().addCleanup(mock_functions.clear)
    mockable_code = mockable_func.__dict__['mockable_code']
    if append:
        mock_functions.setdefault(mockable_code, []).append(mock_func)
    else:
        mock_functions[mockable_code] = [mock_func]


def not_implemented():
    raise NotImplementedError()
