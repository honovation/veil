from __future__ import unicode_literals, print_function, division
from veil_component import *

def bucket_location(base_directory, valid_referers):
    return {
        '_': """
            access_log off;
            expires max;
            if ($query_string !~* "v=(.+)") {
                expires 7d;
                add_header Pragma public;
                add_header Cache-Control "public, must-revalidate, proxy-revalidate";
            }
            if ($uri ~* "\.(gif|png|jpe?g|ico|css|js|pdf|txt|csv|xls|doc|ppt|zip|tgz|gz|rar|swf|flv|mp3|mp4|mpeg|mpg|mpeg4|avi|wmv)$") {
                valid_referers none blocked server_names {};
                if ($invalid_referer) {
                    return 403;
                }
            }
            """.format(valid_referers),
        'alias': as_path(base_directory) / ''
    }