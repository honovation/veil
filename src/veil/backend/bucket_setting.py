from __future__ import unicode_literals, print_function, division
from veil.environment.setting import *
from veil.model.collection import *
from veil.frontend.website_setting import get_website_nginx_server_name
from veil.frontend.nginx_setting import nginx_server_static_file_location_settings
from veil.environment import *

def init():
    register_settings_coordinator(add_bucket_reverse_proxy_static_file_locations)


def bucket_settings(bucket, website, base_directory=None, base_url=None):
    return objectify({
        '{}_bucket'.format(bucket): {
            'type': 'filesystem',
            'base_directory': base_directory or VEIL_VAR_DIR / bucket.replace('_', '-'),
            'website': website,
            'base_url': base_url
        }
    })


def get_bucket_options(purpose):
    config = get_settings()['{}_bucket'.format(purpose)]
    return objectify({
        'type': config.type,
        'base_directory': config.base_directory,
        'base_url': config.base_url
    })


def add_bucket_reverse_proxy_static_file_locations(settings):
    new_settings = settings
    for key, value in settings.items():
        if key.endswith('_bucket'):
            bucket = key.replace('_bucket', '')
            website = value.website
            static_file_location_settings = nginx_server_static_file_location_settings(
                settings, get_website_nginx_server_name(new_settings, website),
                '/{}/'.format(bucket.replace('_', '-')), value.base_directory)
            new_settings = merge_settings(new_settings, static_file_location_settings)
            new_settings = merge_settings(new_settings, {
                key: {
                    'base_url': 'http://{}/{}'.format(
                        get_reverse_proxy_url(new_settings, website), bucket.replace('_', '-'))
                }
            })
    return new_settings


def get_reverse_proxy_url(settings, website):
    website_config = get_website_config(settings, website)
    if 80 == int(website_config.domain_port):
        return website_config.domain
    else:
        return '{}:{}'.format(website_config.domain, website_config.domain_port)


def get_website_config(settings, website):
    website_config = getattr(settings, '{}_website'.format(website), None)
    if not website_config:
        raise Exception('website {} is not defined in settings'.format(website))
    return website_config

init()