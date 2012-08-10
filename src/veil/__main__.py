from __future__ import unicode_literals, print_function, division
import sys
from veil import init_components
from veil.frontend.cli import execute_script

init_components()
execute_script(*sys.argv[1:])