from __future__ import unicode_literals, print_function, division
from sandal.test import TestCase
from ..static_file import relocate_javascript_and_stylesheet_tags

class RelocateJavascriptAndStylesheetTagsTest(TestCase):
    def test_no_tag(self):
        self.assertEqual('', relocate_javascript_and_stylesheet_tags(''))
        self.assertEqual('<html></html>', relocate_javascript_and_stylesheet_tags('<html></html>'))
        self.assertEqual(
            '<p>a<span class="test">b</span>c</p>',
            relocate_javascript_and_stylesheet_tags('<p>a<span class="test">b</span>c</p>'))

    def test_javascript_tag_relocated_before_body_end(self):
        self.assertEqual(
            """
            <html>
            <body>
            <p></p>
            <script>test</script>\r\n</body>
            </html>
            """.strip(), relocate_javascript_and_stylesheet_tags(
            """
            <html>
            <body>
            <script>test</script>
            <p/>
            </body>
            </html>
            """
        ).strip())

    def test_stylesheet_tag_relocated_before_head_end(self):
        self.assertEqual(
            """
            <html>
            <head>
            <title>hello</title>
            <link rel="stylesheet" type="text/css" media="screen" href="a.css"></link>\r\n</head>
            </html>
            """.strip(), relocate_javascript_and_stylesheet_tags(
            """
            <html>
            <head>
            <title>hello</title>
            </head>
            <link rel="stylesheet" type="text/css" media="screen" href="a.css"/>
            </html>
            """
        ).strip())

    def test_relocate_both_javascripot_and_stylesheet_tags(self):
        self.assertEqual(
            """
            <html>
            <head>
            <title>hello</title>
            <link rel="stylesheet" type="text/css" media="screen" href="a.css"></link>\r\n</head>
            <body>
            <script>test</script>\r\n</body>
            </html>
            """.strip(), relocate_javascript_and_stylesheet_tags(
            """
            <html>
            <head>
            <title>hello</title>
            </head>
            <body>
            <script>test</script>
            <link rel="stylesheet" type="text/css" media="screen" href="a.css"/>
            </body>
            </html>
            """
        ).strip())

    def test_combined_scripts(self):
        self.assertEqual('<html><script>test</script>\r\n</html>', relocate_javascript_and_stylesheet_tags(
            '<html><script>test</script><script>test</script></html>'
        ))








