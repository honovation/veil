from __future__ import unicode_literals, print_function, division
from ..widget import widget, page
from ..template import get_template, reset_template_environment
from sandal.fixture import UsingFixture

class WidgetModuleSmokeTest(UsingFixture):
    def tearDown(self):
        reset_template_environment()
        super(WidgetModuleSmokeTest, self).tearDown()

    def test(self):
        @page
        def some_page():
            return get_template(
                template_source='<html><head></head><body>{{ widgets.some_widget() }}</body></html>').render()

        @widget
        def some_widget():
            return 'hello'

        self.assertIn('hello', some_page())
