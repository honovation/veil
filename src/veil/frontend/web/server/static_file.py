from __future__ import unicode_literals, print_function, division
import contextlib
import hashlib
from markupsafe import Markup
import os.path
from logging import getLogger
from veil.backend.path import path as as_path
from veil.frontend.encoding import *
from sandal.hash import *
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
                    pseudo_file_name = generate_pseudo_file_name(template_path)
                    template.inline_javascript = 'v-{}/{}'.format(hash, pseudo_file_name)
                else:
                    template.inline_javascript = 'v-{}'.format(hash)
                script_tag = '<script type="text/javascript" src="/static/{}"></script>\r\n'.format(
                    template.inline_javascript)
                blocks[block_name] = lambda *args, **kwargs: (script_tag)


def delete_first_and_last_non_empty_lines_to_strip_tags_such_as_script(content):
    lines = content.splitlines()
    while True:
        if not lines[0]:
            del lines[0]
        else:
            break
    return '\n'.join(lines[1:-1])


def generate_pseudo_file_name(template_path):
    template_path = os.path.abspath(template_path)
    template_dir = os.path.basename(os.path.dirname(template_path))
    template_name = os.path.splitext(os.path.basename(template_path))[0]
    if template_dir.endswith('_web'):
        return '{}.js'.format(template_name)
    else:
        return '{}-{}.js'.format(template_dir.replace('_', '-'), template_name)

# === combine and move <script> to the bottom ===
def process_script_tags(html, active_widgets):
    SCRIPT_TAG_END = '></script>'
    splitted_parts = html.split('<script')
    striped_parts = [splitted_parts[0]]
    script_tags = []
    for part in splitted_parts[1:]:
        if SCRIPT_TAG_END not in part:
            raise Exception('<script> tag should come in pair and without content: {}'.format(part))
        end_pos = part.find(SCRIPT_TAG_END) + len(SCRIPT_TAG_END)
        striped_parts.append(part[end_pos:])
        script_tag = '<script{}'.format(part[:end_pos])
        if script_tag not in script_tags:
            script_tags.append(script_tag)
    striped_html = ''.join(striped_parts)
    if '</body>' in striped_html:
        return striped_html.replace('</body>', '{}\r\n</body>'.format('\r\n'.join(script_tags)))
    return '{}{}'.format(striped_html, ''.join(script_tags))


def as_markup(text):
    if text is None:
        return None
    return Markup(text)
