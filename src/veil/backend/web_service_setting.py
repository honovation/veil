from __future__ import unicode_literals, print_function, division
from veil.model.collection import *
from veil.environment.setting import *

def web_service_settings(purpose, url):
    return objectify({
        '{}_web_service'.format(purpose): {
            'url': url
        }
    })

def get_web_service_options(purpose):
    config = get_settings()['{}_web_service'.format(purpose)]
    return objectify({
        'url': config.url
    })