from .environment import get_application_components

def init_components():
    for component_name in get_application_components():
        __import__(component_name)