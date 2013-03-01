from __future__ import unicode_literals, print_function, division
from .environment import VEIL_HOME
from .component_map import get_dependent_component_names
from .component_map import list_child_component_names
from .component_map import scan_all_components
from .component_map import get_component_map
from .component_map import get_leaf_component
from .import_collector import list_imports

# static dependency is declared manually assert architecture assertion

def list_expected_static_dependencies():
    file = VEIL_HOME / 'DEP-STATIC'
    code = compile(file.text(), file, 'exec')
    context = {}
    exec code in context
    return context['STATIC_DEPENDENCIES']


def check_static_dependency_integrity():
    scan_all_components()
    check_integrity([], list_expected_static_dependencies())
    for file in (VEIL_HOME / 'src').walk('*.py'):
        module_name = get_module_name(file)
        absolute_imports, relative_imports = list_imports(file.text(), file)
        for relative_import in relative_imports:
            check_relative_import(module_name, relative_import)
        for absolute_import in absolute_imports:
            check_absolute_import(module_name, absolute_import)


def check_relative_import(this_mod, relative_import):
    level, rel, _ = relative_import
    this_comp = get_leaf_component(this_mod)
    if 1 == level:
        base = this_comp
    else:
        base = '.'.join(this_comp.split('.')[:-(level - 1)])
    that_mod = '{}.{}'.format(base, rel)
    that_comp = get_leaf_component(that_mod)
    if this_comp and that_comp and not that_comp.startswith(this_comp):
        print(red('WARNING: {} referenced other component through relative import {}'.format(this_mod, that_mod)))


def check_absolute_import(this_mod, absolute_import):
    if absolute_import in get_component_map():
        return
    that_comp = get_leaf_component(absolute_import)
    this_comp = get_leaf_component(this_mod)
    if this_comp and that_comp and this_comp == that_comp:
        print(red('WARNING: {} should not absolute import {}, use relative import instead'.format(this_mod, absolute_import)))
        return
    if not that_comp:
        return
    if '{}.*'.format(that_comp) == absolute_import:
        return
    print(red('WARNING: {} should absolute import {} using .*'.format(this_mod, absolute_import)))


def _wrap_with(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)

    return inner

red = _wrap_with('31')

def get_module_name(file):
    relpath = (VEIL_HOME / 'src').relpathto(file)
    relpath = relpath.replace('/__init__.py', '')
    relpath = relpath.replace('.py', '')
    relpath = relpath.replace('/', '.')
    return relpath


def check_static_dependency_cycle():
    scan_all_components()
    check_cycle(get_component_map().keys())


def check_cycle(comps, visiting=(), visited=()):
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
        check_cycle(get_dependent_component_names(comp, includes_children=True), next_visiting, visited)
        visited = set(visited)
        visited.add(comp)


def check_integrity(component_names, expected_dependencies):
    if isinstance(expected_dependencies, list):
        return check_component_dependencies(component_names, expected_dependencies, includes_children=True)
    if not isinstance(expected_dependencies, dict):
        raise Exception('do not know how to check architecture for: {}'.format(component_names))
    if component_names:
        if '@' not in expected_dependencies:
            raise Exception('must check component itself dependencies using @: {}'.format(component_names))
        check_component_dependencies(component_names, expected_dependencies.pop('@'), includes_children=False)
    missing_children = list_missing_children(component_names, expected_dependencies.keys())
    if missing_children:
        raise Exception('missing children in DEP-STATIC {}'.format(missing_children))
    for key, value in expected_dependencies.items():
        inner_component_names = list(component_names)
        inner_component_names.append(key)
        check_integrity(inner_component_names, value)


def list_missing_children(component_names, listed_children):
    component_name = ''.join(component_names)
    expected_children = set('{}{}'.format(component_name, child) for child in listed_children)
    actual_descendants = list_child_component_names(component_name)
    actual_children = set(
        child for child in actual_descendants if len(child.split('.')) == len(component_name.split('.')) + 1)
    return actual_children - expected_children


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