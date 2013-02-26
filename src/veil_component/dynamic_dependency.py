from __future__ import unicode_literals, print_function, division
import os
from .environment import VEIL_HOME

DEP_DYNAMIC_RECORDED = VEIL_HOME / 'DEP-DYNAMIC-RECORDED'
is_recording = False
dynamic_dependencies = None
loaded_providers = set()

def start_recording_dynamic_dependencies():
    global is_recording
    is_recording = True

def record_dynamic_dependency_provider(component_name, dynamic_dependency_type, dynamic_dependency_key):
    if should_record(component_name):
        line = '{}<={}:{}\n'.format(component_name, dynamic_dependency_type, dynamic_dependency_key)
        record_line(line)


def record_dynamic_dependency_consumer(component_name, dynamic_dependency_type, dynamic_dependency_key):
    if should_record(component_name):
        line = '{}=>{}:{}\n'.format(component_name, dynamic_dependency_type, dynamic_dependency_key)
        record_line(line)


def load_dynamic_dependency_providers(dynamic_dependency_type, dynamic_dependency_key):
    if (dynamic_dependency_type, dynamic_dependency_key) in loaded_providers:
        return []
    loaded_providers.add((dynamic_dependency_type, dynamic_dependency_key))
    for component_name in list_dynamic_dependency_providers(dynamic_dependency_type, dynamic_dependency_key):
        __import__(component_name)


def list_dynamic_dependency_providers(dynamic_dependency_type, dynamic_dependency_key):
    providers, consumers = list_dynamic_dependencies()
    return providers.get((dynamic_dependency_type, dynamic_dependency_key)) or []


def should_record(component_name):
    if not component_name:
        return False
    if not is_recording:
        return False
    return True


def list_dynamic_dependencies():
    global dynamic_dependencies
    if not dynamic_dependencies:
        providers = {}
        consumers = {}
        if not DEP_DYNAMIC_RECORDED:
            return {}, {}
        if not os.path.exists(DEP_DYNAMIC_RECORDED):
            return {}, {}
        with open(DEP_DYNAMIC_RECORDED, 'r') as f:
            for line in f.readlines():
                line = line.decode('utf8')
                line = line.strip()
                if not line:
                    continue
                if '=>' in line:
                    consumer, type_and_key = line.split('=>')
                    consumers.setdefault(consumer, set()).add(tuple(type_and_key.split(':')))
                elif '<=' in line:
                    provider, type_and_key = line.split('<=')
                    providers.setdefault(tuple(type_and_key.split(':')), set()).add(provider)
                else:
                    raise Exception('invalid dynamic dependencies file: {}\n{}'.format(file, line))
        dynamic_dependencies = providers, consumers
    return dynamic_dependencies


def record_line(line):
    line = line.encode('utf8')
    with open(DEP_DYNAMIC_RECORDED) as f:
        if line in f.read():
            return
    with open(DEP_DYNAMIC_RECORDED, 'a') as f:
        f.write(line)