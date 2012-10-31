from __future__ import unicode_literals, print_function, division
import veil_component

THRESHOLD = 1330
GOAL = 500

def check_loc():
    component_locs = {}
    sub_component_locs = {}
    for component_name in veil_component.get_loaded_components().keys():
        component_locs[component_name] = calculate_component_loc(component_name)
    for component_name in sorted(component_locs.keys()):
        sub_component_locs[component_name] = calculate_sub_component_loc(component_locs, component_name)
    for component_name in sorted(component_locs.keys()):
        component_locs[component_name] -= sub_component_locs.get(component_name, 0)
        own_loc = component_locs[component_name]
        if own_loc > THRESHOLD:
            raise Exception('{} contains {} lines of code, extract component out!'.format(component_name, own_loc))
    max_loc = max(component_locs.values())
    if THRESHOLD > GOAL and THRESHOLD - max_loc > 50:
        raise Exception('Threshold can be reduced to {} now', max_loc)


def calculate_sub_component_loc(component_locs, parent_component_name):
    prefix = '{}.'.format(parent_component_name)
    sub_component_loc = 0
    last_component_name = None
    for component_name in sorted(component_locs.keys()):
        if component_name == parent_component_name:
            continue
        if last_component_name and '{}.'.format(last_component_name) in component_name:
            continue
        if component_name.startswith(prefix):
            sub_component_loc += component_locs[component_name]
            last_component_name = component_name
    return sub_component_loc


def calculate_component_loc(component_name):
    prefix = '{}.'.format(component_name)
    loc = 0
    for module_name, module in veil_component.force_get_all_loaded_modules().items():
        if module_name.startswith(prefix):
            loc += get_loc(module.__file__.replace('.pyc', '.py'))
    return loc


def get_loc(file_path):
    with open(file_path) as f:
        return len(f.readlines())