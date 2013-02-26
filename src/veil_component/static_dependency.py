from __future__ import unicode_literals, print_function, division
from .environment import VEIL_HOME
from .component_map import get_dependent_component_names
from .component_map import list_all_components
from .component_map import list_child_component_names
from .component_map import scan_component
from .component_map import get_component_map

# static dependency is declared manually assert architecture assertion

def list_static_dependencies():
    file = VEIL_HOME / 'DEP-STATIC'
    code = compile(file.text(), file, 'exec')
    context = {}
    exec code in context
    return context['STATIC_DEPENDENCIES']


def check_static_dependency_integrity():
    for component_name in list_all_components():
        scan_component(component_name)
    check_circular_dependency(get_component_map().keys())
    check_component_static_dependency([], list_static_dependencies())


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


def check_component_static_dependency(component_names, expected_dependencies):
    if isinstance(expected_dependencies, list):
        return check_component_dependencies(component_names, expected_dependencies, includes_children=True)
    if not isinstance(expected_dependencies, dict):
        raise Exception('do not know how to check architecture for: {}'.format(component_names))
    if component_names:
        if '@' not in expected_dependencies:
            raise Exception('must check component itself dependencies using @: {}'.format(component_names))
        check_component_dependencies(component_names, expected_dependencies.pop('@'), includes_children=False)
    for key, value in expected_dependencies.items():
        inner_component_names = list(component_names)
        inner_component_names.append(key)
        check_component_static_dependency(inner_component_names, value)


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
    actual_dependencies = get_dependent_component_names(this_component_name)
    if includes_children:
        children = list_child_component_names(this_component_name)
        for child_component_name in children:
            actual_dependencies = actual_dependencies.union(
                calculate_actual_dependencies(child_component_name, includes_children))
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