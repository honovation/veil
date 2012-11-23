import logging
import os
import sys

configured_component_names = set()

def configure_logging(component_name):
    if component_name in configured_component_names:
        return
    for configured_component_name in configured_component_names:
        if component_name.startswith('{}.'.format(configured_component_name)):
            return
        if configured_component_name.startswith('{}.'.format(component_name)):
            print('component logging init order is wrong: {}, {}'.format(component_name, configured_component_name))
    configured_component_names.add(component_name)
    handler = logging.StreamHandler(os.fdopen(sys.stderr.fileno(), 'w', 0))
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger = logging.getLogger(component_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)