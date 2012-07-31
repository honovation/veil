from __future__ import unicode_literals, print_function, division
import os
from veil.backend.path import *
from veil.frontend.cli import *
from veil.model.test import *

CURRENT_DIR = path(os.path.dirname(__file__))

@script('self-check')
def self_check():
    test_package('veil.')