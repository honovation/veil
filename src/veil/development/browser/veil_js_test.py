from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from veil.profile.web import *
from .browser import start_website_and_browser
from .browser import load_page_interactions

class VeilJsTest(TestCase):
    def test_script_element(self):
        @route('GET', '/', website='test')
        def home():
            return get_template('veil-js-test/home.html').render()

        @route('GET', '/widget1', website='test')
        def widget1():
            return get_template('veil-js-test/widget1.html').render()

        @route('GET', '/widget1.js', website='test')
        def widget1_js():
            return get_template('veil-js-test/widget1.js').render()

        start_website_and_browser(
            'test', '/', load_page_interactions('veil-js-test/veil-js.pi'))