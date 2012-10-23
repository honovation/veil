from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.model.collection import *
from veil.frontend.web import *
from veil.environment import *


def bucket_settings(bucket, website):
    return objectify({
        'veil': {
            '{}_bucket'.format(bucket): {
                'type': 'filesystem',
                'base_directory': VEIL_VAR_DIR / bucket.replace('_', '-'),
                'website': website
            }
        }
    })


def add_bucket_reverse_proxy_static_file_locations(settings):
    new_settings = settings
    for key, value in settings.veil.items():
        if key.endswith('_bucket'):
            bucket = key.replace('_bucket', '')
            website = value.website
            static_file_location_settings = nginx_reverse_proxy_static_file_location_settings(
                settings, website, '/{}/'.format(bucket.replace('_', '-')), value.base_directory)
            new_settings = merge_settings(new_settings, static_file_location_settings)
            new_settings.veil[key].base_url = 'http://{}/{}'.format(
                get_reverse_proxy_url(new_settings, website), bucket.replace('_', '-'))
    return new_settings


def get_reverse_proxy_url(settings, website):
    website_config = get_website_config(settings, website)
    if 80 == int(website_config.domain_port):
        return website_config.domain
    else:
        return '{}:{}'.format(website_config.domain, website_config.domain_port)


def get_website_config(settings, website):
    veil_config = getattr(settings, 'veil', None)
    if not veil_config:
        raise Exception('veil is not defined in settings')
    website_config = getattr(settings.veil, '{}_website'.format(website), None)
    if not website_config:
        raise Exception('website {} is not defined in settings'.format(website))
    return website_config