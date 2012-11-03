from __future__ import unicode_literals, print_function, division
from veil.model.collection import *

def web_service_settings(purpose, url):
    return objectify({
        'veil': {
            '{}_web_service'.format(purpose): {
                'url': url
            }
        }
    })