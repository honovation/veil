from __future__ import unicode_literals, print_function, division

def web_service_client_resource(purpose, url):
    return ('web_service_client', {
        'purpose': purpose,
        'url': url
    })