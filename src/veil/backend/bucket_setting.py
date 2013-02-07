from __future__ import unicode_literals, print_function, division
from veil.utility.path import *

def bucket_location(base_directory):
    return {
        '_': """
            expires max;
            if ($args !~* v=(.+)) {
                expires 7d;
                add_header Pragma public;
                add_header Cache-Control "public, must-revalidate, proxy-revalidate";
            }
            """,
        'alias': as_path(base_directory) / ''
    }