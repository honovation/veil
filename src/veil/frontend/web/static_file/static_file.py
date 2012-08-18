from __future__ import unicode_literals, print_function, division
import contextlib
import hashlib
from markupsafe import Markup
from logging import getLogger
import lxml.html
from veil.utility.path import as_path
from veil.utility.hash import *
from veil.frontend.template import *
from veil.environment.setting import *

LOGGER = getLogger(__name__)

static_file_hashes = {}

get_inline_static_files_directory = register_option('website', 'inline_static_files_directory')
get_external_static_files_directory = register_option('website', 'external_static_files_directory')

# === utilities exposed for external usage ===
@contextlib.contextmanager
def clear_static_file_hashes():
    static_file_hashes.clear()
    yield


@template_utility
def static_url(path):
    hash = get_static_file_hash(path)
    if static_file_hashes.get(path):
        return '/static/{}?v={}'.format(path, hash[:5])
    else:
        return '/static/{}'.format(path)


def get_static_file_hash(path):
    if static_file_hashes.get(path) is None:
        static_file_path = as_path(get_external_static_files_directory()) / path
        try:
            with open(static_file_path) as f:
                hash = calculate_file_md5_hash(f)
                static_file_hashes[path] = hash
        except:
            LOGGER.error('Could not open static file {}'.format(static_file_path))
    return static_file_hashes.get(path)


def process_javascript_and_stylesheet_tags(page_handler, html):
# === combine & move <script> to the bottom ===
# === combine & move <link rel="stylesheet"> to the top ===
# === combine & externalize inline <script> ===
# === combine & externalize inline <style> ===
    if not html:
        return html
    if not html.strip():
        return html
    flag = html.strip()[:10].lstrip().lower()
    if flag.startswith('<html') or flag.startswith('<!doctype'):
        fragment = lxml.html.document_fromstring(html)
    else:
        fragment = lxml.html.fragment_fromstring(html, 'dummy-wrapper')
    script_elements = []
    link_elements = []
    inline_js_texts = []
    inline_css_texts = []
    for element in fragment.iterdescendants('script'):
        if 'text/plain' == element.get('type', None):
            continue
        if element.get('src', None):
            script_elements.append(element)
        else:
            inline_js_text = element.text_content().strip()
            if inline_js_text and inline_js_text not in inline_js_texts:
                inline_js_texts.append(wrap_js_to_ensure_load_once(inline_js_text))
        remove_element(element)
    for element in fragment.iterdescendants('style'):
        inline_css_text = element.text_content().strip()
        if inline_css_text and inline_css_text not in inline_css_texts:
            inline_css_texts.append(inline_css_text)
        remove_element(element)
    for element in fragment.iterdescendants('link'):
        if 'stylesheet' == element.get('rel', None):
            link_elements.append(element)
            remove_element(element)
    if inline_js_texts:
        script_elements.append(fragment.makeelement('script', attrib={
            'type': 'text/javascript',
            'src': '/static/{}'.format(write_inline_static_file(page_handler, 'js', '\r\n'.join(inline_js_texts)))
        }))
    if inline_css_texts:
        link_elements.append(fragment.makeelement('link', attrib={
            'rel': 'stylesheet',
            'type': 'text/css',
            'href': '/static/{}'.format(write_inline_static_file(page_handler, 'css', '\r\n'.join(inline_css_texts)))
        }))
    for element in script_elements:
        body_element = fragment.find('body')
        if body_element is not None:
            body_element.append(element)
        else:
            fragment.append(element)
    for i, element in enumerate(link_elements):
        head_element = fragment.find('head')
        if head_element is not None:
            head_element.append(element)
        else:
            fragment.insert(i, element)
    return Markup(lxml.html.tostring(fragment).replace(
        '<dummy-wrapper>', '').replace('</dummy-wrapper>', '').replace('<dummy-wrapper/>', ''))


def wrap_js_to_ensure_load_once(js):
    hash = hashlib.md5(js).hexdigest()
    return "veil.executeOnce('%s', function(){\r\n%s\r\n});" % (hash, js)


def remove_element(element):
    element.getparent().remove(element)


def write_inline_static_file(page_handler, suffix, content):
    hash = hashlib.md5(content).hexdigest()
    inline_static_file = as_path(get_inline_static_files_directory()) / hash
    if not inline_static_file.exists():
        inline_static_file.write_text(content)
    page_name = page_handler.__name__.replace('_widget', '').replace('_page', '').replace('_', '-')
    pseudo_file_name = '{}.{}'.format(page_name, suffix)
    return 'v-{}/{}'.format(hash, pseudo_file_name)