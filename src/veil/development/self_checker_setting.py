from __future__ import unicode_literals, print_function, division
from veil.environment import *

def self_checker_settings():
    if 'test' != VEIL_SERVER:
        return {}
    return {
        'self_checker': {
            'architecture': 'veil.development.architecture.check_architecture',
            'encapsulation': 'veil.development.architecture.check_encapsulation',
            'live-document': 'veil.development.live_document.check_live_document',
            'loc': 'veil.development.loc.check_loc',
            'correctness': 'veil.development.test.check_correctness'
        }
    }