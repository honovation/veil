from __future__ import unicode_literals, print_function, division
import logging
import argparse
from jinja2.loaders import FileSystemLoader
from veil.frontend.locale import get_locale
from veil.frontend.template import *
from veil.frontend.cli import *
from veil.environment import *
from veil.development.source_code_monitor import *
from veil.frontend.website_setting import list_website_components
from .tornado import *
from .locale import *
from .routing import *
from .static_file import *
from .xsrf import *
from .website_installer import load_website_config

LOGGER = logging.getLogger(__name__)

additional_context_managers = {}

def register_website_context_manager(website, context_manager):
    additional_context_managers.setdefault(website.lower(), []).append(context_manager)


@script('up')
def execute_bring_up_website(*argv):
    argument_parser = argparse.ArgumentParser('Website')
    argument_parser.add_argument('purpose', help='which website to bring up')
    argument_parser.add_argument('port', type=int, help='listen on which port')
    argument_parser.add_argument('--component', type=str, action='append', help='where @route is defined', dest='components') # TODO: remove me
    args = argument_parser.parse_args(argv)
    if args.components:
        website_components = args.components
    else:
        website_components = list_website_components(args.purpose)
    start_website(purpose=args.purpose, port=args.port, components=website_components)


def start_test_website(purpose, **kwargs):
    config = load_website_config(purpose)
    http_handler = create_website_http_handler(purpose, config, **kwargs)
    http_server = start_test_http_server(http_handler, host='localhost', port=config.start_port)
    http_server.purpose = purpose
    return http_server


@source_code_monitored
def start_website(purpose, port):
    config = load_website_config(purpose)
    http_handler = create_website_http_handler(purpose, config)
    io_loop = IOLoop.instance()
    io_loop.add_callback(lambda: LOGGER.info('started website: %(purpose)s', {'purpose': purpose}))
    start_http_server(http_handler, io_loop=io_loop, host='localhost', port=port)


def create_website_http_handler(purpose, config):
    if config.locale:
        locale_provider = lambda: get_locale(config.locale)
    else:
        locale_provider = lambda: None
    set_inline_static_files_directory(VEIL_VAR_DIR / 'inline-static-files')
    set_external_static_files_directory(VEIL_HOME / 'static')
    master_template_directory = config.master_template_directory
    if master_template_directory:
        register_template_loader('master', FileSystemLoader(master_template_directory))
    website_context_managers = [create_stack_context(install_translations, locale_provider)]
    if config.prevents_xsrf:
        register_page_post_processor(set_xsrf_cookie_for_page)
        website_context_managers.append(prevent_xsrf)
    if config.recalculates_static_file_hash:
        website_context_managers.append(clear_static_file_hashes)
    if config.clears_template_cache:
        website_context_managers.append(clear_template_caches)
    website_context_managers.extend(additional_context_managers.get(purpose, []))
    return RoutingHTTPHandler(get_routes(purpose), website_context_managers)
