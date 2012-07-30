from __future__ import unicode_literals, print_function, division
from markupsafe import Markup
from .template import template_utility
from .template import get_template

@template_utility
def render_element(element):
    if 'select' == element.type:
        return render_select(element)
    elif 'text' == element.type:
        return render_text(element)
    else:
        raise NotImplementedError('unknown element type: {}'.format(element.type))


def render_select(element):
    html = get_template(
        template_source=
        """
        <select name="{{ element.name }}">
            {% for option in element.options %}
            {% if option.is_selected %}
            <option value="{{ option.value }}" selected>{{ option.label }}</option>
            {% else %}
            <option value="{{ option.value }}">{{ option.label }}</option>
            {% endif %}
            {% endfor %}
        </select>
        """).render(element=element)
    return Markup(html)


def render_text(element):
    html = get_template(
        template_source=
        """
        <input type="text" name="{{ element.name }}" value="{{ element.value }}" maxlength="64"/>
        """).render(element=element)
    return Markup(html)
