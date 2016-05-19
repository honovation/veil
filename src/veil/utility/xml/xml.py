# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

import lxml.objectify
from veil.model.collection import *


def parse_xml(xmltext):
    root = lxml.objectify.fromstring(xmltext)
    return parse_object(root)


def parse_object(obj):
    arguments = DictObject()
    for e in obj.iterchildren():
        if e.countchildren() > 0:
            arguments[e.tag] = parse_object(e)
        else:
            arguments[e.tag] = e.text
    return arguments
