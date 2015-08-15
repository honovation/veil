from __future__ import unicode_literals, print_function, division
from .environment import VEIL_HOME
from .colors import red
from .component_map import get_dependent_component_names
from .component_map import list_child_component_names
from .component_map import scan_all_components
from .component_map import get_component_map
from .component_map import get_leaf_component
from .import_collector import list_imports

# static dependency is declared manually assert architecture assertion


def list_expected_static_dependencies():
    path = VEIL_HOME / 'DEP-STATIC'
    code = compile(path.text(), path, 'exec')
    context = {}
    exec(code, context)
    return context['STATIC_DEPENDENCIES']


def check_static_dependency_integrity():
    scan_all_components()
    component_map = get_component_map()
    expected_static_dependencies = list_expected_static_dependencies()
    for component_name in expected_static_dependencies:
        if component_name not in component_map:
            raise Exception('Invalid component in DEP-STATIC: {}'.format(component_name))
    check_integrity([], expected_static_dependencies)
    for path in (VEIL_HOME / 'src').walk('*.py'):
        module_name = get_module_name(path)
        absolute_imports, relative_imports = list_imports(path.text(), path)
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
        base = '.'.join(this_mod.split('.')[:-level])
    that_mod = '{}.{}'.format(base, rel)
    that_comp = get_leaf_component(that_mod)
    if this_comp and that_comp:
        if this_comp == that_comp:
            pass # relative import within the same component is fine
        elif that_comp.startswith('{}.'.format(this_comp)):
            # relative import child component is allowed, but do not peek inside it
            # a import a.b is ok
            # a import a.b.c is also ok, as long as a.b exposed it (we did not check if it is exposed or not yet)
            # a import a.b.c.d is not ok, given a.b is a component which already encapsulated internal
            if that_comp != that_mod and that_comp != '.'.join(that_mod.split('.')[:-1]):
                print(red('WARNING: {} should not peek inside other component {}'.format(this_mod, that_mod)))
        else:
            # relative backwards is not allowed, from a.b to a
            # relative import sibling is not allowed, from a.b to a.c
            print(red('WARNING: {} referenced other component through relative import {}'.format(this_mod, that_mod)))


def check_absolute_import(this_mod, absolute_import):
    that_comp = get_leaf_component(absolute_import)
    this_comp = get_leaf_component(this_mod)
    if not this_comp:
        return
    if not that_comp:
        return
    if this_comp == that_comp or that_comp.startswith('{}.'.format(this_comp)):
        # from a to reference any thing below a, such as a.b or a.b.c, always use relative import
        print(red(
            'WARNING: {} should not absolute import {}, use relative import instead'.format(this_mod, absolute_import)))
        return
    if '__' in absolute_import:
        # allow __fixture__ or other special export
        return
    if that_comp == absolute_import:
        # normal import a.b
        return
    if that_comp == '.'.join(absolute_import.split('.')[:-1]):
        # from a.b import c, just reference one level, assume c is exposed from a.b (we did not check it yet)
        return
    # given a.b is component, import a.b.c.d is always not allowed
    print(red('WARNING: {} should not peek inside other component {}'.format(this_mod, absolute_import)))


def get_module_name(path):
    rel_path = (VEIL_HOME / 'src').relpathto(path)
    rel_path = rel_path.replace('/__init__.py', '')
    rel_path = rel_path.replace('.py', '')
    rel_path = rel_path.replace('/', '.')
    return rel_path


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
            actual_dependencies |= calculate_actual_dependencies(child_component_name, includes_children)
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