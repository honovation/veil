from __future__ import unicode_literals, print_function, division
import logging
from .dependency_collector import list_dependencies
from .dependency_collector import OnceComponentWalker
from .environment import VEIL_HOME
from .environment import VEIL_FRAMEWORK_HOME

component_map = {}  # component name => set(dependent component names)
component_dependencies = {}  # component name => set(dependent package)
component_walker = OnceComponentWalker()


def scan_all_components():
    for component_name in list_all_components():
        scan_component(component_name)

def scan_component(component_name):
    if component_name in component_map:
        return
    dependencies = list_dependencies(component_name, component_walker.walk_component, recursive=True)
    component_dependencies.update(dependencies)
    component_names = set(component_walker.walked_component_names)
    component_map.update({k: filter_dependent_component_names(k, component_names, v) for k, v in dependencies.items()})


def get_dependent_component_names(component_name, includes_children=False):
    direct = component_map.get(component_name, set())
    if not includes_children:
        return direct
    return direct | list_child_component_names(component_name)


def list_child_component_names(component_name):
    return set(c for c in component_map if c.startswith('{}.'.format(component_name)))


def get_component_map():
    return component_map


def get_component_dependencies():
    return component_dependencies


def get_transitive_dependencies(component_name):
    dependencies = set()
    collect_transitive_dependencies(component_name, dependencies)
    return dependencies


def collect_transitive_dependencies(component_name, dependencies):
    direct_dependent_component_names = get_component_map().get(component_name, set())
    dependent_component_names = direct_dependent_component_names | set(c for c in component_map if c.startswith('{}.'.format(component_name)))
    for dependent_component_name in dependent_component_names:
        if dependent_component_name not in dependencies:
            dependencies.add(dependent_component_name)
            collect_transitive_dependencies(dependent_component_name, dependencies)


def filter_dependent_component_names(my_component_name, component_names, dependencies):
    dependent_component_names = set()
    for component_name in component_names:
        for dependency in dependencies:
            if my_component_name == dependency or dependency.startswith('{}.'.format(my_component_name)):
                continue # exclude myself and my children
            if component_name == dependency or dependency.startswith('{}.'.format(component_name)):
                if my_component_name.startswith('{}.'.format(component_name)):
                    continue # exclude my parents
                dependent_component_names.add(component_name)
    return dependent_component_names


def get_root_component(module_name):
    matched_component_names = []
    for component_name in component_map:
        if module_name == component_name or module_name.startswith('{}.'.format(component_name)):
            matched_component_names.append(component_name)
    if not matched_component_names:
        return None
    return min(matched_component_names)


def get_leaf_component(module_name):
    matched_component_names = []
    for component_name in component_map:
        if module_name == component_name or module_name.startswith('{}.'.format(component_name)):
            matched_component_names.append(component_name)
    if not matched_component_names:
        return None
    return max(matched_component_names)


def load_all_components():
    all_components = list_all_components()
    for component_name in all_components:
        __import__(component_name)
    return all_components


def list_all_components():
    from veil_component import search_components

    all_components = search_components(VEIL_HOME / 'src')
    if VEIL_FRAMEWORK_HOME:
        all_components |= search_components(VEIL_FRAMEWORK_HOME / 'src')
    return all_components


if '__main__' == __name__:
    logging.basicConfig(level=logging.DEBUG)
    scan_component('ljmall')
    print(get_transitive_dependencies('ljmall'))