from __future__ import unicode_literals, print_function, division
import os.path
import veil_component
import sys

WHITE_LIST = {'veil.utility.path', 'veil.frontend.web.tornado'} # copied from somewhere
THRESHOLD = 800
GOAL = 500

def check_loc():
    component_files = {}
    for module_name, module in sys.modules.items():
        component_name = veil_component.get_leaf_component(module_name)
        if component_name and hasattr(module, '__file__'):
            module_file = module.__file__.replace('.pyc', '.py')
            module_loc = get_loc(module_file)
            component_files.setdefault(component_name, []).append((module_file, module_loc))
    max_loc = 0
    for component_name in sorted(component_files.keys()):
        files = component_files[component_name]
        component_loc = sum(f[1] for f in files)
        if component_name not in WHITE_LIST:
            max_loc = max(component_loc, max_loc)
            if component_loc > THRESHOLD:
                raise Exception('{} contains {} lines of code, extract component out!\n{}'.format(
                    component_name, component_loc, '\n'.join([str(f) for f in files])))
    if THRESHOLD > GOAL and THRESHOLD - max_loc > 50:
        raise Exception('Threshold can be reduced to {} now', max_loc)


def get_loc(file_path):
    if not os.path.exists(file_path):
        return 0
    with open(file_path) as f:
        return len(f.readlines())