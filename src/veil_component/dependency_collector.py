from __future__ import unicode_literals, print_function, division
import logging
from .component_walker import ComponentInternalVisitor
from .component_walker import OnceComponentWalker
from .component_walker import InvalidComponentException
from .import_collector import list_imports

LOGGER = logging.getLogger(__name__)

def list_dependencies(component_name, walk_component=None, recursive=False):
    walk_component = walk_component or OnceComponentWalker().walk_component
    dependency_collector = DependencyCollector(component_name, walk_component, recursive=recursive)
    walk_component(component_name, dependency_collector)
    return dependency_collector.component_dependencies


class DependencyCollector(ComponentInternalVisitor):
    def __init__(self, component_name, walk_component, recursive):
        super(DependencyCollector, self).__init__()
        self.component_name = component_name
        self.walk_component = walk_component
        self.recursive = recursive

    def visit_component_start(self, component_name, path, source_code):
        if '.' in component_name:
            self.collect_others_dependencies(component_name[:component_name.rfind('.')])

    def visit_sub_component(self, component_name, path, source_code):
        self.collect_others_dependencies(component_name)

    def visit_package_start(self, package_name, path, source_code):
        absolute_imports, relative_imports = list_imports(source_code, path)
        self.collect_own_dependencies(absolute_imports)

    def visit_module(self, module_name, path, source_code):
        absolute_imports, relative_imports = list_imports(source_code, path)
        self.collect_own_dependencies(absolute_imports)

    def collect_own_dependencies(self, more_dependencies):
        more_dependencies = set(more_dependencies)
        existing_dependencies = self.component_dependencies.get(self.component_name, set())
        self.component_dependencies[self.component_name] = existing_dependencies.union(more_dependencies)
        new_dependencies = more_dependencies - existing_dependencies
        for dependency in new_dependencies:
            self.collect_others_dependencies(dependency)

    def collect_others_dependencies(self, component_name):
        if not self.recursive:
            return
        dependency_collector = DependencyCollector(component_name, self.walk_component, True)
        try:
            self.walk_component(component_name, dependency_collector)
            self.component_dependencies.update(dependency_collector.component_dependencies)
        except InvalidComponentException:
            pass

    @property
    def component_dependencies(self):
        if not hasattr(self, '_component_dependencies'):
            self._component_dependencies = {}
        return self._component_dependencies


if '__main__' == __name__:
    import sys
    import pprint

    logging.basicConfig(level=logging.DEBUG)
    pprint.pprint(list_dependencies(sys.argv[1], recursive=True)[sys.argv[1]])
