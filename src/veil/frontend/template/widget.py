from __future__ import unicode_literals, print_function, division
import functools
import sys
from logging import getLogger
from inspect import getargspec
import traceback
from markupsafe import Markup
from veil.development.test import *
from veil.frontend.encoding import *
from .template import register_template_utility
from .template import require_current_template_directory_relative_to

# === global state ===
original_widgets = None
widgets = {}

LOGGER = getLogger(__name__)

@test_hook
def remember_original_widgets():
    get_executing_test().addCleanup(reset_widgets)
    global original_widgets
    if not original_widgets:
        original_widgets = dict(widgets)


def reset_widgets():
    widgets.clear()
    if original_widgets:
        widgets.update(original_widgets)

# === handle widget ===
def widget(func):
    return WidgetDecorator()(func)


class WidgetDecorator(object):
    def __call__(self, func):
        widget = self.register(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return widget.render(*args, **kwargs)

        return wrapper

    def register(self, func):
        widget_name = func.__name__.replace('_widget', '')
        widget = Widget(name=widget_name, func=func)
        if widget_name in widgets:
            raise Exception('widget {} already registered by {}'.format(
                widget_name, widgets[widget_name].registered_by))
        widgets[widget_name] = widget
        return widget


class Widget(object):
    def __init__(self, name, func):
        self.name = name
        self.func = func
        self.registered_by = '\n'.join(traceback.format_stack())

    def render(self, *args, **kwargs):
        try:
            if 'from_template' in getargspec(self.func).args:
                kwargs['from_template'] = kwargs['from_template'] if 'from_template' in kwargs else False
            else:
                kwargs.pop('from_template', None)
            with require_current_template_directory_relative_to(self.func):
                content = self.func(*args, **kwargs)
                if content is None:
                    return None
                return Markup(to_unicode(content))
        except:
            type, value, traceback = sys.exc_info()
            if not getattr(value, 'EXPECTED_WIDGET_ERROR', None):
                LOGGER.error('failed to render widget: {}'.format(self.name))
            raise

    def __repr__(self):
        return 'widget {}'.format(self.name)


# === export widgets as template utility ===
class WidgetLookup(object):
    def __init__(self, optional=False):
        self.optional = optional

    def __getattr__(self, name):
        if name not in widgets:
            if self.optional:
                return lambda *args, **kwargs: ''
            else:
                raise Exception('widget {} not found'.format(name))
        return append_from_template_flag(widgets[name].render)


def append_from_template_flag(widget):
    @functools.wraps(widget)
    def wrapper(*args, **kwargs):
        kwargs['from_template'] = True
        return widget(*args, **kwargs)

    return wrapper

register_template_utility('widgets', WidgetLookup())
register_template_utility('optional_widgets', WidgetLookup(optional=True))
