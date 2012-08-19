from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from veil.development.browser import *
from veil.frontend.cli import *

__import__('demo.website.demo.server')

class DemoWebsiteTest(TestCase):
    @browsing('demo', '/')
    def test(self):
        interact_with_page(
            """
            console.log($(document).html());
            """)
        print('hello')