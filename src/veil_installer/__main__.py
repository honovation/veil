from __future__ import unicode_literals, print_function, division
import sys
import logging
from .installer import install_resource

logging.basicConfig(level=logging.DEBUG)
component_name = sys.argv[1]
is_dry_run = False
if len(sys.argv) > 2 and '--dry-run' == sys.argv[2]:
    is_dry_run = True
install_resource(is_dry_run, ('component', dict(name=component_name)))

