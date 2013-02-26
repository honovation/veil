from __future__ import unicode_literals, print_function, division
import veil_component
from veil.environment import *
from veil.backend.web_service import check_web_service_dependencies
from veil.backend.database.client import check_database_dependencies
from veil_component import *

architecture_checkers = {
    'web-service': check_web_service_dependencies, # TODO, not checked yet
    'database': check_database_dependencies # TODO, not checked yet
}

def check_architecture():
    for component_name in list_all_components():
        scan_component(component_name)
#    check_circular_dependency(get_component_map().keys())
    architecture = get_application_architecture()
    for component_name, value in architecture.items():
        check_component_architecture([component_name], value)


def check_circular_dependency(comps, visiting=(), visited=()):
# this function is slow, as it need to go through all paths of the graph
# if we reach one node and stop searching then enter same node from another path,
# cycle might still form from another path
# it can be multi-threaded, but not a trivial job, refer to:
# http://stackoverflow.com/questions/10697355/multithreaded-algo-for-cycle-detection-in-a-directed-graph
    for comp in comps:
        if comp in visiting:
            raise Exception('found circular dependency {}=>{}'.format('=>'.join(visiting), comp))
        if comp in visited:
            continue
        next_visiting = set(visiting)
        next_visiting.add(comp)
        check_circular_dependency(get_dependent_component_names(comp, includes_children=True), next_visiting, visited)
        visited = set(visited)
        visited.add(comp)


def check_component_architecture(component_names, architecture):
    if isinstance(architecture, list):
        return check_component_dependencies(component_names, architecture, includes_children=True)
    if not isinstance(architecture, dict):
        raise Exception('do not know how to check architecture for: {}'.format(component_names))
    if '@' not in architecture:
        raise Exception('must check component itself dependencies using @: {}'.format(component_names))
    check_component_dependencies(component_names, architecture.pop('@'), includes_children=False)
    for key, value in architecture.items():
        inner_component_names = list(component_names)
        inner_component_names.append(key)
        inner_architecture = value
        check_component_architecture(inner_component_names, inner_architecture)


def check_component_dependencies(component_names, expected_dependencies, includes_children=False):
    this_component_name = ''.join(component_names)
    parent_component_name = ''.join(component_names[:-1])
    expected_dependencies = make_component_dependencies_absolute(parent_component_name, expected_dependencies)
    actual_dependencies = calculate_actual_dependencies(this_component_name, includes_children=includes_children)
    actual_dependencies = filter_dependencies(actual_dependencies, 'veil', 'veil.', '{}.'.format(this_component_name))
    unexpected_dependencies = actual_dependencies - set(expected_dependencies)
    if unexpected_dependencies:
        raise Exception('{} should not reference {}'.format(this_component_name, unexpected_dependencies))
    unreal_dependencies = set(expected_dependencies) - actual_dependencies
    if unreal_dependencies:
        raise Exception('{} did not reference {}'.format(this_component_name, unreal_dependencies))


def calculate_actual_dependencies(this_component_name, includes_children):
    actual_dependencies = veil_component.get_dependent_component_names(this_component_name)
    if includes_children:
        children = list_child_component_names(this_component_name)
        for child_component_name in children:
            actual_dependencies = actual_dependencies.union(calculate_actual_dependencies(child_component_name, includes_children))
    return actual_dependencies


def make_component_dependencies_absolute(parent_component_name, dependencies):
    absolute_dependencies = set()
    for dependency in dependencies:
        if dependency.startswith('.'):
            absolute_dependencies.add('{}{}'.format(parent_component_name, dependency))
        else:
            absolute_dependencies.add(dependency)
    return absolute_dependencies


def filter_dependencies(dependencies, *white_list):
    white_list = set(white_list)
    filtered_dependencies = set()
    for dependency in dependencies:
        if any(dependency.startswith(prefix) for prefix in white_list):
            continue
        filtered_dependencies.add(dependency)
    return filtered_dependencies

