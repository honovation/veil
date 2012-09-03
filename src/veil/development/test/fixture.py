from __future__ import unicode_literals, print_function, division
from .case import test_hook
from .case import get_executing_test

fixtures = {}

@test_hook
def reset_fixtures():
    get_executing_test().addCleanup(fixtures.clear)


def fixture(func):
    def wrapper():
        fixture_name = func.__name__
        if fixture_name not in fixtures:
            fixtures[fixture_name] = func()
        return fixtures[fixture_name]

    return wrapper