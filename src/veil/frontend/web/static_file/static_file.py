from __future__ import unicode_literals, print_function, division
import contextlib
import hashlib
import re
import logging
from markupsafe import Markup
from veil.environment import *
from veil_component import as_path
from veil.utility.shell import *
from veil.backend.queue import *
from veil.utility.misc import *
from veil.utility.encoding import *
from veil.frontend.template import *
from veil.development.test import *
from ..const import *
from .script_element import process_script_elements
from .link_element import process_link_elements
from .style_element import process_style_elements

LOGGER = logging.getLogger(__name__)

static_file_hashes = {}
external_static_files_directory = None


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
    if hash:
        return '/static/{}?v={}'.format(path, hash)
    else:
        return '/static/{}'.format(path)


def get_static_file_hash(path):
    assert external_static_files_directory
    if static_file_hashes.get(path) is None:
        static_file_path = as_path(external_static_files_directory) / path
        try:
            with open(static_file_path) as f:
                hash = calculate_file_md5_hash(f, hex=True)
                static_file_hashes[path] = hash
        except:
            LOGGER.error('Could not open static file: %(static_file_path)s', {'static_file_path': static_file_path})
    return static_file_hashes.get(path)


def process_stylesheet(page_handler, html):
    if html:
        html, link_elements = process_link_elements(html)
        css_type = get_css_type(html)
        html, css_texts = process_style_elements(html)
        if css_texts:
            combined_css_text = '\n'.join(css_texts)
            url = '/static/{}'.format(write_inline_static_file(page_handler, css_type, combined_css_text))
            link_elements.append('<link rel="stylesheet" type="text/{}" media="screen" href="{}"/>'.format(css_type, url))
        if link_elements:
            pos = html.find(HEAD_END_TAG)
            if pos == -1:
                html = '{}{}'.format(Markup('\n'.join(link_elements)), html)
            else:
                html = '{}{}{}'.format(html[:pos], Markup('\n'.join(link_elements)), html[pos:])
    return html

def get_css_type(html):
    if re.search('type=["\']text/less["\']', html, re.I):
        return 'less'
    return 'css'


def process_javascript(page_handler, html):
    if html:
        html, script_elements, js_texts = process_script_elements(html)
        if js_texts:
            combined_js_text = ';{}'.format('\n'.join(wrap_js_to_ensure_load_once(js_text) for js_text in js_texts))
            url = '/static/{}'.format(write_inline_static_file(page_handler, 'js', combined_js_text))
            script_elements.append('<script type="text/javascript" src="{}"></script>'.format(url))
        if script_elements:
            pos = html.rfind(BODY_END_TAG)
            if pos == -1:
                html = '{}{}'.format(html, Markup('\n'.join(script_elements)))
            else:
                html = '{}{}{}'.format(html[:pos], Markup('\n'.join(script_elements)), html[pos:])
    return html


def wrap_js_to_ensure_load_once(js):
    hash_ = hashlib.md5(to_str(js)).hexdigest()
    return "veil.executeOnce('{}', function(){{\r\n{}\r\n}});".format(hash_, js)


def write_inline_static_file(page_handler, suffix, content):
    hash = hashlib.md5(to_str(content)).hexdigest()
    dir = VEIL_BUCKET_INLINE_STATIC_FILES_DIR / hash[:2]
    dir.makedirs(0755)
    inline_static_file = dir / hash[2:]
    if not inline_static_file.exists():
        inline_static_file.write_text(to_str(content))
    page_name = page_handler.__name__.replace('_widget', '').replace('_page', '').replace('_', '-')
    pseudo_file_name = '{}.{}'.format(page_name, suffix)
    return 'v-{}-{}/{}'.format(hash[:2], hash[2:], pseudo_file_name)


@periodic_job('13 1 * * *')
def clean_up_inline_static_files_job():
    if not VEIL_BUCKET_INLINE_STATIC_FILES_DIR.exists():
        return
    shell_execute('find {} -type f -atime +15 -delete'.format(VEIL_BUCKET_INLINE_STATIC_FILES_DIR), capture=True)
