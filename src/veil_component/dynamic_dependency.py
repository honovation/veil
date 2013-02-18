from __future__ import unicode_literals, print_function, division
import os

dynamic_dependencies_file = None
is_recording = False
cached_content = None
dynamic_dependencies = None
loaded_providers = set()

def set_dynamic_dependencies_file(file):
    global dynamic_dependencies_file
    dynamic_dependencies_file = file


def start_recording_dynamic_dependencies():
    global is_recording
    global cached_content
    is_recording = True
    if os.path.exists(dynamic_dependencies_file):
        with open(dynamic_dependencies_file, 'r') as f:
            cached_content = set(f.readlines())
    else:
        cached_content = set()


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
        return
    loaded_providers.add((dynamic_dependency_type, dynamic_dependency_key))
    providers, consumers = list_dynamic_dependencies()
    for component_name in providers.get((dynamic_dependency_type, dynamic_dependency_key)) or []:
        __import__(component_name)


def should_record(component_name):
    if not component_name:
        return False
    if not is_recording:
        return False
    if not dynamic_dependencies_file:
        return False
    return True


def list_dynamic_dependencies():
    global dynamic_dependencies
    if not dynamic_dependencies:
        providers = {}
        consumers = {}
        if not dynamic_dependencies_file:
            return {}, {}
        if not os.path.exists(dynamic_dependencies_file):
            return {}, {}
        with open(dynamic_dependencies_file, 'r') as f:
            for line in f.readlines():
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
    if line in cached_content:
        return
    cached_content.add(line)
    with open(dynamic_dependencies_file, 'a') as f:
        f.write(line)