from __future__ import unicode_literals, print_function, division
import os

recording_file = None
cached_content = None


def start_recording_dynamic_dependencies(file):
    global recording_file
    global cached_content
    recording_file = file
    if os.path.exists(recording_file):
        with open(recording_file, 'r') as f:
            cached_content = set(f.readlines())
    else:
        cached_content = set()


def add_dynamic_dependency_provider(component_name, dynamic_dependency_type, dynamic_dependency_key):
    if not recording_file:
        return
    line = '{}<={}:{}\n'.format(component_name, dynamic_dependency_type, dynamic_dependency_key)
    record_line(line)


def add_dynamic_dependency_consumer(component_name, dynamic_dependency_type, dynamic_dependency_key):
    if not recording_file:
        return
    line = '{}=>{}:{}\n'.format(component_name, dynamic_dependency_type, dynamic_dependency_key)
    record_line(line)


def list_dynamic_dependencies(file):
    consumers = {}
    providers = {}
    if not os.path.exists(file):
        return set()
    with open(file, 'r') as f:
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
    return providers, consumers


def record_line(line):
    if line in cached_content:
        return
    cached_content.add(line)
    with open(recording_file, 'a') as f:
        f.write(line)