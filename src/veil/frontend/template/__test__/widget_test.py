from __future__ import unicode_literals, print_function, division
from ..widget import widget, page
from ..template import get_template
from sandal.test import TestCase

class WidgetModuleSmokeTest(TestCase):
    def test(self):
        @page
        def some_page():
            return get_template(
                template_source='<html><head></head><body>{{ widgets.some() }}</body></html>').render()

        @widget
        def some_widget():
            return 'hello'

        self.assertIn('hello', some_page())
