from __future__ import unicode_literals, print_function, division
import re
from .script_element import parse_attributes

RE_LINK = re.compile('<link([^>]*?)/?>(.*?</link>)?', re.DOTALL | re.IGNORECASE)

def process_link_elements(html):
    css_urls = []

    def on_link_element(match):
        attributes = parse_attributes(match.group(1))
        if 'stylesheet' != attributes.get('rel'):
            return match.string
        href = attributes.get('href')
        if not href:
            return match.string
        css_urls.append(href)
        return ''

    html = RE_LINK.sub(on_link_element, html)
    return html, css_urls