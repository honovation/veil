from __future__ import unicode_literals, print_function, division
from sandal.script import *
from sandal.template import *
from ...filesystem import create_file
from ...setting import get_environment_settings
from ...layout import VEIL_ETC_DIR

@script('install')
def install_veil():
    settings = get_environment_settings()
    create_file(VEIL_ETC_DIR / 'veil.cfg', get_template('veil.cfg.j2').render(config=settings.veil))