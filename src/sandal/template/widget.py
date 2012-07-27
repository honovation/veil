from __future__ import unicode_literals, print_function, division
import functools
from logging import getLogger
from inspect import getargspec
import os.path
import traceback
from markupsafe import Markup
from sandal.component import force_import_module
from .template import register_template_utility
from .template import require_current_template_directory_relative_to

# === global state ===
original_widgets = None
widgets = {}
active_widget_names = None
page_post_processors = []

LOGGER = getLogger(__name__)

def register_page_post_processor(page_post_processor):
    page_post_processors.append(page_post_processor)


def on_template_environment_ready():
    global original_widgets
    if not original_widgets:
        original_widgets = dict(widgets)


def on_template_environment_reset():
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
                self.activate()
                content = self.func(*args, **kwargs)
                if content is None:
                    return None
                return Markup(content)
        except:
            LOGGER.error('failed to render widget: {}'.format(self.name))
            raise

    def activate(self):
        if active_widget_names is None:
            raise Exception('{} called outside page'.format(widget))
        if self.name not in active_widget_names:
            active_widget_names.append(self.name)

    def __repr__(self):
        return 'widget {}'.format(self.name)


# === handle page ===
def page(func):
    return PageDecorator()(func)


class PageDecorator(WidgetDecorator):
    def __call__(self, func):
        if getattr(func, 'is_page', False):
            return func
        wrapper = super(PageDecorator, self).__call__(func)
        wrapper.is_page = True
        return wrapper

    def register(self, func):
        return Page(name=func.__name__, func=func)


class Page(Widget):
    def render(self, *args, **kwargs):
        global active_widget_names
        if active_widget_names:
            raise Exception('page can not be nested, there are active widgets: {}'.format(active_widget_names))
        active_widget_names = []
        try:
            html = super(Page, self).render(*args, **kwargs)
            if html is not None:
                active_widgets = [widgets[widget_name] for widget_name in active_widget_names]
                active_widgets.append(self)
                for page_post_processor in page_post_processors:
                    html = page_post_processor(html, active_widgets)
                return html
            return html
        finally:
            active_widget_names = None

    def activate(self):
        pass

    def __repr__(self):
        return 'page {}'.format(self.name)

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
