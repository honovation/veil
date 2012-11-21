from __future__ import unicode_literals, print_function, division
from logging import getLogger
from jinja2.loaders import FileSystemLoader
from veil.frontend.template import *
from veil.frontend.cli import *
from veil.environment.setting import *
from veil.frontend.website_setting import get_website_options
from .tornado import *
from .locale import *
from .routing import  *
from .static_file import *
from .xsrf import *

LOGGER = getLogger(__name__)

additional_context_managers = {}

def register_website_context_manager(website, context_manager):
    additional_context_managers.setdefault(website.lower(), []).append(context_manager)


@script('up')
def bring_up_website(website):
    program_config = get_settings().supervisor.programs['{}_website'.format(website)]
    for resource in program_config.resources:
        installer_name, installer_args = resource
        if 'component' == installer_name:
            __import__(installer_args['name'])
    start_website(website)


def start_test_website(purpose, **kwargs):
    http_handler = create_website_http_handler(purpose, **kwargs)
    website_options = get_website_options(purpose)
    http_server = start_test_http_server(
        http_handler,
        host=website_options.host,
        port=website_options.port)
    http_server.purpose = purpose
    return http_server


def start_website(purpose, **kwargs):
    io_loop = IOLoop.instance()
    http_handler = create_website_http_handler(purpose, **kwargs)
    io_loop.add_callback(lambda: LOGGER.info('started website {}'.format(purpose)))
    website_options = get_website_options(purpose)
    start_http_server(
        http_handler, io_loop=io_loop,
        host=website_options.host,
        port=website_options.port,
        processes_count=website_options.processes_count)


def create_website_http_handler(purpose, locale_provider=None):
    website_options = get_website_options(purpose)
    locale_provider = locale_provider or (lambda: None)
    secure_cookie_salt = website_options.secure_cookie_salt
    if secure_cookie_salt:
        set_secure_cookie_salt(secure_cookie_salt)
    set_inline_static_files_directory(website_options.inline_static_files_directory)
    set_external_static_files_directory(website_options.external_static_files_directory)
    master_template_directory = website_options.master_template_directory
    if master_template_directory:
        register_template_loader('master', FileSystemLoader(master_template_directory))
    website_context_managers = [create_stack_context(install_translations, locale_provider)]
    if website_options.prevents_xsrf:
        register_page_post_processor(set_xsrf_cookie_for_page)
        website_context_managers.append(prevent_xsrf)
    if website_options.recalculates_static_file_hash:
        website_context_managers.append(clear_static_file_hashes)
    if website_options.clears_template_cache:
        website_context_managers.append(clear_template_caches)
    website_context_managers.extend(additional_context_managers.get(purpose, []))
    return RoutingHTTPHandler(get_routes(purpose), website_context_managers)
