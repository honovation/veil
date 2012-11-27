from __future__ import unicode_literals, print_function, division
from veil.utility.path import *

def bucket_resource(purpose, type, base_directory, base_url):
    return ('veil.backend.bucket.bucket_resource', {
        'purpose': purpose,
        'config': {
            'type': type,
            'base_directory': base_directory,
            'base_url': base_url
        }
    })


def bucket_location(base_directory):
    return {
        '_': """
            if ($args ~* v=(.+)) {
                expires 365d;
            }
            """,
        'alias': as_path(base_directory) / ''
    }