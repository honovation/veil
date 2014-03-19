# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.profile.web import *
from vsee.feature.person import *

person_route = route_for('person')


@person_route('GET', '/')
def operator_list_page():
    return get_template('person-list-page.html').render(persons=list_persons())