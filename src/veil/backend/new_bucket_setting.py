from __future__ import unicode_literals, print_function, division

def bucket_resource(purpose, type, base_directory, base_url):
    return ('bucket', {
        'purpose': purpose,
        'config': {
            'type': type,
            'base_directory': base_directory,
            'base_url': base_url
        }
    })