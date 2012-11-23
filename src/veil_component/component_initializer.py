from __future__ import unicode_literals, print_function, division
import contextlib
import sys
from .component_walker import ComponentWalker
from .component_walker import ComponentInternalVisitor
from .component_map import scan_component
from .component_logging import configure_logging

loading_component_names = []

@contextlib.contextmanager
def init_component(component_name):
    configure_logging(component_name)
    scan_component(component_name)
    loading_component_names.append(component_name)
    try:
        ComponentWalker().walk_component(component_name, ComponentLoader())
        yield
        loading_component = sys.modules[component_name]
        if hasattr(loading_component, 'init'):
            loading_component.init()
    finally:
        loading_component_names.pop()


def get_loading_component_name():
    return loading_component_names[-1] if loading_component_names else None


class ComponentLoader(ComponentInternalVisitor):
    def visit_module(self, module_name, path, source_code):
        __import__(module_name)

    def visit_package_start(self, package_name, path, source_code):
        __import__(package_name)

    def visit_sub_component(self, component_name, path, source_code):
        __import__(component_name)