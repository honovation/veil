from __future__ import unicode_literals, print_function, division
from logging import getLogger
from jinja2.loaders import FileSystemLoader
from tornado.ioloop import IOLoop
from veil.frontend.template import *
from veil.environment.setting import *
from ..tornado import *
from ..locale import *
from ..routing import  *
from ..static_file import *
from ..xsrf import *
from ..reloading import *

LOGGER = getLogger(__name__)
get_reloads_module = register_option('website', 'reloads_module', bool, default=True)
get_recalculates_static_file_hash = register_option('website', 'recalculates_static_file_hash', bool, default=True)
get_clears_template_cache = register_option('website', 'clears_template_cache', bool, default=True)
get_prevents_xsrf = register_option('website', 'prevents_xsrf', bool, default=True)
get_master_template_directory = register_option('website', 'master_template_directory', default='')

def start_test_website(website, **kwargs):
    http_handler = create_website_http_handler(website, **kwargs)
    return start_test_http_server(handler=http_handler)


def start_website(website, **kwargs):
    io_loop = IOLoop.instance()
    if get_reloads_module():
        start_reloading_check(io_loop)
    http_handler = create_website_http_handler(website, **kwargs)
    io_loop.add_callback(lambda: LOGGER.info('started website {}'.format(website)))
    start_http_server(http_handler, io_loop=io_loop)


def create_website_http_handler(website, additional_context_managers=(), prevents_xsrf=None, locale_provider=None):
    locale_provider = locale_provider or (lambda: None)
    if get_master_template_directory():
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