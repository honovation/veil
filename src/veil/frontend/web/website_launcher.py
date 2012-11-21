from __future__ import unicode_literals, print_function, division
import logging
import argparse
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
from .web_installer import load_website_config

LOGGER = logging.getLogger(__name__)

additional_context_managers = {}

def register_website_context_manager(website, context_manager):
    additional_context_managers.setdefault(website.lower(), []).append(context_manager)


@script('up')
def bring_up_website(*argv):
    argument_parser = argparse.ArgumentParser('Website')
    argument_parser.add_argument('purpose', help='which website to bring up')
    argument_parser.add_argument('--dependency', type=str,
        help='where @periodic_job is defined', nargs='+', dest='dependencies')
    args = argument_parser.parse_args(argv)
    for dependency in args.dependencies:
        __import__(dependency)
    start_website(args.purpose)


def start_test_website(purpose, **kwargs):
    config = load_website_config(purpose)
    http_handler = create_website_http_handler(purpose, **kwargs)
    http_server = start_test_http_server(
        http_handler,
        host=config.host,
        port=config.port)
    http_server.purpose = purpose
    return http_server


def start_website(purpose):
    config = load_website_config(purpose)
    http_handler = create_website_http_handler(purpose, config)
    io_loop = IOLoop.instance()
    io_loop.add_callback(lambda: LOGGER.info('started website {}'.format(purpose)))
    start_http_server(
        http_handler, io_loop=io_loop,
        host=config.host, port=config.port)


def create_website_http_handler(purpose, config):
    locale_provider = lambda: None
    if config.secure_cookie_salt:
        set_secure_cookie_salt(config.secure_cookie_salt)
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
