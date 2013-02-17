from __future__ import unicode_literals, print_function, division
from suds.client import Client
from suds.client import WebFault
import veil_component
from veil_installer import *
from .web_service_client_installer import load_web_service_client_config
from .web_service_client_installer import web_service_client_resource

WebFault = WebFault

instances = {} # purpose => instance
dependencies = {}

def register_web_service(purpose):
    add_application_sub_resource(
        '{}_web_service_client'.format(purpose),
        lambda config: web_service_client_resource(purpose=purpose, **config))
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
        instances[purpose] = WebService(config.url)
    return instances[purpose]


class WebService(object):
    def __init__(self, url):
        self.suds_client = Client(url, timeout=180) # default suds transport timeout is 90 seconds
        self.service_url = str(url.replace('?wsdl', '')) # to work around erp tunnel port not preserved bug

    def new_object_of_type(self, wsdl_type):
        return self.suds_client.factory.create(wsdl_type)

    def __getattr__(self, item):
        service = getattr(self.suds_client.service, item)
        service.method.location = self.service_url
        return service