from __future__ import unicode_literals, print_function, division
import unittest.case
from veil import init_components

executing_test = None
bootstrappers = [init_components]

def register_test_hook(bootstrapper):
    bootstrappers.append(bootstrapper)


def test_hook(func):
    register_test_hook(func)
    return func


def set_executing_test(test):
    global executing_test
    executing_test = test


def get_executing_test(optional=False):
    if executing_test is None and not optional:
        raise Exception('no test executing')
    return executing_test


def set_up_fake_test():
    global executing_test
    if executing_test:
        raise Exception('test is executing')
    else:
        FakeTestCase().setUp()


def tear_down_fake_test():
    executing_test = get_executing_test(optional=True)
    if executing_test:
        executing_test.doCleanups()


class TestCase(unittest.case.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        set_executing_test(self)
        self.addCleanup(lambda: set_executing_test(None))
        for bootstrapper in bootstrappers:
            bootstrapper()


class FakeTestCase(TestCase):
    def runTest(self):
        pass