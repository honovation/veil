from __future__ import unicode_literals, print_function, division
from veil.utility.shell import *
from veil.environment import *
from veil.frontend.web import *

def check_html():
    check_strict_html_start_tag_prefix(VEIL_HOME)
    check_strict_head_end_tag(VEIL_HOME)
    check_strict_body_end_tag(VEIL_HOME)
    check_no_commented_script_or_style_or_link_element(VEIL_HOME)


def check_strict_html_start_tag_prefix(dir):
    htmls_with_prefix = get_html_files_with_content_matching_pattern(dir, '<\s*html', ignore_case=True)
    htmls_with_strict_prefix = get_html_files_with_content_matching_pattern(dir, HTML_START_TAG_PREFIX, ignore_case=False)
    htmls_without_strict_prefix = htmls_with_prefix - htmls_with_strict_prefix
    if htmls_without_strict_prefix:
        raise Exception('HTML files are not with strict html start tag prefix under folder {}: \n{}'.format(
            dir,
            '\n'.join(htmls_without_strict_prefix)
        ))


def check_strict_head_end_tag(dir):
    htmls_with_head_end_tag = get_html_files_with_content_matching_pattern(dir, '<\s*/\s*head\s*>', ignore_case=True)
    htmls_with_strict_head_end_tag = get_html_files_with_content_matching_pattern(dir, HEAD_END_TAG, ignore_case=False)
    htmls_without_strict_head_end_tag = htmls_with_head_end_tag - htmls_with_strict_head_end_tag
    if htmls_without_strict_head_end_tag:
        raise Exception('HTML files are not with strict head end tag under folder {}: \n{}'.format(
            dir,
            '\n'.join(htmls_without_strict_head_end_tag)
        ))


def check_strict_body_end_tag(dir):
    htmls_with_body_end_tag = get_html_files_with_content_matching_pattern(dir, '<\s*/\s*body\s*>', ignore_case=True)
    htmls_with_strict_body_end_tag = get_html_files_with_content_matching_pattern(dir, BODY_END_TAG, ignore_case=False)
    htmls_without_strict_body_end_tag = htmls_with_body_end_tag - htmls_with_strict_body_end_tag
    if htmls_without_strict_body_end_tag:
        raise Exception('HTML files are not with strict body end tag under folder {}: \n{}'.format(
            dir,
            '\n'.join(htmls_without_strict_body_end_tag)
        ))


def check_no_commented_script_or_style_or_link_element(dir):
    htmls_with_commented_script_element = get_html_files_with_content_matching_pattern(dir, '<\!--\s*<script\s*', ignore_case=True)
    htmls_with_commented_style_element = get_html_files_with_content_matching_pattern(dir, '<\!--\s*<style\s*', ignore_case=True)
    htmls_with_commented_link_element = get_html_files_with_content_matching_pattern(dir, '<\!--\s*<link\s*', ignore_case=True)
    htmls_with_commented_script_or_style_or_link_element = htmls_with_commented_script_element | htmls_with_commented_style_element | htmls_with_commented_link_element
    if htmls_with_commented_script_or_style_or_link_element:
        raise Exception('HTML files contain commented script or style or link element under folder {}: \n{}'.format(
            dir,
            '\n'.join(htmls_with_commented_script_or_style_or_link_element)
        ))


def get_html_files_with_content_matching_pattern(dir, pattern, ignore_case):
    files = set()
    try:
        files = shell_execute('grep -rl{} --include="*.html" "{}" .'.format('i' if ignore_case else '', pattern),
            capture=True, cwd=dir)
    except ShellExecutionError:
        pass
    else:
        files = set(files.splitlines(False))
    return files
