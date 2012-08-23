from __future__ import unicode_literals, print_function, division
from unittest.runner import TextTestRunner
from unittest.loader import TestLoader
from unittest.suite import TestSuite
from unittest.runner import TextTestResult
from threading import Timer
from veil.component import force_get_all_loaded_modules
import cProfile

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
                test = test_loader.loadTestsFromModule(module)
                tests.extend(test)
    test_result = TextTestRunner(failfast=True, resultclass=TimedTextTestResult).run(TestSuite(tests))
    if not test_result.wasSuccessful():
        raise Exception('test failed')


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