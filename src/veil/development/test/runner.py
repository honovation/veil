from __future__ import unicode_literals, print_function, division
from unittest.runner import TextTestRunner
from unittest.loader import TestLoader
from unittest.suite import TestSuite
from unittest.runner import TextTestResult
from threading import Timer
import cProfile
import os
from veil.component import get_component_of_module
from veil.component import is_component_loaded
from veil.component import force_get_all_loaded_modules
from veil.component import assert_component_dependencies
from veil.utility.path import *
from veil.frontend.cli import *

CURRENT_DIR = as_path(os.path.dirname(__file__))

@script('self-check')
def self_check():
    package_names = ['veil']
    import __veil__

    for component in __veil__.COMPONENTS:
        package_names.append(component.__name__)
    test_package(*package_names)
    check_dependencies()


def check_dependencies():
    import __veil__

    for component_name, dependencies in __veil__.ARCHITECTURE.items():
        assert_component_dependencies(
            component_name, dependencies)

def profile_package(*package_names):
    import __builtin__

    __builtin__.__dict__['test'] = lambda: test_package(*package_names)
    cProfile.run('test()')


def test_package(*package_names):
    tests = []
    test_loader = TestLoader()
    for module_name, module in force_get_all_loaded_modules().items():
        for package_name in package_names:
            if module_name.startswith('{}.'.format(package_name)):
                module_tests = test_loader.loadTestsFromModule(module)
                module_tests = [t for t in module_tests if is_test_suite_loaded(t)]
                tests.extend(module_tests)
    test_result = TextTestRunner(failfast=True, resultclass=TimedTextTestResult).run(TestSuite(tests))
    if not test_result.wasSuccessful():
        raise Exception('test failed')


def is_test_suite_loaded(suite):
    if 'LoadTestsFailure' == suite.__class__.__name__:
        return False
    for test in suite:
        if not is_component_loaded(get_component_of_module(test.__module__)):
            return False
    return True


class TimedTextTestResult(TextTestResult):
    def startTest(self, test):
        timer = Timer(30, lambda: report_time_out(self, test))
        timer.start()
        test.addCleanup(timer.cancel)
        super(TimedTextTestResult, self).startTest(test)


def report_time_out(result, test):
    result.stream.write('\n')
    result.stream.write('{} time out'.format(test))
    result.stream.flush()