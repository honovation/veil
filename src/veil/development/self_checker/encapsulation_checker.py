from __future__ import unicode_literals, print_function, division
import veil_component
import importlib

def check_encapsulation():
    component_dependencies = veil_component.get_component_dependencies()
    for component_name, dependencies in component_dependencies.items():
        check_component(component_name, dependencies)


def check_component(component_name, dependencies):
    for dependency in dependencies:
        if dependency.startswith('__future__'):
            continue
        if veil_component.get_root_component(dependency) and component_name.startswith('{}.'.format(dependency)):
            raise Exception('{} should not reference its parent {}'.format(component_name, dependency))
        dependency_parent_component_names = list_parent_component_names(dependency)
        if not dependency_parent_component_names:
            continue # not part of component
        should_depend_on = find_proper_level_to_reference(
            component_name, dependency_parent_component_names, dependency)
        if dependency == should_depend_on:
            continue # use the root component should be fine
        if dependency == '{}.*'.format(should_depend_on):
            continue # use all its public api
        public_apis = importlib.import_module(should_depend_on).__all__
        if dependency in set('{}.{}'.format(should_depend_on, api) for api in public_apis):
            continue # use specific public api
        if '__fixture__' in dependency:
            continue # __fixture__ is also public api
        raise Exception('{} should not peek inside {} via {}'.format(
            component_name, should_depend_on, dependency))


def list_parent_component_names(module_name):
    return [c for c in veil_component.get_component_map().keys() if module_name.startswith('{}.'.format(c))]


def find_proper_level_to_reference(from_component_name, to_component_names, to_module_name):
    for to_component_name in sorted(to_component_names):
        if from_component_name.startswith('{}.'.format(to_component_name)):
            continue # I am a.b, the component is a, and I depend on a.c.d, never reference my parent a to get a.c
        elif from_component_name == to_component_name:
            continue # I am a.b, should not reference internal a.b.c via a.b api
        else:
            return to_component_name # I am a.b, a.c.d is module, and a.c is component, should reference via a.c
    return to_module_name # I am a.b, to_module_name is a.c, a is component, I can only reference a.c directly
