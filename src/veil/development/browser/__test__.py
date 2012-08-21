from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from veil.frontend.template import *
from veil.frontend.web import *
from .browser import start_website_and_browser

register_website('test')

TEST_WEBSITE_SETTINGS = website_settings('test', host='localhost', port=10000)

class BrowsingTest(TestCase):
    def test(self):
        @route('GET', '/', website='test')
        def home():
            return get_template(template_source=\
            """
            <html>
            <body>
            <form id="form" method="post" action="/-test/stop">
                {{ xsrf_field() }}
            </form>
            </body>
            </html>
            """).render()

        start_website_and_browser(
            'test', '/',
            ["""
            setTimeout(function(){
                document.getElementById('form').submit();
            }, 1000);
            """])




