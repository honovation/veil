from __future__ import unicode_literals, print_function, division
import contextlib
import traceback
import os.path
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader, PrefixLoader
from sandal.component import force_import_module
from sandal.event import publish_event
from sandal.const import consts

consts.EVENT_TEMPLATE_ENVIRONMENT_READY = 'template-environment-ready'
consts.EVENT_TEMPLATE_ENVIRONMENT_RESET = 'template-environment-reset'

filters = {}
utilities = {}
loaders = {'root': FileSystemLoader('/')}
template_post_processors = []
env = None
current_template_directories = []

def template_filter(func):
# syntax sugar for register_template_filter
    register_template_filter(func.__name__, func)
    return func


def assert_no_env():
    if env:
        raise Exception('Environment already created by: {}'.format(env.created_by))


def register_template_filter(name, filter):
    assert_no_env()
    filters[name] = filter


def template_utility(func):
# syntax sugar for register_template_utility
    register_template_utility(func.__name__, func)
    return func


def register_template_utility(name, utility):
    assert_no_env()
    utilities[name] = utility


def register_template_loader(prefix, loader):
    assert_no_env()
    loaders[prefix] = loader


def register_template_post_processor(template_post_processor):
    template_post_processors.append(template_post_processor)


@contextlib.contextmanager
def require_current_translations_being(translations):
    get_or_create_environment().install_gettext_translations(translations)
    try:
        yield
    finally:
        get_or_create_environment().install_null_translations()


def require_current_template_directory_relative_to(func):
    return require_current_template_directory_being(
        os.path.dirname(os.path.abspath(force_import_module(func.__module__).__file__)))


@contextlib.contextmanager
def require_current_template_directory_being(template_directory):
    if not os.path.isabs(template_directory):
        raise Exception('template directory is not absolute: {}'.format(template_directory))
    current_template_directories.append(template_directory)
    try:
        yield
    finally:
        current_template_directories.pop()


def get_template(template_path=None, template_source=None):
    if not template_path and not template_source:
        raise Exception('must specify either template path or template source')
    if template_path:
        template = get_template_from_file(template_path)
    else:
        template = get_template_from_string(template_source)
    for template_post_processor in template_post_processors:
        template_post_processor(template_path, template)
    return template


def get_template_from_file(template_path):
    if not os.path.isabs(template_path):
        if not current_template_directories:
            raise Exception('unable to get {} from unknown template directory'.format(template_path))
        current_template_directory = current_template_directories[-1]
        template_path = os.path.join(current_template_directory, template_path)
    template = get_or_create_environment().get_template(
        'root:{}'.format(template_path), globals=dict(utilities, consts=consts))
    return template


def get_template_from_string(template_source):
    return get_or_create_environment().from_string(
        template_source, globals=dict(utilities, consts=consts))


def get_template_environment():
    return get_or_create_environment()


def get_or_create_environment():
    global env
    if env:
        return env
    env = Environment(
        loader=PrefixLoader(loaders, delimiter=':'),
        autoescape=True,
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.i18n'])
    env.filters.update(filters)
    env.install_null_translations()
    env.created_by = str('\n').join(traceback.format_stack())
    publish_event(consts.EVENT_TEMPLATE_ENVIRONMENT_READY)
    return env


def reset_template_environment():
    global env
    env = None
    publish_event(consts.EVENT_TEMPLATE_ENVIRONMENT_RESET)
