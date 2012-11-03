from __future__ import unicode_literals, print_function, division
from unittest.runner import TextTestRunner
from unittest.loader import TestLoader
from unittest.suite import TestSuite
from unittest.runner import TextTestResult
from threading import Timer
import os
import sys
from veil.utility.path import *
from veil.environment import *

CURRENT_DIR = as_path(os.path.dirname(__file__))

def check_correctness():
    package_names = ['veil']
    for component_name in get_application_components():
        package_names.append(component_name)
    test_package(*package_names)


def test_package(*package_names):
    tests = []
    test_loader = TestLoader()
    for module_name, module in sys.modules.items():
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
    return True


class TimedTextTestResult(TextTestResult):
    def startTest(self, test):
        timer = Timer(30, lambda: report_time_out(self, test))
        timer.start()
        test.addCleanup(timer.cancel)
        try:
            super(TimedTextTestResult, self).startTest(test)
        except:
            import traceback

            traceback.print_exc()

    def addSkip(self, test, reason):
        test.doCleanups()
        super(TimedTextTestResult, self).startTest(test)


def report_time_out(result, test):
    result.stream.write('\n')
    result.stream.write('{} time out'.format(test))
    result.stream.flush()