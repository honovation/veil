from __future__ import unicode_literals, print_function, division
import veil_component

veil_component.add_must_load_module(__name__)

from veil.environment.installation import *
from veil.model.collection import *

def web_service_settings(purpose, url):
    return objectify({
        'veil': {
            '{}_web_service'.format(purpose): {
                'url': url
            }
        }
    })