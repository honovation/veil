from __future__ import unicode_literals, print_function, division
from veil_installer import *

@composite_installer('pillow')
def install_pillow():
    resources = [
        os_package_resource('libjpeg-dev'),
        os_package_resource('libfreetype6-dev'),
        python_package_resource('Pillow')
    ]
    return [], resources
