from __future__ import unicode_literals, print_function, division
import re

RE_STYLE = re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)

def process_style_elements(html):
    css_texts = []

    def on_style_element(match):
        if 'data-keep="data-keep"' in match.group(0):
            return match.group(0)
        if match.group(1) not in css_texts:
            css_texts.append(match.group(1))
        return ''

    html = RE_STYLE.sub(on_style_element, html)
    return html, css_texts