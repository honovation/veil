from __future__ import unicode_literals, print_function, division
import re
from suds.client import Client
from suds.client import WebFault
from suds.sudsobject import Object
from veil_installer import *
from veil_component import *
from veil.model.collection import *
from .web_service_client_installer import web_service_client_config
from .web_service_client_installer import web_service_client_resource

Object = Object

instances = {} # purpose => instance

def register_web_service(purpose):
    add_application_sub_resource('{}_web_service_client'.format(purpose), lambda config: web_service_client_resource(purpose=purpose, **config))
    loading_component_name = get_loading_component_name()
    if ('web-service', purpose) not in list_consumed_dynamic_dependencies(loading_component_name):
        raise Exception('{} can not reference web service {}'.format(loading_component_name, purpose))
    return lambda: require_web_service(purpose)


def require_web_service(purpose):
    if purpose not in instances:
        config = web_service_client_config(purpose)
        if config.user:
            instances[purpose] = WebService(config.url, username=config.user, password=config.password, proxy_netloc=config.proxy_netloc)
        else:
            instances[purpose] = WebService(config.url, proxy_netloc=config.proxy_netloc)
    return instances[purpose]


RE_NETLOC = re.compile(br'(?<=//)[^/]+(?=/)')

class WebService(object):
    def __init__(self, url, username=None, password=None, proxy_netloc=None):
        self.timeout = 180 # default suds transport timeout is 90 seconds
        faults = True # raise faults raised by server, else return tuple from service method invocation as (httpcode, object).
        if username:
            self.suds_client = Client(url, username=username, password=password, timeout=self.timeout, faults=faults)
        else:
            self.suds_client = Client(url, timeout=self.timeout, faults=faults)
        self.proxy_netloc = str(proxy_netloc) if proxy_netloc else None

    def new_object_of_type(self, wsdl_type, returns_dict_object=False):
        suds_object = self.suds_client.factory.create(wsdl_type)
        if returns_dict_object:
            return DictObject(self.suds_client.dict(suds_object))
        return suds_object

    def last_sent(self):
        return self.suds_client.last_sent()

    def last_received(self):
        return self.suds_client.last_received()

    def __getattr__(self, item):
        service = getattr(self.suds_client.service, item)
        if self.proxy_netloc:
            service.method.location = RE_NETLOC.sub(self.proxy_netloc, service.method.location, count=1)
        return service


def log_web_fault(exception_info, logger):
    type, value, tb = exception_info
    if isinstance(value, WebFault):
        logger.error('web fault: %(faultstring)s', {'faultstring': value.fault.faultstring})
    return exception_info
