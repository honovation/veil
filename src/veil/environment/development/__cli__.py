from __future__ import unicode_literals, print_function, division
import os
from sandal.test import *
from sandal.path import *
from veil.frontend.cli import *

CURRENT_DIR = path(os.path.dirname(__file__))

@script('self-check')
def self_check():
    test_package('veil.')