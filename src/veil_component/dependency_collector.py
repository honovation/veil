from __future__ import unicode_literals, print_function, division
import logging
from .component_walker import ComponentInternalVisitor
from .component_walker import InvalidComponentException
from .component_walker import ComponentWalker
from .import_collector import list_imports

LOGGER = logging.getLogger(__name__)

def list_dependencies(component_name, walk_component=None):
    walk_component = walk_component or OnceComponentWalker().walk_component
    dependency_collector = DependencyCollector(component_name, walk_component)
    walk_component(component_name, dependency_collector)
    return dependency_collector.component_dependencies


class OnceComponentWalker(ComponentWalker):
    def __init__(self):
        super(OnceComponentWalker, self).__init__()
        self.walked_component_names = set()
        self.walked_module_names = set()

    def walk_component(self, component_name, visitor):
        if component_name in self.walked_module_names:
            return
        self.walked_module_names.add(component_name)
        try:
            super(OnceComponentWalker, self).walk_component(component_name, visitor)
            self.walked_component_names.add(component_name)
        except InvalidComponentException:
            pass


class DependencyCollector(ComponentInternalVisitor):
    def __init__(self, component_name, walk_component):
        super(DependencyCollector, self).__init__()
        self.component_name = component_name
        self.walk_component = walk_component

    def visit_top_level_component(self, component_name, path, source_code):
        if '.' in component_name:
            self.collect_others_dependencies(component_name[:component_name.rfind('.')])

    def visit_sub_component(self, component_name, path, source_code):
        self.collect_others_dependencies(component_name)

    def visit_package_start(self, package_name, path, source_code):
        absolute_imports, relative_imports = list_imports(source_code)
        self.collect_own_dependencies(absolute_imports)

    def visit_module(self, module_name, path, source_code):
        absolute_imports, relative_imports = list_imports(source_code)
        self.collect_own_dependencies(absolute_imports)

    def collect_own_dependencies(self, more_dependencies):
        more_dependencies = set(more_dependencies)
        existing_dependencies = self.component_dependencies.get(self.component_name, set())
        self.component_dependencies[self.component_name] = existing_dependencies.union(more_dependencies)
        new_dependencies = more_dependencies - existing_dependencies
        for dependency in new_dependencies:
            self.collect_others_dependencies(dependency)

    def collect_others_dependencies(self, component_name):
        dependency_collector = DependencyCollector(component_name, self.walk_component)
        try:
            self.walk_component(component_name, dependency_collector)
            self.component_dependencies.update(dependency_collector.component_dependencies)
        except:
            LOGGER.error('failed to collect dependencies in {} from {}'.format(
                self.component_name, component_name))
            raise

    @property
    def component_dependencies(self):
        if not hasattr(self, '_component_dependencies'):
            self._component_dependencies = {}
        return self._component_dependencies


if '__main__' == __name__:
    import sys
    import pprint

    logging.basicConfig(level=logging.DEBUG)
    pprint.pprint(list_dependencies(sys.argv[1]))
