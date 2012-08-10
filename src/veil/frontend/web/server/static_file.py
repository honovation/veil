from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import contextlib
import hashlib
from markupsafe import Markup
import os.path
from logging import getLogger
from lxml import etree
from sandal.path import as_path
from sandal.hash import *
from veil.frontend.encoding import *
from veil.frontend.template import *
from veil.environment.runtime import *

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

# === write inline static files after template loaded ===
def process_inline_blocks(template_path, template):
    process_inline_javascript(template, template_path)
    process_inline_stylesheet(template, template_path)


def process_inline_javascript(template, template_path):
    if not hasattr(template, 'inline_javascript'):
        template.inline_javascript = ''
        blocks = template.blocks
        for block_name in blocks.keys():
            if 'inline_javascript' == block_name:
                content = ''.join(list(blocks[block_name](template.new_context())))
                content = delete_first_and_last_non_empty_lines_to_strip_tags_such_as_script(content)
                content = to_str(content)
                hash = hashlib.md5(content).hexdigest()
                inline_static_file = as_path(get_inline_static_files_directory()) / hash
                if not inline_static_file.exists():
                    inline_static_file.write_text(content)
                if template_path:
                    pseudo_file_name = generate_pseudo_file_name(template_path, 'js')
                    template.inline_javascript = 'v-{}/{}'.format(hash, pseudo_file_name)
                else:
                    template.inline_javascript = 'v-{}'.format(hash)
                html_tag = '<script type="text/javascript" src="/static/{}"></script>\r\n'.format(
                    template.inline_javascript)
                blocks[block_name] = lambda *args, **kwargs: (html_tag)


def process_inline_stylesheet(template, template_path):
    if not hasattr(template, 'inline_stylesheet'):
        template.inline_stylesheet = ''
        blocks = template.blocks
        for block_name in blocks.keys():
            if 'inline_stylesheet' == block_name:
                content = ''.join(list(blocks[block_name](template.new_context())))
                content = delete_first_and_last_non_empty_lines_to_strip_tags_such_as_script(content)
                content = to_str(content)
                hash = hashlib.md5(content).hexdigest()
                inline_static_file = as_path(get_inline_static_files_directory()) / hash
                if not inline_static_file.exists():
                    inline_static_file.write_text(content)
                if template_path:
                    pseudo_file_name = generate_pseudo_file_name(template_path, 'css')
                    template.inline_stylesheet = 'v-{}/{}'.format(hash, pseudo_file_name)
                else:
                    template.inline_stylesheet = 'v-{}'.format(hash)
                html_tag = '<link rel="stylesheet" type="text/css" media="screen" href="/static/{}"/>\r\n'.format(
                    template.inline_stylesheet)
                blocks[block_name] = lambda *args, **kwargs: (html_tag)


def delete_first_and_last_non_empty_lines_to_strip_tags_such_as_script(content):
    lines = content.splitlines()
    while True:
        if not lines[0]:
            del lines[0]
        else:
            break
    return '\n'.join(lines[1:-1])


def generate_pseudo_file_name(template_path, suffix):
    template_path = os.path.abspath(template_path)
    template_dir = os.path.basename(os.path.dirname(template_path))
    template_name = os.path.splitext(os.path.basename(template_path))[0]
    if template_dir.endswith('_web'):
        return '{}.{}'.format(template_name, suffix)
    else:
        return '{}-{}.{}'.format(template_dir.replace('_', '-'), template_name, suffix)


# === combine & move <script> to the bottom ===
# === combine & move <style> to the top ===
def relocate_javascript_and_stylesheet_tags(orig_html):
    if not orig_html:
        return orig_html
    if not orig_html.strip():
        return orig_html
    if '</html>' not in orig_html:
        return orig_html
    fragments = []
    javascript_fragments = []
    stylesheet_fragments = []
    head_end_index = None
    body_end_index = None
    context = etree.iterparse(StringIO(orig_html.encode('utf8')), ('start', 'end', 'start-ns', 'end-ns'), encoding='utf8')
    for action, element in context:
        if 'end' == action and 'body' == element.tag:
            body_end_index = len(fragments)
        if 'end' == action and 'head' == element.tag:
            head_end_index = len(fragments)
        if 'script' == element.tag:
            if 'start' == action:
                javascript_fragment = '{}{}</script>'.format(format_start_tag(element), element.text or '')
                if javascript_fragment not in javascript_fragments:
                    javascript_fragments.append(javascript_fragment)
            continue
        if 'style' == element.tag:
            if 'start' == action:
                stylesheet_fragment = '{}{}</style>'.format(format_start_tag(element), element.text or '')
                if stylesheet_fragment not in stylesheet_fragments:
                    stylesheet_fragments.append(stylesheet_fragment)
            continue
        if 'link' == element.tag and 'stylesheet' == element.attrib.get('rel'):
            if 'start' == action:
                stylesheet_fragment = '{}{}</link>'.format(format_start_tag(element), element.text or '')
                if stylesheet_fragment not in stylesheet_fragments:
                    stylesheet_fragments.append(stylesheet_fragment)
            continue
        fragments.extend(to_fragments(action, element))
    if stylesheet_fragments:
        stylesheet_fragments[-1] = '{}\r\n'.format(stylesheet_fragments[-1])
    fragments.insert(head_end_index or 0, '\n'.join(stylesheet_fragments))
    if javascript_fragments:
        javascript_fragments[-1] = '{}\r\n'.format(javascript_fragments[-1])
    fragments.insert(body_end_index + 1 if body_end_index else len(fragments) - 1, '\n'.join(javascript_fragments))
    return ''.join(fragments)

def to_fragments(action, element):
    fragments = []
    if 'start' == action:
        fragments.append(format_start_tag(element))
        if element.text:
            fragments.append(element.text)
    elif 'end' == action:
        fragments.append('</{}>'.format(element.tag))
        if element.tail:
            fragments.append(element.tail)
    return fragments

def format_start_tag(element):
    if element.attrib:
        return '<{} {}>'.format(element.tag, ' '.join(
            ['{}="{}"'.format(k, v) for k, v in element.attrib.items()]))
    else:
        return '<{}>'.format(element.tag)


def as_markup(text):
    if text is None:
        return None
    return Markup(text)
