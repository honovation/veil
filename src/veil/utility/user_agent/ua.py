# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from user_agents import parse


def is_mobile_device(user_agent):
    return parse(user_agent).is_mobile


def is_web_spider(user_agent):
    return parse(user_agent).is_bot
