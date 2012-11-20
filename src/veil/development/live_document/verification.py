# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import traceback
from .browser import report_error

def verify(value):
    if not value:
        traceback.print_stack()
        report_error('验证失败')

