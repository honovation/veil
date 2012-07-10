from __future__ import unicode_literals, print_function, division
import logging
from unittest.case import TestCase
from sandal.collection import DictObject

__all__ = ['fixtures', 'register_fixture', 'fixture', 'UsingFixture', 'get_executing_test']

fixtures = DictObject()

def register_fixture(fixture_name, fixture):
    fixtures[fixture_name] = fixture

def fixture(function):
    fixture_name = function.__name__.replace('_fixture', '')
    fixtures[fixture_name] = function
    return function

executing_test = None

def set_executing_test(test):
    global executing_test
    executing_test = test


def get_executing_test():
    if executing_test is None:
        raise Exception('no test executing')
    return executing_test


class UsingFixture(TestCase):
    def setUp(self):
        super(UsingFixture, self).setUp()
        set_executing_test(self)
        self.addCleanup(lambda: set_executing_test(None))
        self.configure_basic_logging()

    def configure_basic_logging(self):
        logging.basicConfig()