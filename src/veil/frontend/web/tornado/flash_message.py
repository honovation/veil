# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from veil.frontend.template import *

from .cookie import get_secure_cookie, clear_cookie, set_secure_cookie

FLASH_COOKIE_NAME = 'vfm'


def set_flash_message(message):
    set_secure_cookie(name=FLASH_COOKIE_NAME, value=message)


@template_utility
def clear_and_return_flash_message():
    message = get_secure_cookie(FLASH_COOKIE_NAME, default='')
    if message:
        clear_cookie(FLASH_COOKIE_NAME)
    return message
