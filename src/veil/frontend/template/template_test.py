from __future__ import unicode_literals, print_function, division
import os.path
from veil.development.test import TestCase
from .template import get_template
from .template import register_template_utility
from .template import require_current_template_directory_being

class TemplateTest(TestCase):
    def test_template_from_source(self):
        self.assertEqual('hello', get_template(template_source='{{ a }}').render(a='hello'))

    def test_template_from_absolute_path(self):
        template_path = os.path.join(os.path.dirname(__file__), 'template.txt.j2')
        self.assertEqual('hello', get_template(template_path).render())

    def test_template_from_relative_path(self):
        with self.assertRaises(Exception):
            get_template('template.txt.j2').render()
        with require_current_template_directory_being(os.path.dirname(__file__)):
            self.assertEqual('hello', get_template('template.txt.j2').render())

    def test_utility(self):
        register_template_utility('a', 'hello')
        register_template_utility('x', lambda x: x)
        self.assertEqual('hello', get_template(template_source='{{ a }}').render())
        self.assertEqual('hello', get_template(template_source='{{ x("hello") }}').render())
