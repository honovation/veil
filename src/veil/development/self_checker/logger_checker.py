from __future__ import unicode_literals, print_function, division
import logging
import sys
import veil_component

LOGGER = logging.getLogger(__name__)

def check_logger():
    wrong_usages_count = 0
    for module_name, module in sys.modules.items():
        component_name = veil_component.get_leaf_component(module_name)
        if component_name and hasattr(module, '__file__'):
            module_file = module.__file__.replace('.pyc', '.py')
            if check_file(module_file):
                wrong_usages_count += 1
    if wrong_usages_count:
        raise Exception('Loggers were not being used correctly, in {} places'.format(wrong_usages_count))

def check_file(file_path):
    failed = False
    with open(file_path) as f:
        for line_no, line in enumerate(f.readlines()):
            used_format = str('.format(') in line
            used_format_arg = str('{}') in line
            if str('LOGGER') in line and (used_format or used_format_arg):
                LOGGER.error('logger used in the wrong way: at %(file_path)s:%(line_no)s, we do not need to format log message as itself is a format', {
                    'file_path': file_path,
                    'line_no': line_no + 1
                })
                failed = True
    return failed
