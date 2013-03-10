from __future__ import unicode_literals, print_function, division
from veil_component import *

def bucket_location(base_directory):
    return {
        '_': """
            access_log off;
            expires max;
            if ($query_string !~* "v=(.+)") {
                expires 7d;
                add_header Pragma public;
                add_header Cache-Control "public, must-revalidate, proxy-revalidate";
            }
            """,
        'alias': as_path(base_directory) / ''
    }