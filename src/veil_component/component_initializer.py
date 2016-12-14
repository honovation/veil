from __future__ import unicode_literals, print_function, division
import contextlib
import sys
import time
import logging

from .component_walker import ComponentWalker
from .component_walker import ComponentInternalVisitor
from .component_map import scan_component
from .component_logging import configure_logging

LOGGER = logging.getLogger(__name__)
loading_component_names = []


@contextlib.contextmanager
def init_component(component_name):
    before = time.time()
    scan_component(component_name)
    configure_logging(component_name)
    loading_component_names.append(component_name)
    try:
        ComponentWalker().walk_component(component_name, ComponentLoader())
        yield
        loading_component = sys.modules[component_name]
        if hasattr(loading_component, 'init'):
            loading_component.init()
    finally:
        loading_component_names.pop()
        after = time.time()
        LOGGER.log(logging.DEBUG - 1, 'loaded component: %(component_name)s, took %(elapsed_seconds)s seconds', {
            'component_name': component_name, 'elapsed_seconds': after - before
        })


def get_loading_component_name():
    return loading_component_names[-1] if loading_component_names else None


class ComponentLoader(ComponentInternalVisitor):
    def visit_module(self, module_name, path, source_code):
        # print('v>module> {}'.format(module_name))
        __import__(module_name)

    def visit_package_start(self, package_name, path, source_code):
        # print('v>package> {}'.format(package_name))
        __import__(package_name)

    def visit_sub_component(self, component_name, path, source_code):
        # print('v>component> {}'.format(component_name))
        __import__(component_name)