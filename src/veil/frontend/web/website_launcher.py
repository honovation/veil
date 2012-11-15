from __future__ import unicode_literals, print_function, division
from logging import getLogger
from jinja2.loaders import FileSystemLoader
from veil.frontend.template import *
from veil.frontend.cli import *
from veil.environment import *
from veil.environment.setting import *
from .tornado import *
from .locale import *
from .routing import  *
from .static_file import *
from .xsrf import *

LOGGER = getLogger(__name__)

registry = {} # website => get_website_options
additional_context_managers = {}

def register_website_context_manager(website, context_manager):
    additional_context_managers.setdefault(website.lower(), []).append(context_manager)


@script('up')
def bring_up_website(website):
    load_all_website_components()
    start_website(website)

def load_all_website_components():
    # before we know the reverse dependencies, we have to ensure all application components loaded
    for component_name in get_application_components():
        __import__(component_name)

def start_test_website(website, **kwargs):
    http_handler = create_website_http_handler(website, **kwargs)
    return start_test_http_server(
        http_handler,
        host=get_website_option(website, 'host'),
        port=get_website_option(website, 'port'))


def start_website(website, **kwargs):
    io_loop = IOLoop.instance()
    http_handler = create_website_http_handler(website, **kwargs)
    io_loop.add_callback(lambda: LOGGER.info('started website {}'.format(website)))
    start_http_server(
        http_handler, io_loop=io_loop,
        host=get_website_option(website, 'host'),
        port=get_website_option(website, 'port'),
        processes_count=get_website_option(website, 'processes_count'))


def create_website_http_handler(website, locale_provider=None):
    locale_provider = locale_provider or (lambda: None)
    secure_cookie_salt = get_website_option(website, 'secure_cookie_salt')
    if secure_cookie_salt:
        set_secure_cookie_salt(secure_cookie_salt)
    set_inline_static_files_directory(get_website_option(website, 'inline_static_files_directory'))
    set_external_static_files_directory(get_website_option(website, 'external_static_files_directory'))
    master_template_directory = get_website_option(website, 'master_template_directory')
    if master_template_directory:
        register_template_loader('master', FileSystemLoader(master_template_directory))
    website_context_managers = [create_stack_context(install_translations, locale_provider)]
    if get_website_option(website, 'prevents_xsrf'):
        register_page_post_processor(set_xsrf_cookie_for_page)
        website_context_managers.append(prevent_xsrf)
    if get_website_option(website, 'recalculates_static_file_hash'):
        website_context_managers.append(clear_static_file_hashes)
    if get_website_option(website, 'clears_template_cache'):
        website_context_managers.append(clear_template_caches)
    website_context_managers.extend(additional_context_managers.get(website, []))
    return RoutingHTTPHandler(get_routes(website), website_context_managers)


def register_website_options(website):
    if website in registry:
        return
    section = '{}_website'.format(website.lower()) # for example shopper_website
    get_recalculates_static_file_hash = register_option(section, 'recalculates_static_file_hash', bool, default=True)
    get_clears_template_cache = register_option(section, 'clears_template_cache', bool, default=True)
    get_prevents_xsrf = register_option(section, 'prevents_xsrf', bool, default=True)
    get_master_template_directory = register_option(section, 'master_template_directory', default='')
    get_secure_cookie_salt = register_option(section, 'secure_cookie_salt', default='')
    get_host = register_option(section, 'host')
    get_port = register_option(section, 'port', int)
    get_processes_count = register_option(section, 'processes_count', default=1)
    get_inline_static_files_directory = register_option(section, 'inline_static_files_directory')
    get_external_static_files_directory = register_option(section, 'external_static_files_directory')
    get_domain = register_option(section, 'domain')
    get_domain_port = register_option(section, 'domain_port')

    def get_website_options():
        return {
            'recalculates_static_file_hash': get_recalculates_static_file_hash(),
            'clears_template_cache': get_clears_template_cache(),
            'prevents_xsrf': get_prevents_xsrf(),
            'master_template_directory': get_master_template_directory(),
            'secure_cookie_salt': get_secure_cookie_salt(),
            'host': get_host(),
            'port': get_port(),
            'processes_count': get_processes_count(),
            'inline_static_files_directory': get_inline_static_files_directory(),
            'external_static_files_directory': get_external_static_files_directory(),
            'domain': get_domain(),
            'domain_port': get_domain_port()
        }

    registry[website] = get_website_options


def get_website_option(website, name):
    website = website.lower()
    return registry[website]()[name]
