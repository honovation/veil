# -*- coding: UTF-8 -*-
"""
Usually there are two redis instances for every veil application per their persistence attributes: 'persist_store' and 'memory_cache'
In order to avoid key conflicts, all redis keys for the veil application are defined in this module
"""
from __future__ import unicode_literals, print_function, division


# SECTION: persistent_store

# captcha in veil
# def captcha_redis_key(challenge_code):
#     return 'CAPTCHA:{}'.format(challenge_code)


# user tracking in veil
# def logged_in_user_id_key(session):
#     return 'lu:{}:{}'.format(session.purpose, session.browser_code)


# person
