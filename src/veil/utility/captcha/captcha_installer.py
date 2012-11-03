from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *
from veil.utility.pillow import *

register_pillow_dependency_provider(lambda: install_ubuntu_package('libfreetype6-dev'))

@installation_script()
def install_captcha_component():
    install_pillow()


