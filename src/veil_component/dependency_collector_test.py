from __future__ import unicode_literals, print_function, division
import unittest
from .component_walker import InvalidComponentException
from .dependency_collector import list_dependencies

class ListDependenciesTest(unittest.TestCase):
    def test_module_dependencies(self):
        def walk_component(component_name, visitor):
            if 'a.b.c' == component_name:
                visitor.visit_module('a.b.c.d', None, 'import some_package')
            else:
                raise InvalidComponentException()

        self.assertEqual({'a.b.c': {'some_package'}}, list_dependencies('a.b.c', walk_component))

    def test_package_dependencies(self):
        def walk_component(component_name, visitor):
            if 'a.b.c' == component_name:
                visitor.visit_package_start('a.b.c.d', None, 'import some_package')
            else:
                raise InvalidComponentException()

        self.assertEqual({'a.b.c': {'some_package'}}, list_dependencies('a.b.c', walk_component))

    def test_follow_sub_component(self):
        def walk_component(component_name, visitor):
            if 'a.b.c' == component_name:
                visitor.visit_sub_component('a.b.c.d', None, None)
            elif 'a.b.c.d' == component_name:
                visitor.visit_module('a.b.c.d', None, 'import some_package')
            else:
                raise InvalidComponentException()

        self.assertEqual({'a.b.c': set(), 'a.b.c.d': {'some_package'}}, list_dependencies('a.b.c', walk_component))

    def test_follow_dependent_component(self):
        def walk_component(component_name, visitor):
            if 'a.b.c' == component_name:
                visitor.visit_module('a.b.c.d', None, 'import another_component')
            elif 'another_component' == component_name:
                visitor.visit_module('another_component.e', None, 'import some_package')
            else:
                raise InvalidComponentException()

        expected = {'a.b.c': {'another_component'}, 'another_component': {'some_package'}}
        self.assertEqual(expected, list_dependencies('a.b.c', walk_component))

