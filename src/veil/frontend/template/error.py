from __future__ import unicode_literals, print_function, division
from markupsafe import Markup
from .template import template_utility

@template_utility
def error_html(all_errors, field=None):
    field_errors = get_field_errors(all_errors, field) if field else all_errors
    if not field_errors:
        return ''
    lines = ['<span class="label label-warning"><i class="icon-info-sign icon-white"></i>  ']
    for field_error in field_errors:
        lines.append(field_error)
    lines.append('</span>')
    return Markup(''.join(lines))

@template_utility
def error_css(all_errors, field=None, hide=False):
    if get_field_errors(all_errors, field):
        return 'having-error'
    if hide:
        return 'no-error'
    return ''

def get_field_errors(all_errors, field):
    if not field:
        return all_errors
    field_errors = []
    for field_or_fields, errors in all_errors.items():
        if isinstance(field_or_fields, (list, tuple)):
            if field in field_or_fields:
                field_errors.extend(errors)
        elif field_or_fields == field:
            field_errors.extend(errors)
    return field_errors