from __future__ import unicode_literals, print_function, division
from veil.development.test import *
from veil.profile.web import *
from .browser import start_website_and_browser

class VeilJsTest(TestCase):
    def test_script_element(self):
        @route('GET', '/', website='test')
        def home():
            return """
            <html>
            <head>
            <script src="/-test/jquery.js"></script>
            <script src="/-test/jquery-cookie.js"></script>
            <script src="/-test/veil.js"></script>
            <script>
                $(document).ready(function() {
                    veil.resource.get('/widget1', function(html) {
                        veil.assertEqual('abc', html);
                        $('#widget-itself').html(html);
                    });
                });
            </script>
            </head>
            <body>
            <div id="widget-itself"></div>
            <div id="referenced-js"></div>
            </body>
            </html>
            """

        @route('GET', '/widget1', website='test')
        def widget1():
            return 'abc<script src="/widget1.js"></script>'

        @route('GET', '/widget1.js', website='test')
        def widget1_js():
            return "$('#referenced-js').html('loaded')"

        start_website_and_browser(
            'test', '/',
            ["""
            veil.waitUntil(function(){
                return 'abc' == $('#widget-itself').html() && 'loaded' == $('#referenced-js').html();
            }, veil.stopTest);
            """])