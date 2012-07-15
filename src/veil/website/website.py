from __future__ import unicode_literals, print_function, division
from logging import getLogger
import signal
from jinja2.loaders import FileSystemLoader
from tornado.ioloop import IOLoop
from sandal.option import register_option
from sandal.template import get_template_environment
from sandal.template import register_template_loader
from veil.http import *
from .locale import install_translations
from .routing import  RoutingHTTPHandler, get_routes
from .static_file import clear_static_file_hashes
from . import reloading

LOGGER = getLogger(__name__)
get_port = register_option('http', 'port', int)
get_host = register_option('http', 'host')
get_processes_count = register_option('http', 'processes_count', int)
get_website_type = register_option('website', 'type')

def start_website(website, website_type=None, port=None, host=None, processes_count=None, prevents_xsrf=True, **kwargs):
    website_type = website_type or get_website_type() or 'development'
    port = port or get_port() or 80
    host = host or get_host() or 'localhost'
    processes_count = processes_count or get_processes_count() or 1
    LOGGER.info(
        'starting {} website {} at port {} with {} process(es)...'.format(website_type, website, port, processes_count))
    io_loop = IOLoop.instance()
    if 'development' == website_type:
        reloading.start(io_loop)
    http_handler = create_website_http_handler(website, website_type=website_type, **kwargs)
    http_server = create_http_server(http_handler, io_loop=io_loop, prevents_xsrf=prevents_xsrf)
    http_server.bind(port, host)
    http_server.start(processes_count)
    LOGGER.info('started {} website'.format(website))
    signal.signal(signal.SIGINT, lambda *args: io_loop.stop())
    io_loop.start()


def create_website_http_handler(website, website_type=None, context_managers=(),
                                master_template_dir=None, locale_provider=None):
    website_type = website_type or get_website_type()
    locale_provider = locale_provider or (lambda : None)
    all_context_managers = [create_stack_context(install_translations, locale_provider)]
    if master_template_dir:
        register_template_loader('master', FileSystemLoader(master_template_dir))
    if 'development' == website_type:
        all_context_managers.append(create_stack_context(
            clear_static_file_hashes
        ))
        get_template_environment().cache = {}
    all_context_managers.extend(context_managers)
    return RoutingHTTPHandler(get_routes(website), all_context_managers)