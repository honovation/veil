# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from veil.profile.web import *
from veil.profile.model import *
from const import GENDER

LOGGER = logging.getLogger(__name__)
db = register_database('vsee')

def list_persons():
    return db().list('SELECT * FROM person ORDER BY id')


@template_filter('gender')
def render_gender(value):
    return GENDER[value]
