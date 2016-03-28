# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import lxml.objectify

from veil.model.collection import *


def parse_xml(xmltext):
    arguments = DictObject()
    root = lxml.objectify.fromstring(xmltext)
    for e in root.iterchildren():
        if e.text:
            arguments[e.tag] = e.text
    return arguments
