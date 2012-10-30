from __future__ import unicode_literals, print_function, division
import veil_component
from veil.environment.setting import *
from suds.client import Client
from suds.client import WebFault

WebFault = WebFault

registry = {} # purpose => get_web+service_options
instances = {} # purpose => instance
dependencies = {}

def register_web_service(purpose):
    dependencies.setdefault(veil_component.get_loading_component().__name__, set()).add(purpose)
    if purpose not in registry:
        registry[purpose] = register_web_service_options(purpose)
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


def register_web_service_options(purpose):
    section = '{}_web_service'.format(purpose) # for example contact_index_database
    get_url = register_option(section, 'url')

    def get_web_service_options():
        return {
            'url': get_url()
        }

    return get_web_service_options


def require_web_service(purpose):
    if purpose not in registry:
        raise Exception('web service for purpose {} is not registered'.format(purpose))
    if purpose not in instances:
        web_service_options = registry[purpose]()
        suds_client = Client(web_service_options['url'])
        instances[purpose] = WebService(suds_client)
    return instances[purpose]


class WebService(object):
    def __init__(self, suds_client):
        self.suds_client = suds_client

    def new_object_of_type(self, wsdl_type):
        return self.suds_client.factory.create(wsdl_type)

    def __getattr__(self, item):
        return getattr(self.suds_client.service, item)