from __future__ import unicode_literals, print_function, division
from .dependency_collector import list_dependencies
from .dependency_collector import OnceComponentWalker

component_map = {}
component_walker = OnceComponentWalker()

def add_component(component_name):
    if component_name in component_map:
        return
    components_dependencies = list_dependencies(component_name, component_walker.walk_component)
    component_names = set(component_walker.walked_component_names)
    component_map.update({k: filter_dependent_component_names(k, component_names, v)
                          for k, v in components_dependencies.items()})


def get_component_map():
    return dict(component_map)


def get_transitive_dependencies(component_name):
    dependencies = list()
    collect_transitive_dependencies(component_name, dependencies)
    return dependencies


def collect_transitive_dependencies(component_name, dependencies):
    direct_dependencies = get_component_map().get(component_name, ())
    sub_component_names = [c for c in component_walker.walked_component_names
                           if c.startswith('{}.'.format(component_name))]
    for dependency in set(direct_dependencies).union(set(sub_component_names)):
        if dependency not in dependencies:
            dependencies.append(dependency)
            collect_transitive_dependencies(dependency, dependencies)


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

