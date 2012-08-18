from __future__ import unicode_literals, print_function, division
from logging import getLogger
from jinja2.loaders import FileSystemLoader
from tornado.ioloop import IOLoop
from veil.frontend.template import *
from ..tornado import *
from ..locale import *
from ..routing import  *
from ..static_file import *
from ..xsrf import *
from ..reloading import *
from .option import get_website_option

LOGGER = getLogger(__name__)


def start_test_website(website, **kwargs):
    http_handler = create_website_http_handler(website, **kwargs)
    secure_cookie_salt = get_website_option(website, 'secure_cookie_salt')
    if secure_cookie_salt:
        set_secure_cookie_salt(secure_cookie_salt)
    return start_test_http_server(
        http_handler,
        host=get_website_option(website, 'host'),
        port=get_website_option(website, 'port'))


def start_website(website, **kwargs):
    io_loop = IOLoop.instance()
    if get_website_option(website, 'reloads_module'):
        start_reloading_check(io_loop)
    http_handler = create_website_http_handler(website, **kwargs)
    io_loop.add_callback(lambda: LOGGER.info('started website {}'.format(website)))
    secure_cookie_salt = get_website_option(website, 'secure_cookie_salt')
    if secure_cookie_salt:
        set_secure_cookie_salt(secure_cookie_salt)
    start_http_server(
        http_handler, io_loop=io_loop,
        host=get_website_option(website, 'host'),
        port=get_website_option(website, 'port'),
        processes_count=get_website_option(website, 'processes_count'))


def create_website_http_handler(website, additional_context_managers=(), locale_provider=None):
    locale_provider = locale_provider or (lambda: None)
    master_template_directory = get_website_option(website, 'master_template_directory')
    if master_template_directory:
        register_template_loader('master', FileSystemLoader(master_template_directory))
    context_managers = [create_stack_context(install_translations, locale_provider)]
    if get_website_option(website, 'prevents_xsrf'):
        context_managers.append(prevent_xsrf)
    if get_website_option(website, 'recalculates_static_file_hash'):
        context_managers.append(clear_static_file_hashes)
    if get_website_option(website, 'clears_template_cache'):
        context_managers.append(clear_template_caches)
    context_managers.extend(additional_context_managers)
    return RoutingHTTPHandler(get_routes(website), context_managers)