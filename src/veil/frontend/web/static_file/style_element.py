from __future__ import unicode_literals, print_function, division
import re

RE_STYLE = re.compile('<style[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)

def process_style_elements(html):
    css_texts = []

    def on_style_element(match):
        css_texts.append(match.group(1))
        return ''

    html = RE_STYLE.sub(on_style_element, html)
    return html, css_texts