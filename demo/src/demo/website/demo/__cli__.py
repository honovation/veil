from __future__ import unicode_literals, print_function, division
from veil.frontend.web import *
from veil.frontend.cli import *

@script('up')
def bring_up_demo():
    start_website(website='DEMO')