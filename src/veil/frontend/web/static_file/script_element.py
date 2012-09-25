from __future__ import unicode_literals, print_function, division
import re

RE_SCRIPT = re.compile(r'<script([^>]*)>(.*?)</script>', re.DOTALL | re.IGNORECASE)
RE_SRC_ATTRIBUTE = re.compile(r'.*src="(.*?)"', re.IGNORECASE)

def process_script_elements(html):
    js_urls = []
    js_texts = []

    def on_script_element(match):
        if 'text/plain' in match.group(1):
            return match.group(0)
        src_match = RE_SRC_ATTRIBUTE.match(match.group(1))
        if src_match:
            js_urls.append(src_match.group(1))
        else:
            if match.group(2) not in js_texts:
                js_texts.append(match.group(2))
        return ''

    html = RE_SCRIPT.sub(on_script_element, html)
    return html, js_urls, js_texts