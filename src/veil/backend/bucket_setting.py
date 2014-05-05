from __future__ import unicode_literals, print_function, division

def bucket_location(base_directory):
    return {
        '_': '''
            alias {}/;
            access_log off;
            expires max;
            if ($query_string !~ "v=.+") {{
                expires 4h;
            }}
            '''.format(base_directory)
    }