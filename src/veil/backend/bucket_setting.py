from __future__ import unicode_literals, print_function, division
from veil.utility.path import *

def bucket_location(base_directory):
    return {
        '_': """
            if ($args ~* v=(.+)) {
                expires max;
            }
            """,
        'alias': as_path(base_directory) / ''
    }