from __future__ import unicode_literals, print_function, division
import unittest.case

executing_test = None
bootstrappers = []
bootstrapped = False

def register_test_bootstrapper(bootstrapper):
    bootstrappers.append(bootstrapper)


def test_bootstrapper(func):
    register_test_bootstrapper(func)
    return func


def set_executing_test(test):
    global executing_test
    executing_test = test


def get_executing_test(optional=False):
    if executing_test is None and not optional:
        raise Exception('no test executing')
    return executing_test


class TestCase(unittest.case.TestCase):
    def setUp(self):
        global bootstrapped
        super(TestCase, self).setUp()
        set_executing_test(self)
        self.addCleanup(lambda: set_executing_test(None))
        if not bootstrapped:
            for bootstrapper in bootstrappers:
                bootstrapper()
            bootstrapped = True