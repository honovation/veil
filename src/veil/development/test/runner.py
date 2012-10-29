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
from veil.component import get_component_dependencies
from veil.utility.path import *
from veil.frontend.cli import *

CURRENT_DIR = as_path(os.path.dirname(__file__))
architecture_checkers = {}

def register_architecture_checker(key, checker):
    architecture_checkers[key] = checker


@script('self-check')
def self_check():
    package_names = ['veil']
    import __veil__

    for component_name in getattr(__veil__, 'COMPONENTS', []):
        package_names.append(component_name)
    test_package(*package_names)
    check_architecture()


@script('check-architecture')
def check_architecture():
    import __veil__

    architecture = getattr(__veil__, 'ARCHITECTURE', {})
    for component_name, value in architecture.items():
        check_component_architecture([component_name], value)


def check_component_architecture(component_names, architecture):
    if isinstance(architecture, list):
        return check_component_dependencies(component_names, architecture)
    if not isinstance(architecture, dict):
        raise Exception('do not know how to check architecture for: {}'.format(component_names))
    component_dependencies = architecture.pop('DEPENDENCIES', None)
    if component_dependencies:
        check_component_dependencies(component_names, component_dependencies)
    for key, value in architecture.items():
        if key.startswith('.'):
            inner_component_names = list(component_names)
            inner_component_names.append(key)
            inner_architecture = value
            check_component_architecture(inner_component_names, inner_architecture)
        else:
            architecture_checkers[key](component_names, value)


def check_component_dependencies(component_names, expected_dependencies):
    actual_dependencies = set()
    component_name_prefix = ''.join(component_names)
    parent_component_name_prefix = ''.join(component_names[:-1])
    expected_dependencies = make_component_dependencies_absolute(parent_component_name_prefix, expected_dependencies)
    for component_name, dependencies in get_component_dependencies().items():
        if component_name.startswith(component_name_prefix):
            actual_dependencies = actual_dependencies.union(
                filter_dependencies(dependencies, 'veil.', '{}.'.format(component_name_prefix)))
    unexpected_dependencies = actual_dependencies - set(expected_dependencies)
    if unexpected_dependencies:
        raise Exception('{} should not reference {}'.format(component_name_prefix, unexpected_dependencies))
    unreal_dependencies = set(expected_dependencies) - actual_dependencies
    if unreal_dependencies:
        raise Exception('{} did not reference {}'.format(component_name_prefix, unreal_dependencies))


def make_component_dependencies_absolute(component_name_prefix, dependencies):
    absolute_dependencies = set()
    for dependency in dependencies:
        if dependency.startswith('.'):
            absolute_dependencies.add('{}{}'.format(component_name_prefix, dependency))
        else:
            absolute_dependencies.add(dependency)
    return absolute_dependencies


def filter_dependencies(dependencies, *white_list):
    white_list = set(white_list)
    filtered_dependencies = set()
    for dependency in dependencies:
        if any(dependency.startswith(prefix) for prefix in white_list):
            continue
        filtered_dependencies.add(dependency)
    return filtered_dependencies


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