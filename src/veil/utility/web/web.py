# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
from user_agents import parse

WEIXIN_USER_AGENT_MARK = 'MicroMessenger'


def is_mobile_device(user_agent):
    if user_agent is None:
        user_agent = ''
    return parse(user_agent).is_mobile


def is_web_spider(user_agent):
    if user_agent is None:
        user_agent = ''
    return parse(user_agent).is_bot


def is_ajax_request(request):
    return request and request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def is_weixin_request(request):
    user_agent = request.headers.get('user-agent')
    return user_agent and WEIXIN_USER_AGENT_MARK in user_agent
