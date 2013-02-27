from __future__ import unicode_literals, print_function, division
from suds.client import Client
from suds.client import WebFault
from veil_installer import *
from veil_component import *
from .web_service_client_installer import load_web_service_client_config
from .web_service_client_installer import web_service_client_resource

WebFault = WebFault

instances = {} # purpose => instance

def register_web_service(purpose):
    add_application_sub_resource(
        '{}_web_service_client'.format(purpose),
        lambda config: web_service_client_resource(purpose=purpose, **config))
    loading_component_name = get_loading_component_name()
    if ('web-service', purpose) not in list_consumed_dynamic_dependencies(loading_component_name):
        raise Exception('{} can not reference web service {}'.format(loading_component_name, purpose))
    return lambda: require_web_service(purpose)


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