from __future__ import unicode_literals, print_function, division
import contextlib
import logging
import argparse
from jinja2.loaders import FileSystemLoader
from veil.frontend.locale import get_locale
from veil.frontend.template import *
from veil.frontend.cli import *
from veil.environment import *
from veil.development.source_code_monitor import *
from .tornado import *
from .locale import *
from .routing import *
from .static_file import *
from .xsrf import *
from .website_installer import website_config, get_website_parent_domain

LOGGER = logging.getLogger(__name__)

additional_context_managers = {}


def register_website_context_manager(website, context_manager):
    additional_context_managers.setdefault(website.lower(), []).append(context_manager)


@script('up')
def execute_bring_up_website(*argv):
    argument_parser = argparse.ArgumentParser('Website')
    argument_parser.add_argument('purpose', help='which website to bring up')
    argument_parser.add_argument('port', type=int, help='listen on which port')
    args = argument_parser.parse_args(argv)
    start_website(args.purpose, args.port)


def start_test_website(purpose):
    config = website_config(purpose)
    http_handler = create_website_http_handler(purpose, config)
    http_server = start_test_http_server(http_handler, host='localhost', port=config.start_port)
    http_server.purpose = purpose
    return http_server


@source_code_monitored
def start_website(purpose, port):
    config = website_config(purpose)
    http_handler = create_website_http_handler(purpose, config)
    io_loop = IOLoop.instance()
    io_loop.add_callback(lambda: LOGGER.info('started website: %(purpose)s', {'purpose': purpose}))
    start_http_server(http_handler, io_loop=io_loop, host='localhost', port=port)


def create_website_http_handler(purpose, config):
    if config.locale:
        locale_provider = lambda: get_locale(config.locale)
    else:
        locale_provider = lambda: None
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
    if config.process_page_javascript:
        register_page_post_processor(process_javascript)
    if config.process_page_stylesheet:
        register_page_post_processor(process_stylesheet)
    if config.clears_template_cache:
        website_context_managers.append(clear_template_caches)
    website_context_managers.extend(additional_context_managers.get(purpose, []))
    return RoutingHTTPHandler(get_routes(purpose), website_context_managers)


def remove_no_longer_used_cookies(purpose, current_domain_names=(), parent_domain_names=()):
    assert current_domain_names or parent_domain_names

    @contextlib.contextmanager
    def f():
        request = get_current_http_request()
        parent_domain = get_website_parent_domain(purpose)
        try:
            for name in current_domain_names:
                clear_cookie(name, domain=None)
            for name in parent_domain_names:
                clear_cookie(name, domain=parent_domain)
        except Exception:
            LOGGER.exception('failed to clear no-longer-used cookies: %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
                'uri': request.uri,
                'referer': request.headers.get('Referer'),
                'remote_ip': request.remote_ip,
                'user_agent': request.headers.get('User-Agent')
            })
        finally:
            yield

    return f
