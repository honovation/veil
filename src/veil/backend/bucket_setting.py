from __future__ import unicode_literals, print_function, division


def bucket_location(base_directory, valid_referer_domains=None):
    if valid_referer_domains:
        stop_referring = '''
            valid_referers none blocked {};
            if ($invalid_referer) {{
                return 403;
            }}
            '''.format(valid_referer_domains)
    else:
        stop_referring = ''
    return {
        '_': '''
            {}
            alias {}/;
            access_log off;
            expires max;
            if ($query_string !~ "v=.+") {{
                expires 4h;
            }}
            '''.format(stop_referring, base_directory)
    }