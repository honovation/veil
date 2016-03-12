# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from user_agents import parse

from veil.utility.memoize import *

WEIXIN_USER_AGENT_MARK = 'MicroMessenger'


@memoize(maxsize=2 ** 15, timeout=60 * 20)
def parse_user_agent(user_agent):
    return parse(user_agent or '')


def is_mobile_device(user_agent):
    return parse_user_agent(user_agent).is_mobile


def is_web_spider(user_agent):
    return parse_user_agent(user_agent).is_bot


def is_ajax_request(request):
    return request and request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def is_weixin_request(request):
    user_agent = request.headers.get('user-agent')
    return user_agent and WEIXIN_USER_AGENT_MARK in user_agent
