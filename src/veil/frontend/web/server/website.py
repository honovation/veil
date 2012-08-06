from __future__ import unicode_literals, print_function, division
from logging import getLogger
import signal
from jinja2.loaders import FileSystemLoader
from tornado.ioloop import IOLoop
from veil.frontend.template import *
from veil.frontend.web.tornado import *
from veil.environment.runtime import *
from .locale import install_translations
from .routing import  RoutingHTTPHandler, get_routes
from .static_file import clear_static_file_hashes
from .xsrf import prevent_xsrf
from . import reloading

LOGGER = getLogger(__name__)
get_reloads_module = register_option('website', 'reloads_module', bool)
get_recalculates_static_file_hash = register_option('website', 'recalculates_static_file_hash', bool)
get_clears_template_cache = register_option('website', 'clears_template_cache', bool)
get_prevents_xsrf = register_option('website', 'prevents_xsrf', bool)
get_master_template_directory = register_option('website', 'master_template_directory')

def start_test_website(website, **kwargs):
    http_handler = create_website_http_handler(website, **kwargs)
    return start_test_http_server(handler=http_handler)


def start_website(website, **kwargs):
    io_loop = IOLoop.instance()
    if get_reloads_module():
        reloading.start(io_loop)
    http_handler = create_website_http_handler(website, **kwargs)
    io_loop.add_callback(lambda: print('!!!'))
    start_http_server(http_handler, io_loop=io_loop)


def create_website_http_handler(website, additional_context_managers=(), prevents_xsrf=None, locale_provider=None):
    locale_provider = locale_provider or (lambda: None)
    register_template_loader('master', FileSystemLoader(get_master_template_directory()))
    context_managers = [create_stack_context(install_translations, locale_provider)]
    prevents_xsrf = prevents_xsrf if prevents_xsrf is not None else get_prevents_xsrf()
    if prevents_xsrf:
        context_managers.append(prevent_xsrf)
    if get_recalculates_static_file_hash():
        context_managers.append(clear_static_file_hashes)
    if get_clears_template_cache():
        context_managers.append(clear_template_caches)
    context_managers.extend(additional_context_managers)
    return RoutingHTTPHandler(get_routes(website), context_managers)