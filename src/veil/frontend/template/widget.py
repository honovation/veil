from __future__ import unicode_literals, print_function, division
import functools
import sys
from logging import getLogger
from inspect import getargspec
import traceback
from markupsafe import Markup
import contextlib
import veil.component
from veil.development.test import *
from veil.frontend.encoding import *
from .template import register_template_utility
from .template import require_current_template_directory_relative_to

# === global state ===
original_widgets = None
widgets = {}
current_widget_template_spaces = []

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
        widget_name = func.__name__.replace('_widget', '')
        widget = Widget(name=widget_name, func=func)
        if widget_name in widgets:
            raise Exception('widget {} already registered by {}'.format(
                widget_name, widgets[widget_name].registered_by))

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return widget.render(*args, **kwargs)

        loading_component = veil.component.get_loading_component()
        if loading_component:
            namespace = loading_component.__name__
        else:
            namespace = None
        widgets.setdefault(namespace, {})[widget_name] = wrapper
        return wrapper


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


def import_widget(widget_handler):
    loading_component = veil.component.get_loading_component()
    if loading_component:
        namespace = loading_component.__name__
    else:
        namespace = None
    widget_name = widget_handler.__name__.replace('_widget', '')
    widgets.setdefault(namespace, {})[widget_name] = widget_handler


# === export widgets as template utility ===
@contextlib.contextmanager
def require_current_widget_namespace_being(namespace):
    current_widget_template_spaces.append(namespace)
    try:
        yield
    finally:
        current_widget_template_spaces.pop()


class WidgetLookup(object):
    def __init__(self, optional=False):
        self.optional = optional

    def __getattr__(self, name):
        widget_handler = widgets.get(current_widget_template_spaces[-1], {}).get(name, None)
        if not widget_handler:
            if self.optional:
                return lambda *args, **kwargs: ''
            else:
                raise Exception('widget {} not found'.format(name))
        return append_from_template_flag(widget_handler)


def append_from_template_flag(widget):
    @functools.wraps(widget)
    def wrapper(*args, **kwargs):
        kwargs['from_template'] = True
        return widget(*args, **kwargs)

    return wrapper

register_template_utility('widgets', WidgetLookup())
register_template_utility('optional_widgets', WidgetLookup(optional=True))
