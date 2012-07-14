from __future__ import unicode_literals, print_function, division

import sys
import os.path

__dir__ = os.path.dirname(__file__)
if __dir__ in sys.path:
    sys.path.remove(__dir__) # disable old style relative import

from sandal.script import execute_script
from sandal.component import scan_components
from veil.environment import VEIL_HOME

for component_name in scan_components(VEIL_HOME / 'src'):
    __import__(component_name)

execute_script(sys.argv[1:])