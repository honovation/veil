from __future__ import unicode_literals, print_function, division
import re

RE_SCRIPT = re.compile(r'<script([^>]*)>(.*?)</script>', re.DOTALL | re.IGNORECASE)
RE_SRC_ATTRIBUTE = re.compile(r'src="(.*?)"', re.IGNORECASE)

def process_script_elements(html):
    script_elements = []
    js_texts = []

    def on_script_element(match):
        if 'text/plain' in match.group(1):
            return match.group(0)
        if RE_SRC_ATTRIBUTE.search(match.group(1)):
            script_elements.append(match.group(0))
        else:
            if match.group(2) not in js_texts:
                js_texts.append(match.group(2))
        return ''

    html = RE_SCRIPT.sub(on_script_element, html)
    return html, script_elements, js_texts