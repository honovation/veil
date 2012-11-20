from __future__ import unicode_literals, print_function, division
import veil_component
from veil.environment.setting import *
from suds.client import Client
from suds.client import WebFault
from .web_service_client_installer import load_web_service_client_config

WebFault = WebFault

instances = {} # purpose => instance
dependencies = {}

def register_web_service(purpose):
    dependencies.setdefault(veil_component.get_loading_component_name(), set()).add(purpose)
    return lambda: require_web_service(purpose)


def check_web_service_dependencies(component_names, expected_dependencies):
    component_name_prefix = ''.join(component_names)
    actual_dependencies = set()
    for component_name, component_dependencies in dependencies.items():
        if component_name.startswith(component_name_prefix):
            actual_dependencies = actual_dependencies.union(component_dependencies)
    unexpected_dependencies = actual_dependencies - set(expected_dependencies)
    if unexpected_dependencies:
        raise Exception('{} should not reference web service {}'.format(component_name_prefix, unexpected_dependencies))
    unreal_dependencies = set(expected_dependencies) - actual_dependencies
    if unreal_dependencies:
        raise Exception('{} did not reference web service {}'.format(component_name_prefix, unreal_dependencies))


def require_web_service(purpose):
    if purpose not in instances:
        config = load_web_service_client_config(purpose)
        suds_client = Client(config.url)
        instances[purpose] = WebService(suds_client)
    return instances[purpose]


class WebService(object):
    def __init__(self, suds_client):
        self.suds_client = suds_client

    def new_object_of_type(self, wsdl_type):
        return self.suds_client.factory.create(wsdl_type)

    def __getattr__(self, item):
        return getattr(self.suds_client.service, item)