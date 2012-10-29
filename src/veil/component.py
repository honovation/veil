from __future__ import unicode_literals, print_function, division
import contextlib
import importlib
import sys
import traceback
import os
import inspect

__all__ = [
    'init_component', 'force_get_all_loaded_modules', 'force_import_module', 'get_loading_component',
    'is_dummy_module_member', 'get_component_dependencies', 'assert_component_loaded',
    'get_component_of_module', 'is_component_loaded', 'get_loaded_components',
    'add_must_load_module', 'assert_module_is_must_load']

encapsulated_modules = {}
components = {}
loading_components = []
errors = {}
dependencies = {}
must_load_module_names = []

def init_components(component_names):
    for component_name in component_names:
        __import__(component_name)
    for component_name, component in components.items():
        sys.modules[component_name] = component


@contextlib.contextmanager
def init_component(component_name):
    component = sys.modules[component_name]
    if loading_components:
        loading_component_name = loading_components[-1].__name__
        if not loading_component_name.startswith(component_name):
            dependencies.setdefault(loading_component_name, set()).add(component_name)
    if component_name in components:
        try:
            loading_components.append(component)
            yield
        except ImportError:
            pass # second time import will reference encapsulated module
        finally:
            loading_components.pop()
        sys.modules[component_name] = components[component_name]
        return
    components[component.__name__] = component
    try:
        loading_components.append(component)
        remove_loaded_components()
        loader = ComponentLoader(component)
        loader.load_component()
        yield
        if hasattr(component, 'init'):
            component.init()
        loader.encapsulate_loaded_packages_and_modules()
    finally:
        remove_loaded_components()
        loading_components.pop()


def add_must_load_module(qualified_module_name):
    must_load_module_names.append(qualified_module_name)


def assert_module_is_must_load(qualified_module_name):
    if qualified_module_name not in must_load_module_names:
        print('{} is not marked as must load'.format(qualified_module_name))
        os._exit(1)


def assert_component_loaded(component_name, visited_component_names=None):
    if not visited_component_names:
        visited_component_names = [component_name]
    else:
        visited_component_names.append(component_name)
        if component_name in visited_component_names[:-1]:
            raise Exception('circular dependency detected: {}'.format(visited_component_names))
    if component_name in errors:
        print(errors[component_name][0])
        #        for error in errors[component_name]:
        #            print(error)
        raise Exception('component {} did not load successfully'.format(component_name))
    for dependency in dependencies.get(component_name, ()):
        assert_component_loaded(dependency, list(visited_component_names))


def is_component_loaded(component_name, visited_component_names=None):
    if not visited_component_names:
        visited_component_names = [component_name]
    else:
        visited_component_names.append(component_name)
        if component_name in visited_component_names[:-1]:
            raise Exception('circular dependency detected: {}'.format(visited_component_names))
    if component_name in errors:
        return False
    for dependency in dependencies.get(component_name, ()):
        if not is_component_loaded(dependency, list(visited_component_names)):
            return False
    return True


def get_component_of_module(module_name):
    matched_component_names = []
    for component_name in components:
        if module_name.startswith(component_name):
            matched_component_names.append(component_name)
    return max(matched_component_names)


def get_component_dependencies():
    return dependencies


def remove_loaded_components():
    loaded_components = set(components.values())
    loaded_components = loaded_components - set(loading_components)
    for loaded_component in loaded_components:
        if loaded_component.__name__ in sys.modules:
            del sys.modules[loaded_component.__name__]


def get_loading_component():
    if loading_components:
        return loading_components[-1]
    else:
        return None


def record_error(message=None):
    message = message or traceback.format_exc()
    errors.setdefault(loading_components[-1].__name__, []).append(message)


def force_get_all_loaded_modules():
    all_loaded_modules = {}
    for module_name, module in encapsulated_modules.items():
        all_loaded_modules[module_name] = module
    for module_name, module in sys.modules.items():
        if module and not module_name.startswith('veil.'):
            all_loaded_modules[module_name] = module
    return all_loaded_modules


def get_loaded_components():
    return components


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
                record_error()


    def load_sub_modules(self, package):
        sub_module_names = find_sub_module_names(package)
        self.packages.setdefault(package, []).extend(sub_module_names)
        for sub_module_name in sub_module_names:
            try:
                sub_module = load_module(package.__name__, sub_module_name)
                self.modules.append(sub_module)
            except ImportError, e:
                record_error()

    def encapsulate_loaded_packages_and_modules(self):
        for module in self.modules:
            if not(self.is_public_module(module.__name__.split('.')[-1])):
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

    def is_public_module(self, module_name):
        return module_name.startswith('__') and module_name.endswith('__')


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
        if qualified_module_name in must_load_module_names:
            print('failed to load {}'.format(loading_components))
            traceback.print_exc()
            os._exit(1)
        record_error()
        module = DummyModule(qualified_module_name, e)
        sys.modules[qualified_module_name] = module
        return module
    except:
        print('failed to load {}'.format(loading_components))
        traceback.print_exc()
        os._exit(1)


class DummyModule(object):
    def __init__(self, qualified_module_name, error):
        self.__name__ = qualified_module_name
        self.error = error

    @property
    def __file__(self):
        raise Exception('can not get __file__ from DummyModule {}'.format(self.__name__))

    def __getattr__(self, item):
        return DummyModuleMember(self, item)

    def __repr__(self):
        return '<DummyModule: {}>'.format(self.__name__)


class DummyModuleMember(object):
    def __init__(self, dummy_module, name):
        self.dummy_module = dummy_module
        self.__name__ = name

    def __call__(self, func=None, *args, **kwargs):
        error = ImportError(
            'module {} did not load properly, due to {}'.format(
                self.dummy_module.__name__,
                self.dummy_module.error.message))
        if loading_components:
            record_error(error.message)
            return func if inspect.isfunction(func) else self
        else:
            raise error

    def __repr__(self):
        return '<DummyModuleMember: {}.{}>'.format(self.dummy_module.__name__, self.__name__)


def is_dummy_module_member(func):
    return isinstance(func, DummyModuleMember)

