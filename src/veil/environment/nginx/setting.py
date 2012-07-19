from __future__ import unicode_literals, print_function, division
from sandal.collection import *
from ..layout import VEIL_LOG_DIR, VEIL_ETC_DIR, VEIL_VAR_DIR, VEIL_HOME

NGINX_BASE_SETTINGS = objectify({
    'nginx': {
        'log_directory': VEIL_LOG_DIR / 'nginx',
        'config_file': VEIL_ETC_DIR / 'nginx.conf',
        'uploaded_files_directory': VEIL_VAR_DIR / 'uploaded-files',
        'inline_static_files_directory': VEIL_VAR_DIR / 'inline-static-files',
        'external_static_files_directory': VEIL_HOME / 'static'
    }
})
