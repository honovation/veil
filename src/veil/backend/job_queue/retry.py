# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division

from tasktiger.exceptions import StopRetry


def _discrete(retry, delay_list):
    if retry > len(delay_list):
        raise StopRetry()
    return delay_list[retry - 1]


def discrete(delay_list):
    if delay_list:
        return (_discrete, (delay_list, ))
    else:
        return None
