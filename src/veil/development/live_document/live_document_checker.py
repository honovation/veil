from __future__ import unicode_literals, print_function, division
from veil.environment import *

def check_live_document():
    for doc in get_application_live_document().walkfiles('*.py'):
        exec(compile(doc.text(), doc, 'exec'))