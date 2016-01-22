# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from veil.utility.encoding import *
from user_agents import parse


def is_mobile(user_agents):
    ua = parse(to_str(user_agents))
    return ua.is_mobile
