from __future__ import unicode_literals, print_function, division
from veil.development.test import TestCase
from .widget import widget
from .template import get_template
from .widget import require_current_widget_namespace_being

class WidgetModuleSmokeTest(TestCase):
    def test(self):
        def some_page():
            return get_template(
                template_source='<html><head></head><body>{{ widgets.some() }}</body></html>').render()

        @widget
        def some_widget():
            return 'hello'

        with require_current_widget_namespace_being(None):
            self.assertIn('hello', some_page())
