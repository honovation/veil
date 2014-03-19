from __future__ import unicode_literals, print_function, division
from veil.profile.setting import *
from __env_development__ import ENV_DEVELOPMENT
from __env_test__ import ENV_TEST

CODEBASE = 'git@github.com:honovation/vsee.git'

ENVIRONMENTS = merge_multiple_settings(ENV_DEVELOPMENT, ENV_TEST)