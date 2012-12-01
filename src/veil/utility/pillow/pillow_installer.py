from __future__ import unicode_literals, print_function, division
from veil.profile.installer import *

@composite_installer
def pillow_resource():
    resources = [
        os_package_resource(name='libjpeg-dev'),
        os_package_resource(name='libfreetype6-dev'),
        python_package_resource(name='Pillow')
    ]
    return resources
