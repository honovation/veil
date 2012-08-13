from __future__ import unicode_literals, print_function, division
import contextlib
import importlib
import sys
import traceback
import os

__all__ = [
    'init_component', 'force_get_all_loaded_modules', 'force_import_module', 'get_loading_components',
    'is_dummy_function', 'get_component_dependencies']

encapsulated_modules = {}
components = {}
loading_components = []
errors = {}
dependencies = {}

@contextlib.contextmanager
def init_component(qualified_module_name):
    component = sys.modules[qualified_module_name]
    if loading_components:
        loading_component_name = loading_components[-1].__name__
        if not loading_component_name.startswith(qualified_module_name):
            dependencies.setdefault(loading_component_name, []).append(qualified_module_name)
    if qualified_module_name in components:
        try:
            yield
        except ImportError:
            pass # second time import will reference encapsulated module
        sys.modules[qualified_module_name] = components[qualified_module_name]
        return
    components[component.__name__] = component
    try:
        remove_loaded_components(qualified_module_name)
        loading_components.append(component)
        loader = ComponentLoader(component)
        loader.load_component()
        yield
        if hasattr(component, 'init'):
            component.init()
        loader.encapsulate_loaded_packages_and_modules()
    except:
        raise
    finally:
        loading_components.pop()
        restore_loaded_components()


def get_component_dependencies():
    return dependencies


def remove_loaded_components(qualified_module_name):
    for component_name in components.keys():
        if component_name != qualified_module_name and component_name in sys.modules:
            del sys.modules[component_name]


def restore_loaded_components():
    for component_name, component in components.items():
        sys.modules[component_name] = component


def get_loading_components():
    return loading_components


def force_get_all_loaded_modules():
    all_loaded_modules = {}
    for module_name, module in encapsulated_modules.items():
        all_loaded_modules[module_name] = module
    for module_name, module in sys.modules.items():
        if module and not module_name.startswith('veil.'):
            all_loaded_modules[module_name] = module
    return all_loaded_modules


def force_import_module(module_name):
    try:
        __import__(module_name)
    except ImportError:
        exc_class, exc, tb = sys.exc_info()
    if module_name in encapsulated_modules:
        return encapsulated_modules[module_name]
    if module_name in sys.modules:
        return sys.modules[module_name]
    raise exc_class, exc, tb


class ComponentLoader(object):
    def __init__(self, component):
        self.component = component
        self.modules = []
        self.packages = {}

    def load_component(self):
        self.load_sub_packages_and_modules(self.component)
        self.packages.pop(self.component)

    def load_sub_packages_and_modules(self, package):
        self.load_sub_packages(package)
        self.load_sub_modules(package)

    def load_sub_packages(self, package):
        sub_package_names = find_sub_package_names(package)
        self.packages.setdefault(package, []).extend(sub_package_names)
        for sub_package_name in sub_package_names:
            try:
                sub_package = load_module(package.__name__, sub_package_name)
                if sub_package not in components.values():
                    self.load_sub_packages_and_modules(sub_package)
            except ImportError, e:
                errors.setdefault(loading_components[-1], []).append(e)


    def load_sub_modules(self, package):
        sub_module_names = find_sub_module_names(package)
        self.packages.setdefault(package, []).extend(sub_module_names)
        for sub_module_name in sub_module_names:
            try:
                sub_module = load_module(package.__name__, sub_module_name)
                self.modules.append(sub_module)
            except ImportError, e:
                errors.setdefault(loading_components[-1], []).append(e)

    def encapsulate_loaded_packages_and_modules(self):
        for module in self.modules:
            encapsulated_modules[module.__name__] = module
            sys.modules[module.__name__] = None
        for package in self.packages.keys():
            encapsulated_modules[package.__name__] = package
            sys.modules[package.__name__] = None
            if package.__name__ in components:
                del components[package.__name__]
            for module_name in self.packages[package]:
                if hasattr(package, module_name):
                    delattr(package, module_name)


def find_sub_package_names(package):
    package_file = package.__file__
    package_dir = os.path.dirname(package_file)
    files = os.listdir(package_dir)
    sub_package_names = []
    for file in files:
        if os.path.isdir(os.path.join(package_dir, file)):
            if os.path.exists(os.path.join(package_dir, file, '__init__.py')):
                sub_package_names.append(file)
    return sub_package_names


def find_sub_module_names(package):
    package_file = package.__file__
    package_dir = os.path.dirname(package_file)
    files = os.listdir(package_dir)
    module_names = []
    for file in files:
        if os.path.isfile(os.path.join(package_dir, file)):
            file_base_name, file_ext = os.path.splitext(file)
            if '__init__' == file_base_name:
                continue
            if '__main__' == file_base_name:
                continue
            if file_ext == '.py':
                module_names.append(file_base_name)
    return module_names


def load_module(*module_name_segments):
    qualified_module_name = '.'.join(module_name_segments)
    try:
        return importlib.import_module(qualified_module_name)
    except ImportError, e:
        errors.setdefault(loading_components[-1], []).append(e)
        module = DummyModule(qualified_module_name, e)
        sys.modules[qualified_module_name] = module
        return module
    except:
        print('failed to load {}'.format(loading_components))
        raise


class DummyModule(object):
    def __init__(self, qualified_module_name, error):
        self.__name__ = qualified_module_name
        self.error = error

    def __getattr__(self, item):
        return DummyModuleMember(self, item)


class DummyModuleMember(object):
    def __init__(self, dummy_module, name):
        self.dummy_module = dummy_module
        self.__name__ = name

    def __call__(self, *args, **kwargs):
        error = ImportError(
            'module {} did not load properly, due to {}'.format(
                self.dummy_module.__name__,
                self.dummy_module.error.message))
        if loading_components:
            errors.setdefault(loading_components[-1], []).append(error)
        else:
            raise error


def is_dummy_function(func):
    return isinstance(func, DummyModuleMember)

