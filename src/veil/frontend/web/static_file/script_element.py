from __future__ import unicode_literals, print_function, division
import re

RE_SCRIPT = re.compile(r'<script([^>]*)>(.*?)</script>', re.DOTALL | re.IGNORECASE)

def process_script_elements(html):
    js_urls = []
    js_texts = []

    def on_script_element(match):
        if 'text/plain' in match.group(1):
            return match.group(0)
        attributes = parse_attributes(match.group(1))
        if 'src' in attributes:
            js_urls.append(attributes['src'])
        else:
            if match.group(2) not in js_texts:
                js_texts.append(match.group(2))
        return ''

    html = RE_SCRIPT.sub(on_script_element, html)
    return html, js_urls, js_texts


def parse_attributes(text):
    attributes = {}
    for part in text.split(' '):
        if '=' in part:
            attributes[part.split('=')[0].lower()] = part.split('=')[1].strip().strip('"').strip("'").strip().lower()
    return attributes
