from __future__ import unicode_literals, print_function, division
from veil.frontend.cli import *
from .launcher import start_website

@script('up')
def bring_up_website(website):
    start_website(website)