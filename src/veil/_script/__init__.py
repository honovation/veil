from __future__ import unicode_literals, print_function, division
from sandal.template import *
from veil.script import *
from veil.layout import *
from veil.environment import create_file
from veil.environment import get_environment_settings

@script('generate-configuration')
def generate_configuration():
    settings = get_environment_settings()
    create_file(VEIL_ETC_DIR / 'veil.cfg', get_template('veil.cfg.j2').render(config=settings.veil))