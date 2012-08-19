from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from veil.frontend.template import *
from veil.frontend.web import *
from veil.model.collection import *
from .browser import browsing
from .browser import interact_with_page

register_website('test')

TEST_WEBSITE_SETTINGS = objectify({
    'veil': {
        'test_website': {
            'host': 'localhost',
            'port': 10000
        }
    }
})

class Spike(TestCase):
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

        @browsing('test', '/')
        def interact_with_pages():
            interact_with_page(
                """
                document.getElementById('form').submit();
                """)

        interact_with_pages()



