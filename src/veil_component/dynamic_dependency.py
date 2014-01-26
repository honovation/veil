from __future__ import unicode_literals, print_function, division
from .environment import VEIL_HOME

# dynamic dependency recorded and manually maintained to reflect
# relationship between components other than direct import

DEP_DYNAMIC_RECORDED = VEIL_HOME / 'DEP-DYNAMIC-RECORDED'
DEP_DYNAMIC_MANUAL = VEIL_HOME / 'DEP-DYNAMIC-MANUAL'
is_recording = False
dynamic_dependencies = None
loaded_providers = set()

def start_recording_dynamic_dependencies():
    global is_recording
    is_recording = True


def record_dynamic_dependency_provider(component_name, dynamic_dependency_type, dynamic_dependency_key):
    if should_record(component_name):
        line = '{}<={}:{}'.format(component_name, dynamic_dependency_type, dynamic_dependency_key)
        record_line(line)


def record_dynamic_dependency_consumer(component_name, dynamic_dependency_type, dynamic_dependency_key):
    if should_record(component_name):
        line = '{}=>{}:{}'.format(component_name, dynamic_dependency_type, dynamic_dependency_key)
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


def list_consumed_dynamic_dependencies(component_name):
    providers, consumers = list_dynamic_dependencies()
    return consumers.get(component_name) or []


def should_record(component_name):
    return component_name and is_recording


def list_dynamic_dependencies():
    global dynamic_dependencies
    if not dynamic_dependencies:
        providers = {}
        consumers = {}
        read_from_file(DEP_DYNAMIC_RECORDED, providers, consumers)
        read_from_file(DEP_DYNAMIC_MANUAL, providers, consumers)
        dynamic_dependencies = providers, consumers
    return dynamic_dependencies


def read_from_file(file_path, providers, consumers):
    if not file_path.exists():
        return
    for line in file_path.lines(encoding='UTF-8'):
        line = line.strip()
        if not line:
            continue
        if '=>' in line:
            consumer, type_and_key = [x.strip() for x in line.split('=>')]
            consumers.setdefault(consumer, set()).add(tuple(x.strip() for x in type_and_key.split(':')))
        elif '<=' in line:
            provider, type_and_key = [x.strip() for x in line.split('<=')]
            providers.setdefault(tuple(x.strip() for x in type_and_key.split(':')), set()).add(provider)
        else:
            raise Exception('invalid dynamic dependencies file: {}\n{}'.format(file_path, line))


lines = []

def record_line(line):
    global lines
    if line not in lines:
        lines = DEP_DYNAMIC_RECORDED.lines(encoding='UTF-8', retain=False) if DEP_DYNAMIC_RECORDED.exists() else []
        if line not in lines:
            lines.append(line)
            DEP_DYNAMIC_RECORDED.write_text('\n'.join(sorted(lines)), encoding='UTF-8')