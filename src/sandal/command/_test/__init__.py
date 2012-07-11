from __future__ import unicode_literals, print_function, division
from inspect import isfunction
import functools
from sandal.collection import DictObject
from sandal.fixture import register_fixture, fixture
from sandal.fixture import get_executing_test

test_objects = DictObject()

def command_fixture(command_handler):
# syntax sugar for CommandFixtureDecorator
    return CommandFixtureDecorator(command_handler)


class CommandFixtureDecorator(object):
    def __init__(self, command_handler):
        self.command_handler = command_handler

    def __call__(self, command_factory):
        @functools.wraps(command_factory)
        def wrapper(**kwargs):
            return self.command_handler(**create_command(command_factory, **kwargs))

        register_fixture(command_factory.__name__, wrapper)
        register_fixture(
            'command_for_{}'.format(command_factory.__name__),
            lambda **kwargs: create_command(command_factory, **kwargs))
        return wrapper


def create_command(command_factory, **kwargs):
    command_or_command_and_defaults = command_factory(**kwargs)
    if isinstance(command_or_command_and_defaults, tuple):
        command, defaults = command_or_command_and_defaults
        for key, default in defaults.items():
            if key in command:
                continue
            command[key] = default() if isfunction(default) else default
    else:
        command = command_or_command_and_defaults
    return DictObject(command)


def test_object_provider(func):
    @functools.wraps(func)
    def wrapper(**kwargs):
        get_executing_test().addCleanup(test_objects.clear)
        sig = generate_signature(dict(
            func=func,
            kwargs=kwargs
        ))
        if sig not in test_objects:
            test_objects[sig] = func(**kwargs)
        return test_objects[sig]

    return fixture(wrapper)


def generate_signature(obj):
    if isinstance(obj, (dict, DictObject)):
        return frozenset([generate_signature(item) for item in obj.items()])
    if isinstance(obj, (tuple, list)):
        return frozenset([generate_signature(item) for item in obj])
    return obj