from __future__ import unicode_literals, print_function, division
import re

RE_LINK = re.compile(r'<link([^>]*?)/?>(.*?</link>)?', re.DOTALL | re.IGNORECASE)

def process_link_elements(html):
    css_elements = []

    def on_link_element(match):
        if 'rel="stylesheet' not in match.group(1):
            return match.group(0)
        if 'data-keep="true"' in match.group(0):
            return match.group(0)
        if match.group(0) not in css_elements:
            css_elements.append(match.group(0))
        return ''

    html = RE_LINK.sub(on_link_element, html)
    return html, css_elements