from __future__ import unicode_literals, print_function, division
from veil.development.test import TestCase
from .routing import PathTemplate

class PathTemplateTest(TestCase):
    def test_simple_template(self):
        self.assertEqual('/some$', PathTemplate('/some', {}).translate_to_regex())

    def test_with_dot(self):
        self.assertEqual('/some\.html$', PathTemplate('/some.html', {}).translate_to_regex())

    def test_with_arg(self):
        self.assertEqual(r'/some/(?P<id>.*)$', PathTemplate('/some/{{ id }}', {'id':'.*'}).translate_to_regex())

    def test_not_enough_params(self):
        self.assertRaises(Exception, lambda: PathTemplate('/some/{{ id }}', {}))

    def test_too_many_params(self):
        self.assertRaises(Exception, lambda: PathTemplate('/some', {'id': '.*'}))