from __future__ import unicode_literals, print_function, division
import contextlib
import hashlib
import re
import markupsafe
import logging
import lxml.html
from veil.development.test import *
from veil.frontend.web.tornado import *
from veil.utility.path import as_path
from veil.utility.hash import *
from veil.frontend.template import *
from veil.frontend.encoding import *

LOGGER = logging.getLogger(__name__)
REGEX_CLOSED_TAG = re.compile(r'<([^>]*?)/>')

static_file_hashes = {}
inline_static_files_directory = None
external_static_files_directory = None
script_elements_processors = []
original_script_elements_processors = []

def register_script_elements_processor(processor):
    script_elements_processors.append(processor)


def clear_script_elements_processors():
    global script_elements_processors
    script_elements_processors = []


@test_hook
def remember_script_elements_processors():
    get_executing_test().addCleanup(reset_script_elements_processors)
    global original_script_elements_processors
    if not original_script_elements_processors:
        original_script_elements_processors = list(script_elements_processors)


def reset_script_elements_processors():
    global script_elements_processors
    script_elements_processors = []
    if original_script_elements_processors:
        script_elements_processors.extend(original_script_elements_processors)


def set_inline_static_files_directory(value):
    global inline_static_files_directory
    executing_test = get_executing_test(optional=True)
    if executing_test:
        def reset():
            global inline_static_files_directory
            inline_static_files_directory = None

        executing_test.addCleanup(reset)
    inline_static_files_directory = value


def set_external_static_files_directory(value):
    global external_static_files_directory
    executing_test = get_executing_test(optional=True)
    if executing_test:
        def reset():
            global external_static_files_directory
            external_static_files_directory = None

        executing_test.addCleanup(reset)
    external_static_files_directory = value


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
    assert external_static_files_directory
    if static_file_hashes.get(path) is None:
        static_file_path = as_path(external_static_files_directory) / path
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
    http_response = get_current_http_response(optional=True)
    if http_response:
        if 'text/html' not in http_response.headers.get('Content-Type', ''):
            return html
    if not html:
        return html
    if not html.strip():
        return html
    flag = html.strip()[:10].lstrip().lower()
    parser = lxml.html.XHTMLParser(strip_cdata=False)
    is_full_page = True
    if flag.startswith('<html') or flag.startswith('<!doctype'):
        fragment = lxml.html.document_fromstring(html, parser=parser)
    else:
        is_full_page = False
        fragment = lxml.html.fragment_fromstring(html, 'dummy-wrapper', parser=parser)
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
        script_element = fragment.makeelement('script', attrib={
            'type': 'text/javascript',
            'src': '/static/{}'.format(write_inline_static_file(page_handler, 'js', '\r\n'.join(inline_js_texts)))
        })
        script_elements.append(script_element)
    if inline_css_texts:
        link_elements.append(fragment.makeelement('link', attrib={
            'rel': 'stylesheet',
            'type': 'text/css',
            'href': '/static/{}'.format(write_inline_static_file(page_handler, 'css', '\r\n'.join(inline_css_texts)))
        }))
    if is_full_page:
        for processor in script_elements_processors:
            script_elements = processor(parser, script_elements)
    inserted_external_script_paths = set()
    for element in script_elements:
        body_element = fragment.find('body')
        external_script_path = element.get('src', None)
        if external_script_path:
            if external_script_path in inserted_external_script_paths:
                continue
            inserted_external_script_paths.add(external_script_path)
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
    processed_html = lxml.html.tostring(fragment, method='xml', encoding='utf-8')
    processed_html = to_unicode(processed_html)
    post_processed_html = processed_html.replace(
        '<dummy-wrapper>', '').replace('</dummy-wrapper>', '').replace('<dummy-wrapper/>', '')
    post_processed_html = open_closed_tags(post_processed_html)
    return markupsafe.Markup(post_processed_html)


def wrap_js_to_ensure_load_once(js):
    hash = hashlib.md5(to_str(js)).hexdigest()
    return "veil.executeOnce('%s', function(){\r\n%s\r\n});" % (hash, js)


def remove_element(element):
    element.getparent().remove(element)


def write_inline_static_file(page_handler, suffix, content):
    assert inline_static_files_directory
    hash = hashlib.md5(to_str(content)).hexdigest()
    dir = as_path(inline_static_files_directory)
    if not dir.exists():
        dir.mkdir(0755)
    inline_static_file = dir / hash
    if not inline_static_file.exists():
        inline_static_file.write_text(to_str(content))
    page_name = page_handler.__name__.replace('_widget', '').replace('_page', '').replace('_', '-')
    pseudo_file_name = '{}.{}'.format(page_name, suffix)
    return 'v-{}/{}'.format(hash, pseudo_file_name)


def open_closed_tags(html):
    return REGEX_CLOSED_TAG.sub(open_closed_tag, html)


def open_closed_tag(match):
    tag_and_attributes = match.group(1).strip()
    tag = tag_and_attributes.split(' ')[0]
    return '<{}></{}>'.format(tag_and_attributes, tag)