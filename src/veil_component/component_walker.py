from __future__ import unicode_literals, print_function, division
import logging
import os.path
import pkgutil
import traceback


LOGGER = logging.getLogger(__name__)

class ComponentInternalVisitor(object):
    def visit_component_start(self, component_name, path, source_code):
        pass

    def visit_component_end(self, component_name, path, source_code):
        pass

    def visit_sub_component(self, component_name, path, source_code):
        pass

    def visit_package_start(self, package_name, path, source_code):
        pass

    def visit_package_end(self, package_name, path, source_code):
        pass

    def visit_module(self, module_name, path, source_code):
        pass


# walk through the internals of a component
# stops at sub component
# passing path/source_code to ModuleCollector
class ComponentWalker(object):
    def walk_component(self, component_name, visitor):
        self.walk_module(component_name, visitor, at_top_level=True)

    def walk_module(self, module_name, visitor, at_top_level=False):
        try:
            module_loader = pkgutil.find_loader(module_name)
        except:
            raise InvalidComponentException('{} not found, {}'.format(module_name, traceback.format_exc()))
        if not module_loader:
            raise InvalidComponentException('{} might be system builtin'.format(module_name))
        path = module_loader.get_filename()
        if not path:
            raise InvalidComponentException('{} does not have source code'.format(module_name))
        source_code = module_loader.get_source() or ''
        if self.is_component(source_code):
            if at_top_level:
                visitor.visit_component_start(module_name, path, source_code)
                self.walk_package(module_name, path, visitor, source_code)
                visitor.visit_component_end(module_name, path, source_code)
            else:
                visitor.visit_sub_component(module_name, path, source_code)
        elif at_top_level:
            raise InvalidComponentException('{} is not component'.format(module_name))
        elif module_loader.is_package(module_name):
            self.walk_package(module_name, path, visitor, source_code)
        else:
            visitor.visit_module(module_name, path, source_code)

    def walk_package(self, module_name, path, visitor, source_code):
        visitor.visit_package_start(module_name, path, source_code)
        module_dir = os.path.dirname(path)
        for child, is_package in pkgutil.get_importer(module_dir).iter_modules():
            self.walk_module('{}.{}'.format(module_name, child), visitor)
            visitor.visit_package_end(module_name, path, source_code)

    def is_component(self, source_code):
        return str('.init_component') in source_code


class InvalidComponentException(Exception):
    pass


class OnceComponentWalker(ComponentWalker):
    def __init__(self):
        super(OnceComponentWalker, self).__init__()
        self.walked_component_names = set()
        self.walked_module_names = set()

    def walk_component(self, component_name, visitor):
        if component_name in self.walked_module_names:
            return
        self.walked_module_names.add(component_name)
        super(OnceComponentWalker, self).walk_component(component_name, visitor)
        self.walked_component_names.add(component_name)

if '__main__' == __name__:
    import sys

    class PrintTrail(ComponentInternalVisitor):
        def visit_sub_component(self, component_name, path, source_code):
            print('[component] {}'.format(component_name))

        def visit_package_start(self, package_name, path, source_code):
            print('[package] {}'.format(package_name))

        def visit_module(self, module_name, path, source_code):
            print('[module] {}'.format(module_name))

    ComponentWalker().walk_component(sys.argv[1], PrintTrail())