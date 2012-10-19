from __future__ import unicode_literals, print_function, division
from veil.development.test import TestCase
from .template import get_template
from .widget import widget
from .widget import require_current_widget_namespace_being
from .widget import import_widget

class WidgetModuleSmokeTest(TestCase):
    def test(self):
        with require_current_widget_namespace_being(None):
            def some_page():
                return get_template(
                    template_source='<html><head></head><body>{{ widgets.some() }}</body></html>').render()

            @widget
            def some_widget():
                return 'hello'

            self.assertIn('hello', some_page())


class AbstractWidgetTest(TestCase):
    def test_implements_abstract(self):
        with require_current_widget_namespace_being(None):
            @widget(is_abstract=True)
            def some_widget():
                pass

            @widget(implements=some_widget)
            def another_widget():
                return 'hello'

            self.assertEqual('hello', get_template(template_source='{{ widgets.some() }}').render())

    def test_implements_non_abstract(self):
        with require_current_widget_namespace_being(None):
            @widget
            def some_widget():
                pass

            with self.assertRaises(Exception):
                @widget(implements=some_widget)
                def another_widget():
                    return 'hello'

    def test_implements_with_different_signature(self):
        with require_current_widget_namespace_being(None):
            @widget(is_abstract=True)
            def some_widget():
                pass

            with self.assertRaises(Exception):
                @widget(implements=some_widget)
                def another_widget(some_param):
                    return 'hello'

    def test_import_abstract_widget(self):
        with require_current_widget_namespace_being(None):
            @widget(is_abstract=True)
            def some_widget():
                pass

            with self.assertRaises(Exception):
                import_widget(some_widget)





