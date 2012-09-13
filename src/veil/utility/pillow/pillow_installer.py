from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *

dependency_providers = []

def register_pillow_dependency_provider(dependency_provider):
    dependency_providers.append(dependency_provider)


def install_pillow():
    for dependency_provider in dependency_providers:
        dependency_provider()
    install_python_package('pillow')
