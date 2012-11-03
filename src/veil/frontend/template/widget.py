from __future__ import unicode_literals, print_function, division
import functools
import sys
import inspect
import traceback
import logging
from markupsafe import Markup
import contextlib
import veil_component
from veil.development.test import *
from veil.frontend.encoding import *
from .template import register_template_utility
from .template import require_current_template_directory_relative_to

# === global state ===
original_widgets = None
widgets = {}
current_widget_template_namespaces = []

LOGGER = logging.getLogger(__name__)

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
def widget(func=None, is_abstract=False, implements=None):
    if func:
        return WidgetDecorator()(func)
    else:
        return WidgetDecorator(is_abstract=is_abstract, implements=implements)


class WidgetDecorator(object):
    def __init__(self, is_abstract=False, implements=None):
        self.is_abstract = is_abstract
        self.implements = implements
        if implements:
            assert is_abstract_widget(implements), '{} is not abstract widget'.format(implements)

    def __call__(self, func):
        widget_name = func.__name__.replace('_widget', '')
        widget = Widget(name=widget_name, func=func)
        if widget_name in widgets:
            raise Exception('widget {} already registered by {}'.format(
                widget_name, widgets[widget_name].registered_by))

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return widget.render(*args, **kwargs)

        loading_component_name = veil_component.get_loading_component_name()
        if loading_component_name:
            namespace = loading_component_name
        else:
            namespace = None
        if self.is_abstract:
            def report_abstract_error(*args, **kwargs):
                raise Exception('widget {}.{} is not implemented yet'.format(namespace, widget_name))

            widgets.setdefault(namespace, {})[widget_name] = report_abstract_error
            func.IS_ABSTRACT_WIDGET = 'true'
            func.namespace = namespace
            return func
        else:
            if self.implements:
                expected_args = inspect.getargspec(self.implements).args
                actual_args = inspect.getargspec(func).args
                assert expected_args == actual_args, '{} does not implement {}, expected args: {}, actual args: {}'.format(
                    func, self.implements, expected_args, actual_args)
                target_widget_namespace = self.implements.namespace
                target_widget_name = self.implements.__name__.replace('_widget', '')
                widgets.setdefault(target_widget_namespace, {})[target_widget_name] = wrapper
            widgets.setdefault(namespace, {})[widget_name] = wrapper
            return wrapper


def is_abstract_widget(widget_handler):
    return getattr(widget_handler, 'IS_ABSTRACT_WIDGET', None)


class Widget(object):
    def __init__(self, name, func):
        self.name = name
        self.func = func
        self.registered_by = '\n'.join(traceback.format_stack())
        loading_component_name = veil_component.get_loading_component_name()
        if loading_component_name:
            self.namespace = loading_component_name
        else:
            self.namespace = None

    def render(self, *args, **kwargs):
        try:
            with require_current_template_directory_relative_to(self.func):
                with require_current_widget_namespace_being(self.namespace):
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
    if is_abstract_widget(widget_handler):
        raise Exception('can not import abstract widget: {}'.format(widget_handler))
    loading_component_name = veil_component.get_loading_component_name()
    if loading_component_name:
        namespace = loading_component_name
    else:
        namespace = None
    widget_name = widget_handler.__name__.replace('_widget', '')
    widgets.setdefault(namespace, {})[widget_name] = widget_handler


@contextlib.contextmanager
def require_current_widget_namespace_being(namespace):
    current_widget_template_namespaces.append(namespace)
    try:
        yield
    finally:
        current_widget_template_namespaces.pop()


class WidgetLookup(object):
    def __init__(self, optional=False):
        self.optional = optional

    def __getattr__(self, name):
        widget_handler = widgets.get(current_widget_template_namespaces[-1], {}).get(name, None)
        if not widget_handler:
            if self.optional:
                return lambda *args, **kwargs: ''
            else:
                raise Exception('widget {} not found'.format(name))
        return widget_handler


register_template_utility('widgets', WidgetLookup())
register_template_utility('optional_widgets', WidgetLookup(optional=True))
